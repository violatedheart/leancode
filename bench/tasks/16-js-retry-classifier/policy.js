function shouldRetry(error) {
  return Boolean(error && error.status >= 400);
}

module.exports = { shouldRetry };
