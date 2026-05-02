import { useEffect, useRef, useState } from "react";
import { Download, Pause, Play, Radio } from "lucide-react";

type GenerateProgressProps = {
  progress: number;
  isGenerating: boolean;
  format: string;
  message: string;
  downloadUrl: string | null;
  error: string | null;
};

export function GenerateProgress({ progress, isGenerating, format, message, downloadUrl, error }: GenerateProgressProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
  }, [downloadUrl]);

  const playbackProgress = duration > 0 ? Math.min(100, (currentTime / duration) * 100) : 0;

  function formatTime(seconds: number) {
    if (!Number.isFinite(seconds) || seconds <= 0) {
      return "0:00";
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }

  function ensureAudio() {
    if (!downloadUrl) {
      return null;
    }
    if (!audioRef.current) {
      const audio = new Audio(downloadUrl);
      audio.addEventListener("ended", () => setIsPlaying(false));
      audio.addEventListener("pause", () => setIsPlaying(false));
      audio.addEventListener("play", () => setIsPlaying(true));
      audio.addEventListener("loadedmetadata", () => setDuration(audio.duration || 0));
      audio.addEventListener("timeupdate", () => {
        setCurrentTime(audio.currentTime || 0);
        setDuration(audio.duration || 0);
      });
      audioRef.current = audio;
    }
    return audioRef.current;
  }

  function togglePlayback() {
    const audio = ensureAudio();
    if (!audio) return;
    if (audio.paused) {
      audio.play().catch(() => setIsPlaying(false));
    } else {
      audio.pause();
    }
  }

  function seek(value: string) {
    const audio = ensureAudio();
    const nextTime = Number(value);
    setCurrentTime(nextTime);
    if (audio) {
      audio.currentTime = nextTime;
    }
  }

  return (
    <section className="panel output-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Step 4</p>
          <h2>輸出</h2>
        </div>
        <Radio className={isGenerating ? "pulse" : ""} size={22} />
      </div>

      <div className="progress-shell">
        <div className="progress-meta">
          <span>{error ?? message}</span>
          <strong>{progress}%</strong>
        </div>
        <div className="progress-track">
          <div style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="player-strip">
        <button className="icon-button" type="button" title={isPlaying ? "暫停" : "播放"} onClick={togglePlayback} disabled={!downloadUrl}>
          {isPlaying ? <Pause size={18} /> : <Play size={18} />}
        </button>
        <div className="audio-timeline">
          <div className="waveform" aria-hidden="true">
            {Array.from({ length: 34 }).map((_, index) => (
              <span
                key={index}
                className={index / 34 <= playbackProgress / 100 ? "played" : ""}
                style={{ height: `${18 + ((index * 9) % 30)}px` }}
              />
            ))}
          </div>
          <input
            aria-label="播放進度"
            className="timeline-range"
            disabled={!downloadUrl}
            max={duration || 0}
            min={0}
            onChange={(event) => seek(event.target.value)}
            step={0.1}
            type="range"
            value={duration ? currentTime : 0}
          />
          <div className="time-row">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
        <a className={`download-button ${!downloadUrl ? "disabled" : ""}`} href={downloadUrl ?? undefined} download>
          <Download size={18} />
          <span>{format.toUpperCase()}</span>
        </a>
      </div>
    </section>
  );
}
