const { shouldRetry } = require('./policy');

async function requestWithRetry(send, maxAttempts) {
  let attempt = 0;
  while (attempt < maxAttempts) {
    try {
      return await send();
    } catch (error) {
      attempt += 1;
      if (attempt >= maxAttempts || !shouldRetry(error)) throw error;
    }
  }
}

module.exports = { requestWithRetry };
