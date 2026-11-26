const scenarios = new Map<string, string>();

/**
 * Which named case (a top-level key in `contracts/fixtures/auth/<key>.json`)
 * the handler for `key` should answer with. Unset means `"ok"`.
 */
export function setScenario(key: string, scenario: string): void {
  scenarios.set(key, scenario);
}

export function getScenario(key: string): string {
  return scenarios.get(key) ?? "ok";
}

export function resetScenarios(): void {
  scenarios.clear();
}
