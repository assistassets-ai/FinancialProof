import {
  buildFilterOptions,
  createDemoWorkspace,
  formatIndicatorValue,
  formatTimestamp,
  matchesWorkspaceFilters,
  normalizeWorkspace,
  parseWorkspace,
  summarizeWorkspace,
} from "./library.mjs";

const STORAGE_KEY = "financialproof-workspace-v1";
const CACHE_STATUS = document.querySelector("#cache-status");
const RESTORE_STATUS = document.querySelector("#restore-status");
const IMPORT_FEEDBACK = document.querySelector("#import-feedback");
const FILE_INPUT = document.querySelector("#file-input");
const JSON_INPUT = document.querySelector("#json-input");
const SEARCH_INPUT = document.querySelector("#search-input");
const ASSET_FILTER = document.querySelector("#asset-filter");
const PATTERN_FILTER = document.querySelector("#pattern-filter");

const state = {
  workspace: null,
  filters: {
    query: "",
    assetType: "",
    patternClass: "",
  },
};

function setFeedback(message, tone = "") {
  IMPORT_FEEDBACK.textContent = message;
  IMPORT_FEEDBACK.className = `feedback ${tone}`.trim();
}

function saveWorkspace(workspace) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace));
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

  for (const card of summarizeWorkspace(workspace)) {
    const article = document.createElement("article");
    article.className = "summary-card";
    article.innerHTML = `
      <h3>${card.label}</h3>
      <p class="summary-number">${card.value}</p>
      <p>${card.detail}</p>
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
    renderEmpty("#watchlist", "Keine Watchlist-Einträge im aktuellen Filter.", "card-grid empty-state");
    return;
  }

  container.className = "card-grid";
  container.replaceChildren();

  for (const item of items) {
    const article = document.createElement("article");
    article.className = "entity-card";
    article.innerHTML = `
      <h3>${item.symbol}</h3>
      <p class="meta">${item.display_name} · ${item.asset_type}</p>
      <p class="tagline">${item.notes || "Keine Notiz hinterlegt."}</p>
      <div class="badge-row">
        <span class="badge">${formatTimestamp(item.created_at)}</span>
      </div>
    `;
    container.append(article);
  }
}

function renderPresets(presets) {
  const container = document.querySelector("#presets");
  if (!presets.length) {
    renderEmpty("#presets", "Keine Presets im aktuellen Filter.", "card-grid empty-state");
    return;
  }

  container.className = "card-grid";
  container.replaceChildren();

  for (const preset of presets) {
    const requiredSignals = preset.rules.pattern_rules.required_signals;
    const article = document.createElement("article");
    article.className = "entity-card";

    const signalText = requiredSignals.length ? requiredSignals.join(", ") : "keine Pflichtsignale";
    article.innerHTML = `
      <h3>${preset.name}</h3>
      <p class="meta">${preset.asset_type}</p>
      <div class="badge-row">
        <span class="badge ${preset.is_active ? "active" : ""}">
          ${preset.is_active ? "Aktiv" : "Nicht aktiv"}
        </span>
        <span class="badge">Min. Confidence ${preset.rules.pattern_rules.min_confidence ?? "–"}</span>
      </div>
      <ul class="rule-list">
        <li>Max. RSI: ${preset.rules.pattern_rules.max_rsi ?? "–"}</li>
        <li>Min. Volumenfaktor: ${preset.rules.pattern_rules.min_volume_ratio ?? "–"}</li>
        <li>Pflichtsignale: ${signalText}</li>
        <li>Volatilitätswarnung: ${preset.rules.risk_notes.volatility_warning_percent ?? "–"}%</li>
      </ul>
    `;
    container.append(article);
  }
}

function renderSnapshots(snapshots) {
  const container = document.querySelector("#snapshots");
  if (!snapshots.length) {
    renderEmpty("#snapshots", "Keine Analyse-Snapshots im aktuellen Filter.", "snapshot-list empty-state");
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
        <span>${key}</span>
        <strong>${formatIndicatorValue(value)}</strong>
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
      <h3>${snapshot.symbol}</h3>
      <p class="meta">${snapshot.timeframe} · ${formatTimestamp(snapshot.created_at)} · Klasse ${snapshot.pattern_class}</p>
      <div class="badge-row">
        <span class="badge">Confidence ${formatIndicatorValue(snapshot.confidence)}</span>
      </div>
      <p class="tagline">${snapshot.summary}</p>
    `;

    article.append(indicators, warningList);
    container.append(article);
  }
}

function populateFilters(workspace) {
  const { assetTypes, patternClasses } = buildFilterOptions(workspace);

  ASSET_FILTER.innerHTML = '<option value="">Alle</option>';
  PATTERN_FILTER.innerHTML = '<option value="">Alle</option>';

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
    renderEmpty("#watchlist", "Noch kein Workspace geladen.", "card-grid empty-state");
    renderEmpty("#presets", "Noch kein Workspace geladen.", "card-grid empty-state");
    renderEmpty("#snapshots", "Noch kein Workspace geladen.", "snapshot-list empty-state");
    document.querySelector("#summary-cards").replaceChildren();
    document.querySelector("#legal-box").replaceChildren();
    return;
  }

  renderLegal(state.workspace);
  renderSummary(state.workspace);
  populateFilters(state.workspace);

  const filtered = matchesWorkspaceFilters(state.workspace, state.filters);
  renderWatchlist(filtered.watchlist);
  renderPresets(filtered.presets);
  renderSnapshots(filtered.analysis_snapshots);
}

function activateWorkspace(workspace, sourceLabel) {
  state.workspace = workspace;
  saveWorkspace(workspace);
  RESTORE_STATUS.textContent = `${sourceLabel} · lokal für Offline-Start gespeichert`;
  renderWorkspace();
}

function importText(rawText, sourceLabel) {
  try {
    const workspace = parseWorkspace(rawText);
    activateWorkspace(workspace, sourceLabel);
    setFeedback(`Workspace erfolgreich geladen: ${workspace.watchlist.length} Watchlist-Einträge, ${workspace.analysis_snapshots.length} Snapshots.`, "success");
  } catch (error) {
    setFeedback(error.message, "error");
  }
}

function restoreWorkspace() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    renderWorkspace();
    return;
  }

  try {
    activateWorkspace(normalizeWorkspace(JSON.parse(stored)), "Letzter lokaler Workspace");
    setFeedback("Letzter lokaler Workspace automatisch wiederhergestellt.", "success");
  } catch (error) {
    localStorage.removeItem(STORAGE_KEY);
    RESTORE_STATUS.textContent = "Lokale Wiederherstellung verworfen";
    setFeedback(`Gespeicherter Workspace war ungültig und wurde entfernt: ${error.message}`, "error");
  }
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    CACHE_STATUS.textContent = "Kein Service Worker verfügbar";
    return;
  }

  try {
    await navigator.serviceWorker.register("./sw.js");
    CACHE_STATUS.textContent = "Offline-Cache aktiv";
  } catch (error) {
    CACHE_STATUS.textContent = `Offline-Cache fehlgeschlagen: ${error.message}`;
  }
}

function bindEvents() {
  document.querySelector("#load-demo").addEventListener("click", () => {
    const workspace = createDemoWorkspace();
    JSON_INPUT.value = JSON.stringify(workspace, null, 2);
    activateWorkspace(workspace, "Demo-Workspace");
    setFeedback("Demo-Workspace geladen.", "success");
  });

  document.querySelector("#import-json").addEventListener("click", () => {
    importText(JSON_INPUT.value, "JSON-Text");
  });

  FILE_INPUT.addEventListener("change", async (event) => {
    const [file] = event.target.files || [];
    if (!file) {
      return;
    }
    JSON_INPUT.value = await file.text();
    importText(JSON_INPUT.value, `Datei ${file.name}`);
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

  if (new URLSearchParams(window.location.search).get("demo") === "1") {
    const workspace = createDemoWorkspace();
    JSON_INPUT.value = JSON.stringify(workspace, null, 2);
    activateWorkspace(workspace, "Demo-Workspace per URL");
    setFeedback("Demo-Workspace per URL geladen.", "success");
  }
}

bindEvents();
restoreWorkspace();
registerServiceWorker();
