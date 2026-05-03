import { useEffect, useMemo, useRef, useState } from "react";
import {
  absoluteApiUrl,
  fetchBgmCatalog,
  fetchClassicScript,
  fetchClassicsCatalog,
  fetchJob,
  fetchVoices,
  openJobEvents,
  previewVoice,
  startGenerate,
  type BgmTrack,
  type ClassicEntry,
  type StoryFilter,
  type JobEvent,
  type VoiceCatalogItem,
} from "../api";
import { type Template } from "../data/templates";
import { useAutoSave, loadDraft } from "./useProject";

export type VoiceId = string;

export type VoiceSlot = {
  id: number;
  role: string;
  voice: VoiceId;
  sampleState: "idle" | "loading" | "ready";
  previewUrl?: string;
};

export type OutputFormat = "mp3" | "wav";

export type VoiceOption = {
  id: VoiceId;
  label: string;
  provider: VoiceCatalogItem["provider"];
  provider_voice_id?: string;
  language: string;
  langLabel: string;
  tone: string;
  tags: string[];
  source: "static" | "dynamic";
};

const fallbackVoices: VoiceOption[] = [
  { id: "edge:zh-TW-HsiaoChenNeural", label: "雅琪", provider: "edge", provider_voice_id: "zh-TW-HsiaoChenNeural", language: "zh-TW", langLabel: "繁體中文", tone: "成人女聲", tags: ["female", "warm", "host"], source: "static" },
  { id: "edge:zh-TW-YunJheNeural", label: "建宏", provider: "edge", provider_voice_id: "zh-TW-YunJheNeural", language: "zh-TW", langLabel: "繁體中文", tone: "成人男聲", tags: ["male", "clear", "host"], source: "static" },
  { id: "edge:zh-TW-HsiaoYuNeural", label: "靜怡", provider: "edge", provider_voice_id: "zh-TW-HsiaoYuNeural", language: "zh-TW", langLabel: "繁體中文", tone: "成人女聲柔和", tags: ["female", "soft", "storytelling"], source: "static" },
  { id: "edge:zh-TW-YunJheNeural__adult-male-2", label: "柏宇", provider: "edge", provider_voice_id: "zh-TW-YunJheNeural", language: "zh-TW", langLabel: "繁體中文", tone: "成人男聲低沉", tags: ["male", "low", "guest"], source: "static" },
];

function toVoiceOption(item: VoiceCatalogItem): VoiceOption {
  return {
    ...item,
    langLabel: languageLabel(item),
    tags: item.tags ?? [],
    source: item.source ?? "static",
  };
}

function languageLabel(item: VoiceCatalogItem): string {
  if (item.provider === "openai") return "OpenAI";
  if (item.provider === "elevenlabs") return "ElevenLabs";
  if (item.language === "zh-TW") return "繁體中文";
  if (item.language === "ja-JP") return "日本語";
  if (item.language.startsWith("en-")) return "English";
  return item.language;
}

function estimateScriptStats(script: string) {
  const content = script
    .replace(/^\s*---PAUSE:\d+(?:\.\d+)?s---\s*$/gm, "")
    .replace(/^\s*\[.+?\][:：]\s*/gm, "");
  const cjkCount = content.match(/[\u4e00-\u9fff]/g)?.length ?? 0;
  const japaneseCount = content.match(/[\u3040-\u30ff\u4e00-\u9fff]/g)?.length ?? 0;
  const englishWords = content.match(/[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?/g)?.length ?? 0;
  const usesEnglish = englishWords > Math.max(cjkCount, japaneseCount) / 2;
  const usesJapanese = !usesEnglish && japaneseCount > cjkCount;
  const units = usesEnglish ? englishWords : usesJapanese ? japaneseCount : cjkCount;
  const unitsPerMinute = usesEnglish ? 150 : usesJapanese ? 300 : 200;
  return {
    units,
    unitLabel: usesEnglish ? "字詞" : "字數",
    minutes: Math.max(1, Math.ceil(units / unitsPerMinute)),
  };
}

function providerForVoice(voices: VoiceOption[], voiceId: string): VoiceOption["provider"] | undefined {
  return voices.find((voice) => voice.id === voiceId)?.provider;
}

const defaultScript = `[主持人A]: 大家好，歡迎收聽 Wavescript。
[主持人B]: 今天我們來聊聊 AI 如何改變日常創作。
---PAUSE:0.5s---
[主持人A]: 我們會從文稿、聲線到輸出流程一路拆解。`;

const defaultSlots: VoiceSlot[] = [
  { id: 1, role: "主持人A", voice: "edge:zh-TW-HsiaoChenNeural", sampleState: "idle" },
  { id: 2, role: "主持人B", voice: "edge:zh-TW-YunJheNeural", sampleState: "idle" },
  { id: 3, role: "主持人C", voice: "edge:zh-TW-HsiaoYuNeural", sampleState: "idle" },
  { id: 4, role: "主持人D", voice: "edge:zh-TW-YunJheNeural__adult-male-2", sampleState: "idle" },
];

export function useStudio() {
  const [step, setStep] = useState(1);
  const [script, setScript] = useState(defaultScript);
  const [hostCount, setHostCount] = useState(2);
  const [voiceSlots, setVoiceSlots] = useState(defaultSlots);
  const [voiceCatalog, setVoiceCatalog] = useState<VoiceOption[]>(fallbackVoices);
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
  const [showAiModal, setShowAiModal] = useState(false);
  const [analysisContext, setAnalysisContext] = useState("");

  const visibleSlots = voiceSlots.slice(0, hostCount);
  const eventsRef = useRef<EventSource | null>(null);
  const voiceSlotsRef = useRef<VoiceSlot[]>(defaultSlots);

  useEffect(() => {
    voiceSlotsRef.current = voiceSlots;
  }, [voiceSlots]);

  useEffect(() => {
    return () => {
      eventsRef.current?.close();
      voiceSlotsRef.current.forEach((slot) => {
        if (slot.previewUrl) URL.revokeObjectURL(slot.previewUrl);
      });
    };
  }, []);

  // Restore draft from localStorage on first mount
  useEffect(() => {
    const draft = loadDraft();
    if (!draft) return;
    setScript(draft.script);
    setHostCount(draft.hostCount);
    setSpeed(draft.speed);
    setPauseMs(draft.pauseMs);
    setBgmEnabled(draft.bgmEnabled);
    setBgmVolumeDb(draft.bgmVolumeDb);
    setBgmFadeMs(draft.bgmFadeMs);
    if (draft.format === "mp3" || draft.format === "wav") setFormat(draft.format);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const draftState = useMemo(
    () => ({ script, hostCount, speed, pauseMs, bgmEnabled, bgmVolumeDb, bgmFadeMs, format }),
    [script, hostCount, speed, pauseMs, bgmEnabled, bgmVolumeDb, bgmFadeMs, format],
  );

  // Auto-save key state to localStorage (3s debounce)
  useAutoSave(draftState);

  useEffect(() => {
    fetchVoices()
      .then((items) => setVoiceCatalog(items.map(toVoiceOption)))
      .catch(() => setVoiceCatalog(fallbackVoices));
  }, []);

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
    const measured = estimateScriptStats(script);
    const speakerMatches = Array.from(script.matchAll(/^\[(.+?)\][:：]/gm)).map((match) => match[1]);
    const speakers = [...new Set(speakerMatches)];
    return {
      chars: measured.units,
      unitLabel: measured.unitLabel,
      minutes: measured.minutes,
      detectedHosts: speakers.length || 1,
      speakers,
    };
  }, [script]);

  function updateSlot(id: number, changes: Partial<VoiceSlot>) {
    const hasPreviewUrl = Object.prototype.hasOwnProperty.call(changes, "previewUrl");
    setVoiceSlots((slots) =>
      slots.map((slot) => {
        if (slot.id !== id) return slot;
        if (changes.voice && slot.previewUrl) {
          URL.revokeObjectURL(slot.previewUrl);
        }
        return {
          ...slot,
          ...changes,
          previewUrl: changes.voice ? undefined : hasPreviewUrl ? changes.previewUrl : slot.previewUrl,
          sampleState: changes.voice ? "idle" : changes.sampleState ?? slot.sampleState,
        };
      }),
    );
  }

  async function previewSlot(id: number) {
    const slot = voiceSlots.find((item) => item.id === id);
    if (!slot) {
      return;
    }
    const voiceInfo = voiceCatalog.find((v) => v.id === slot.voice);
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
    if (slot.previewUrl) {
      URL.revokeObjectURL(slot.previewUrl);
    }
    updateSlot(id, { sampleState: "loading", previewUrl: undefined });
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

  function applyTemplate(template: Template) {
    setScript(template.script);
    setHostCount(template.hostCount);
    setScriptMode("manual");
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
      eventsRef.current?.close();
      const selectedProviders = new Set(visibleSlots.map((slot) => providerForVoice(voiceCatalog, slot.voice)).filter(Boolean));
      if (selectedProviders.size > 1) {
        setIsGenerating(false);
        setStatusMessage("請統一聲線來源");
        setError("同一個生成任務目前需要使用同一個 TTS provider。請將所有主持人的聲線改成同一來源。");
        return;
      }

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
      eventsRef.current = events;
      const closeEvents = () => {
        events.close();
        if (eventsRef.current === events) {
          eventsRef.current = null;
        }
      };
      events.onmessage = (event) => {
        let data: JobEvent;
        try {
          data = JSON.parse(event.data) as JobEvent;
        } catch {
          setIsGenerating(false);
          setError("Connection error. Please refresh and try again.");
          closeEvents();
          return;
        }
        setProgress(data.progress);
        setStatusMessage(data.message);
        if (data.status === "done") {
          closeEvents();
          void finishJob(data.file_url);
        }
        if (data.status === "failed") {
          setIsGenerating(false);
          setError(data.error ?? data.message);
          closeEvents();
        }
      };
      events.onerror = () => {
        setIsGenerating(false);
        setError("SSE connection failed.");
        closeEvents();
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
    voices: voiceCatalog,
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
    showAiModal,
    setShowAiModal,
    applyTemplate,
    analysisContext,
    setAnalysisContext,
  };
}
