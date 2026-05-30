import test from "node:test";
import assert from "node:assert/strict";

import {
  buildFilterOptions,
  createDemoWorkspace,
  matchesWorkspaceFilters,
  normalizeWorkspace,
  parseWorkspace,
} from "../library.mjs";

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
