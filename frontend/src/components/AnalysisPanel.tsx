import { useState } from "react";
import { CheckCircle, ChevronRight } from "lucide-react";
import { analyzeText, type AnalysisFinding, type AnalysisResult } from "../api";

type Props = {
  script: string;
  onApplyContext: (enrichedContext: string) => void;
};

const BADGE_LABEL: Record<AnalysisFinding["type"], string> = {
  gap: "缺口",
  boundary: "邊界條件",
  suggestion: "建議",
  strength: "優點",
};

function ScoreRing({ score }: { score: number }) {
  const r = 20;
  const circumference = 2 * Math.PI * r;
  const dash = (score / 100) * circumference;

  return (
    <svg width="48" height="48" viewBox="0 0 48 48" className="analysis-score-wrap" aria-label={`邏輯評分 ${score}`}>
      <circle cx="24" cy="24" r={r} fill="none" stroke="var(--teal-bg)" strokeWidth="4" />
      <circle
        cx="24"
        cy="24"
        r={r}
        fill="none"
        stroke="var(--teal)"
        strokeWidth="4"
        strokeDasharray={`${dash} ${circumference}`}
        strokeLinecap="round"
        transform="rotate(-90 24 24)"
      />
      <text x="24" y="28" textAnchor="middle" fontSize="11" fontWeight="800" fill="var(--ink-1)">
        {score}
      </text>
    </svg>
  );
}

function FindingBadge({ type }: { type: AnalysisFinding["type"] }) {
  return (
    <span className={`finding-badge finding-badge-${type}`}>
      {BADGE_LABEL[type]}
    </span>
  );
}

export function AnalysisPanel({ script, onApplyContext }: Props) {
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canAnalyze = script.trim().length >= 50;

  async function handleAnalyze() {
    setStatus("loading");
    setError(null);
    setResult(null);
    try {
      const res = await analyzeText({ text: script, language: "zh-TW" });
      setResult(res);
      setStatus("done");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "分析失敗，請稍後再試。");
      setStatus("error");
    }
  }

  return (
    <div>
      <button
        className="analysis-trigger"
        type="button"
        disabled={!canAnalyze || status === "loading"}
        onClick={handleAnalyze}
        title={canAnalyze ? "分析文本的邏輯結構與邊界條件" : "請先輸入至少 50 個字元"}
      >
        {status === "loading" ? (
          <>
            <span className="analysis-spinner" />
            分析中…
          </>
        ) : (
          <>
            <ChevronRight size={14} />
            分析邏輯
          </>
        )}
      </button>

      {status === "loading" && (
        <div className="analysis-panel">
          <div className="analysis-spinner-wrap">
            <span className="analysis-spinner" />
            <span>Gemini 正在分析邏輯結構與邊界條件…</span>
          </div>
        </div>
      )}

      {status === "error" && error && (
        <div className="analysis-panel">
          <p className="analysis-error">{error}</p>
        </div>
      )}

      {status === "done" && result && (
        <div className="analysis-panel">
          <div className="analysis-header">
            <ScoreRing score={result.logical_score} />
            <p className="analysis-summary">{result.summary}</p>
          </div>

          {result.findings.length > 0 && (
            <div className="analysis-findings">
              {result.findings.map((f, i) => (
                <div key={i} className="analysis-finding">
                  <FindingBadge type={f.type} />
                  <span>{f.content}</span>
                </div>
              ))}
            </div>
          )}

          {result.enriched_context && (
            <button
              className="analysis-apply-btn"
              type="button"
              onClick={() => onApplyContext(result.enriched_context)}
            >
              <CheckCircle size={15} />
              套用分析，前往 AI 生成
            </button>
          )}
        </div>
      )}
    </div>
  );
}
