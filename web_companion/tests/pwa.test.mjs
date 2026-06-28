import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

const manifest = JSON.parse(readFileSync(join(root, "manifest.webmanifest"), "utf8"));
const swSrc = readFileSync(join(root, "sw.js"), "utf8");
const indexSrc = readFileSync(join(root, "index.html"), "utf8");
const appSrc = readFileSync(join(root, "app.mjs"), "utf8");
const cssSrc = readFileSync(join(root, "app.css"), "utf8");

describe("manifest — installability", () => {
  it("has display:standalone", () => {
    assert.equal(manifest.display, "standalone");
  });

  it("has start_url", () => {
    assert.ok(manifest.start_url, "start_url muss gesetzt sein");
  });

  it("has id field", () => {
    assert.ok("id" in manifest, "id-Feld fehlt (PWA-Installierbarkeit)");
  });

  it("has scope field", () => {
    assert.ok("scope" in manifest, "scope-Feld fehlt");
  });

  it("has name and short_name", () => {
    assert.ok(manifest.name, "name fehlt");
    assert.ok(manifest.short_name, "short_name fehlt");
  });
});

describe("manifest — icons", () => {
  it("declares 192x192 any-icon (PNG)", () => {
    const icon = manifest.icons.find(
      (i) => i.sizes === "192x192" && i.type === "image/png" && !i.purpose,
    );
    assert.ok(icon, "192x192 any-icon fehlt");
  });

  it("declares 512x512 any-icon (PNG)", () => {
    const icon = manifest.icons.find(
      (i) => i.sizes === "512x512" && i.type === "image/png" && !i.purpose,
    );
    assert.ok(icon, "512x512 any-icon fehlt");
  });

  it("has maskable icon", () => {
    const icon = manifest.icons.find((i) => i.purpose === "maskable");
    assert.ok(icon, "maskable-Icon fehlt");
  });

  it("all manifest icon files exist on disk", () => {
    for (const icon of manifest.icons) {
      const p = join(root, icon.src.replace(/^\.\//, ""));
      assert.ok(existsSync(p), `Icon-Datei fehlt: ${icon.src}`);
    }
  });
});

describe("service worker", () => {
  it("CACHE_NAME contains 'financialproof'", () => {
    assert.match(swSrc, /financialproof/);
  });

  it("CACHE_NAME is v5", () => {
    assert.match(swSrc, /financialproof-web-companion-v5/);
  });

  it("has skipWaiting()", () => {
    assert.match(swSrc, /self\.skipWaiting\(\)/);
  });

  it("has clients.claim()", () => {
    assert.match(swSrc, /self\.clients\.claim\(\)/);
  });

  it("uses ignoreSearch in cache lookup (query-param offline fix)", () => {
    assert.match(swSrc, /ignoreSearch\s*:\s*true/);
  });

  it("all manifest PNG icons are in SW ASSETS (offline defect fix)", () => {
    for (const icon of manifest.icons) {
      assert.ok(
        swSrc.includes(icon.src),
        `SW ASSETS fehlt: ${icon.src}`,
      );
    }
  });
});

describe("integration", () => {
  it("index.html references manifest.webmanifest", () => {
    assert.match(indexSrc, /manifest\.webmanifest/);
  });

  it("app.mjs registers sw.js", () => {
    assert.match(appSrc, /sw\.js/);
  });

  it("app.mjs definiert escHtml (XSS-Schutz für innerHTML)", () => {
    assert.match(appSrc, /function escHtml/);
  });

  it("app.mjs schützt alle innerHTML-Blöcke mit escHtml", () => {
    const inlineCount = (appSrc.match(/article\.innerHTML\s*=/g) || []).length + (appSrc.match(/row\.innerHTML\s*=/g) || []).length;
    const escHtmlCount = (appSrc.match(/escHtml\(/g) || []).length;
    assert.ok(escHtmlCount >= inlineCount, `escHtml-Aufrufe (${escHtmlCount}) sollen >= innerHTML-Blöcke (${inlineCount}) sein`);
  });

  it("app.mjs importiert i18n.mjs", () => {
    assert.match(appSrc, /from\s+["']\.\/i18n\.mjs["']/);
  });

  it("sw.js ASSETS enthält i18n.mjs", () => {
    assert.match(swSrc, /i18n\.mjs/);
  });

  it("index.html enthält lang-select Element", () => {
    assert.match(indexSrc, /id="lang-select"/);
  });

  it("app.mjs restoreWorkspace hat Guard gegen überschreiben geladener Workspaces", () => {
    assert.match(appSrc, /if \(state\.workspace\) return/);
  });

  it("app.mjs Demo-Button normalisiert Workspace (konsistente Sortierung beim Erstladen)", () => {
    assert.match(appSrc, /normalizeWorkspace\(createDemoWorkspace\(\)\)/);
  });
});

describe("iOS Safari installability", () => {
  it("index.html: viewport meta enthält viewport-fit=cover", () => {
    assert.match(indexSrc, /viewport-fit\s*=\s*cover/);
  });

  it("index.html: apple-touch-icon Link vorhanden und zeigt auf PNG", () => {
    assert.match(indexSrc, /rel="apple-touch-icon"/);
    assert.match(indexSrc, /apple-touch-icon.*\.png/s);
  });

  it("apple-touch-icon-180.png existiert und ist 180×180", () => {
    const iconPath = join(root, "icons", "apple-touch-icon-180.png");
    assert.ok(existsSync(iconPath), "icons/apple-touch-icon-180.png fehlt");
    const buf = readFileSync(iconPath);
    const width = buf.readUInt32BE(16);
    const height = buf.readUInt32BE(20);
    assert.equal(width, 180, `Breite muss 180 sein, ist ${width}`);
    assert.equal(height, 180, `Höhe muss 180 sein, ist ${height}`);
  });

  it("index.html: apple-mobile-web-app-title gesetzt", () => {
    assert.match(indexSrc, /apple-mobile-web-app-title/);
  });

  it("index.html: apple-mobile-web-app-status-bar-style ist default", () => {
    assert.match(indexSrc, /apple-mobile-web-app-status-bar-style/);
    assert.match(indexSrc, /content="default"/);
  });

  it("app.css: safe-area-inset auf allen vier Seiten (Notch-Schutz)", () => {
    assert.match(cssSrc, /safe-area-inset-top/);
    assert.match(cssSrc, /safe-area-inset-bottom/);
    assert.match(cssSrc, /safe-area-inset-left/);
    assert.match(cssSrc, /safe-area-inset-right/);
  });

  it("app.css: Button-Elemente haben min-height von 44px (Apple HIG)", () => {
    assert.match(cssSrc, /min-height\s*:\s*44px/);
  });

  it("sw.js ASSETS enthält apple-touch-icon-180.png", () => {
    assert.match(swSrc, /apple-touch-icon-180\.png/);
  });
});

describe("bugfix-library-transfer W1/W2 (2026-06-20)", () => {
  it("W1: sw.js fetch(event.request) hat .catch() — Offline-Fallback statt unhandled rejection", () => {
    assert.match(swSrc, /fetch\(event\.request\)\.catch\(/,
      "fetch(event.request) muss .catch() haben um Offline-Fehler sauber abzufangen");
  });

  it("W2: app.mjs localStorage.setItem ist in try/catch eingeschlossen (QuotaExceededError/SecurityError)", () => {
    assert.match(appSrc, /try\s*\{\s*localStorage\.setItem\(/,
      "localStorage.setItem muss in try/catch sein — Safari Private/Firefox Full-Storage wirft sonst Exception");
  });
});
