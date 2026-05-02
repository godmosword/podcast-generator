import { ArrowRight, Mic, Moon, Music, Sparkles, Sun } from "lucide-react";
import { Link } from "react-router-dom";
import { useDarkMode } from "../hooks/useDarkMode";

const FEATURES = [
  {
    icon: <Sparkles size={22} />,
    title: "AI 智能腳本",
    body: "貼入任何文字或輸入主題，Gemini 自動分析邏輯結構與邊界條件，生成流暢的多人對話稿。",
    delay: "320ms",
  },
  {
    icon: <Mic size={22} />,
    title: "多語音角色",
    body: "20+ 種真人語音，繁體中文、英文、日文皆支援，一鍵試聽，靈活分配給每位主持人。",
    delay: "400ms",
  },
  {
    icon: <Music size={22} />,
    title: "BGM 混音輸出",
    body: "內建配樂曲庫，自動淡入淡出、LUFS 標準化，一鍵匯出 MP3 / WAV 成品。",
    delay: "480ms",
  },
];

export function Landing() {
  const [dark, setDark] = useDarkMode();

  return (
    <main className="landing-shell">
      <nav className="landing-nav">
        <div className="landing-nav-logo">
          <Sparkles size={21} />
        </div>
        <div className="landing-nav-brand">
          <strong>Wavescript</strong>
          <span>AI Podcast Generator</span>
        </div>
        <div className="landing-nav-actions">
          <button
            className="icon-button theme-toggle"
            onClick={() => setDark((d) => !d)}
            type="button"
            aria-label={dark ? "切換淺色模式" : "切換深色模式"}
            title={dark ? "淺色模式" : "深色模式"}
          >
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link to="/studio" className="landing-nav-link">
            進入 Studio
            <ArrowRight size={15} />
          </Link>
        </div>
      </nav>

      <section className="landing-hero">
        <span className="landing-eyebrow animate-fade-in-up" style={{ animationDelay: "0ms" }}>
          AI Podcast Generator
        </span>
        <h1
          className="animate-fade-in-up"
          style={{ animationDelay: "80ms" }}
        >
          讓任何文字，<em>成為一集 Podcast</em>
        </h1>
        <p className="animate-fade-in-up" style={{ animationDelay: "160ms" }}>
          從主題或文稿到可下載的播客成品，Wavescript 以 AI 分析邏輯、生成劇本、
          合成語音、混入配樂，全流程一鍵完成。
        </p>
        <div className="landing-ctas animate-fade-in-up" style={{ animationDelay: "240ms" }}>
          <Link to="/studio" className="landing-cta-primary">
            <Sparkles size={17} />
            開始創作
          </Link>
          <a href="#features" className="landing-cta-secondary">
            了解功能
            <ArrowRight size={15} />
          </a>
        </div>
      </section>

      <section className="features-section" id="features">
        <p className="features-section-label">核心功能</p>
        <div className="features-grid">
          {FEATURES.map((f) => (
            <article
              key={f.title}
              className="feature-card animate-fade-in-up"
              style={{ animationDelay: f.delay }}
            >
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </article>
          ))}
        </div>
      </section>

      <footer className="landing-footer">
        <span>© {new Date().getFullYear()} Wavescript — Powered by Gemini AI</span>
      </footer>
    </main>
  );
}
