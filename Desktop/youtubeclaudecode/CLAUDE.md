# CLAUDE.md — YouTube AI Factory v3.0

> **Project:** AI-powered Bible Explainer video production pipeline
> **Architecture:** brain/ (shared logic) → skills (execution) → channels/ (output)
> **Isolation:** Độc lập hoàn toàn với trading-system.

---

## PROJECT PURPOSE

Bộ công cụ AI pipeline sản xuất video YouTube Bible Explainer. 3 skill chính + shared config system:

| Skill | Trigger Phrases | Output |
|-------|----------------|--------|
| **script-bible-explainer** | "viết script", "Bible script", "Every X Explained", "kịch bản" | Script 3,500-4,000 từ English TTS-ready |
| **image-bible-explainer** | "tạo ảnh", "watercolor Bible", "image prompts" | [N] prompts English cho Google Flow |
| **thumbnail-bible-explainer** | "thumbnail", "thumb Bible", "tạo thumb" | 6 prompts (3 var × 2 ver) |

---

## NGÔN NGỮ & PHONG CÁCH

* Giao tiếp **tiếng Việt**, thuật ngữ kỹ thuật để tiếng Anh.
* Ngắn gọn, có cấu trúc. Không lan man.
* Hỏi config TRƯỚC KHI generate.
* Prompt ảnh/thumbnail: LUÔN bằng **tiếng Anh**.

---

## HÀNH ĐỘNG TỰ ĐỘNG

* **"viết script [topic]"**, **"Bible script"** → script-bible-explainer
* **"tạo ảnh"**, **"image prompt"** → image-bible-explainer
* **"thumbnail"**, **"tạo thumb"** → thumbnail-bible-explainer
* **"video mới"**, **"full production"** → workflow 9 bước (brain/workflows/full-production.md)
* **"xuất bản"**, **"publish"** → publishing checklist

---

## ARCHITECTURE (v3.0)

```
brain/prompts/style-signature.md     ← SINGLE SOURCE OF TRUTH: colors, watercolor, fonts
brain/prompts/color-palette.md       ← Exact hex codes
brain/prompts/competitor-brief.md    ← Competitor intel + patterns
brain/templates/                     ← Reusable templates
brain/workflows/                     ← Multi-step workflows

channels/bible-explainer/            ← Channel output
  ├── scripts/    ← Final scripts (.md)
  ├── images/     ← Prompts + generated .jpeg
  ├── thumbnails/ ← Prompts + generated .jpeg
  ├── audio/      ← TTS .mp3
  ├── video/      ← Final .mp4
  └── publishing/ ← Logs + A/B test results

automation/                          ← Utility scripts
  ├── new-video.sh                   ← Scaffold project
  ├── organize-output.sh             ← Move files to channels/
  └── publish-checklist.sh           ← Pre-upload verification

archive/                             ← Old/completed projects
configs/channels.json                ← Channel registry
```

**Nguyên tắc:** `brain/prompts/style-signature.md` là single source of truth. Mọi skill tham chiếu từ đó — KHÔNG duplicate.

---

## STYLE SYSTEM (Quick Ref)

**Visual:** Watercolor + hand-drawn ink outlines + white/cream background. Middle Eastern characters. 16:9.

**Colors:** `#1E2A4A` navy | `#B25D29` burnt orange | `#F5EBD8` cream | `#8B6F47` sepia

**Typography:** Cinzel Bold (title, ALL CAPS, `#1E2A4A`) + Playfair (subtitle, `#B25D29`). Google Fonts.

**Script:** 3-Act + 3,500-4,000 từ + "you" ≥60 + zero brackets + TTS-ready.

Full spec: `brain/prompts/style-signature.md`

---

## WORKFLOW 9 BƯỚC

```
IDEA → RESEARCH → SCRIPT → IMAGE PROMPTS → THUMBNAIL → TTS → VIDEO ASSEMBLY → EXPORT → UPLOAD
```

Xem: `brain/workflows/full-production.md`

---

## NAMING CONVENTIONS

| Loại | Format | Ví dụ |
|------|--------|-------|
| Script file | `[topic]_[YYYYMMDD].md` | `fear-not_20260521.md` |
| Image prompt | `img_[NN]_[scene].md` | `img_01_paul-writing.md` |
| Generated image | `Watercolor_[desc]_[timestamp].jpeg` | (auto từ Flow) |
| Thumbnail prompt | `thumb_[pattern]_[var]_[ver].md` | `thumb_a_v1_with-text.md` |
| Channel dir | `kebab-case` | `bible-explainer` |
| Topic dir | `kebab-case` | `fear-not` |

---

## ANTI-CONTAMINATION

* KHÔNG load file từ `/Users/ttcenter/trading-system/`
* KHÔNG dùng trading commands (/open, /close, /scalp-sniper...)
* KHÔNG kết nối TradingView MCP
* Muốn trading → `cd ~/trading-system`

Đây là **VIDEO PRODUCTION STUDIO** — không phải trading desk.

---

> **Version:** v3.0.0 | **Refactored:** 2026-05-21
> **Single source of truth:** brain/prompts/style-signature.md
