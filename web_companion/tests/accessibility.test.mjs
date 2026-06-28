import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");

test("Dateiimport nutzt fokussierbaren Trigger, Live-Status und verstecktes File-Input", () => {
  const html = readFileSync(join(ROOT, "index.html"), "utf8");

  assert.match(html, /id="file-trigger"/);
  assert.match(html, /aria-describedby="file-selection"/);
  assert.match(html, /id="file-selection" class="file-selection" aria-live="polite"/);
  assert.match(html, /id="file-input"[\s\S]*tabindex="-1"/);
  assert.match(html, /id="file-input"[\s\S]*aria-hidden="true"/);
});

test("Companion-Skript aktualisiert Dateistatus und öffnet das versteckte Input gezielt", () => {
  const script = readFileSync(join(ROOT, "app.mjs"), "utf8");

  assert.match(script, /const FILE_TRIGGER = document\.querySelector\("#file-trigger"\);/);
  assert.match(script, /const FILE_SELECTION = document\.querySelector\("#file-selection"\);/);
  assert.match(script, /FILE_TRIGGER\.addEventListener\("click", \(\) => \{\s*FILE_INPUT\.click\(\);/s);
  assert.match(script, /FILE_SELECTION\.textContent\s*=\s*t\("status\.noFile"\)/);
  assert.match(script, /FILE_SELECTION\.textContent\s*=.*t\("feedback\.fileSelected"\)/);
});

test("Fokuszustände bleiben für Tastaturnutzung sichtbar", () => {
  const css = readFileSync(join(ROOT, "app.css"), "utf8");

  assert.match(css, /button:focus-visible/);
  assert.match(css, /input\[type="search"\]:focus-visible/);
  assert.match(css, /select:focus-visible/);
  assert.match(css, /textarea:focus-visible/);
});
