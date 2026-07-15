/** Strip tier prefix (smoke/, judge/) for UI display; keeps full id for API/keys. */
export function formatScenarioDisplayName(scenarioId: string): string {
  return scenarioId.replace(/^(?:smoke|judge)\//, "");
}
