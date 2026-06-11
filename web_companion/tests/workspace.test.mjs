import test from "node:test";
import assert from "node:assert/strict";

import {
  buildFilterOptions,
  createDemoWorkspace,
  matchesWorkspaceFilters,
  normalizeWorkspace,
  parseWorkspace,
} from "../library.mjs";

test("normalizeWorkspace sortiert Snapshot ohne created_at ans Ende (nicht Jahr-2000-Bug)", () => {
  // Vergleichs-Datum vor Jahr 2000: altes Date.parse(created_at || 0) würde
  // leeres created_at als Jahr 2000 (≈946681200000) > 1990 einordnen und falsch
  // an den Anfang stellen. Neues (Date.parse(created_at) || 0) gibt 0 → Ende.
  const workspace = normalizeWorkspace({
    schema: "financialproof-workspace-v1",
    app: { name: "FP", version: "t" },
    legal: { not_financial_advice: true },
    watchlist: [],
    analysis_presets: [],
    analysis_snapshots: [
      { symbol: "AAPL", created_at: null, summary: "leer" },
      { symbol: "MSFT", created_at: "1990-01-01T00:00:00Z", summary: "vor-2000" },
    ],
  });

  assert.equal(workspace.analysis_snapshots[0].summary, "vor-2000");
  assert.equal(workspace.analysis_snapshots[1].summary, "leer");
});

test("normalizeWorkspace akzeptiert gültigen Workspace und sortiert Snapshots absteigend", () => {
  const workspace = normalizeWorkspace({
    schema: "financialproof-workspace-v1",
    app: {
      name: "FinancialProof",
      version: "test",
      exported_at: "2026-05-30T11:00:00+02:00",
      source: "desktop",
    },
    legal: {
      disclaimer_hash: "abc",
      not_financial_advice: true,
    },
    watchlist: [
      { symbol: "msft", display_name: "Microsoft", asset_type: "stock" },
      { symbol: "aapl", display_name: "Apple", asset_type: "stock" },
    ],
    analysis_presets: [],
    analysis_snapshots: [
      { symbol: "AAPL", created_at: "2026-05-29T11:00:00+02:00", summary: "alt" },
      { symbol: "AAPL", created_at: "2026-05-30T11:00:00+02:00", summary: "neu" },
    ],
  });

  assert.equal(workspace.watchlist[0].symbol, "AAPL");
  assert.equal(workspace.analysis_snapshots[0].summary, "neu");
});

test("parseWorkspace lehnt unbekanntes Schema ab", () => {
  assert.throws(
    () => parseWorkspace(JSON.stringify({
      schema: "other",
      app: {},
      legal: {},
    })),
    /Unbekanntes Schema/,
  );
});

test("parseWorkspace lehnt kaputte Top-Level-Listen sichtbar ab", () => {
  assert.throws(
    () => parseWorkspace(JSON.stringify({
      schema: "financialproof-workspace-v1",
      app: {},
      legal: { not_financial_advice: true },
      watchlist: {},
      analysis_presets: [],
      analysis_snapshots: [],
    })),
    /watchlist muss eine Liste sein/,
  );
});

test("normalizeWorkspace lehnt leere Symbole in der Watchlist ab", () => {
  assert.throws(
    () => normalizeWorkspace({
      schema: "financialproof-workspace-v1",
      app: {},
      legal: { not_financial_advice: true },
      watchlist: [{ symbol: "   " }],
      analysis_presets: [],
      analysis_snapshots: [],
    }),
    /watchlist\[0\]\.symbol darf nicht leer sein/,
  );
});

test("normalizeWorkspace lehnt nicht endliche Snapshot-Confidence ab", () => {
  assert.throws(
    () => normalizeWorkspace({
      schema: "financialproof-workspace-v1",
      app: {},
      legal: { not_financial_advice: true },
      watchlist: [],
      analysis_presets: [],
      analysis_snapshots: [{ symbol: "AAPL", confidence: "NaN" }],
    }),
    /analysis_snapshots\[0\]\.confidence muss eine endliche Zahl sein/,
  );
});

test("normalizeWorkspace toleriert unbekannte Zusatzfelder bei gültigem Vertrag", () => {
  const workspace = normalizeWorkspace({
    schema: "financialproof-workspace-v1",
    app: {
      name: "FinancialProof",
      version: "test",
      source: "desktop",
      unknown_field: "bleibt ignoriert",
    },
    legal: {
      disclaimer_hash: "abc",
      not_financial_advice: true,
      warnings: ["Nur lokal lesen."],
      another_unknown_field: true,
    },
    watchlist: [{ symbol: "aapl", extra: "ok" }],
    analysis_presets: [{ name: "Basis", rules: { unknown: true } }],
    analysis_snapshots: [{ symbol: "AAPL", unknown: { nested: true } }],
    root_unknown: { ok: true },
  });

  assert.equal(workspace.watchlist[0].symbol, "AAPL");
  assert.equal(workspace.analysis_presets[0].name, "Basis");
  assert.equal(workspace.analysis_snapshots[0].confidence, 0);
});

test("createDemoWorkspace liefert mobile Companion-Daten mit Warnhinweisen", () => {
  const workspace = createDemoWorkspace();

  assert.equal(workspace.schema, "financialproof-workspace-v1");
  assert.ok(workspace.watchlist.length >= 2);
  assert.ok(workspace.legal.warnings.some((warning) => warning.includes("Anlageberatung")));
});

test("Filter berücksichtigen Suche, Asset-Typ und Musterklasse", () => {
  const workspace = normalizeWorkspace(createDemoWorkspace());
  const filtered = matchesWorkspaceFilters(workspace, {
    query: "bitcoin",
    assetType: "CRYPTO",
    patternClass: "neutral",
  });

  assert.equal(filtered.watchlist.length, 1);
  assert.equal(filtered.watchlist[0].symbol, "BTC-USD");
  assert.equal(filtered.analysis_snapshots.length, 1);
  assert.equal(filtered.analysis_snapshots[0].pattern_class, "neutral");
});

test("buildFilterOptions sammelt Asset-Typen und Musterklassen", () => {
  const workspace = normalizeWorkspace(createDemoWorkspace());
  const options = buildFilterOptions(workspace);

  assert.ok(options.assetTypes.includes("CRYPTO"));
  assert.ok(options.assetTypes.includes("ETF"));
  assert.ok(options.patternClasses.includes("bullish"));
});
