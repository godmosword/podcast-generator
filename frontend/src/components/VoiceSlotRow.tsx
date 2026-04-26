import { Play, Volume2 } from "lucide-react";
import type { VoiceId, VoiceSlot } from "../hooks/useStudio";
import { voices } from "../hooks/useStudio";

type VoiceSlotRowProps = {
  slot: VoiceSlot;
  onChange: (changes: Partial<VoiceSlot>) => void;
  onPreview: () => void;
};

// Group voices by language for <optgroup> display
const voiceGroups = voices.reduce<Array<{ langLabel: string; items: typeof voices }>>((groups, voice) => {
  const existing = groups.find((g) => g.langLabel === voice.langLabel);
  if (existing) {
    existing.items.push(voice);
  } else {
    groups.push({ langLabel: voice.langLabel, items: [voice] });
  }
  return groups;
}, []);

export function VoiceSlotRow({ slot, onChange, onPreview }: VoiceSlotRowProps) {
  const selectedVoice = voices.find((voice) => voice.id === slot.voice);

  return (
    <div className="voice-row">
      <div className="voice-number">{slot.id}</div>
      <label>
        <span>角色</span>
        <input value={slot.role} onChange={(event) => onChange({ role: event.target.value })} />
      </label>
      <label>
        <span>聲線</span>
        <select value={slot.voice} onChange={(event) => onChange({ voice: event.target.value as VoiceId })}>
          {voiceGroups.map((group) => (
            <optgroup key={group.langLabel} label={group.langLabel}>
              {group.items.map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.label} · {voice.tone}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </label>
      <div className="voice-tone">
        <Volume2 size={17} />
        <span>{selectedVoice?.tone}</span>
      </div>
      <button className="icon-button" onClick={onPreview} title="試聽" type="button">
        <Play size={18} />
      </button>
      <div className={`sample-state ${slot.sampleState}`}>
        {slot.sampleState === "loading" ? "生成中" : slot.sampleState === "ready" ? "可播放" : "待試聽"}
      </div>
    </div>
  );
}
