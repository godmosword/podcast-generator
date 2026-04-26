import { Download, Radio } from "lucide-react";

type GenerateProgressProps = {
  progress: number;
  isGenerating: boolean;
  format: string;
  message: string;
  downloadUrl: string | null;
  error: string | null;
};

export function GenerateProgress({ progress, isGenerating, format, message, downloadUrl, error }: GenerateProgressProps) {
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
        <button className="icon-button" type="button" title="播放">
          <Radio size={18} />
        </button>
        <div className="waveform" aria-hidden="true">
          {Array.from({ length: 34 }).map((_, index) => (
            <span key={index} style={{ height: `${18 + ((index * 9) % 30)}px` }} />
          ))}
        </div>
        <a className={`download-button ${!downloadUrl ? "disabled" : ""}`} href={downloadUrl ?? undefined} download>
          <Download size={18} />
          <span>{format.toUpperCase()}</span>
        </a>
      </div>
    </section>
  );
}
