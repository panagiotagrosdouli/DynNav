import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");

test("research landing page exposes the core DynNav concepts", () => {
  for (const phrase of [
    "Risk-aware dynamic navigation",
    "Occupancy belief grid",
    "Uncertainty propagation",
    "Risk and recoverability fields",
    "Runtime monitor",
  ]) {
    assert.match(page, new RegExp(phrase, "i"));
  }
});

test("public claims remain explicitly scoped", () => {
  assert.match(page, /research prototype/i);
  assert.match(page, /synthetic benchmark/i);
  assert.doesNotMatch(page, /certified safety/i);
  assert.doesNotMatch(page, /hardware validated/i);
});

test("page keeps a semantic top-level main and heading hierarchy", () => {
  assert.match(page, /<main\b/);
  assert.match(page, /<h1\b/);
  assert.match(page, /<h2\b/);
});
