import { test } from "node:test";
import assert from "node:assert/strict";
import { slugify } from "./slug.js";

test("normalizes accents and punctuation", () => {
  assert.equal(slugify("Crème brûlée & Tea!"), "creme-brulee-tea");
});
