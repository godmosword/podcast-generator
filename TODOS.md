# Wavescript TODOs

Wavescript 的產品定位先聚焦在「中文友善、多主持人、文稿一鍵生成播客」，避開完整錄音剪輯工作站的高複雜度，優先把從文稿到可下載成品的流程做紮實。

## P0 — 成熟 MVP 必要項

- [x] 建立 FastAPI backend 專案結構
  - [x] `POST /api/generate`：建立生成任務並透過 SSE 回報進度
  - [x] `POST /api/preview`：針對單段文字與聲線生成 15 秒試聽
  - [x] `GET /api/files/{id}`：下載 MP3/WAV 成品
  - [x] 統一錯誤格式與任務狀態：queued、parsing、synthesizing、mixing、exporting、done、failed

- [x] 補齊多主持人後端能力
  - [x] `script_parser` 回傳 speaker turns、speaker count、原始順序 index
  - [x] 支援無角色標記時自動歸為 `speaker_1`
  - [x] 限制 1–4 位主持人，超過時回傳可理解的錯誤
  - [x] 新增 `role_mapper`，支援自動映射與前端手動覆蓋
  - [x] 確保每段文字依照原始段落順序合併

- [x] 前端接上真 API
  - [x] Studio 表單送出 `/api/generate`
  - [x] 使用 EventSource 接收 SSE 進度
  - [x] 聲線試聽接 `/api/preview`
  - [x] 生成完成後顯示播放器與下載連結
  - [x] 顯示錯誤、重試與取消狀態

- [x] 音訊輸出品質升級
  - [x] 使用真 LUFS loudness normalization，目標 -16 LUFS
  - [x] 加入 limiter，避免合併與 BGM 後爆音
  - [x] BGM 支援淡入淡出與 ducking
  - [x] 支援 MP3/WAV 輸出格式
  - [x] 寫入 ID3 metadata：title、artist、album、year

- [x] Docker Compose 一鍵啟動
  - [x] backend Dockerfile
  - [x] frontend Dockerfile
  - [x] 根目錄 `docker-compose.yml`
  - [x] `output/` volume 掛載
  - [x] `.env.example` 補齊前後端設定

## P1 — 產品完成度

- [x] 內建配樂曲庫
  - [x] `assets/bgm/` 曲庫目錄與 manifest
  - [x] `GET /api/bgm` 曲庫 API
  - [x] `GET /api/bgm/{id}/preview` 試聽 API
  - [x] 前端曲庫選擇、試聽、音量與淡入淡出控制
  - [x] 生成時依 `bgm_id` 混入配樂

- [ ] 專案草稿與版本保存
  - [ ] 儲存 script、host count、voice mapping、audio settings
  - [ ] 支援 autosave
  - [ ] 支援重新打開舊專案並再次生成
  - [ ] 生成任務與輸出檔案建立可追蹤 id

- [ ] AI 輔助文稿
  - [ ] 從主題生成 podcast 大綱
  - [ ] 將大綱展開為 1–4 位主持人的對話稿
  - [ ] 支援語氣調整：輕鬆、專業、故事型、教學型
  - [ ] 自動產生節目標題、摘要、章節、show notes

- [ ] 聲線與角色體驗
  - [ ] 聲線清單由後端提供
  - [ ] 每個聲線顯示語言、性別、風格、provider
  - [ ] 避免同一節目中預設分配到過於相似的聲線
  - [ ] 顯示 provider 成本與可用性

- [ ] 更可靠的長文生成
  - [ ] chunking 支援中文與英文標點
  - [ ] 過長句子可硬切且不超過 provider 限制
  - [ ] provider 失敗時支援 retry/backoff
  - [ ] 任務中斷後可標記 failed，避免留下不可辨識檔案

## P2 — 對標成熟工具的進階能力

- [ ] 簡易音訊時間軸
  - [ ] 顯示 speaker clips 與 pause blocks
  - [ ] 支援調整段落停頓
  - [ ] 支援插入 intro/outro/BGM/sound effect
  - [ ] 支援重新生成單段，而不是整集重跑

- [ ] 後製與清理
  - [ ] 人聲 EQ/preset
  - [ ] 降噪或 Enhance Speech 類流程
  - [ ] silence trim
  - [ ] 每位主持人獨立音量

- [ ] 發佈與交付
  - [ ] 批次下載 project assets
  - [ ] 匯出章節時間戳
  - [ ] 匯出 show notes Markdown
  - [ ] 未來串接 YouTube、RSS hosting 或 podcast hosting 平台

## Engineering Hygiene

- [ ] 新增 backend tests
  - [x] parser tests
  - [x] role mapper tests
  - [x] BGM catalog tests
  - [x] BGM validation tests
  - [ ] TTS provider mock tests
  - [ ] exporter metadata tests

- [ ] 新增 frontend tests
  - [ ] host count picker interaction
  - [ ] voice slot update
  - [ ] generate progress states
  - [ ] mobile layout smoke test

- [x] 新增專案文件
  - [x] `README.md`：本機啟動、Docker 啟動、環境變數
  - [x] `ARCHITECTURE.md`：資料流、API、任務狀態、音訊管線
  - [x] `CONTRIBUTING.md`：開發流程與測試方式
