import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  createDemoWorkspace,
  filteredToJson,
  matchesWorkspaceFilters,
  normalizeWorkspace,
  parseWorkspace,
  snapshotsToCsv,
  watchlistToCsv,
} from "../library.mjs";

import { catalogs } from "../i18n.mjs";

// --- Hilfsfunktion: leere Filter ---
function noFilter() {
  return { query: "", assetType: "", patternClass: "" };
}

// --- watchlistToCsv ---

describe("watchlistToCsv", () => {
  it("gibt bei leerer Liste nur die Header-Zeile zurück", () => {
    const csv = watchlistToCsv([]);
    const lines = csv.split("\r\n");
    assert.equal(lines.length, 1);
    assert.ok(lines[0].includes("Symbol"), `Header muss 'Symbol' enthalten: ${lines[0]}`);
  });

  it("enthält alle Pflicht-Spalten im Header", () => {
    const csv = watchlistToCsv([]);
    assert.ok(csv.includes("Symbol"));
    assert.ok(csv.includes("Name"));
    assert.ok(csv.includes("Asset-Typ"));
    assert.ok(csv.includes("Notiz"));
    assert.ok(csv.includes("Erstellt"));
  });

  it("exportiert Watchlist-Einträge korrekt", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    const csv = watchlistToCsv(workspace.watchlist);
    const lines = csv.split("\r\n");
    // Header + mindestens 2 Datenzeilen
    assert.ok(lines.length >= 3, `Erwartet >= 3 Zeilen, erhalten: ${lines.length}`);
    // AAPL muss in einer Zeile vorkommen (Watchlist ist nach Symbol sortiert)
    assert.ok(lines.some((line) => line.includes("AAPL")));
  });

  it("neutralisiert CSV-Injection bei '=' am Zeilenanfang", () => {
    const item = {
      symbol: "=CMD",
      display_name: "Injection-Test",
      asset_type: "STOCK",
      notes: "=SUM(1+2)",
      created_at: "2026-01-01T00:00:00Z",
    };
    const csv = watchlistToCsv([item]);
    // Injizierte Formeln dürfen NICHT ungeschützt beginnen
    assert.ok(!csv.includes(',"=CMD"'), `Ungeschützte Formel gefunden: ${csv}`);
    assert.ok(!csv.includes(',"=SUM'), `Ungeschützte Formel gefunden: ${csv}`);
    // Tab-Präfix muss vorhanden sein
    assert.ok(csv.includes("\t=CMD") || csv.includes('\t='), `Tab-Präfix fehlt: ${csv}`);
  });

  it("neutralisiert CSV-Injection bei '+', '-', '@', '|' am Zeilenanfang", () => {
    const items = ["+plus", "-minus", "@at", "|pipe"].map((sym) => ({
      symbol: sym,
      display_name: sym,
      asset_type: "STOCK",
      notes: "",
      created_at: "",
    }));
    const csv = watchlistToCsv(items);
    // Kein unkodiertes Formelzeichen am Zellenanfang
    assert.ok(!csv.match(/",\+|",\-|",@|",\|/), `Ungeschützte Formelzeichen: ${csv}`);
  });

  it("escaped Semikolon und doppelte Anführungszeichen in Zellwerten", () => {
    const item = {
      symbol: "TEST",
      display_name: 'Name mit "Anführungszeichen"',
      asset_type: "STOCK",
      notes: "Notiz; mit Semikolon",
      created_at: "",
    };
    const csv = watchlistToCsv([item]);
    // Doppelte Anführungszeichen werden als "" escaped
    assert.ok(csv.includes('""Anführungszeichen""'), `Escape fehlt: ${csv}`);
    // Semikolon in Anführungszeichen eingeschlossen (kein nacktes ;)
    const dataLine = csv.split("\r\n")[1];
    assert.ok(dataLine.includes('"Notiz; mit Semikolon"'), `Semikolon-Escaping fehlt: ${dataLine}`);
  });

  it("kein UTF-8-BOM im reinen CSV-String (BOM liegt Verantwortung beim Download)", () => {
    const csv = watchlistToCsv([]);
    assert.ok(!csv.startsWith("﻿"), "BOM darf nicht im reinen CSV-String sein");
  });
});

// --- snapshotsToCsv ---

describe("snapshotsToCsv", () => {
  it("gibt bei leerer Liste nur die Header-Zeile zurück", () => {
    const csv = snapshotsToCsv([]);
    const lines = csv.split("\r\n");
    assert.equal(lines.length, 1);
    assert.ok(lines[0].includes("Symbol"));
  });

  it("enthält alle Pflicht-Spalten im Header", () => {
    const csv = snapshotsToCsv([]);
    assert.ok(csv.includes("Symbol"));
    assert.ok(csv.includes("Musterklasse"));
    assert.ok(csv.includes("Confidence"));
    assert.ok(csv.includes("RSI"));
    assert.ok(csv.includes("MACD"));
    assert.ok(csv.includes("Zusammenfassung"));
  });

  it("exportiert Snapshot-Einträge korrekt", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    const csv = snapshotsToCsv(workspace.analysis_snapshots);
    const lines = csv.split("\r\n");
    assert.ok(lines.length >= 2, `Erwartet >= 2 Zeilen, erhalten: ${lines.length}`);
    assert.ok(lines.some((line) => line.includes("AAPL") || line.includes("BTC")));
  });

  it("setzt fehlende Indicators auf leere Zeichenkette", () => {
    const snapshot = {
      symbol: "XYZ",
      timeframe: "1m",
      created_at: "",
      summary: "Test",
      pattern_class: "neutral",
      confidence: 0.5,
      indicators: {},
      warnings: [],
    };
    const csv = snapshotsToCsv([snapshot]);
    // Drei Indicator-Zellen sollen als "" erscheinen
    const dataLine = csv.split("\r\n")[1];
    assert.ok(dataLine, "Datenzeile fehlt");
    // Vier aufeinanderfolgende Semikolon-getrennte leere Zellen für rsi/macd/vol
    assert.ok(dataLine.includes('"";"";"";'), `Leere Indicator-Zellen fehlen: ${dataLine}`);
  });

  it("kein UTF-8-BOM im reinen CSV-String", () => {
    const csv = snapshotsToCsv([]);
    assert.ok(!csv.startsWith("﻿"), "BOM darf nicht im reinen CSV-String sein");
  });
});

// --- filteredToJson ---

describe("filteredToJson", () => {
  it("gibt validen JSON-String zurück der schema-Feld enthält", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    const filtered = matchesWorkspaceFilters(workspace, noFilter());
    const json = filteredToJson(workspace, filtered);
    const parsed = JSON.parse(json);
    assert.equal(parsed.schema, "financialproof-workspace-v1");
  });

  it("setzt app.source auf 'companion-export'", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    const filtered = matchesWorkspaceFilters(workspace, noFilter());
    const json = filteredToJson(workspace, filtered);
    const parsed = JSON.parse(json);
    assert.equal(parsed.app.source, "companion-export");
  });

  it("behält legal-Abschnitt unverändert", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    const filtered = matchesWorkspaceFilters(workspace, noFilter());
    const json = filteredToJson(workspace, filtered);
    const parsed = JSON.parse(json);
    assert.ok(parsed.legal.not_financial_advice === true);
    assert.ok(Array.isArray(parsed.legal.warnings));
  });

  it("verwendet die gefilterten Listen (watchlist, presets, snapshots)", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    const filtered = matchesWorkspaceFilters(workspace, {
      query: "",
      assetType: "CRYPTO",
      patternClass: "",
    });
    const json = filteredToJson(workspace, filtered);
    const parsed = JSON.parse(json);
    // Nur Crypto-Einträge sollen in der Watchlist sein
    for (const item of parsed.watchlist) {
      assert.equal(item.asset_type, "CRYPTO", `Nicht-Crypto in Export: ${item.symbol}`);
    }
    assert.ok(parsed.watchlist.length > 0, "Gefilterte Watchlist darf nicht leer sein");
  });

  it("Ausgabe ist per parseWorkspace() re-importierbar (End-to-End-Roundtrip)", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    const filtered = matchesWorkspaceFilters(workspace, noFilter());
    const json = filteredToJson(workspace, filtered);
    // Darf nicht werfen
    const reimported = parseWorkspace(json);
    assert.equal(reimported.schema, "financialproof-workspace-v1");
    assert.ok(Array.isArray(reimported.watchlist));
    assert.ok(Array.isArray(reimported.analysis_snapshots));
  });

  it("Roundtrip mit Filter behält nur gefilterte Symbole und ist weiterhin valide", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    const filtered = matchesWorkspaceFilters(workspace, {
      query: "bitcoin",
      assetType: "",
      patternClass: "",
    });
    const json = filteredToJson(workspace, filtered);
    const reimported = parseWorkspace(json);
    assert.ok(reimported.watchlist.every((item) =>
      item.symbol.includes("BTC") || item.display_name.toLowerCase().includes("bitcoin"),
    ), "Nur Bitcoin-Einträge erwartet");
  });
});

// --- I18N-Parität: export.* Schlüssel ---

describe("i18n catalog — export.*-Parität", () => {
  const exportKeys = [
    "export.title",
    "export.description",
    "export.csvWatchlist",
    "export.csvSnapshots",
    "export.json",
    "export.noData",
    "export.downloaded",
  ];

  for (const key of exportKeys) {
    it(`DE-Katalog enthält Schlüssel '${key}'`, () => {
      assert.ok(key in catalogs.de, `DE-Katalog fehlt: ${key}`);
      assert.ok(catalogs.de[key].length > 0, `DE-Wert leer: ${key}`);
    });

    it(`EN-Katalog enthält Schlüssel '${key}'`, () => {
      assert.ok(key in catalogs.en, `EN-Katalog fehlt: ${key}`);
      assert.ok(catalogs.en[key].length > 0, `EN-Wert leer: ${key}`);
    });
  }
});
