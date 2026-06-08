import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "gardenagent.config.previewRatio";
const MIN_RATIO = 0.22;
const MAX_RATIO = 0.72;

function readStoredRatio(fallback: number): number {
  if (typeof window === "undefined") {
    return fallback;
  }
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return fallback;
  }
  const n = Number.parseFloat(raw);
  if (Number.isFinite(n) && n >= MIN_RATIO && n <= MAX_RATIO) {
    return n;
  }
  return fallback;
}

export function useConfigSplitPane(defaultRatio = 0.4) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [ratio, setRatio] = useState(() => readStoredRatio(defaultRatio));
  const [dragging, setDragging] = useState(false);

  const startDrag = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  useEffect(() => {
    if (!dragging) {
      return;
    }

    const onMove = (e: MouseEvent) => {
      const el = containerRef.current;
      if (!el) {
        return;
      }
      const rect = el.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const next = x / rect.width;
      setRatio(Math.min(MAX_RATIO, Math.max(MIN_RATIO, next)));
    };

    const onUp = () => {
      setDragging(false);
      setRatio((current) => {
        localStorage.setItem(STORAGE_KEY, String(current));
        return current;
      });
    };

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);

    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [dragging]);

  return { containerRef, ratio, dragging, startDrag };
}
