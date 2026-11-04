const test = require('node:test');
const assert = require('node:assert/strict');
const { shouldRetry } = require('../policy');
const { requestWithRetry } = require('../retry');

test('retry only 429 and 5xx', () => {
  assert.equal(shouldRetry({ status: 429 }), true);
  assert.equal(shouldRetry({ status: 503 }), true);
  assert.equal(shouldRetry({ status: 400 }), false);
});

test('request stops at attempt limit', async () => {
  let calls = 0;
  await assert.rejects(requestWithRetry(async () => { calls++; throw { status: 503 }; }, 2));
  assert.equal(calls, 2);
});
