import { FileText, Upload } from "lucide-react";

type ScriptEditorProps = {
  script: string;
  onChange: (value: string) => void;
  chars: number;
  minutes: number;
  detectedHosts: number;
};

export function ScriptEditor({ script, onChange, chars, minutes, detectedHosts }: ScriptEditorProps) {
  return (
    <section className="panel editor-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Step 1</p>
          <h2>文稿</h2>
        </div>
        <button className="icon-text-button" type="button">
          <Upload size={17} />
          <span>TXT</span>
        </button>
      </div>

      <textarea
        value={script}
        onChange={(event) => onChange(event.target.value)}
        spellCheck={false}
        aria-label="Podcast script"
      />

      <div className="stats-grid">
        <div>
          <FileText size={18} />
          <span>{chars.toLocaleString()} 字</span>
        </div>
        <div>
          <span className="stat-number">{minutes}</span>
          <span>分鐘</span>
        </div>
        <div>
          <span className="stat-number">{detectedHosts}</span>
          <span>角色</span>
        </div>
      </div>
    </section>
  );
}
