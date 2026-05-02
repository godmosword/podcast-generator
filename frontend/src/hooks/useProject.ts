import { useEffect, useRef } from "react";

const DRAFT_KEY = "wavescript-draft";

export type DraftState = {
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
  const saverRef = useRef(createDraftAutoSaver(debounceMs));
  const latestStateRef = useRef(state);

  useEffect(() => {
    latestStateRef.current = state;
  }, [state]);

  useEffect(() => {
    saverRef.current.schedule(state);
  }, [state]);

  useEffect(() => {
    const flush = () => saverRef.current.flush(latestStateRef.current);

    const handleVisibilityChange = () => {
      if (typeof document !== "undefined" && document.visibilityState === "hidden") {
        flush();
      }
    };

    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", handleVisibilityChange);
    }

    return () => {
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", handleVisibilityChange);
      }
      flush();
    };
  }, []);
}

export function createDraftAutoSaver(debounceMs = 3000, save: (state: DraftState) => void = saveDraft) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let latestState: DraftState | null = null;

  return {
    schedule(state: DraftState): void {
      latestState = state;
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        timer = null;
        save(state);
      }, debounceMs);
    },
    flush(fallbackState?: DraftState): void {
      if (timer) clearTimeout(timer);
      timer = null;
      const stateToSave = latestState ?? fallbackState;
      if (stateToSave) {
        save(stateToSave);
      }
    },
  };
}

export function saveDraft(state: DraftState): void {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(state));
  } catch {
    // localStorage full or unavailable — silently skip
  }
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
