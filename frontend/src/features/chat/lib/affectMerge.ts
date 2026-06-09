import type { AffectTurnRecord, VadPoint } from "../types";

export function computeVadDelta(after: VadPoint, base: VadPoint): VadPoint {
  return {
    v: after.v - base.v,
    a: after.a - base.a,
    d: after.d - base.d,
  };
}

export function upsertAffectRecord(
  history: AffectTurnRecord[],
  record: AffectTurnRecord,
  max = 30,
): AffectTurnRecord[] {
  const without = history.filter((h) => h.turnId !== record.turnId);
  return [record, ...without].slice(0, max);
}

export function baseAgentVadForDelta(
  history: AffectTurnRecord[],
  turnId: string,
  currentAgentVad: VadPoint | null,
  fallback: VadPoint,
): VadPoint {
  const existingIndex = history.findIndex((item) => item.turnId === turnId);
  if (existingIndex >= 0) {
    return (
      history[existingIndex + 1]?.agentVadAfter ??
      currentAgentVad ??
      history[existingIndex]?.agentVadAfter ??
      fallback
    );
  }
  return history[0]?.agentVadAfter ?? currentAgentVad ?? fallback;
}
