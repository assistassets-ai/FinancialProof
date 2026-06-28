import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  createDemoWorkspace,
  normalizeWorkspace,
  SNAPSHOT_SORT_FIELDS,
  sortSnapshots,
  sortWatchlist,
  WATCHLIST_SORT_FIELDS,
} from "../library.mjs";

import { catalogs } from "../i18n.mjs";

// --- Hilfsfunktion: normalisierter Demo-Workspace ---
function demoWs() {
  return normalizeWorkspace(createDemoWorkspace());
}

// --- WATCHLIST_SORT_FIELDS ---

describe("WATCHLIST_SORT_FIELDS", () => {
  it("ist ein Array mit mindestens 4 Einträgen", () => {
    assert.ok(Array.isArray(WATCHLIST_SORT_FIELDS));
    assert.ok(WATCHLIST_SORT_FIELDS.length >= 4, `Erwartet >= 4 Felder, erhalten: ${WATCHLIST_SORT_FIELDS.length}`);
  });

  it("enthält die Felder symbol, display_name, asset_type, created_at", () => {
    const values = WATCHLIST_SORT_FIELDS.map((f) => f.value);
    assert.ok(values.includes("symbol"));
    assert.ok(values.includes("display_name"));
    assert.ok(values.includes("asset_type"));
    assert.ok(values.includes("created_at"));
  });

  it("jeder Eintrag hat ein labelKey-Feld", () => {
    for (const entry of WATCHLIST_SORT_FIELDS) {
      assert.ok(typeof entry.labelKey === "string" && entry.labelKey.length > 0,
        `labelKey fehlt oder leer: ${JSON.stringify(entry)}`);
    }
  });
});

// --- SNAPSHOT_SORT_FIELDS ---

describe("SNAPSHOT_SORT_FIELDS", () => {
  it("ist ein Array mit mindestens 4 Einträgen", () => {
    assert.ok(Array.isArray(SNAPSHOT_SORT_FIELDS));
    assert.ok(SNAPSHOT_SORT_FIELDS.length >= 4, `Erwartet >= 4 Felder, erhalten: ${SNAPSHOT_SORT_FIELDS.length}`);
  });

  it("enthält die Felder created_at, symbol, confidence, pattern_class", () => {
    const values = SNAPSHOT_SORT_FIELDS.map((f) => f.value);
    assert.ok(values.includes("created_at"));
    assert.ok(values.includes("symbol"));
    assert.ok(values.includes("confidence"));
    assert.ok(values.includes("pattern_class"));
  });

  it("jeder Eintrag hat ein labelKey-Feld", () => {
    for (const entry of SNAPSHOT_SORT_FIELDS) {
      assert.ok(typeof entry.labelKey === "string" && entry.labelKey.length > 0,
        `labelKey fehlt oder leer: ${JSON.stringify(entry)}`);
    }
  });
});

// --- sortWatchlist ---

describe("sortWatchlist — leere Liste", () => {
  it("gibt leeres Array bei leerer Eingabe zurück", () => {
    assert.deepStrictEqual(sortWatchlist([]), []);
  });
});

describe("sortWatchlist — symbol", () => {
  it("sortiert nach symbol aufsteigend", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "symbol", "asc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].symbol.localeCompare(sorted[i + 1].symbol) <= 0,
        `Reihenfolge falsch: ${sorted[i].symbol} > ${sorted[i + 1].symbol}`,
      );
    }
  });

  it("sortiert nach symbol absteigend", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "symbol", "desc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].symbol.localeCompare(sorted[i + 1].symbol) >= 0,
        `Reihenfolge falsch: ${sorted[i].symbol} < ${sorted[i + 1].symbol}`,
      );
    }
  });
});

describe("sortWatchlist — display_name", () => {
  it("sortiert nach display_name aufsteigend", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "display_name", "asc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].display_name.localeCompare(sorted[i + 1].display_name) <= 0,
        `Reihenfolge falsch: ${sorted[i].display_name} > ${sorted[i + 1].display_name}`,
      );
    }
  });

  it("sortiert nach display_name absteigend", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "display_name", "desc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].display_name.localeCompare(sorted[i + 1].display_name) >= 0,
        `Reihenfolge falsch: ${sorted[i].display_name} < ${sorted[i + 1].display_name}`,
      );
    }
  });
});

describe("sortWatchlist — asset_type", () => {
  it("sortiert nach asset_type aufsteigend", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "asset_type", "asc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].asset_type.localeCompare(sorted[i + 1].asset_type) <= 0,
        `Reihenfolge falsch: ${sorted[i].asset_type} > ${sorted[i + 1].asset_type}`,
      );
    }
  });

  it("sortiert nach asset_type absteigend", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "asset_type", "desc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].asset_type.localeCompare(sorted[i + 1].asset_type) >= 0,
        `Reihenfolge falsch: ${sorted[i].asset_type} < ${sorted[i + 1].asset_type}`,
      );
    }
  });
});

describe("sortWatchlist — created_at", () => {
  it("sortiert nach created_at aufsteigend (ältester zuerst)", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "created_at", "asc");
    for (let i = 0; i < sorted.length - 1; i++) {
      const leftTime = Date.parse(sorted[i].created_at) || 0;
      const rightTime = Date.parse(sorted[i + 1].created_at) || 0;
      assert.ok(leftTime <= rightTime, `Zeitstempel falsch geordnet: ${sorted[i].created_at} > ${sorted[i + 1].created_at}`);
    }
  });

  it("sortiert nach created_at absteigend (neuester zuerst)", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "created_at", "desc");
    for (let i = 0; i < sorted.length - 1; i++) {
      const leftTime = Date.parse(sorted[i].created_at) || 0;
      const rightTime = Date.parse(sorted[i + 1].created_at) || 0;
      assert.ok(leftTime >= rightTime, `Zeitstempel falsch geordnet: ${sorted[i].created_at} < ${sorted[i + 1].created_at}`);
    }
  });
});

describe("sortWatchlist — Seiteneffekte und Fallback", () => {
  it("mutiert das Original-Array nicht", () => {
    const ws = demoWs();
    const original = ws.watchlist.map((item) => item.symbol);
    sortWatchlist(ws.watchlist, "symbol", "desc");
    const after = ws.watchlist.map((item) => item.symbol);
    assert.deepStrictEqual(after, original, "Original-Array wurde verändert");
  });

  it("unbekanntes field fällt auf symbol-Sortierung zurück", () => {
    const ws = demoWs();
    const sorted = sortWatchlist(ws.watchlist, "unknown_field_xyz", "asc");
    // Muss eine sortierte Liste zurückgeben (kein Fehler)
    assert.ok(Array.isArray(sorted) && sorted.length === ws.watchlist.length);
    // Prüfe aufsteigende symbol-Reihenfolge (Fallback-Verhalten)
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].symbol.localeCompare(sorted[i + 1].symbol) <= 0,
        `Fallback-Sortierung nach symbol fehlgeschlagen`,
      );
    }
  });
});

// --- sortSnapshots ---

describe("sortSnapshots — leere Liste", () => {
  it("gibt leeres Array bei leerer Eingabe zurück", () => {
    assert.deepStrictEqual(sortSnapshots([]), []);
  });
});

describe("sortSnapshots — symbol", () => {
  it("sortiert nach symbol aufsteigend", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "symbol", "asc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].symbol.localeCompare(sorted[i + 1].symbol) <= 0,
        `Reihenfolge falsch: ${sorted[i].symbol} > ${sorted[i + 1].symbol}`,
      );
    }
  });

  it("sortiert nach symbol absteigend", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "symbol", "desc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].symbol.localeCompare(sorted[i + 1].symbol) >= 0,
        `Reihenfolge falsch: ${sorted[i].symbol} < ${sorted[i + 1].symbol}`,
      );
    }
  });
});

describe("sortSnapshots — confidence", () => {
  it("sortiert nach confidence aufsteigend (kleinster Wert zuerst)", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "confidence", "asc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].confidence <= sorted[i + 1].confidence,
        `Reihenfolge falsch: ${sorted[i].confidence} > ${sorted[i + 1].confidence}`,
      );
    }
  });

  it("sortiert nach confidence absteigend (größter Wert zuerst)", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "confidence", "desc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].confidence >= sorted[i + 1].confidence,
        `Reihenfolge falsch: ${sorted[i].confidence} < ${sorted[i + 1].confidence}`,
      );
    }
  });

  it("confidence-Sortierung: höchste Confidence steht bei desc an erster Stelle", () => {
    const snapshots = [
      { symbol: "A", confidence: 0.5, created_at: "", pattern_class: "neutral",
        timeframe: "1y", summary: "", indicators: {}, warnings: [] },
      { symbol: "B", confidence: 0.9, created_at: "", pattern_class: "bullish",
        timeframe: "1y", summary: "", indicators: {}, warnings: [] },
      { symbol: "C", confidence: 0.3, created_at: "", pattern_class: "bearish",
        timeframe: "1y", summary: "", indicators: {}, warnings: [] },
    ];
    const sorted = sortSnapshots(snapshots, "confidence", "desc");
    assert.equal(sorted[0].confidence, 0.9, "Höchste Confidence muss an erster Stelle stehen");
    assert.equal(sorted[sorted.length - 1].confidence, 0.3, "Niedrigste Confidence muss ans Ende");
  });
});

describe("sortSnapshots — pattern_class", () => {
  it("sortiert nach pattern_class aufsteigend", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "pattern_class", "asc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].pattern_class.localeCompare(sorted[i + 1].pattern_class) <= 0,
        `Reihenfolge falsch: ${sorted[i].pattern_class} > ${sorted[i + 1].pattern_class}`,
      );
    }
  });

  it("sortiert nach pattern_class absteigend", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "pattern_class", "desc");
    for (let i = 0; i < sorted.length - 1; i++) {
      assert.ok(
        sorted[i].pattern_class.localeCompare(sorted[i + 1].pattern_class) >= 0,
        `Reihenfolge falsch: ${sorted[i].pattern_class} < ${sorted[i + 1].pattern_class}`,
      );
    }
  });
});

describe("sortSnapshots — created_at", () => {
  it("sortiert nach created_at absteigend (neuester zuerst, Standard)", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "created_at", "desc");
    for (let i = 0; i < sorted.length - 1; i++) {
      const leftTime = Date.parse(sorted[i].created_at) || 0;
      const rightTime = Date.parse(sorted[i + 1].created_at) || 0;
      assert.ok(leftTime >= rightTime, `Zeitstempel falsch geordnet`);
    }
  });

  it("sortiert nach created_at aufsteigend (ältester zuerst)", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "created_at", "asc");
    for (let i = 0; i < sorted.length - 1; i++) {
      const leftTime = Date.parse(sorted[i].created_at) || 0;
      const rightTime = Date.parse(sorted[i + 1].created_at) || 0;
      assert.ok(leftTime <= rightTime, `Zeitstempel falsch geordnet`);
    }
  });
});

describe("sortSnapshots — Seiteneffekte und Fallback", () => {
  it("mutiert das Original-Array nicht", () => {
    const ws = demoWs();
    const original = ws.analysis_snapshots.map((s) => s.symbol);
    sortSnapshots(ws.analysis_snapshots, "symbol", "asc");
    const after = ws.analysis_snapshots.map((s) => s.symbol);
    assert.deepStrictEqual(after, original, "Original-Array wurde verändert");
  });

  it("unbekanntes field fällt auf created_at-Sortierung zurück", () => {
    const ws = demoWs();
    const sorted = sortSnapshots(ws.analysis_snapshots, "unknown_field_xyz", "desc");
    assert.ok(Array.isArray(sorted) && sorted.length === ws.analysis_snapshots.length);
    // Prüfe absteigende Zeitstempel-Reihenfolge (Fallback-Verhalten)
    for (let i = 0; i < sorted.length - 1; i++) {
      const leftTime = Date.parse(sorted[i].created_at) || 0;
      const rightTime = Date.parse(sorted[i + 1].created_at) || 0;
      assert.ok(leftTime >= rightTime, `Fallback-Sortierung nach created_at fehlgeschlagen`);
    }
  });
});

// --- I18N-Parität: sort.* Schlüssel ---

describe("i18n catalog — sort.*-Parität", () => {
  const sortKeys = [
    "sort.fieldLabel",
    "sort.dirLabel",
    "sort.asc",
    "sort.desc",
    "sort.field.symbol",
    "sort.field.name",
    "sort.field.assetType",
    "sort.field.createdAt",
    "sort.field.confidence",
    "sort.field.patternClass",
  ];

  for (const key of sortKeys) {
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
