import {
  buildFilterOptions,
  createDemoWorkspace,
  filteredToJson,
  formatIndicatorValue,
  formatTimestamp,
  matchesWorkspaceFilters,
  normalizeWorkspace,
  parseWorkspace,
  snapshotsToCsv,
  sortSnapshots,
  sortWatchlist,
  summarizeWorkspace,
  watchlistToCsv,
} from "./library.mjs";

import {
  availableLocales,
  getDateLocale,
  getLocale,
  hydrateI18n,
  setLocale,
  t,
} from "./i18n.mjs";

const STORAGE_KEY = "financialproof-workspace-v1";

function escHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
const CACHE_STATUS = document.querySelector("#cache-status");
const RESTORE_STATUS = document.querySelector("#restore-status");
const IMPORT_FEEDBACK = document.querySelector("#import-feedback");
const EXPORT_FEEDBACK = document.querySelector("#export-feedback");
const FILE_TRIGGER = document.querySelector("#file-trigger");
const FILE_INPUT = document.querySelector("#file-input");
const FILE_SELECTION = document.querySelector("#file-selection");
const JSON_INPUT = document.querySelector("#json-input");
const SEARCH_INPUT = document.querySelector("#search-input");
const ASSET_FILTER = document.querySelector("#asset-filter");
const PATTERN_FILTER = document.querySelector("#pattern-filter");
const LANG_SELECT = document.querySelector("#lang-select");
const WATCHLIST_SORT_FIELD = document.querySelector("#watchlist-sort-field");
const WATCHLIST_SORT_DIR = document.querySelector("#watchlist-sort-dir");
const SNAPSHOTS_SORT_FIELD = document.querySelector("#snapshots-sort-field");
const SNAPSHOTS_SORT_DIR = document.querySelector("#snapshots-sort-dir");

const state = {
  workspace: null,
  filters: {
    query: "",
    assetType: "",
    patternClass: "",
  },
  watchlistSort: { field: "symbol", dir: "asc" },
  snapshotsSort: { field: "created_at", dir: "desc" },
};

function setFeedback(message, tone = "") {
  IMPORT_FEEDBACK.textContent = message;
  IMPORT_FEEDBACK.className = `feedback ${tone}`.trim();
}

function setExportFeedback(message, tone = "") {
  EXPORT_FEEDBACK.textContent = message;
  EXPORT_FEEDBACK.className = `feedback ${tone}`.trim();
}

/**
 * Löst einen Datei-Download im Browser aus.
 * Für CSV-Dateien die BOM ("﻿") in `content` voranstellen,
 * damit Excel-DE die Umlaute korrekt darstellt.
 */
function triggerDownload(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function saveWorkspace(workspace) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace)); } catch (_) {}
}

function renderLegal(workspace) {
  const container = document.querySelector("#legal-box");
  container.replaceChildren();

  const title = document.createElement("h3");
  title.textContent = workspace.legal.not_financial_advice
    ? "Keine Anlageberatung"
    : "Rechtshinweis prüfen";

  const paragraph = document.createElement("p");
  paragraph.textContent =
    "FinancialProof bleibt auch im Companion ein Werkzeug für historische, deskriptive Auswertungen. Der Reader erzeugt keine Prognosen, startet keine Trades und lädt keine Live-Marktdaten.";

  const meta = document.createElement("p");
  meta.className = "meta";
  meta.textContent = `Disclaimer-Version ${workspace.legal.disclaimer_version} · Hash ${workspace.legal.disclaimer_hash}`;

  const list = document.createElement("ul");
  list.className = "warning-list";
  for (const warning of workspace.legal.warnings) {
    const item = document.createElement("li");
    item.textContent = warning;
    list.append(item);
  }

  container.append(title, paragraph, meta, list);
}

function renderSummary(workspace) {
  const container = document.querySelector("#summary-cards");
  container.replaceChildren();

  for (const card of summarizeWorkspace(workspace, getDateLocale())) {
    const label = t(`summary.${card.key}`);
    const detail = card.key === "export" ? card.detail : t(`summary.${card.key}Detail`);
    const article = document.createElement("article");
    article.className = "summary-card";
    article.innerHTML = `
      <h3>${escHtml(label)}</h3>
      <p class="summary-number">${escHtml(card.value)}</p>
      <p>${escHtml(detail)}</p>
    `;
    container.append(article);
  }
}

function renderEmpty(containerSelector, message, className) {
  const container = document.querySelector(containerSelector);
  container.className = className;
  container.textContent = message;
}

function renderWatchlist(items) {
  const container = document.querySelector("#watchlist");
  if (!items.length) {
    renderEmpty("#watchlist", t("watchlist.empty"), "card-grid empty-state");
    return;
  }

  container.className = "card-grid";
  container.replaceChildren();

  for (const item of items) {
    const article = document.createElement("article");
    article.className = "entity-card";
    article.innerHTML = `
      <h3>${escHtml(item.symbol)}</h3>
      <p class="meta">${escHtml(item.display_name)} · ${escHtml(item.asset_type)}</p>
      <p class="tagline">${escHtml(item.notes || t("general.noNotes"))}</p>
      <div class="badge-row">
        <span class="badge">${escHtml(formatTimestamp(item.created_at, getDateLocale()))}</span>
      </div>
    `;
    container.append(article);
  }
}

function renderPresets(presets) {
  const container = document.querySelector("#presets");
  if (!presets.length) {
    renderEmpty("#presets", t("presets.empty"), "card-grid empty-state");
    return;
  }

  container.className = "card-grid";
  container.replaceChildren();

  for (const preset of presets) {
    const requiredSignals = preset.rules.pattern_rules.required_signals;
    const article = document.createElement("article");
    article.className = "entity-card";

    const signalText = requiredSignals.length ? requiredSignals.join(", ") : t("presets.noSignals");
    article.innerHTML = `
      <h3>${escHtml(preset.name)}</h3>
      <p class="meta">${escHtml(preset.asset_type)}</p>
      <div class="badge-row">
        <span class="badge ${preset.is_active ? "active" : ""}">
          ${preset.is_active ? escHtml(t("presets.active")) : escHtml(t("presets.inactive"))}
        </span>
        <span class="badge">${escHtml(t("presets.minConfidence"))} ${escHtml(preset.rules.pattern_rules.min_confidence ?? "–")}</span>
      </div>
      <ul class="rule-list">
        <li>${escHtml(t("presets.maxRsi"))} ${escHtml(preset.rules.pattern_rules.max_rsi ?? "–")}</li>
        <li>${escHtml(t("presets.minVolumeRatio"))} ${escHtml(preset.rules.pattern_rules.min_volume_ratio ?? "–")}</li>
        <li>${escHtml(t("presets.requiredSignals"))} ${escHtml(signalText)}</li>
        <li>${escHtml(t("presets.volatilityWarning"))} ${escHtml(preset.rules.risk_notes.volatility_warning_percent ?? "–")}%</li>
      </ul>
    `;
    container.append(article);
  }
}

function renderSnapshots(snapshots) {
  const container = document.querySelector("#snapshots");
  if (!snapshots.length) {
    renderEmpty("#snapshots", t("snapshots.empty"), "snapshot-list empty-state");
    return;
  }

  container.className = "snapshot-list";
  container.replaceChildren();

  for (const snapshot of snapshots) {
    const article = document.createElement("article");
    article.className = "snapshot-card";

    const indicators = document.createElement("div");
    indicators.className = "indicators";
    for (const [key, value] of Object.entries(snapshot.indicators)) {
      const row = document.createElement("div");
      row.className = "indicator-row";
      row.innerHTML = `
        <span>${escHtml(key)}</span>
        <strong>${escHtml(formatIndicatorValue(value))}</strong>
      `;
      indicators.append(row);
    }

    const warningList = document.createElement("ul");
    warningList.className = "warning-list";
    for (const warning of snapshot.warnings) {
      const item = document.createElement("li");
      item.textContent = warning;
      warningList.append(item);
    }

    article.innerHTML = `
      <h3>${escHtml(snapshot.symbol)}</h3>
      <p class="meta">${escHtml(snapshot.timeframe)} · ${escHtml(formatTimestamp(snapshot.created_at, getDateLocale()))} · ${escHtml(t("general.class"))} ${escHtml(snapshot.pattern_class)}</p>
      <div class="badge-row">
        <span class="badge">${escHtml(t("general.confidence"))} ${formatIndicatorValue(snapshot.confidence)}</span>
      </div>
      <p class="tagline">${escHtml(snapshot.summary)}</p>
    `;

    article.append(indicators, warningList);
    container.append(article);
  }
}

function populateFilters(workspace) {
  const { assetTypes, patternClasses } = buildFilterOptions(workspace);

  ASSET_FILTER.innerHTML = `<option value="">${escHtml(t("filter.all"))}</option>`;
  PATTERN_FILTER.innerHTML = `<option value="">${escHtml(t("filter.all"))}</option>`;

  for (const assetType of assetTypes) {
    const option = document.createElement("option");
    option.value = assetType;
    option.textContent = assetType;
    ASSET_FILTER.append(option);
  }

  for (const patternClass of patternClasses) {
    const option = document.createElement("option");
    option.value = patternClass;
    option.textContent = patternClass;
    PATTERN_FILTER.append(option);
  }

  ASSET_FILTER.value = state.filters.assetType;
  PATTERN_FILTER.value = state.filters.patternClass;
}

function renderWorkspace() {
  if (!state.workspace) {
    renderEmpty("#watchlist", t("general.noWorkspace"), "card-grid empty-state");
    renderEmpty("#presets", t("general.noWorkspace"), "card-grid empty-state");
    renderEmpty("#snapshots", t("general.noWorkspace"), "snapshot-list empty-state");
    document.querySelector("#summary-cards").replaceChildren();
    document.querySelector("#legal-box").replaceChildren();
    return;
  }

  renderLegal(state.workspace);
  renderSummary(state.workspace);
  populateFilters(state.workspace);

  const filtered = matchesWorkspaceFilters(state.workspace, state.filters);
  const sortedWatchlist = sortWatchlist(filtered.watchlist, state.watchlistSort.field, state.watchlistSort.dir);
  const sortedSnapshots = sortSnapshots(filtered.analysis_snapshots, state.snapshotsSort.field, state.snapshotsSort.dir);
  renderWatchlist(sortedWatchlist);
  renderPresets(filtered.presets);
  renderSnapshots(sortedSnapshots);
}

function activateWorkspace(workspace, sourceLabel) {
  state.workspace = workspace;
  saveWorkspace(workspace);
  RESTORE_STATUS.textContent = `${sourceLabel} · ${t("general.savedLocally")}`;
  renderWorkspace();
}

function importText(rawText, sourceLabel) {
  try {
    const workspace = parseWorkspace(rawText);
    activateWorkspace(workspace, sourceLabel);
    setFeedback(
      `${t("feedback.importSuccess")} ${workspace.watchlist.length} ${t("feedback.watchlistEntries")}, ${workspace.analysis_snapshots.length} ${t("feedback.snapshotEntries")}.`,
      "success",
    );
  } catch (error) {
    setFeedback(error.message, "error");
  }
}

function restoreWorkspace() {
  if (state.workspace) return;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    renderWorkspace();
    return;
  }

  try {
    activateWorkspace(normalizeWorkspace(JSON.parse(stored)), t("source.restored"));
    setFeedback(t("feedback.restored"), "success");
  } catch (error) {
    localStorage.removeItem(STORAGE_KEY);
    RESTORE_STATUS.textContent = t("status.restoreDiscarded");
    setFeedback(`${t("feedback.invalidRemoved")} ${error.message}`, "error");
  }
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    CACHE_STATUS.textContent = t("status.cacheUnavailable");
    return;
  }

  try {
    await navigator.serviceWorker.register("./sw.js");
    CACHE_STATUS.textContent = t("status.cacheActive");
  } catch (error) {
    CACHE_STATUS.textContent = `${t("status.cacheFailed")} ${error.message}`;
  }
}

function bindEvents() {
  document.querySelector("#load-demo").addEventListener("click", () => {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    JSON_INPUT.value = JSON.stringify(workspace, null, 2);
    activateWorkspace(workspace, t("source.demo"));
    setFeedback(t("feedback.demoLoaded"), "success");
  });

  FILE_TRIGGER.addEventListener("click", () => {
    FILE_INPUT.click();
  });

  FILE_TRIGGER.addEventListener("click", () => {
    FILE_INPUT.click();
  });

  document.querySelector("#import-json").addEventListener("click", () => {
    importText(JSON_INPUT.value, t("source.jsonText"));
  });

  FILE_INPUT.addEventListener("change", async (event) => {
    const [file] = event.target.files || [];
    if (!file) {
      FILE_SELECTION.textContent = t("status.noFile");
      return;
    }
    try {
      FILE_SELECTION.textContent = `${t("feedback.fileSelected")} ${file.name}`;
      JSON_INPUT.value = await file.text();
      importText(JSON_INPUT.value, `${t("source.file")} ${file.name}`);
    } catch (error) {
      FILE_SELECTION.textContent = `${t("feedback.fileReadError")} ${file.name}`;
      setFeedback(`${t("feedback.fileReadError")} ${error.message}`, "error");
    }
  });

  SEARCH_INPUT.addEventListener("input", (event) => {
    state.filters.query = event.target.value;
    renderWorkspace();
  });

  ASSET_FILTER.addEventListener("change", (event) => {
    state.filters.assetType = event.target.value;
    renderWorkspace();
  });

  PATTERN_FILTER.addEventListener("change", (event) => {
    state.filters.patternClass = event.target.value;
    renderWorkspace();
  });

  if (LANG_SELECT) {
    LANG_SELECT.value = getLocale();
    LANG_SELECT.addEventListener("change", (event) => {
      setLocale(event.target.value);
      hydrateI18n();
      renderWorkspace();
    });
  }

  if (WATCHLIST_SORT_FIELD) {
    WATCHLIST_SORT_FIELD.addEventListener("change", (event) => {
      state.watchlistSort.field = event.target.value;
      renderWorkspace();
    });
  }

  if (WATCHLIST_SORT_DIR) {
    WATCHLIST_SORT_DIR.addEventListener("change", (event) => {
      state.watchlistSort.dir = event.target.value;
      renderWorkspace();
    });
  }

  if (SNAPSHOTS_SORT_FIELD) {
    SNAPSHOTS_SORT_FIELD.addEventListener("change", (event) => {
      state.snapshotsSort.field = event.target.value;
      renderWorkspace();
    });
  }

  if (SNAPSHOTS_SORT_DIR) {
    SNAPSHOTS_SORT_DIR.addEventListener("change", (event) => {
      state.snapshotsSort.dir = event.target.value;
      renderWorkspace();
    });
  }

  document.querySelector("#export-watchlist-csv").addEventListener("click", () => {
    if (!state.workspace) {
      setExportFeedback(t("export.noData"), "error");
      return;
    }
    const filtered = matchesWorkspaceFilters(state.workspace, state.filters);
    const csv = watchlistToCsv(filtered.watchlist);
    triggerDownload("﻿" + csv, "watchlist.csv", "text/csv;charset=utf-8");
    setExportFeedback(`${t("export.downloaded")} watchlist.csv`, "success");
  });

  document.querySelector("#export-snapshots-csv").addEventListener("click", () => {
    if (!state.workspace) {
      setExportFeedback(t("export.noData"), "error");
      return;
    }
    const filtered = matchesWorkspaceFilters(state.workspace, state.filters);
    const csv = snapshotsToCsv(filtered.analysis_snapshots);
    triggerDownload("﻿" + csv, "snapshots.csv", "text/csv;charset=utf-8");
    setExportFeedback(`${t("export.downloaded")} snapshots.csv`, "success");
  });

  document.querySelector("#export-json").addEventListener("click", () => {
    if (!state.workspace) {
      setExportFeedback(t("export.noData"), "error");
      return;
    }
    const filtered = matchesWorkspaceFilters(state.workspace, state.filters);
    const json = filteredToJson(state.workspace, filtered);
    triggerDownload(json, "workspace-export.json", "application/json;charset=utf-8");
    setExportFeedback(`${t("export.downloaded")} workspace-export.json`, "success");
  });

  if (new URLSearchParams(window.location.search).get("demo") === "1") {
    const workspace = normalizeWorkspace(createDemoWorkspace());
    JSON_INPUT.value = JSON.stringify(workspace, null, 2);
    activateWorkspace(workspace, t("source.demoUrl"));
    setFeedback(t("feedback.demoUrlLoaded"), "success");
  }
}

hydrateI18n();
bindEvents();
restoreWorkspace();
registerServiceWorker();
