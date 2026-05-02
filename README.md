# Wavescript

**Languages:** [繁體中文](#繁體中文) | [English](#english) | [日本語](#日本語)

---

## 繁體中文

Wavescript 是一個中文友善的 AI Podcast 生成器。你可以貼上有角色標記的文稿，為 1-4 位主持人分配聲線，試聽聲音，透過 SSE 查看生成進度，最後輸出可下載的 MP3/WAV 節目檔。

目前專案包含 FastAPI 後端、React/Vite 前端 Studio UI，以及可供 CLI 和 API 共用的 Python 音訊管線。

### 功能特色

- 支援 1-4 位主持人的文字轉 Podcast 生成
- 支援 `[主持人A]: 內容` 角色標記
- 自動偵測講者並映射到聲線
- 預設使用 OpenAI TTS，並保留 Edge TTS / ElevenLabs provider 模組
- AI 文稿生成與分析使用 Gemini
- 單段聲線試聽
- Server-Sent Events 即時生成進度
- MP3/WAV 輸出
- MP3 ID3 metadata
- LUFS 正規化，並提供 dBFS fallback
- Peak limiting、淡入淡出、BGM 混音
- 內建配樂曲庫，支援試聽、音量與淡入淡出控制
- Docker Compose 一鍵啟動前後端

### 專案結構

```text
.
├── backend/              # FastAPI API server
├── assets/bgm/           # 內建配樂曲庫
├── core/                 # Parser、role mapping、audio processing、exporter
├── frontend/             # React + Vite Studio UI
├── pipeline/             # 共用 Podcast 生成流程
├── providers/            # TTS provider implementations
├── utils/                # File、text chunking、SSML helpers
├── docker-compose.yml
├── main.py               # Typer CLI entry point
├── requirements.txt
└── TODOS.md
```

### 需求

- Python 3.12+ 建議
- Node.js 22+ 建議
- Docker，可選
- 本機音訊輸出需要 `ffmpeg`

Docker backend image 會自動安裝 `ffmpeg`。如果你直接在本機跑 backend，需要自行安裝 `ffmpeg`。

### 環境變數

從 `.env.example` 建立 `.env`：

```env
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3-flash-preview
APP_ENV=development
BGM_PATH=
TTS_PROVIDER=edge
OUTPUT_DIR=output
JOB_TTL_SECONDS=21600
CORS_ORIGINS=http://localhost:3000
TRUST_PROXY_HEADERS=false
TRUSTED_PROXY_CIDRS=
RATE_LIMIT_GENERATE_PER_MINUTE=5
RATE_LIMIT_PREVIEW_PER_MINUTE=20
RATE_LIMIT_AI_PER_MINUTE=10
VITE_API_BASE_URL=http://localhost:8000
```

Edge TTS 是預設 provider，TTS 不需要 API key。若改用 OpenAI TTS，需要 `OPENAI_API_KEY`。若使用 ElevenLabs 聲線或帳號內的自訂/clone voices，需要 `ELEVENLABS_API_KEY`。AI 文稿生成與分析需要 `GEMINI_API_KEY`。

正式環境請設定 `APP_ENV=production`，並把 `CORS_ORIGINS` 改成實際前端網域；production 模式不允許空值或 `*`。若 backend 位於 CDN 或反向代理後方，請設定 `TRUST_PROXY_HEADERS=true` 並填入可信代理的 `TRUSTED_PROXY_CIDRS`，否則限流會使用直接連線 IP。

### Docker 啟動

```bash
docker compose up --build
```

開啟：

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API health: `http://localhost:8000/api/health`

Docker backend 會以非 root 使用者執行。若使用 `./output:/app/output` bind mount，請確保主機上的 `output/` 目錄允許容器使用者寫入。

### 本機開發

安裝 Python dependencies：

```bash
python3 -m pip install -r requirements.txt
```

安裝 frontend dependencies：

```bash
cd frontend
npm install
```

啟動 backend：

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

另一個 terminal 啟動 frontend：

```bash
cd frontend
npm run dev
```

開啟 `http://localhost:3000`。

### CLI 使用

從文稿生成 MP3：

```bash
python3 main.py generate --script sample_multi.txt --output output/sample.mp3
```

列出中文 Edge TTS 聲線：

```bash
python3 main.py voices
```

### 文稿格式

```text
[主持人A]: 大家好，歡迎收聽 Wavescript。
[主持人B]: 今天我們來聊聊 AI 如何改變日常創作。
---PAUSE:0.5s---
[主持人A]: 我們會從文稿、聲線到輸出流程一路拆解。
```

支援：

- `[Speaker]: text`
- `[Speaker]：text`
- `---PAUSE:1.5s---`
- 純文字，若沒有角色標記，會視為單一講者

### 內建配樂

把 MP3 或 WAV 放到 `assets/bgm/`，Wavescript 會掃描曲庫並透過 `GET /api/bgm` 提供給前端。

你也可以在 `assets/bgm/manifest.json` 補曲目資訊：

```json
[
  {
    "id": "warm-intro",
    "title": "Warm Intro",
    "mood": "warm",
    "filename": "warm-intro.mp3",
    "duration": 30
  }
]
```

如果沒有放入音檔，前端會顯示空曲庫狀態，生成時不會混入配樂。

### API 總覽

- `GET /api/health`：檢查 backend 狀態
- `GET /api/voices`：取得聲線清單
- `GET /api/bgm`：取得內建配樂曲庫
- `GET /api/bgm/{id}/preview`：串流配樂試聽
- `POST /api/preview`：生成短聲線試聽
- `POST /api/generate`：建立生成任務
- `GET /api/generate/{id}`：取得任務狀態
- `GET /api/generate/{id}/events`：SSE 進度串流
- `GET /api/files/{id}`：下載輸出音檔

### 測試與檢查

```bash
python3 -m compileall backend core pipeline providers utils main.py config.py
python3 -m unittest
```

```bash
cd frontend
npm run build
```

```bash
docker compose config --quiet
```

### 目前限制

- 任務狀態存在記憶體，backend 重啟後會清空
- 同一個生成任務目前不支援混用多個 TTS provider
- 專案草稿、autosave、永久歷史紀錄、時間軸編輯尚未實作
- 本機非 Docker 生成音訊需要安裝 `ffmpeg`
- 配樂目前限內建 `assets/bgm/` 曲庫，尚未支援使用者上傳

### 授權

MIT. See [LICENSE](LICENSE).

---

## English

Wavescript is a Chinese-friendly AI podcast generator. It converts marked-up scripts into multi-host podcast episodes with voice assignment, voice preview, SSE progress updates, audio post-processing, and downloadable MP3/WAV output.

### Highlights

- Generate podcasts for 1-4 hosts from text scripts
- Use speaker tags like `[Host A]: dialogue`
- Auto-detect speakers and map them to voices
- OpenAI TTS by default, with optional Edge TTS and ElevenLabs provider modules
- Gemini for AI script generation and analysis
- Voice preview and real-time generation progress
- MP3/WAV export with MP3 ID3 metadata
- LUFS normalization, peak limiting, fades, and optional BGM mixing
- Built-in background music catalog with preview, volume, and fade controls
- Docker Compose setup for frontend and backend

### Quick Start With Docker

```bash
docker compose up --build
```

Open:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Health check: `http://localhost:8000/api/health`

### Local Development

```bash
python3 -m pip install -r requirements.txt
```

```bash
cd frontend
npm install
```

Run the backend:

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Run the frontend:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

### Script Format

```text
[Host A]: Welcome to Wavescript.
[Host B]: Today we are talking about AI podcast production.
---PAUSE:0.5s---
[Host A]: Let's walk through scripts, voices, and export.
```

Supported syntax:

- `[Speaker]: text`
- `[Speaker]：text`
- `---PAUSE:1.5s---`
- Plain text, treated as a single speaker when no speaker tags are present

### Background Music

Place MP3 or WAV files in `assets/bgm/`. Wavescript scans the folder and exposes tracks through `GET /api/bgm`.

Optional metadata can be added in `assets/bgm/manifest.json`:

```json
[
  {
    "id": "warm-intro",
    "title": "Warm Intro",
    "mood": "warm",
    "filename": "warm-intro.mp3",
    "duration": 30
  }
]
```

### Checks

```bash
python3 -m compileall backend core pipeline providers utils main.py config.py
python3 -m unittest
```

```bash
cd frontend
npm run build
```

```bash
docker compose config --quiet
```

### Limitations

- Jobs are stored in memory.
- Mixed TTS providers in one generation job are not supported yet.
- Drafts, autosave, persistent history, and timeline editing are planned but not implemented yet.
- Local audio generation requires `ffmpeg` outside Docker.
- User-uploaded BGM is not implemented yet.

### License

MIT. See [LICENSE](LICENSE).

---

## 日本語

Wavescript は、中国語に強い AI Podcast 生成ツールです。話者タグ付きの台本から、複数ホストの Podcast 音声を生成し、声の割り当て、試聴、進捗表示、音声後処理、MP3/WAV 出力まで行えます。

### 主な機能

- 1-4 人のホストに対応
- `[主持人A]: テキスト` のような話者タグをサポート
- 話者の自動検出と voice mapping
- デフォルトは OpenAI TTS、Edge TTS / ElevenLabs provider も用意
- AI 台本生成と分析には Gemini を使用
- 声のプレビュー
- SSE による生成進捗
- MP3/WAV 出力
- LUFS normalization、peak limiting、fade、BGM mix
- 内蔵 BGM ライブラリ、試聴、音量、fade 調整
- Docker Compose で frontend/backend を起動

### Docker で起動

```bash
docker compose up --build
```

開く URL:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Health check: `http://localhost:8000/api/health`

### ローカル開発

```bash
python3 -m pip install -r requirements.txt
```

```bash
cd frontend
npm install
npm run dev
```

別 terminal で backend を起動:

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 台本フォーマット

```text
[主持人A]: 大家好，歡迎收聽 Wavescript。
[主持人B]: 今天我們來聊聊 AI 如何改變日常創作。
---PAUSE:0.5s---
[主持人A]: 我們會從文稿、聲線到輸出流程一路拆解。
```

話者タグがない場合は、単一話者として処理されます。

### BGM

MP3 または WAV を `assets/bgm/` に入れると、`GET /api/bgm` 経由で frontend に表示されます。曲名や mood は `assets/bgm/manifest.json` で指定できます。

### ライセンス

MIT. See [LICENSE](LICENSE).
