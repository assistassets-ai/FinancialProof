import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  availableLocales,
  catalogs,
  getDateLocale,
  getLocale,
  setLocale,
  t,
} from "../i18n.mjs";

import { formatTimestamp, normalizeWorkspace } from "../library.mjs";

describe("catalog parity", () => {
  const deKeys = Object.keys(catalogs.de).sort();
  const enKeys = Object.keys(catalogs.en).sort();

  it("DE and EN catalogs have the same keys", () => {
    assert.deepStrictEqual(deKeys, enKeys);
  });

  it("no empty values in DE catalog", () => {
    for (const [key, value] of Object.entries(catalogs.de)) {
      assert.ok(typeof value === "string" && value.length > 0, `DE key "${key}" is empty`);
    }
  });

  it("no empty values in EN catalog", () => {
    for (const [key, value] of Object.entries(catalogs.en)) {
      assert.ok(typeof value === "string" && value.length > 0, `EN key "${key}" is empty`);
    }
  });
});

describe("t() function", () => {
  it("returns DE string when locale is de", () => {
    setLocale("de");
    assert.equal(t("hero.demo"), "Demo laden");
  });

  it("returns EN string when locale is en", () => {
    setLocale("en");
    assert.equal(t("hero.demo"), "Load Demo");
    setLocale("de");
  });

  it("falls back to key for unknown keys", () => {
    assert.equal(t("nonexistent.key.xyz"), "nonexistent.key.xyz");
  });

  it("ignores invalid locale in setLocale", () => {
    setLocale("de");
    setLocale("xx");
    assert.equal(getLocale(), "de");
  });
});

describe("locale utilities", () => {
  it("availableLocales returns de and en", () => {
    const locales = availableLocales();
    assert.ok(locales.includes("de"));
    assert.ok(locales.includes("en"));
  });

  it("getDateLocale maps de → de-DE", () => {
    setLocale("de");
    assert.equal(getDateLocale(), "de-DE");
  });

  it("getDateLocale maps en → en-US", () => {
    setLocale("en");
    assert.equal(getDateLocale(), "en-US");
    setLocale("de");
  });
});

describe("formatTimestamp locale support", () => {
  const isoDate = "2026-05-30T10:00:00+02:00";

  it("formats with de-DE locale", () => {
    const result = formatTimestamp(isoDate, "de-DE");
    assert.ok(result.includes("2026"), `Expected year in output: ${result}`);
    assert.ok(result.length > 5, `Expected formatted date, got: ${result}`);
  });

  it("formats with en-US locale", () => {
    const result = formatTimestamp(isoDate, "en-US");
    assert.ok(result.includes("2026"), `Expected year in output: ${result}`);
    assert.ok(result.length > 5, `Expected formatted date, got: ${result}`);
  });

  it("de-DE and en-US produce different output for the same date", () => {
    const de = formatTimestamp(isoDate, "de-DE");
    const en = formatTimestamp(isoDate, "en-US");
    assert.notEqual(de, en, `Expected different formats: DE="${de}" EN="${en}"`);
  });

  it("defaults to de-DE when no locale is passed", () => {
    const withDefault = formatTimestamp(isoDate);
    const withExplicit = formatTimestamp(isoDate, "de-DE");
    assert.equal(withDefault, withExplicit);
  });
});

describe("UTF-8 smoke tests — data integrity across scripts", () => {
  it("German umlauts survive normalizeWorkspace roundtrip", () => {
    const workspace = normalizeWorkspace({
      schema: "financialproof-workspace-v1",
      app: { name: "FP", version: "1.0" },
      legal: { not_financial_advice: true },
      watchlist: [{ symbol: "TEST", display_name: "Ölpreisüberwachung", notes: "Größe prüfen — Ärger vermeiden" }],
      analysis_presets: [],
      analysis_snapshots: [],
    });
    assert.equal(workspace.watchlist[0].display_name, "Ölpreisüberwachung");
    assert.ok(workspace.watchlist[0].notes.includes("Größe"));
    assert.ok(workspace.watchlist[0].notes.includes("Ärger"));
  });

  it("CJK characters survive normalizeWorkspace roundtrip (zh-Hans)", () => {
    const workspace = normalizeWorkspace({
      schema: "financialproof-workspace-v1",
      app: { name: "FP", version: "1.0" },
      legal: { not_financial_advice: true },
      watchlist: [{ symbol: "TEST", display_name: "上海指数", notes: "观察中国市场走势" }],
      analysis_presets: [],
      analysis_snapshots: [],
    });
    assert.equal(workspace.watchlist[0].display_name, "上海指数");
    assert.equal(workspace.watchlist[0].notes, "观察中国市场走势");
  });

  it("Japanese characters survive normalizeWorkspace roundtrip (JA)", () => {
    const workspace = normalizeWorkspace({
      schema: "financialproof-workspace-v1",
      app: { name: "FP", version: "1.0" },
      legal: { not_financial_advice: true },
      watchlist: [{ symbol: "NIKKEI", display_name: "日経平均株価", notes: "東京証券取引所" }],
      analysis_presets: [],
      analysis_snapshots: [],
    });
    assert.equal(workspace.watchlist[0].display_name, "日経平均株価");
    assert.equal(workspace.watchlist[0].notes, "東京証券取引所");
  });

  it("Cyrillic characters survive normalizeWorkspace roundtrip (RU)", () => {
    const workspace = normalizeWorkspace({
      schema: "financialproof-workspace-v1",
      app: { name: "FP", version: "1.0" },
      legal: { not_financial_advice: true },
      watchlist: [{ symbol: "MOEX", display_name: "Московская биржа", notes: "Индекс российского рынка" }],
      analysis_presets: [],
      analysis_snapshots: [],
    });
    assert.equal(workspace.watchlist[0].display_name, "Московская биржа");
    assert.equal(workspace.watchlist[0].notes, "Индекс российского рынка");
  });

  it("Spanish accented characters survive normalizeWorkspace roundtrip (ES)", () => {
    const workspace = normalizeWorkspace({
      schema: "financialproof-workspace-v1",
      app: { name: "FP", version: "1.0" },
      legal: { not_financial_advice: true },
      watchlist: [{ symbol: "IBEX", display_name: "Índice Bursátil Español", notes: "Análisis histórico según parámetros" }],
      analysis_presets: [],
      analysis_snapshots: [],
    });
    assert.equal(workspace.watchlist[0].display_name, "Índice Bursátil Español");
    assert.ok(workspace.watchlist[0].notes.includes("Análisis"));
    assert.ok(workspace.watchlist[0].notes.includes("parámetros"));
  });

  it("mixed-script snapshot summary and warnings survive normalization", () => {
    const workspace = normalizeWorkspace({
      schema: "financialproof-workspace-v1",
      app: { name: "FP", version: "1.0" },
      legal: { not_financial_advice: true },
      watchlist: [],
      analysis_presets: [],
      analysis_snapshots: [{
        symbol: "MIX",
        summary: "Analyse für 日本語 und Кириллица — résumé",
        warnings: ["Achtung: 警告 · Внимание · señal de advertencia"],
      }],
    });
    const snapshot = workspace.analysis_snapshots[0];
    assert.ok(snapshot.summary.includes("日本語"));
    assert.ok(snapshot.summary.includes("Кириллица"));
    assert.ok(snapshot.summary.includes("résumé"));
    assert.ok(snapshot.warnings[0].includes("警告"));
    assert.ok(snapshot.warnings[0].includes("Внимание"));
    assert.ok(snapshot.warnings[0].includes("advertencia"));
  });
});
