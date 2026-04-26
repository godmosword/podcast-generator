import { BookOpen, FileText, Upload } from "lucide-react";
import type { ClassicEntry, DurationCategory } from "../api";

const DURATION_TABS: Array<{ key: DurationCategory | "all"; label: string }> = [
  { key: "all", label: "全部" },
  { key: "short", label: "短篇 5-10分" },
  { key: "medium", label: "中篇 10-20分" },
  { key: "long", label: "長篇 20-30分" },
];

function categoryLabel(category: string): string {
  if (category === "zh-classic") return "中國經典";
  if (category === "western-fairy-tale") return "西方童話";
  return "西方經典";
}

type ClassicsSelectorProps = {
  script: string;
  onScriptChange: (value: string) => void;
  chars: number;
  minutes: number;
  detectedHosts: number;
  mode: "manual" | "classic";
  onModeChange: (mode: "manual" | "classic") => void;
  classics: ClassicEntry[];
  classicsLoading: boolean;
  classicsError: string | null;
  selectedClassicId: string | null;
  onSelectClassic: (id: string) => void;
  durationFilter: DurationCategory | "all";
  onDurationFilter: (filter: DurationCategory | "all") => void;
};

export function ClassicsSelector({
  script,
  onScriptChange,
  chars,
  minutes,
  detectedHosts,
  mode,
  onModeChange,
  classics,
  classicsLoading,
  classicsError,
  selectedClassicId,
  onSelectClassic,
  durationFilter,
  onDurationFilter,
}: ClassicsSelectorProps) {
  return (
    <section className="panel editor-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Step 1</p>
          <h2>文稿</h2>
        </div>
        <div className="mode-toggle" role="group" aria-label="Script mode">
          <button
            className={mode === "manual" ? "selected" : ""}
            onClick={() => onModeChange("manual")}
            type="button"
          >
            手動輸入
          </button>
          <button
            className={mode === "classic" ? "selected" : ""}
            onClick={() => onModeChange("classic")}
            type="button"
          >
            <BookOpen size={14} />
            選擇名著
          </button>
        </div>
      </div>

      {mode === "classic" && (
        <div className="duration-tabs" role="tablist">
          {DURATION_TABS.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={durationFilter === tab.key}
              className={`duration-tab${durationFilter === tab.key ? " active" : ""}`}
              onClick={() => onDurationFilter(tab.key)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {mode === "manual" ? (
        <>
          <textarea
            value={script}
            onChange={(event) => onScriptChange(event.target.value)}
            spellCheck={false}
            aria-label="Podcast script"
          />
          <button className="icon-text-button upload-btn" type="button">
            <Upload size={17} />
            <span>TXT</span>
          </button>
        </>
      ) : (
        <div className="classics-grid">
          {classicsLoading && <div className="classics-status">載入中…</div>}
          {classicsError && <div className="classics-status classics-error">{classicsError}</div>}
          {!classicsLoading &&
            !classicsError &&
            classics.length === 0 && (
              <div className="classics-status">此分類暫無故事</div>
            )}
          {classics.map((classic) => (
            <button
              key={classic.id}
              className={`classic-card${selectedClassicId === classic.id ? " selected" : ""}`}
              onClick={() => onSelectClassic(classic.id)}
              type="button"
            >
              <div className="classic-card-header">
                <span className="classic-category-badge">{categoryLabel(classic.category)}</span>
                <span className="classic-duration-badge">
                  {classic.duration_minutes}分鐘
                </span>
              </div>
              <h3 className="classic-title">{classic.title}</h3>
              <p className="classic-author">{classic.author}</p>
              <p className="classic-desc">{classic.description}</p>
              <div className="classic-tags">
                {classic.tags.map((tag) => (
                  <span key={tag} className="classic-tag">
                    {tag}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      )}

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
