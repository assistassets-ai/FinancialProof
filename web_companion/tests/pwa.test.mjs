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

  it("CACHE_NAME is v2", () => {
    assert.match(swSrc, /financialproof-web-companion-v2/);
  });

  it("has skipWaiting()", () => {
    assert.match(swSrc, /self\.skipWaiting\(\)/);
  });

  it("has clients.claim()", () => {
    assert.match(swSrc, /self\.clients\.claim\(\)/);
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
});
