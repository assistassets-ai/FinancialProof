const SCHEMA_NAME = "financialproof-workspace-v1";

const DEMO_WORKSPACE = {
  schema: SCHEMA_NAME,
  app: {
    name: "FinancialProof",
    version: "1.1-demo",
    exported_at: "2026-05-30T10:00:00+02:00",
    source: "demo",
  },
  legal: {
    disclaimer_hash: "demo-disclaimer-hash",
    disclaimer_version: "2026-05-16",
    not_financial_advice: true,
    warnings: [
      "Keine Anlageberatung; nur historische Auswertung.",
      "Keine Live-Marktdaten, Orders oder Broker-Funktionen im Companion.",
    ],
  },
  watchlist: [
    {
      symbol: "AAPL",
      asset_type: "stock",
      display_name: "Apple Inc.",
      notes: "Beobachtung für defensive Tech-Gewichtung.",
      created_at: "2026-05-28T09:12:00+02:00",
    },
    {
      symbol: "MSCI",
      asset_type: "etf",
      display_name: "MSCI World ETF",
      notes: "Langfristiger Kernbaustein.",
      created_at: "2026-05-27T14:40:00+02:00",
    },
    {
      symbol: "BTC-USD",
      asset_type: "crypto",
      display_name: "Bitcoin",
      notes: "Nur als volatile Beimischung im Blick behalten.",
      created_at: "2026-05-29T08:00:00+02:00",
    },
  ],
  analysis_presets: [
    {
      name: "ETF defensiv",
      asset_type: "ETF",
      is_active: true,
      rules: {
        pattern_rules: {
          min_confidence: 0.72,
          max_rsi: 68,
          required_signals: ["bullish"],
          min_volume_ratio: 0.9,
        },
        risk_notes: {
          max_rsi_warning: 70,
          volatility_warning_percent: 4.5,
        },
      },
    },
    {
      name: "Krypto vorsichtig",
      asset_type: "CRYPTO",
      is_active: false,
      rules: {
        pattern_rules: {
          min_confidence: 0.81,
          max_rsi: 60,
          required_signals: ["bullish", "volume_spike"],
          min_volume_ratio: 1.25,
        },
        risk_notes: {
          max_rsi_warning: 62,
          volatility_warning_percent: 8,
        },
      },
    },
  ],
  analysis_snapshots: [
    {
      symbol: "AAPL",
      timeframe: "1y",
      created_at: "2026-05-30T09:58:00+02:00",
      summary: "Historische Musteranalyse mit moderatem Momentum und neutralem RSI.",
      pattern_class: "bullish",
      confidence: 0.78,
      indicators: {
        rsi: 58.4,
        macd: 1.2,
        volatility_percent: 2.9,
      },
      warnings: [
        "Nur historische Auswertung; keine Prognose.",
      ],
    },
    {
      symbol: "BTC-USD",
      timeframe: "6m",
      created_at: "2026-05-30T09:40:00+02:00",
      summary: "Hohe Schwankung bei uneinheitlichem Signalbild.",
      pattern_class: "neutral",
      confidence: 0.54,
      indicators: {
        rsi: 63.1,
        macd: -0.4,
        volatility_percent: 7.6,
      },
      warnings: [
        "Erhöhte Volatilität im Snapshot.",
        "Keine Anlageberatung; nur historische Betrachtung.",
      ],
    },
  ],
};

function assertObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} muss ein Objekt sein`);
  }
}

function assertArray(value, label) {
  if (!Array.isArray(value)) {
    throw new Error(`${label} muss eine Liste sein`);
  }
}

function cleanText(value, fallback = "") {
  if (value === null || value === undefined) {
    return fallback;
  }
  return String(value).trim() || fallback;
}

function requireText(value, label) {
  const text = cleanText(value);
  if (!text) {
    throw new Error(`${label} darf nicht leer sein`);
  }
  return text;
}

function toIsoOrEmpty(value) {
  const text = cleanText(value);
  if (!text) {
    return "";
  }
  const parsed = new Date(text);
  return Number.isNaN(parsed.getTime()) ? text : parsed.toISOString();
}

function normalizeAssetType(value) {
  return cleanText(value, "stock").toUpperCase();
}

function normalizeWarnings(rawWarnings, fallback, label = "warnings") {
  if (rawWarnings !== undefined && rawWarnings !== null && !Array.isArray(rawWarnings)) {
    throw new Error(`${label} muss eine Liste sein`);
  }

  const values = Array.isArray(rawWarnings) ? rawWarnings : [];
  const normalized = values
    .map((entry) => cleanText(entry))
    .filter(Boolean);
  if (!normalized.length && fallback) {
    normalized.push(fallback);
  }
  return normalized;
}

function normalizeIndicators(rawIndicators, label = "indicators") {
  if (rawIndicators === undefined || rawIndicators === null) {
    return {};
  }
  assertObject(rawIndicators, label);

  const pairs = Object.entries(rawIndicators)
    .filter(([key]) => cleanText(key))
    .map(([key, value]) => [cleanText(key), value]);

  return Object.fromEntries(pairs);
}

function normalizePresetRules(rawRules, label = "rules") {
  if (rawRules === undefined || rawRules === null) {
    return {
      pattern_rules: {
        min_confidence: null,
        max_rsi: null,
        required_signals: [],
        min_volume_ratio: null,
      },
      risk_notes: {
        max_rsi_warning: null,
        volatility_warning_percent: null,
      },
    };
  }
  assertObject(rawRules, label);

  const patternRules = rawRules.pattern_rules === undefined || rawRules.pattern_rules === null
    ? {}
    : (assertObject(rawRules.pattern_rules, `${label}.pattern_rules`), rawRules.pattern_rules);
  const riskNotes = rawRules.risk_notes === undefined || rawRules.risk_notes === null
    ? {}
    : (assertObject(rawRules.risk_notes, `${label}.risk_notes`), rawRules.risk_notes);

  return {
    pattern_rules: {
      min_confidence: patternRules.min_confidence ?? null,
      max_rsi: patternRules.max_rsi ?? null,
      required_signals: Array.isArray(patternRules.required_signals)
        ? [...new Set(patternRules.required_signals.map((entry) => cleanText(entry).toLowerCase()).filter(Boolean))]
        : [],
      min_volume_ratio: patternRules.min_volume_ratio ?? null,
    },
    risk_notes: {
      max_rsi_warning: riskNotes.max_rsi_warning ?? null,
      volatility_warning_percent: riskNotes.volatility_warning_percent ?? null,
    },
  };
}

function normalizeConfidence(value, label) {
  if (value === undefined || value === null || value === "") {
    return 0;
  }

  const numericValue = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numericValue)) {
    throw new Error(`${label} muss eine endliche Zahl sein`);
  }
  return numericValue;
}

export function createDemoWorkspace() {
  return structuredClone(DEMO_WORKSPACE);
}

export function parseWorkspace(rawText) {
  const source = cleanText(rawText);
  if (!source) {
    throw new Error("Bitte zuerst JSON einfügen oder auswählen");
  }

  let parsed;
  try {
    parsed = JSON.parse(source);
  } catch (error) {
    throw new Error(`Ungültiges JSON: ${error.message}`);
  }

  return normalizeWorkspace(parsed);
}

export function normalizeWorkspace(workspace) {
  assertObject(workspace, "Workspace");

  if (workspace.schema !== SCHEMA_NAME) {
    throw new Error(
      `Unbekanntes Schema: ${cleanText(workspace.schema, "leer")} (erwartet ${SCHEMA_NAME})`,
    );
  }

  assertObject(workspace.app, "app");
  assertObject(workspace.legal, "legal");
  assertArray(workspace.watchlist, "watchlist");
  assertArray(workspace.analysis_presets, "analysis_presets");
  assertArray(workspace.analysis_snapshots, "analysis_snapshots");

  if (workspace.legal.not_financial_advice === false) {
    throw new Error("legal.not_financial_advice muss true sein");
  }

  const normalized = {
    schema: SCHEMA_NAME,
    app: {
      name: cleanText(workspace.app.name, "FinancialProof"),
      version: cleanText(workspace.app.version, "unbekannt"),
      exported_at: toIsoOrEmpty(workspace.app.exported_at),
      source: cleanText(workspace.app.source, "desktop"),
    },
    legal: {
      disclaimer_hash: cleanText(workspace.legal.disclaimer_hash, "unbekannt"),
      disclaimer_version: cleanText(workspace.legal.disclaimer_version, "unbekannt"),
      not_financial_advice: workspace.legal.not_financial_advice !== false,
      warnings: normalizeWarnings(
        workspace.legal.warnings,
        "Keine Anlageberatung; nur historische Auswertung.",
        "legal.warnings",
      ),
    },
    watchlist: workspace.watchlist
      .map((item, index) => {
          assertObject(item, "watchlist-Eintrag");
          return {
            symbol: requireText(item.symbol, `watchlist[${index}].symbol`).toUpperCase(),
            asset_type: normalizeAssetType(item.asset_type),
            display_name: cleanText(item.display_name || item.name, cleanText(item.symbol, "Ohne Namen")),
            notes: cleanText(item.notes),
            created_at: toIsoOrEmpty(item.created_at),
          };
        }),
    analysis_presets: workspace.analysis_presets
      .map((preset, index) => {
          assertObject(preset, "Preset");
          return {
            name: requireText(preset.name, `analysis_presets[${index}].name`),
            asset_type: normalizeAssetType(preset.asset_type),
            is_active: Boolean(preset.is_active),
            rules: normalizePresetRules(preset.rules, `analysis_presets[${index}].rules`),
          };
        }),
    analysis_snapshots: workspace.analysis_snapshots
      .map((snapshot, index) => {
          assertObject(snapshot, "Snapshot");
          return {
            symbol: requireText(snapshot.symbol, `analysis_snapshots[${index}].symbol`).toUpperCase(),
            timeframe: cleanText(snapshot.timeframe, "ohne Zeitraum"),
            created_at: toIsoOrEmpty(snapshot.created_at),
            summary: cleanText(snapshot.summary, "Keine Zusammenfassung hinterlegt."),
            pattern_class: cleanText(snapshot.pattern_class, "neutral").toLowerCase(),
            confidence: normalizeConfidence(
              snapshot.confidence,
              `analysis_snapshots[${index}].confidence`,
            ),
            indicators: normalizeIndicators(
              snapshot.indicators,
              `analysis_snapshots[${index}].indicators`,
            ),
            warnings: normalizeWarnings(
              snapshot.warnings,
              "Keine Anlageberatung; nur historische Auswertung.",
              `analysis_snapshots[${index}].warnings`,
            ),
          };
        }),
  };

  normalized.analysis_snapshots.sort((left, right) => {
    const leftTime = Date.parse(left.created_at) || 0;
    const rightTime = Date.parse(right.created_at) || 0;
    return rightTime - leftTime;
  });

  normalized.watchlist.sort((left, right) => left.symbol.localeCompare(right.symbol));
  normalized.analysis_presets.sort((left, right) => left.name.localeCompare(right.name));

  return normalized;
}

export function buildFilterOptions(workspace) {
  const assetTypes = new Set();
  const patternClasses = new Set();

  for (const item of workspace.watchlist) {
    assetTypes.add(item.asset_type);
  }
  for (const preset of workspace.analysis_presets) {
    assetTypes.add(preset.asset_type);
  }
  for (const snapshot of workspace.analysis_snapshots) {
    patternClasses.add(snapshot.pattern_class);
  }

  return {
    assetTypes: [...assetTypes].sort(),
    patternClasses: [...patternClasses].sort(),
  };
}

export function summarizeWorkspace(workspace, locale) {
  return [
    {
      key: "watchlist",
      label: "Watchlist",
      value: String(workspace.watchlist.length),
      detail: "Symbole im geladenen Snapshot",
    },
    {
      key: "presets",
      label: "Presets",
      value: String(workspace.analysis_presets.length),
      detail: "Deskriptive Regelsets",
    },
    {
      key: "snapshots",
      label: "Snapshots",
      value: String(workspace.analysis_snapshots.length),
      detail: "Historische Analyseergebnisse",
    },
    {
      key: "export",
      label: "Export",
      value: formatTimestamp(workspace.app.exported_at, locale),
      detail: `${workspace.app.name} ${workspace.app.version}`,
    },
  ];
}

export function formatTimestamp(value, locale = "de-DE") {
  const text = cleanText(value, "unbekannt");
  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) {
    return text;
  }
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

export function formatIndicatorValue(value) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  return cleanText(value, "–");
}

// --- CSV/JSON-Export (Pure Logic, kein DOM) ---

/**
 * Escaped einen Zellwert für CSV mit Semikolon-Delimiter.
 * - CSV-Injection-Schutz: Formeln (=, +, -, @, |) werden mit Tab-Präfix neutralisiert.
 * - Alle Zellen werden in doppelte Anführungszeichen eingeschlossen.
 */
function escapeCsvCell(value) {
  const text = String(value ?? "");
  const safe = /^[=+\-@|]/.test(text) ? `\t${text}` : text;
  return `"${safe.replace(/"/g, '""')}"`;
}

/**
 * Wandelt eine Watchlist-Liste in einen CSV-String (Semikolon-Delimiter, kein BOM).
 * Bei leerer Liste wird nur die Header-Zeile zurückgegeben.
 */
export function watchlistToCsv(items) {
  const D = ";";
  const header = ["Symbol", "Name", "Asset-Typ", "Notiz", "Erstellt"]
    .map(escapeCsvCell).join(D);
  const rows = items.map((item) =>
    [item.symbol, item.display_name, item.asset_type, item.notes, item.created_at]
      .map(escapeCsvCell).join(D),
  );
  return [header, ...rows].join("\r\n");
}

/**
 * Wandelt eine Snapshot-Liste in einen CSV-String (Semikolon-Delimiter, kein BOM).
 * Indicator-Spalten: rsi, macd, volatility_percent (feste Spalten mit Fallback "").
 */
export function snapshotsToCsv(snapshots) {
  const D = ";";
  const header = ["Symbol", "Zeitraum", "Musterklasse", "Confidence",
    "RSI", "MACD", "Volatilität %", "Erstellt", "Zusammenfassung"]
    .map(escapeCsvCell).join(D);
  const rows = snapshots.map((snapshot) =>
    [
      snapshot.symbol,
      snapshot.timeframe,
      snapshot.pattern_class,
      snapshot.confidence,
      snapshot.indicators?.rsi ?? "",
      snapshot.indicators?.macd ?? "",
      snapshot.indicators?.volatility_percent ?? "",
      snapshot.created_at,
      snapshot.summary,
    ]
      .map(escapeCsvCell).join(D),
  );
  return [header, ...rows].join("\r\n");
}

/**
 * Erzeugt einen schema-validen JSON-String aus den gefilterten Workspace-Daten.
 * Das Ergebnis kann per parseWorkspace() re-importiert werden.
 * filtered = { watchlist, presets, analysis_snapshots } (Rückgabe von matchesWorkspaceFilters).
 */
export function filteredToJson(workspace, filtered) {
  const out = {
    schema: workspace.schema,
    app: {
      ...workspace.app,
      source: "companion-export",
    },
    legal: workspace.legal,
    watchlist: filtered.watchlist,
    analysis_presets: filtered.presets,
    analysis_snapshots: filtered.analysis_snapshots,
  };
  return JSON.stringify(out, null, 2);
}

// --- Sortierung (Pure Logic, kein DOM) ---

export const WATCHLIST_SORT_FIELDS = [
  { value: "symbol", labelKey: "sort.field.symbol" },
  { value: "display_name", labelKey: "sort.field.name" },
  { value: "asset_type", labelKey: "sort.field.assetType" },
  { value: "created_at", labelKey: "sort.field.createdAt" },
];

export const SNAPSHOT_SORT_FIELDS = [
  { value: "created_at", labelKey: "sort.field.createdAt" },
  { value: "symbol", labelKey: "sort.field.symbol" },
  { value: "confidence", labelKey: "sort.field.confidence" },
  { value: "pattern_class", labelKey: "sort.field.patternClass" },
];

/**
 * Sortiert eine Watchlist-Kopie nach field und direction.
 * Mutiert das Original nicht.
 * Unbekannte field-Werte fallen auf "symbol" zurück.
 */
export function sortWatchlist(items, field = "symbol", direction = "asc") {
  const known = WATCHLIST_SORT_FIELDS.map((f) => f.value);
  const sortField = known.includes(field) ? field : "symbol";
  const sign = direction === "desc" ? -1 : 1;

  return [...items].sort((left, right) => {
    if (sortField === "created_at") {
      const leftTime = Date.parse(left.created_at) || 0;
      const rightTime = Date.parse(right.created_at) || 0;
      return sign * (leftTime - rightTime);
    }
    const leftVal = String(left[sortField] ?? "");
    const rightVal = String(right[sortField] ?? "");
    return sign * leftVal.localeCompare(rightVal);
  });
}

/**
 * Sortiert eine Snapshot-Kopie nach field und direction.
 * Mutiert das Original nicht.
 * Unbekannte field-Werte fallen auf "created_at" zurück.
 */
export function sortSnapshots(snapshots, field = "created_at", direction = "desc") {
  const known = SNAPSHOT_SORT_FIELDS.map((f) => f.value);
  const sortField = known.includes(field) ? field : "created_at";
  const sign = direction === "desc" ? -1 : 1;

  return [...snapshots].sort((left, right) => {
    if (sortField === "created_at") {
      const leftTime = Date.parse(left.created_at) || 0;
      const rightTime = Date.parse(right.created_at) || 0;
      return sign * (leftTime - rightTime);
    }
    if (sortField === "confidence") {
      return sign * ((left.confidence ?? 0) - (right.confidence ?? 0));
    }
    const leftVal = String(left[sortField] ?? "");
    const rightVal = String(right[sortField] ?? "");
    return sign * leftVal.localeCompare(rightVal);
  });
}

export function matchesWorkspaceFilters(workspace, filters) {
  const query = cleanText(filters.query).toLowerCase();
  const assetType = cleanText(filters.assetType).toUpperCase();
  const patternClass = cleanText(filters.patternClass).toLowerCase();

  return {
    watchlist: workspace.watchlist.filter((item) => {
      const haystack = `${item.symbol} ${item.display_name} ${item.notes}`.toLowerCase();
      if (assetType && item.asset_type !== assetType) {
        return false;
      }
      return !query || haystack.includes(query);
    }),
    presets: workspace.analysis_presets.filter((preset) => {
      const haystack = `${preset.name} ${preset.asset_type} ${preset.rules.pattern_rules.required_signals.join(" ")}`.toLowerCase();
      if (assetType && preset.asset_type !== assetType) {
        return false;
      }
      return !query || haystack.includes(query);
    }),
    analysis_snapshots: workspace.analysis_snapshots.filter((snapshot) => {
      const matchingWatchlist = workspace.watchlist.find((item) => item.symbol === snapshot.symbol);
      const linkedWatchlistText = matchingWatchlist
        ? `${matchingWatchlist.display_name} ${matchingWatchlist.notes}`
        : "";
      const haystack = `${snapshot.symbol} ${snapshot.summary} ${snapshot.pattern_class} ${snapshot.warnings.join(" ")} ${linkedWatchlistText}`.toLowerCase();
      if (patternClass && snapshot.pattern_class !== patternClass) {
        return false;
      }
      if (assetType) {
        if (matchingWatchlist && matchingWatchlist.asset_type !== assetType) {
          return false;
        }
      }
      return !query || haystack.includes(query);
    }),
  };
}
