import { useEffect, useState } from "react";
import { Sparkles, X } from "lucide-react";
import { generateScript, type ScriptGenerationPayload } from "../api";

type Tone = ScriptGenerationPayload["tone"];
type Language = ScriptGenerationPayload["language"];

type Props = {
  hostCount: number;
  onClose: () => void;
  onScriptGenerated: (script: string) => void;
  initialExtraContext?: string;
};

const TONES: Array<{ value: Tone; label: string }> = [
  { value: "educational", label: "教育性" },
  { value: "entertainment", label: "娛樂性" },
  { value: "storytelling", label: "故事敘述" },
  { value: "interview", label: "訪談" },
  { value: "debate", label: "辯論" },
];

const LANGUAGES: Array<{ value: Language; label: string }> = [
  { value: "zh-TW", label: "繁體中文" },
  { value: "zh-CN", label: "简体中文" },
  { value: "en", label: "English" },
  { value: "ja", label: "日本語" },
];

export function ScriptGeneratorModal({ hostCount, onClose, onScriptGenerated, initialExtraContext }: Props) {
  const [topic, setTopic] = useState("");
  const [durationMin, setDurationMin] = useState(10);
  const [hosts, setHosts] = useState(hostCount);
  const [tone, setTone] = useState<Tone>("educational");
  const [language, setLanguage] = useState<Language>("zh-TW");
  const [extraContext, setExtraContext] = useState(initialExtraContext ?? "");

  useEffect(() => {
    if (initialExtraContext) setExtraContext(initialExtraContext);
  }, [initialExtraContext]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [generated, setGenerated] = useState<string | null>(null);

  async function handleGenerate() {
    if (!topic.trim()) return;
    setIsGenerating(true);
    setError(null);
    setWarnings([]);
    setGenerated(null);
    try {
      const result = await generateScript({
        topic: topic.trim(),
        duration_min: durationMin,
        host_count: hosts,
        tone,
        language,
        extra_context: extraContext.trim() || undefined,
      });
      setWarnings(result.warnings);
      setGenerated(result.script);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  function handleApply() {
    if (generated) {
      onScriptGenerated(generated);
      onClose();
    }
  }

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-box">
        <div className="modal-header">
          <h3>AI 生成劇本</h3>
          <button className="icon-button" onClick={onClose} type="button" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <label className="modal-field">
            <span>主題</span>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="例如：AI 如何改變未來的工作方式"
              maxLength={200}
              rows={2}
            />
          </label>

          <div className="modal-row">
            <div className="modal-field">
              <span>時長</span>
              <div className="segmented">
                {[5, 10, 15, 20].map((min) => (
                  <button
                    key={min}
                    className={durationMin === min ? "selected" : ""}
                    onClick={() => setDurationMin(min)}
                    type="button"
                  >
                    {min}分
                  </button>
                ))}
              </div>
            </div>

            <div className="modal-field">
              <span>主持人數</span>
              <div className="segmented">
                {[1, 2, 3, 4].map((n) => (
                  <button
                    key={n}
                    className={hosts === n ? "selected" : ""}
                    onClick={() => setHosts(n)}
                    type="button"
                  >
                    {n}人
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="modal-row">
            <label className="modal-field">
              <span>風格</span>
              <select value={tone} onChange={(e) => setTone(e.target.value as Tone)}>
                {TONES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="modal-field">
              <span>語言</span>
              <select value={language} onChange={(e) => setLanguage(e.target.value as Language)}>
                {LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="modal-field">
            <span>補充說明（選填）</span>
            <textarea
              value={extraContext}
              onChange={(e) => setExtraContext(e.target.value)}
              placeholder="例如：面向科技初學者，輕鬆愉快的語調"
              maxLength={500}
              rows={2}
            />
          </label>

          {warnings.length > 0 && (
            <div className="modal-warnings">
              {warnings.map((w, i) => (
                <p key={i}>{w}</p>
              ))}
            </div>
          )}

          {error && <div className="modal-error">{error}</div>}

          {generated && (
            <div className="modal-preview">
              <p className="modal-preview-label">預覽（前200字）</p>
              <pre>{generated.slice(0, 200)}{generated.length > 200 ? "…" : ""}</pre>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button onClick={onClose} type="button">
            取消
          </button>
          {generated ? (
            <button className="primary-action" onClick={handleApply} type="button">
              <Sparkles size={16} />
              套用劇本
            </button>
          ) : (
            <button
              className="primary-action"
              onClick={handleGenerate}
              disabled={!topic.trim() || isGenerating}
              type="button"
            >
              <Sparkles size={16} />
              {isGenerating ? "生成中…" : "生成劇本"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
