import type { OutputFormat, VoiceSlot } from "./hooks/useStudio";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type GeneratePayload = {
  script: string;
  hostCount: number;
  voiceSlots: VoiceSlot[];
  speed: number;
  pauseMs: number;
  bgmEnabled: boolean;
  bgmId: string | null;
  bgmVolumeDb: number;
  bgmFadeMs: number;
  format: OutputFormat;
};

export type BgmTrack = {
  id: string;
  title: string;
  mood: string;
  duration: number;
  preview_url: string;
};

export type VoiceCatalogItem = {
  id: string;
  label: string;
  provider: "edge" | "openai" | "elevenlabs";
  language: string;
  tone: string;
};

export type GenerateResponse = {
  job_id: string;
  events_url: string;
  file_url: string | null;
};

export type JobEvent = {
  id: string;
  status: "queued" | "parsing" | "synthesizing" | "mixing" | "exporting" | "done" | "failed";
  progress: number;
  message: string;
  file_url?: string;
  error?: string;
};

export type JobSnapshot = JobEvent;

export async function startGenerate(payload: GeneratePayload): Promise<GenerateResponse> {
  const response = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      script: payload.script,
      host_count: payload.hostCount,
      voice_assignments: payload.voiceSlots.map((slot) => ({ role: slot.role, voice: slot.voice })),
      audio: {
        speed: payload.speed,
        pause_ms: payload.pauseMs,
        bgm_enabled: payload.bgmEnabled,
        bgm_id: payload.bgmId,
        bgm_volume_db: payload.bgmVolumeDb,
        bgm_fade_ms: payload.bgmFadeMs,
        output_format: payload.format,
        normalize: true,
      },
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Generate request failed.");
  }

  return response.json();
}

export async function fetchBgmCatalog(): Promise<BgmTrack[]> {
  const response = await fetch(`${API_BASE}/api/bgm`);
  if (!response.ok) {
    throw new Error("BGM catalog request failed.");
  }
  return response.json();
}

export async function fetchVoices(): Promise<VoiceCatalogItem[]> {
  const response = await fetch(`${API_BASE}/api/voices`);
  if (!response.ok) {
    throw new Error("Voice catalog request failed.");
  }
  return response.json();
}

export async function fetchJob(jobId: string): Promise<JobSnapshot> {
  const response = await fetch(`${API_BASE}/api/generate/${jobId}`);
  if (!response.ok) {
    throw new Error("Job status request failed.");
  }
  return response.json();
}

export function openJobEvents(eventsUrl: string): EventSource {
  return new EventSource(`${API_BASE}${eventsUrl}`);
}

export async function previewVoice(text: string, voice: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice, seconds: 15 }),
  });

  if (!response.ok) {
    throw new Error("Preview request failed.");
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export function absoluteApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export type DurationCategory = "short" | "medium" | "long";
export type StoryFilter = "all" | "children" | DurationCategory;

export type ClassicEntry = {
  id: string;
  title: string;
  author: string;
  category: string;
  duration_category: DurationCategory;
  duration_minutes: number;
  language: string;
  description: string;
  speaker_count: number;
  tags: string[];
};

export async function fetchClassicsCatalog(): Promise<ClassicEntry[]> {
  const response = await fetch(`${API_BASE}/api/classics`);
  if (!response.ok) {
    throw new Error("Classics catalog request failed.");
  }
  return response.json();
}

export async function fetchClassicScript(classicId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/classics/${classicId}/script`);
  if (!response.ok) {
    throw new Error("Classic script request failed.");
  }
  const data = (await response.json()) as { id: string; script: string };
  return data.script;
}

export type ScriptGenerationPayload = {
  topic: string;
  duration_min: number;
  host_count: number;
  tone: "educational" | "entertainment" | "storytelling" | "interview" | "debate";
  language: "zh-TW" | "zh-CN" | "en" | "ja";
  extra_context?: string;
};

export type ScriptGenerationResult = {
  script: string;
  estimated_duration_sec: number;
  warnings: string[];
};

export async function generateScript(payload: ScriptGenerationPayload): Promise<ScriptGenerationResult> {
  const response = await fetch(`${API_BASE}/api/script/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error((error as { detail?: string } | null)?.detail ?? "Script generation failed.");
  }
  return response.json() as Promise<ScriptGenerationResult>;
}

export type AnalysisFinding = {
  type: "gap" | "boundary" | "suggestion" | "strength";
  severity: "info" | "warning" | "critical";
  content: string;
};

export type AnalysisResult = {
  logical_score: number;
  summary: string;
  findings: AnalysisFinding[];
  enriched_context: string;
};

export type AnalyzePayload = {
  text: string;
  topic?: string;
  language?: "zh-TW" | "zh-CN" | "en" | "ja";
};

export async function analyzeText(payload: AnalyzePayload): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error((error as { detail?: string } | null)?.detail ?? "Analysis failed.");
  }
  return response.json() as Promise<AnalysisResult>;
}
