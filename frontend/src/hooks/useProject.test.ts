import { afterEach, describe, expect, it, vi } from "vitest";
import { createDraftAutoSaver, type DraftState } from "./useProject";

const draft: DraftState = {
  script: "hello",
  hostCount: 2,
  speed: 1,
  pauseMs: 500,
  bgmEnabled: false,
  bgmVolumeDb: -20,
  bgmFadeMs: 1500,
  format: "mp3",
};

describe("createDraftAutoSaver", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("writes after debounce", () => {
    vi.useFakeTimers();
    const saved: DraftState[] = [];
    const saver = createDraftAutoSaver(100, (state) => saved.push(state));

    saver.schedule(draft);
    vi.advanceTimersByTime(99);
    expect(saved).toEqual([]);

    vi.advanceTimersByTime(1);
    expect(saved).toEqual([draft]);
  });

  it("flushes the latest pending draft", () => {
    vi.useFakeTimers();
    const saved: DraftState[] = [];
    const saver = createDraftAutoSaver(100, (state) => saved.push(state));
    const latest = { ...draft, script: "latest" };

    saver.schedule(draft);
    saver.schedule(latest);
    saver.flush();
    vi.advanceTimersByTime(100);

    expect(saved).toEqual([latest]);
  });
});
