const LOCALE_KEY = "financialproof-locale";

export const catalogs = {
  de: {
    "hero.title": "Lokaler Reader für Watchlist und Analyse-Snapshots",
    "hero.description":
      'Dieser Companion liest nur lokale <code>financialproof-workspace-v1.json</code>-Dateien. Er lädt keine Marktdaten nach, speichert keine API-Keys und bleibt klar im Modus "historische Auswertung, keine Anlageberatung".',
    "hero.demo": "Demo laden",
    "hero.fileSelect": "Datei auswählen",

    "status.cacheChecking": "Offline-Cache wird geprüft …",
    "status.noWorkspace": "Noch kein lokaler Workspace geladen",
    "status.noFile": "Noch keine Datei ausgewählt.",
    "status.cacheActive": "Offline-Cache aktiv",
    "status.cacheUnavailable": "Kein Service Worker verfügbar",
    "status.cacheFailed": "Offline-Cache fehlgeschlagen:",
    "status.restoreDiscarded": "Lokale Wiederherstellung verworfen",

    "import.title": "Import",
    "import.description": "JSON lokal einfügen oder per Datei laden.",
    "import.button": "Text importieren",

    "legal.title": "Rechtlicher Rahmen",
    "legal.description": "Immer sichtbar, auch im Offline-Modus.",

    "summary.title": "Workspace-Überblick",
    "summary.description": "Zusammenfassung des zuletzt geladenen Exports.",
    "summary.watchlist": "Watchlist",
    "summary.presets": "Presets",
    "summary.snapshots": "Snapshots",
    "summary.export": "Export",
    "summary.watchlistDetail": "Symbole im geladenen Snapshot",
    "summary.presetsDetail": "Deskriptive Regelsets",
    "summary.snapshotsDetail": "Historische Analyseergebnisse",

    "filter.title": "Filter",
    "filter.description": "Suche über Watchlist, Presets und Snapshots.",
    "filter.search": "Suche",
    "filter.assetType": "Asset-Typ",
    "filter.patternClass": "Musterklasse",
    "filter.all": "Alle",

    "watchlist.title": "Watchlist",
    "watchlist.description": "Lokale Symbol- und Notizübersicht.",
    "watchlist.empty": "Keine Watchlist-Einträge im aktuellen Filter.",

    "presets.title": "Analyse-Presets",
    "presets.description": "Aktive Regeln und Risikohinweise im Snapshot.",
    "presets.empty": "Keine Presets im aktuellen Filter.",
    "presets.active": "Aktiv",
    "presets.inactive": "Nicht aktiv",
    "presets.minConfidence": "Min. Confidence",
    "presets.maxRsi": "Max. RSI:",
    "presets.minVolumeRatio": "Min. Volumenfaktor:",
    "presets.requiredSignals": "Pflichtsignale:",
    "presets.volatilityWarning": "Volatilitätswarnung:",
    "presets.noSignals": "keine Pflichtsignale",

    "snapshots.title": "Analyse-Snapshots",
    "snapshots.description": "Historische Auswertungen, keine Prognosen.",
    "snapshots.empty": "Keine Analyse-Snapshots im aktuellen Filter.",

    "general.noWorkspace": "Noch kein Workspace geladen.",
    "general.noNotes": "Keine Notiz hinterlegt.",
    "general.confidence": "Confidence",
    "general.class": "Klasse",
    "general.savedLocally": "lokal für Offline-Start gespeichert",

    "feedback.demoLoaded": "Demo-Workspace geladen.",
    "feedback.demoUrlLoaded": "Demo-Workspace per URL geladen.",
    "feedback.restored": "Letzter lokaler Workspace automatisch wiederhergestellt.",
    "feedback.invalidRemoved": "Gespeicherter Workspace war ungültig und wurde entfernt:",
    "feedback.importSuccess": "Workspace erfolgreich validiert und geladen:",
    "feedback.watchlistEntries": "Watchlist-Einträge",
    "feedback.snapshotEntries": "Snapshots",
    "feedback.fileSelected": "Ausgewählt:",
    "feedback.fileReadError": "Datei konnte nicht gelesen werden:",

    "source.demo": "Demo-Workspace",
    "source.demoUrl": "Demo-Workspace per URL",
    "source.restored": "Letzter lokaler Workspace",
    "source.jsonText": "JSON-Text",
    "source.file": "Datei",

    "export.title": "Gefilterter Export",
    "export.description": "Aktuelle Ansicht als Datei herunterladen.",
    "export.csvWatchlist": "Watchlist als CSV",
    "export.csvSnapshots": "Snapshots als CSV",
    "export.json": "Workspace als JSON",
    "export.noData": "Kein Workspace geladen — bitte zuerst importieren.",
    "export.downloaded": "Heruntergeladen:",
  },
  en: {
    "hero.title": "Local Reader for Watchlist and Analysis Snapshots",
    "hero.description":
      'This companion reads only local <code>financialproof-workspace-v1.json</code> files. It does not fetch market data, store API keys, and remains in "historical analysis, no investment advice" mode.',
    "hero.demo": "Load Demo",
    "hero.fileSelect": "Select File",

    "status.cacheChecking": "Checking offline cache …",
    "status.noWorkspace": "No local workspace loaded",
    "status.noFile": "No file selected.",
    "status.cacheActive": "Offline cache active",
    "status.cacheUnavailable": "No Service Worker available",
    "status.cacheFailed": "Offline cache failed:",
    "status.restoreDiscarded": "Local restore discarded",

    "import.title": "Import",
    "import.description": "Paste JSON locally or load from file.",
    "import.button": "Import Text",

    "legal.title": "Legal Framework",
    "legal.description": "Always visible, even in offline mode.",

    "summary.title": "Workspace Overview",
    "summary.description": "Summary of the last loaded export.",
    "summary.watchlist": "Watchlist",
    "summary.presets": "Presets",
    "summary.snapshots": "Snapshots",
    "summary.export": "Export",
    "summary.watchlistDetail": "Symbols in the loaded snapshot",
    "summary.presetsDetail": "Descriptive rule sets",
    "summary.snapshotsDetail": "Historical analysis results",

    "filter.title": "Filter",
    "filter.description": "Search across watchlist, presets and snapshots.",
    "filter.search": "Search",
    "filter.assetType": "Asset Type",
    "filter.patternClass": "Pattern Class",
    "filter.all": "All",

    "watchlist.title": "Watchlist",
    "watchlist.description": "Local symbol and notes overview.",
    "watchlist.empty": "No watchlist entries in the current filter.",

    "presets.title": "Analysis Presets",
    "presets.description": "Active rules and risk notes in the snapshot.",
    "presets.empty": "No presets in the current filter.",
    "presets.active": "Active",
    "presets.inactive": "Inactive",
    "presets.minConfidence": "Min. Confidence",
    "presets.maxRsi": "Max. RSI:",
    "presets.minVolumeRatio": "Min. Volume Ratio:",
    "presets.requiredSignals": "Required Signals:",
    "presets.volatilityWarning": "Volatility Warning:",
    "presets.noSignals": "no required signals",

    "snapshots.title": "Analysis Snapshots",
    "snapshots.description": "Historical analyses, no forecasts.",
    "snapshots.empty": "No analysis snapshots in the current filter.",

    "general.noWorkspace": "No workspace loaded.",
    "general.noNotes": "No notes provided.",
    "general.confidence": "Confidence",
    "general.class": "Class",
    "general.savedLocally": "saved locally for offline access",

    "feedback.demoLoaded": "Demo workspace loaded.",
    "feedback.demoUrlLoaded": "Demo workspace loaded via URL.",
    "feedback.restored": "Last local workspace automatically restored.",
    "feedback.invalidRemoved": "Stored workspace was invalid and removed:",
    "feedback.importSuccess": "Workspace successfully validated and loaded:",
    "feedback.watchlistEntries": "watchlist entries",
    "feedback.snapshotEntries": "snapshots",
    "feedback.fileSelected": "Selected:",
    "feedback.fileReadError": "Could not read file:",

    "source.demo": "Demo Workspace",
    "source.demoUrl": "Demo Workspace via URL",
    "source.restored": "Last local workspace",
    "source.jsonText": "JSON Text",
    "source.file": "File",

    "export.title": "Filtered Export",
    "export.description": "Download the current view as a file.",
    "export.csvWatchlist": "Watchlist as CSV",
    "export.csvSnapshots": "Snapshots as CSV",
    "export.json": "Workspace as JSON",
    "export.noData": "No workspace loaded — please import first.",
    "export.downloaded": "Downloaded:",
  },
};

const DATE_LOCALES = { de: "de-DE", en: "en-US" };

let locale = "de";

function detectLocale() {
  if (typeof localStorage !== "undefined") {
    try {
      const stored = localStorage.getItem(LOCALE_KEY);
      if (stored && catalogs[stored]) return stored;
    } catch (_) {}
  }
  if (typeof navigator !== "undefined") {
    const nav = (navigator.language || "de").split("-")[0].toLowerCase();
    if (catalogs[nav]) return nav;
  }
  return "de";
}

export function getLocale() {
  return locale;
}

export function getDateLocale() {
  return DATE_LOCALES[locale] ?? "de-DE";
}

export function setLocale(code) {
  if (!catalogs[code]) return;
  locale = code;
  if (typeof localStorage !== "undefined") {
    try { localStorage.setItem(LOCALE_KEY, code); } catch (_) {}
  }
  if (typeof document !== "undefined") {
    document.documentElement.lang = getDateLocale();
  }
}

export function t(key) {
  return catalogs[locale]?.[key]
    ?? catalogs.en?.[key]
    ?? catalogs.de?.[key]
    ?? key;
}

export function hydrateI18n() {
  if (typeof document === "undefined") return;
  for (const el of document.querySelectorAll("[data-i18n]")) {
    el.textContent = t(el.dataset.i18n);
  }
  for (const el of document.querySelectorAll("[data-i18n-html]")) {
    el.innerHTML = t(el.dataset.i18nHtml);
  }
  for (const el of document.querySelectorAll("[data-i18n-placeholder]")) {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  }
}

export function availableLocales() {
  return Object.keys(catalogs);
}

if (typeof navigator !== "undefined") {
  locale = detectLocale();
  if (typeof document !== "undefined") {
    document.documentElement.lang = getDateLocale();
  }
}
