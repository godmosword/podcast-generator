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
  language: string;
  langLabel: string;
  tone: string;
};

const fallbackVoices: VoiceOption[] = [
  { id: "zh-TW-YunJheNeural", label: "建宏", provider: "edge", language: "zh-TW", langLabel: "繁體中文", tone: "成人男聲" },
  { id: "zh-TW-YunJheNeural__adult-male-2", label: "柏宇", provider: "edge", language: "zh-TW", langLabel: "繁體中文", tone: "成人男聲低沉" },
  { id: "zh-TW-HsiaoChenNeural", label: "雅琪", provider: "edge", language: "zh-TW", langLabel: "繁體中文", tone: "成人女聲" },
  { id: "zh-TW-HsiaoYuNeural", label: "靜怡", provider: "edge", language: "zh-TW", langLabel: "繁體中文", tone: "成人女聲柔和" },
  { id: "zh-TW-YunJheNeural__boy-1", label: "小宇", provider: "edge", language: "zh-TW", langLabel: "繁體中文", tone: "5歲小男孩" },
  { id: "zh-TW-YunJheNeural__boy-2", label: "小傑", provider: "edge", language: "zh-TW", langLabel: "繁體中文", tone: "5歲小男孩明亮" },
  { id: "zh-TW-HsiaoChenNeural__girl-1", label: "小安", provider: "edge", language: "zh-TW", langLabel: "繁體中文", tone: "5歲小女孩" },
  { id: "zh-TW-HsiaoYuNeural__girl-2", label: "小晴", provider: "edge", language: "zh-TW", langLabel: "繁體中文", tone: "5歲小女孩柔和" },
  { id: "en-US-AndrewNeural", label: "Andrew", provider: "edge", language: "en-US", langLabel: "English", tone: "adult male" },
  { id: "en-US-BrianNeural", label: "Brian", provider: "edge", language: "en-US", langLabel: "English", tone: "adult male casual" },
  { id: "en-US-AvaNeural", label: "Ava", provider: "edge", language: "en-US", langLabel: "English", tone: "adult female" },
  { id: "en-US-EmmaNeural", label: "Emma", provider: "edge", language: "en-US", langLabel: "English", tone: "adult female conversational" },
  { id: "en-US-RogerNeural__boy-1", label: "Oliver", provider: "edge", language: "en-US", langLabel: "English", tone: "5-year-old boy" },
  { id: "en-US-AndrewNeural__boy-2", label: "Leo", provider: "edge", language: "en-US", langLabel: "English", tone: "bright 5-year-old boy" },
  { id: "en-US-AnaNeural", label: "Ana", provider: "edge", language: "en-US", langLabel: "English", tone: "5-year-old girl" },
  { id: "en-GB-MaisieNeural__girl-2", label: "Maisie", provider: "edge", language: "en-GB", langLabel: "English", tone: "bright 5-year-old girl" },
  { id: "ja-JP-KeitaNeural", label: "啓太", provider: "edge", language: "ja-JP", langLabel: "日本語", tone: "成人男性" },
  { id: "ja-JP-KeitaNeural__adult-male-2", label: "悠真", provider: "edge", language: "ja-JP", langLabel: "日本語", tone: "成人男性低め" },
  { id: "ja-JP-NanamiNeural", label: "七海", provider: "edge", language: "ja-JP", langLabel: "日本語", tone: "成人女性" },
  { id: "ja-JP-NanamiNeural__adult-female-2", label: "葵", provider: "edge", language: "ja-JP", langLabel: "日本語", tone: "成人女性明るめ" },
  { id: "ja-JP-KeitaNeural__boy-1", label: "湊", provider: "edge", language: "ja-JP", langLabel: "日本語", tone: "5歳男の子" },
  { id: "ja-JP-KeitaNeural__boy-2", label: "陽翔", provider: "edge", language: "ja-JP", langLabel: "日本語", tone: "明るい5歳男の子" },
  { id: "ja-JP-NanamiNeural__girl-1", label: "結菜", provider: "edge", language: "ja-JP", langLabel: "日本語", tone: "5歳女の子" },
  { id: "ja-JP-NanamiNeural__girl-2", label: "陽菜", provider: "edge", language: "ja-JP", langLabel: "日本語", tone: "明るい5歳女の子" },
  { id: "elevenlabs:Rachel", label: "Rachel", provider: "elevenlabs", language: "multi", langLabel: "ElevenLabs", tone: "adult female" },
  { id: "elevenlabs:Adam", label: "Adam", provider: "elevenlabs", language: "multi", langLabel: "ElevenLabs", tone: "adult male" },
  { id: "alloy", label: "Alloy", provider: "openai", language: "multi", langLabel: "OpenAI", tone: "balanced" },
  { id: "nova", label: "Nova", provider: "openai", language: "multi", langLabel: "OpenAI", tone: "warm" },
  { id: "echo", label: "Echo", provider: "openai", language: "multi", langLabel: "OpenAI", tone: "clear" },
  { id: "fable", label: "Fable", provider: "openai", language: "multi", langLabel: "OpenAI", tone: "storytelling" },
  { id: "onyx", label: "Onyx", provider: "openai", language: "multi", langLabel: "OpenAI", tone: "deep" },
  { id: "shimmer", label: "Shimmer", provider: "openai", language: "multi", langLabel: "OpenAI", tone: "bright" },
];

function toVoiceOption(item: VoiceCatalogItem): VoiceOption {
  return {
    ...item,
    langLabel: languageLabel(item),
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
  { id: 1, role: "主持人A", voice: "zh-TW-HsiaoChenNeural", sampleState: "idle" },
  { id: 2, role: "主持人B", voice: "zh-TW-YunJheNeural", sampleState: "idle" },
  { id: 3, role: "主持人C", voice: "zh-TW-HsiaoYuNeural", sampleState: "idle" },
  { id: 4, role: "主持人D", voice: "zh-TW-YunJheNeural__adult-male-2", sampleState: "idle" },
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
