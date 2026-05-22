# YouTube AI Factory — Bible Explainer Production Studio

AI-powered production pipeline cho kênh YouTube Bible Explainer. Từ ý tưởng đến video published trong 3 sessions.

---

## Quick Start

```bash
cd ~/Desktop/youtubeclaudecode
# Nói "video mới" để bắt đầu full production
# Hoặc gọi từng skill:
#   "viết script về [chủ đề]" → script-bible-explainer
#   "tạo ảnh cho script"        → image-bible-explainer
#   "tạo thumbnail"             → thumbnail-bible-explainer
```

---

## Cấu trúc

```
youtubeclaudecode/
├── brain/                     ← AI prompts, templates, workflows
│   ├── skills/                ← (symlinks to root SKILL.md dirs)
│   ├── prompts/               ← Single source of truth: style, colors, competitors
│   ├── templates/             ← Reusable templates
│   └── workflows/             ← Multi-step workflow definitions
│
├── channels/                  ← Output per channel (multi-channel ready)
│   └── bible-explainer/       ← Channel 1
│       ├── scripts/           ← Final scripts
│       ├── images/            ← Generated images
│       ├── thumbnails/        ← Generated thumbnails
│       ├── audio/             ← TTS output
│       ├── video/             ← Final video files
│       └── publishing/        ← Publishing logs + A/B test results
│
├── assets/                    ← Shared assets (fonts, logos, templates)
├── archive/                   ← Old/completed projects
├── configs/                   ← Channel configs
├── automation/                ← Utility scripts
├── script-bible-explainer/    ← Skill: viết kịch bản
├── image-bible-explainer/     ← Skill: tạo prompt ảnh
├── thumbnail-bible-explainer/ ← Skill: tạo thumbnail
└── img/, thumb/               ← Legacy output (đang migrate sang channels/)
```

---

## Workflow 9 Bước

```
IDEA → RESEARCH → SCRIPT → IMAGE PROMPTS → THUMBNAIL → TTS → VIDEO ASSEMBLY → EXPORT → UPLOAD
```

Xem chi tiết: [brain/workflows/full-production.md](brain/workflows/full-production.md)

---

## 3 Skills

| Skill | Trigger | Output |
|-------|---------|--------|
| **script-bible-explainer** | "viết script", "Bible script" | Script 3,500-4,000 từ English TTS-ready |
| **image-bible-explainer** | "tạo ảnh", "watercolor Bible" | [N] prompt ảnh English cho Google Flow |
| **thumbnail-bible-explainer** | "thumbnail", "Bible thumb" | 6 prompt thumbnail (3 var × 2 ver) |

---

## Style System

Mọi visual dùng chung **Watercolor Bible Illustration** style:
- Watercolor + hand-drawn ink outlines
- White/cream paper background
- Palette: `#1E2A4A` navy, `#B25D29` burnt orange, `#F5EBD8` cream
- Cinzel/Playfair typography
- Middle Eastern accurate characters

Single source of truth: [brain/prompts/style-signature.md](brain/prompts/style-signature.md)

---

## Tools

| Stage | Tool |
|-------|------|
| Script | Claude Code + script-bible-explainer |
| Images | Google Flow (Imagen 4) |
| Thumbnails | Google Flow + Canva |
| Voiceover | ElevenLabs TTS |
| Video Editing | CapCut / Premiere Pro |
| Publishing | YouTube Studio |

---

## Multi-Channel Scaling

Thêm channel mới:
```bash
mkdir -p channels/[channel-name]/{scripts,images,thumbnails,audio,video,publishing}
```

Shared brain/prompts/ dùng cho mọi channel. Mỗi channel có output riêng.
