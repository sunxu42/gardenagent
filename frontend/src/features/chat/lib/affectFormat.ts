import type { VadPoint } from "../types";
import { formatVad } from "./vadRadarUtils";

export function formatAffectNum(n: number, digits = 2): string {
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

export function formatVadTriple(p: VadPoint): string {
  return `V ${formatVad(p.v)} / A ${formatVad(p.a)} / D ${formatVad(p.d)}`;
}

export function deltaToneClass(value: number): string {
  if (value > 0) return "text-red-500";
  if (value < 0) return "text-emerald-500";
  return "text-muted-foreground";
}

export function shortTurnId(turnId: string): string {
  return turnId.length > 8 ? turnId.slice(0, 8) : turnId;
}

export function formatTimestamp(ms: number): string {
  if (!Number.isFinite(ms)) return "—";
  return new Date(ms).toLocaleTimeString();
}
