import { useEffect, useMemo, useState } from "react";
import {
  absoluteApiUrl,
  fetchBgmCatalog,
  fetchClassicScript,
  fetchClassicsCatalog,
  openJobEvents,
  previewVoice,
  startGenerate,
  type BgmTrack,
  type ClassicEntry,
  type DurationCategory,
  type JobEvent,
} from "../api";

export type VoiceId =
  | "zh-TW-HsiaoChenNeural"
  | "zh-TW-YunJheNeural"
  | "zh-TW-HsiaoYuNeural"
  | "zh-CN-YunxiNeural";

export type VoiceSlot = {
  id: number;
  role: string;
  voice: VoiceId;
  sampleState: "idle" | "loading" | "ready";
  previewUrl?: string;
};

export type OutputFormat = "mp3" | "wav";

export const voices: Array<{
  id: VoiceId;
  label: string;
  provider: "Edge" | "OpenAI";
  tone: string;
}> = [
  { id: "zh-TW-HsiaoChenNeural", label: "雅琪", provider: "Edge", tone: "清亮穩定" },
  { id: "zh-TW-YunJheNeural", label: "建宏", provider: "Edge", tone: "溫和低頻" },
  { id: "zh-TW-HsiaoYuNeural", label: "靜怡", provider: "Edge", tone: "親切柔和" },
  { id: "zh-CN-YunxiNeural", label: "雲希", provider: "Edge", tone: "年輕清晰" },
];

const defaultScript = `[主持人A]: 大家好，歡迎收聽 Wavescript。
[主持人B]: 今天我們來聊聊 AI 如何改變日常創作。
---PAUSE:0.5s---
[主持人A]: 我們會從文稿、聲線到輸出流程一路拆解。`;

const defaultSlots: VoiceSlot[] = [
  { id: 1, role: "主持人A", voice: "zh-TW-HsiaoChenNeural", sampleState: "idle" },
  { id: 2, role: "主持人B", voice: "zh-TW-YunJheNeural", sampleState: "idle" },
  { id: 3, role: "主持人C", voice: "zh-TW-HsiaoYuNeural", sampleState: "idle" },
  { id: 4, role: "主持人D", voice: "zh-CN-YunxiNeural", sampleState: "idle" },
];

export function useStudio() {
  const [step, setStep] = useState(1);
  const [script, setScript] = useState(defaultScript);
  const [hostCount, setHostCount] = useState(2);
  const [voiceSlots, setVoiceSlots] = useState(defaultSlots);
  const [speed, setSpeed] = useState(1);
  const [pauseMs, setPauseMs] = useState(500);
  const [bgmEnabled, setBgmEnabled] = useState(true);
  const [bgmTracks, setBgmTracks] = useState<BgmTrack[]>([]);
  const [selectedBgmId, setSelectedBgmId] = useState<string | null>(null);
  const [bgmVolumeDb, setBgmVolumeDb] = useState(-20);
  const [bgmFadeMs, setBgmFadeMs] = useState(1500);
  const [format, setFormat] = useState<OutputFormat>("mp3");
  const [progress, setProgress] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [statusMessage, setStatusMessage] = useState("待命");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [scriptMode, setScriptMode] = useState<"manual" | "classic">("manual");
  const [classicsCatalog, setClassicsCatalog] = useState<ClassicEntry[]>([]);
  const [classicsLoading, setClassicsLoading] = useState(false);
  const [classicsError, setClassicsError] = useState<string | null>(null);
  const [selectedClassicId, setSelectedClassicId] = useState<string | null>(null);
  const [durationFilter, setDurationFilter] = useState<DurationCategory | "all">("all");

  const visibleSlots = voiceSlots.slice(0, hostCount);

  useEffect(() => {
    if (scriptMode !== "classic") return;
    if (classicsCatalog.length > 0) return;
    setClassicsLoading(true);
    setClassicsError(null);
    fetchClassicsCatalog()
      .then((entries) => setClassicsCatalog(entries))
      .catch((err: unknown) =>
        setClassicsError(err instanceof Error ? err.message : "Failed to load classics."),
      )
      .finally(() => setClassicsLoading(false));
  }, [scriptMode, classicsCatalog.length]);

  useEffect(() => {
    fetchBgmCatalog()
      .then((tracks) => {
        setBgmTracks(tracks);
        setSelectedBgmId((current) => current ?? tracks[0]?.id ?? null);
        if (tracks.length === 0) {
          setBgmEnabled(false);
        }
      })
      .catch((catalogError) => {
        setError(catalogError instanceof Error ? catalogError.message : "BGM catalog failed.");
        setBgmEnabled(false);
      });
  }, []);

  const stats = useMemo(() => {
    const normalized = script.replace(/\s+/g, "");
    const chineseChars = [...normalized].filter((char) => /[\u4e00-\u9fff]/.test(char)).length;
    const minutes = Math.max(1, Math.ceil(chineseChars / 200));
    const speakerMatches = Array.from(script.matchAll(/^\[(.+?)\][:：]/gm)).map((match) => match[1]);
    const speakers = [...new Set(speakerMatches)];
    return {
      chars: chineseChars,
      minutes,
      detectedHosts: speakers.length || 1,
      speakers,
    };
  }, [script]);

  function updateSlot(id: number, changes: Partial<VoiceSlot>) {
    setVoiceSlots((slots) =>
      slots.map((slot) => (slot.id === id ? { ...slot, ...changes, sampleState: changes.voice ? "idle" : slot.sampleState } : slot)),
    );
  }

  async function previewSlot(id: number) {
    const slot = voiceSlots.find((item) => item.id === id);
    if (!slot) {
      return;
    }
    updateSlot(id, { sampleState: "loading" });
    try {
      const url = await previewVoice("這是一段 Wavescript 聲線試聽。", slot.voice);
      updateSlot(id, { sampleState: "ready", previewUrl: url });
      new Audio(url).play().catch(() => undefined);
    } catch (previewError) {
      updateSlot(id, { sampleState: "idle" });
      setError(previewError instanceof Error ? previewError.message : "Preview failed.");
    }
  }

  function previewBgm() {
    const track = bgmTracks.find((item) => item.id === selectedBgmId);
    if (!track) {
      return;
    }
    new Audio(absoluteApiUrl(track.preview_url)).play().catch(() => undefined);
  }

  async function selectClassic(classicId: string) {
    setSelectedClassicId(classicId);
    setClassicsError(null);
    try {
      const scriptText = await fetchClassicScript(classicId);
      setScript(scriptText);
      setScriptMode("manual");
    } catch (err: unknown) {
      setClassicsError(err instanceof Error ? err.message : "Failed to load script.");
    }
  }

  const filteredClassics = durationFilter === "all" ? classicsCatalog : classicsCatalog.filter((c) => c.duration_category === durationFilter);

  async function generate() {
    setStep(4);
    setIsGenerating(true);
    setProgress(0);
    setDownloadUrl(null);
    setError(null);
    setStatusMessage("送出任務");

    try {
      const response = await startGenerate({
        script,
        hostCount,
        voiceSlots: visibleSlots,
        speed,
        pauseMs,
        bgmEnabled,
        bgmId: bgmEnabled ? selectedBgmId : null,
        bgmVolumeDb,
        bgmFadeMs,
        format,
      });
      const events = openJobEvents(response.events_url);
      events.onmessage = (event) => {
        const data = JSON.parse(event.data) as JobEvent;
        setProgress(data.progress);
        setStatusMessage(data.message);
        if (data.status === "done") {
          setIsGenerating(false);
          setDownloadUrl(data.file_url ? absoluteApiUrl(data.file_url) : null);
          events.close();
        }
        if (data.status === "failed") {
          setIsGenerating(false);
          setError(data.error ?? data.message);
          events.close();
        }
      };
      events.onerror = () => {
        setIsGenerating(false);
        setError("SSE connection failed.");
        events.close();
      };
    } catch (generateError) {
      setIsGenerating(false);
      setError(generateError instanceof Error ? generateError.message : "Generate failed.");
    }
  }

  return {
    step,
    setStep,
    script,
    setScript,
    hostCount,
    setHostCount,
    visibleSlots,
    updateSlot,
    previewSlot,
    speed,
    setSpeed,
    pauseMs,
    setPauseMs,
    bgmEnabled,
    setBgmEnabled,
    bgmTracks,
    selectedBgmId,
    setSelectedBgmId,
    bgmVolumeDb,
    setBgmVolumeDb,
    bgmFadeMs,
    setBgmFadeMs,
    previewBgm,
    format,
    setFormat,
    progress,
    isGenerating,
    statusMessage,
    downloadUrl,
    error,
    generate,
    stats,
    scriptMode,
    setScriptMode,
    classicsCatalog,
    classicsLoading,
    classicsError,
    selectedClassicId,
    selectClassic,
    durationFilter,
    setDurationFilter,
    filteredClassics,
  };
}
