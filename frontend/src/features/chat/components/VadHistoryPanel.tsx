import { useState } from "react";
import type { VadHistoryItem, VadPoint } from "../types";
import { formatVad, getPrevAgentVad } from "../lib/vadRadarUtils";
import { VadRadarChart } from "./VadRadarChart";

interface VadHistoryPanelProps {
  history?: VadHistoryItem[];
  currentAgentVad?: VadPoint | null;
  baselineVad?: VadPoint | null;
}

function deltaClassName(value: number): string {
  if (value > 0) return "text-red-500";
  if (value < 0) return "text-emerald-500";
  return "text-muted-foreground";
}

function VadTriple({ label, point }: { label: string; point: VadPoint }) {
  return (
    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
      <span className="text-muted-foreground">{label}</span>
      <span>
        V {formatVad(point.v)} / A {formatVad(point.a)} / D {formatVad(point.d)}
      </span>
    </div>
  );
}

export function VadHistoryPanel({ history, currentAgentVad, baselineVad }: VadHistoryPanelProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const safeHistory = Array.isArray(history) ? history : [];

  const headerLayers =
    baselineVad && currentAgentVad
      ? [
          {
            point: baselineVad,
            stroke: "#6b7280",
            fill: "#6b7280",
            fillOpacity: 0.2,
            strokeWidth: 2,
          },
          {
            point: currentAgentVad,
            stroke: "#3b82f6",
            fill: "#3b82f6",
            fillOpacity: 0.2,
            strokeWidth: 2,
          },
        ]
      : [];

  return (
    <aside className="chat-vad-panel hidden min-h-0 shrink-0 flex-col border bg-card p-3 lg:flex">
      <header className="border-b pb-3">
        <h3 className="text-sm font-semibold">VAD History</h3>
        {headerLayers.length === 2 ? (
          <div className="mt-2 flex items-start gap-3">
            <VadRadarChart size={128} layers={headerLayers} showLabels className="shrink-0 text-border" />
            <div className="min-w-0 flex-1 space-y-1 text-xs text-muted-foreground">
              <p>
                <span className="inline-block h-2 w-2 rounded-full bg-gray-600 align-middle" /> Baseline:{" "}
                {baselineVad
                  ? `V ${formatVad(baselineVad.v)} / A ${formatVad(baselineVad.a)} / D ${formatVad(baselineVad.d)}`
                  : "N/A"}
              </p>
              <p>
                <span className="inline-block h-2 w-2 rounded-full bg-blue-500 align-middle" /> Current:{" "}
                {currentAgentVad
                  ? `V ${formatVad(currentAgentVad.v)} / A ${formatVad(currentAgentVad.a)} / D ${formatVad(currentAgentVad.d)}`
                  : "N/A"}
              </p>
            </div>
          </div>
        ) : (
          <>
            <p className="mt-1 text-xs text-muted-foreground">
              Current:{" "}
              {currentAgentVad == null
                ? "N/A"
                : `V ${formatVad(currentAgentVad.v)} / A ${formatVad(currentAgentVad.a)} / D ${formatVad(currentAgentVad.d)}`}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Baseline:{" "}
              {baselineVad == null
                ? "N/A"
                : `V ${formatVad(baselineVad.v)} / A ${formatVad(baselineVad.a)} / D ${formatVad(baselineVad.d)}`}
            </p>
          </>
        )}
      </header>

      <div className="mt-2 min-h-0 flex-1 overflow-y-auto pr-1">
        {safeHistory.length === 0 ? (
          <p className="pt-4 text-xs text-muted-foreground">暂无 VAD 历史数据</p>
        ) : (
          <ul className="space-y-2">
            {safeHistory.map((item, index) => {
              const isOpen = Boolean(expanded[item.turnId]);
              const prevAgent =
                safeHistory[index + 1]?.agentVadAfter ??
                (baselineVad ? baselineVad : getPrevAgentVad(item.agentVadAfter, item.delta));

              return (
                <li key={item.turnId} className="rounded-md border bg-background p-2 text-xs">
                  <button
                    type="button"
                    className="w-full cursor-pointer rounded-md text-left transition-colors duration-200 hover:bg-muted/60"
                    onClick={() =>
                      setExpanded((prev) => ({
                        ...prev,
                        [item.turnId]: !prev[item.turnId],
                      }))
                    }
                  >
                    <div className="font-medium text-foreground">
                      #{safeHistory.length - index} {item.userText || "(空文本)"}
                    </div>
                    {!isOpen ? (
                      <div className="truncate text-muted-foreground">{item.userText || "(空文本)"}</div>
                    ) : null}
                  </button>
                  {isOpen ? (
                    <p className="mt-1 whitespace-pre-wrap break-words text-muted-foreground">{item.userText}</p>
                  ) : null}

                  <div className="mt-2 flex gap-2">
                    <VadRadarChart
                      size={80}
                      className="shrink-0 text-border"
                      compareDelta={item.delta}
                      layers={[
                        {
                          point: prevAgent,
                          stroke: "#6b7280",
                          fill: "#6b7280",
                          fillOpacity: 0.18,
                          strokeWidth: 2,
                        },
                        {
                          point: item.agentVadAfter,
                          stroke: "#6b7280",
                          fill: "#ef4444",
                          fillOpacity: 0.16,
                          strokeWidth: 2.4,
                        },
                      ]}
                      amplifyDeltaFactor={2.8}
                      minVisualDelta={0.035}
                    />
                    <div className="min-w-0 flex-1 grid gap-1">
                      <VadTriple label="句子:" point={item.utteranceVad} />
                      <VadTriple label="Agent:" point={item.agentVadAfter} />
                      <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
                        <span className="text-muted-foreground">Δ:</span>
                        <span>
                          <span className={deltaClassName(item.delta.v)}>
                            {item.delta.v >= 0 ? "+" : ""}
                            {formatVad(item.delta.v)}
                          </span>
                          {" / "}
                          <span className={deltaClassName(item.delta.a)}>
                            {item.delta.a >= 0 ? "+" : ""}
                            {formatVad(item.delta.a)}
                          </span>
                          {" / "}
                          <span className={deltaClassName(item.delta.d)}>
                            {item.delta.d >= 0 ? "+" : ""}
                            {formatVad(item.delta.d)}
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
