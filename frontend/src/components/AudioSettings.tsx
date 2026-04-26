import { Music, Play, SlidersHorizontal } from "lucide-react";
import type { BgmTrack } from "../api";
import type { OutputFormat } from "../hooks/useStudio";

type AudioSettingsProps = {
  speed: number;
  setSpeed: (value: number) => void;
  pauseMs: number;
  setPauseMs: (value: number) => void;
  bgmEnabled: boolean;
  setBgmEnabled: (value: boolean) => void;
  bgmTracks: BgmTrack[];
  selectedBgmId: string | null;
  setSelectedBgmId: (value: string | null) => void;
  bgmVolumeDb: number;
  setBgmVolumeDb: (value: number) => void;
  bgmFadeMs: number;
  setBgmFadeMs: (value: number) => void;
  previewBgm: () => void;
  format: OutputFormat;
  setFormat: (value: OutputFormat) => void;
};

export function AudioSettings({
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
}: AudioSettingsProps) {
  const selectedTrack = bgmTracks.find((track) => track.id === selectedBgmId);

  return (
    <section className="panel settings-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Step 3</p>
          <h2>音效</h2>
        </div>
        <SlidersHorizontal size={22} />
      </div>

      <div className="setting-line">
        <label htmlFor="speed">語速</label>
        <input id="speed" max="1.35" min="0.75" onChange={(event) => setSpeed(Number(event.target.value))} step="0.05" type="range" value={speed} />
        <strong>{speed.toFixed(2)}x</strong>
      </div>

      <div className="setting-line">
        <label htmlFor="pause">停頓</label>
        <input id="pause" max="1200" min="100" onChange={(event) => setPauseMs(Number(event.target.value))} step="50" type="range" value={pauseMs} />
        <strong>{pauseMs}ms</strong>
      </div>

      <div className="switch-line">
        <div>
          <Music size={18} />
          <span>BGM</span>
        </div>
        <button
          className={`switch ${bgmEnabled ? "on" : ""}`}
          disabled={bgmTracks.length === 0}
          onClick={() => setBgmEnabled(!bgmEnabled)}
          type="button"
          aria-pressed={bgmEnabled}
        >
          <span />
        </button>
      </div>

      <div className="bgm-picker">
        <label>
          <span>曲庫</span>
          <select
            disabled={!bgmEnabled || bgmTracks.length === 0}
            value={selectedBgmId ?? ""}
            onChange={(event) => setSelectedBgmId(event.target.value || null)}
          >
            {bgmTracks.length === 0 ? (
              <option value="">尚未放入配樂</option>
            ) : (
              bgmTracks.map((track) => (
                <option key={track.id} value={track.id}>
                  {track.title} · {track.mood}
                </option>
              ))
            )}
          </select>
        </label>
        <button className="icon-text-button" disabled={!bgmEnabled || !selectedTrack} onClick={previewBgm} type="button">
          <Play size={17} />
          <span>試聽</span>
        </button>
        <div className="bgm-meta">
          {selectedTrack ? `${selectedTrack.mood} · ${Math.round(selectedTrack.duration)}s` : "將 MP3/WAV 放入 assets/bgm"}
        </div>
      </div>

      <div className="setting-line">
        <label htmlFor="bgm-volume">配樂音量</label>
        <input
          disabled={!bgmEnabled}
          id="bgm-volume"
          max="-6"
          min="-36"
          onChange={(event) => setBgmVolumeDb(Number(event.target.value))}
          step="1"
          type="range"
          value={bgmVolumeDb}
        />
        <strong>{bgmVolumeDb}dB</strong>
      </div>

      <div className="setting-line">
        <label htmlFor="bgm-fade">淡入淡出</label>
        <input
          disabled={!bgmEnabled}
          id="bgm-fade"
          max="8000"
          min="0"
          onChange={(event) => setBgmFadeMs(Number(event.target.value))}
          step="250"
          type="range"
          value={bgmFadeMs}
        />
        <strong>{(bgmFadeMs / 1000).toFixed(1)}s</strong>
      </div>

      <div className="format-row" role="group" aria-label="Output format">
        {(["mp3", "wav"] as OutputFormat[]).map((option) => (
          <button className={format === option ? "selected" : ""} key={option} onClick={() => setFormat(option)} type="button">
            {option.toUpperCase()}
          </button>
        ))}
      </div>
    </section>
  );
}
