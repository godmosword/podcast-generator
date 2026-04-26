import { useEffect, useMemo, useState } from "react";
import {
  absoluteApiUrl,
  fetchBgmCatalog,
  fetchClassicScript,
  fetchClassicsCatalog,
  fetchJob,
  openJobEvents,
  previewVoice,
  startGenerate,
  type BgmTrack,
  type ClassicEntry,
  type StoryFilter,
  type JobEvent,
} from "../api";

export type VoiceId =
  // 繁體中文
  | "zh-TW-HsiaoChenNeural"
  | "zh-TW-YunJheNeural"
  | "zh-TW-HsiaoYuNeural"
  // 簡體中文
  | "zh-CN-YunxiNeural"
  | "zh-CN-XiaoxiaoNeural"
  | "zh-CN-XiaoyiNeural"
  | "zh-CN-YunxiaNeural"
  // 英語
  | "en-US-JennyNeural"
  | "en-US-GuyNeural"
  | "en-GB-SoniaNeural"
  // 日語
  | "ja-JP-NanamiNeural"
  | "ja-JP-KeitaNeural"
  // 韓語
  | "ko-KR-SunHiNeural"
  | "ko-KR-InJoonNeural"
  // 法語
  | "fr-FR-DeniseNeural"
  // 西班牙語
  | "es-ES-ElviraNeural";

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
  language: string;
  langLabel: string;
  tone: string;
}> = [
  { id: "zh-TW-HsiaoChenNeural", label: "雅琪", language: "zh-TW", langLabel: "繁體中文", tone: "清亮穩定" },
  { id: "zh-TW-YunJheNeural",    label: "建宏", language: "zh-TW", langLabel: "繁體中文", tone: "溫和低頻" },
  { id: "zh-TW-HsiaoYuNeural",   label: "靜怡", language: "zh-TW", langLabel: "繁體中文", tone: "親切柔和" },
  { id: "zh-CN-YunxiNeural",     label: "雲希", language: "zh-CN", langLabel: "簡體中文", tone: "年輕清晰" },
  { id: "zh-CN-XiaoxiaoNeural",  label: "曉曉", language: "zh-CN", langLabel: "簡體中文", tone: "溫暖親切" },
  { id: "zh-CN-XiaoyiNeural",    label: "小女孩", language: "zh-CN", langLabel: "簡體中文", tone: "活潑口語" },
  { id: "zh-CN-YunxiaNeural",    label: "小男孩", language: "zh-CN", langLabel: "簡體中文", tone: "可愛童聲" },
  { id: "en-US-JennyNeural",     label: "Jenny", language: "en-US", langLabel: "English (US)", tone: "friendly" },
  { id: "en-US-GuyNeural",       label: "Guy",   language: "en-US", langLabel: "English (US)", tone: "casual" },
  { id: "en-GB-SoniaNeural",     label: "Sonia", language: "en-GB", langLabel: "English (UK)", tone: "formal" },
  { id: "ja-JP-NanamiNeural",    label: "Nanami", language: "ja-JP", langLabel: "日本語", tone: "gentle" },
  { id: "ja-JP-KeitaNeural",     label: "Keita",  language: "ja-JP", langLabel: "日本語", tone: "natural" },
  { id: "ko-KR-SunHiNeural",     label: "SunHi",  language: "ko-KR", langLabel: "한국어", tone: "bright" },
  { id: "ko-KR-InJoonNeural",    label: "InJoon", language: "ko-KR", langLabel: "한국어", tone: "calm" },
  { id: "fr-FR-DeniseNeural",    label: "Denise", language: "fr-FR", langLabel: "Français", tone: "expressive" },
  { id: "es-ES-ElviraNeural",    label: "Elvira", language: "es-ES", langLabel: "Español", tone: "vivid" },
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
  const [speed, setSpeed] = useState(1.06);
  const [pauseMs, setPauseMs] = useState(350);
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
  const [storyFilter, setStoryFilter] = useState<StoryFilter>("all");

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
    const voiceInfo = voices.find((v) => v.id === slot.voice);
    const previewText = voiceInfo?.language.startsWith("zh")
      ? "這是一段 Wavescript 聲線試聽。"
      : voiceInfo?.language.startsWith("ja")
        ? "これは Wavescript の音声サンプルです。"
        : voiceInfo?.language.startsWith("ko")
          ? "이것은 Wavescript 음성 샘플입니다."
          : voiceInfo?.language.startsWith("fr")
            ? "Ceci est un exemple de voix Wavescript."
            : voiceInfo?.language.startsWith("es")
              ? "Esta es una muestra de voz de Wavescript."
              : "This is a Wavescript voice preview.";
    updateSlot(id, { sampleState: "loading" });
    try {
      const url = await previewVoice(previewText, slot.voice);
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

  const filteredClassics =
    storyFilter === "all"
      ? classicsCatalog
      : storyFilter === "children"
        ? classicsCatalog.filter((c) => c.category === "children")
        : classicsCatalog.filter((c) => c.category !== "children" && c.duration_category === storyFilter);

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
      const finishJob = async (fileUrl?: string | null) => {
        let resolvedUrl = fileUrl ?? response.file_url;
        if (!resolvedUrl) {
          const snapshot = await fetchJob(response.job_id);
          resolvedUrl = snapshot.file_url ?? null;
        }
        setIsGenerating(false);
        setDownloadUrl(resolvedUrl ? absoluteApiUrl(resolvedUrl) : null);
        if (!resolvedUrl) {
          setError("Export finished, but download link was not returned.");
        }
      };

      const events = openJobEvents(response.events_url);
      events.onmessage = (event) => {
        const data = JSON.parse(event.data) as JobEvent;
        setProgress(data.progress);
        setStatusMessage(data.message);
        if (data.status === "done") {
          events.close();
          void finishJob(data.file_url);
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
    storyFilter,
    setStoryFilter,
    filteredClassics,
  };
}
