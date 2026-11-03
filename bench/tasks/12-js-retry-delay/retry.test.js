import { test } from "node:test";
import assert from "node:assert/strict";
import { retryDelay } from "./retry.js";

test("uses capped exponential backoff", () => {
  assert.deepEqual([0, 1, 2, 4, 8].map(n => retryDelay(n, 100, 500)), [100, 100, 200, 400, 500]);
  assert.equal(retryDelay(-1), 0);
});
