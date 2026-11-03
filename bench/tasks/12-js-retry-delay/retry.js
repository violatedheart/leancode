export function retryDelay(attempt, baseMs = 100, maxMs = 5000) {
  return baseMs * attempt;
}
