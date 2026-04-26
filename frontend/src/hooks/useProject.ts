import { useEffect, useRef } from "react";

const DRAFT_KEY = "wavescript-draft";

type DraftState = {
  script: string;
  hostCount: number;
  speed: number;
  pauseMs: number;
  bgmEnabled: boolean;
  bgmVolumeDb: number;
  bgmFadeMs: number;
  format: string;
};

export function useAutoSave(state: DraftState, debounceMs = 3000): void {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify(state));
      } catch {
        // localStorage full — silently skip
      }
    }, debounceMs);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [state, debounceMs]);
}

export function loadDraft(): DraftState | null {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    return raw ? (JSON.parse(raw) as DraftState) : null;
  } catch {
    return null;
  }
}

export function clearDraft(): void {
  localStorage.removeItem(DRAFT_KEY);
}
