export type Template = {
  id: string;
  name: string;
  description: string;
  hostCount: number;
  durationMin: number;
  script: string;
};

export const TEMPLATES: Template[] = [
  {
    id: "solo-5",
    name: "單人旁白 5分鐘",
    description: "適合故事朗讀或單人評論",
    hostCount: 1,
    durationMin: 5,
    script: `[主持人A]: 大家好，歡迎收聽今天的節目。
[主持人A]: 今天我想跟大家聊一個讓我最近很有感觸的話題。
[主持人A]: 請在這裡輸入您的內容，或使用「AI 生成」功能快速建立劇本。`,
  },
  {
    id: "dual-10",
    name: "雙人對談 10分鐘",
    description: "最受歡迎的 Podcast 格式",
    hostCount: 2,
    durationMin: 10,
    script: `[主持人A]: 大家好，歡迎收聽今天的節目！
[主持人B]: 很高興又和大家見面了，我是主持人B。
[主持人A]: 今天我們要討論一個非常有趣的話題，你準備好了嗎？
[主持人B]: 當然！我已經等不及想和大家分享了。
[主持人A]: 那我們就開始吧。
[主持人B]: 對，讓我們先從背景說起……`,
  },
  {
    id: "interview-15",
    name: "主持+來賓訪談 15分鐘",
    description: "適合訪談或深度問答",
    hostCount: 2,
    durationMin: 15,
    script: `[主持人A]: 大家好，今天我們有一位非常特別的來賓。
[主持人B]: 謝謝邀請，很高興能來到這個節目。
[主持人A]: 可以先跟聽眾自我介紹一下嗎？
[主持人B]: 當然，我從事這個領域已經有十年了……
[主持人A]: 哇，十年！那您一定有很多精彩的故事可以分享。
[主持人B]: 是的，其中有幾個經歷讓我記憶深刻。`,
  },
  {
    id: "roundtable-20",
    name: "四人圓桌討論 20分鐘",
    description: "多元觀點的深度對話",
    hostCount: 4,
    durationMin: 20,
    script: `[主持人A]: 歡迎各位來到今天的圓桌討論！
[主持人B]: 很高興能和大家一起探討這個主題。
[主持人C]: 我覺得這個議題非常值得深入討論。
[主持人D]: 同意，讓我們從不同的角度來看這個問題。
[主持人A]: 那我們就先從現況說起……`,
  },
];
