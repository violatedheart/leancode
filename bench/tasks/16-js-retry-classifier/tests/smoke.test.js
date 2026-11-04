const test = require('node:test');
const assert = require('node:assert/strict');
const { requestWithRetry } = require('../retry');

test('request entry point exists', () => {
  assert.equal(typeof requestWithRetry, 'function');
});
