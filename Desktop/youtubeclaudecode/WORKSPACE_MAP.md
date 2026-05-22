# WORKSPACE_MAP.md — Final Architecture Map

> **Generated:** 2026-05-21
> **Version:** v3.0.0

---

## Complete Directory Tree

```
youtubeclaudecode/                        ← PROJECT ROOT
│
├── 📄 CLAUDE.md                          ← Project identity + auto-rules (loaded every session)
├── 📄 README.md                          ← Tổng quan cho người mới
├── 📄 WORKFLOW.md                        ← End-to-end pipeline (9 steps)
├── 📄 PROJECT_MAP.md                     ← Dependency graph + architecture rationale
├── 📄 STYLE_GUIDE.md                     ← Visual style quick reference (for humans)
├── 📄 NAMING_CONVENTIONS.md              ← File/directory naming rules
├── 📄 AUTOMATION_PLAN.md                 ← Automation roadmap (Phase 1-3)
├── 📄 CLEANUP_PLAN.md                    ← Migration log + cleanup instructions
├── 📄 WORKSPACE_MAP.md                   ← FILE NÀY — final architecture snapshot
│
├── 🧠 brain/                             ← SHARED AI LOGIC
│   ├── 📄 README.md
│   ├── prompts/                          ← SINGLE SOURCE OF TRUTH
│   │   ├── 📄 README.md
│   │   ├── 📄 index.md                   ← Prompt fragment map + reusable blocks
│   │   ├── 📄 style-signature.md         ← Visual constitution (watercolor, ink, typography)
│   │   ├── 📄 color-palette.md           ← Exact hex codes
│   │   └── 📄 competitor-brief.md        ← Đối thủ + pattern viral rates
│   ├── templates/                        ← Reusable structures
│   │   ├── 📄 README.md
│   │   ├── 📄 script-template.md         ← Script 3-Act structure + checklist
│   │   ├── 📄 image-prompt-template.md   ← Prompt format + consistency method
│   │   └── 📄 thumbnail-brief.md         ← 6 patterns + typography specs
│   └── workflows/                        ← Multi-step orchestration
│       ├── 📄 README.md
│       ├── 📄 full-production.md         ← Pipeline 9 bước
│       ├── 📄 script-only.md             ← Fast path: chỉ script
│       ├── 📄 visual-only.md             ← Fast path: chỉ images + thumbnail
│       └── 📄 rapid-thumbnail.md         ← Fast path: chỉ thumbnail
│
├── 🎬 channels/                          ← OUTPUT (multi-channel)
│   ├── 📄 README.md
│   └── bible-explainer/                  ← Channel 1 (active)
│       ├── 📄 README.md
│       ├── scripts/                      ← Final scripts (.md)
│       ├── images/fear-not/              ← 24 ảnh watercolor
│       ├── thumbnails/fear-not/          ← 3 thumbnails A/B test
│       ├── audio/                        ← TTS output (pending)
│       ├── video/                        ← Final rendered (pending)
│       └── publishing/                   ← Logs + A/B test results (pending)
│
├── 🎨 assets/                            ← SHARED RESOURCES
│   ├── 📄 README.md
│   ├── fonts/.gitkeep                    ← Cinzel, Playfair (tải từ Google Fonts)
│   ├── logos/.gitkeep                    ← Channel logos, watermarks
│   └── templates/.gitkeep                ← Canva templates, Premiere presets
│
├── ⚙️ automation/                        ← SCRIPTS
│   ├── 📄 README.md
│   ├── workflow.sh                       ← ⭐ Central dispatcher
│   ├── new-video.sh                      ← Scaffold project mới
│   ├── organize-output.sh                ← Di chuyển file vào channels/
│   └── publish-checklist.sh              ← Verify assets trước upload
│
├── ⚙️ configs/                           ← CONFIGURATION
│   ├── 📄 README.md
│   └── channels.json                     ← Channel registry
│
├── 📦 archive/                           ← OLD PROJECTS + BACKUPS
│   ├── 📄 README.md
│   ├── 2026-05-14-fear-not/              ← Video đầu tiên (ảnh + thumbnail gốc)
│   ├── backups/                          ← 3 ZIP files (May 2026)
│   ├── legacy/                           ← File hệ thống cũ
│   ├── legacy-modules/                   ← Modules v2 (đã migrate)
│   ├── legacy-workflows/                 ← Workflows v2 (đã migrate)
│   └── competitor-analysis.xlsx          ← Phân tích đối thủ gốc
│
├── 📊 logs/                              ← SYSTEM LOGS
│   ├── 📄 README.md
│   └── .gitkeep
│
├── 🎯 script-bible-explainer/            ← SKILL: Script writing
│   └── SKILL.md                          ← v3.0 thin (~150 dòng, refs brain/)
├── 🎯 image-bible-explainer/             ← SKILL: Image prompts
│   └── SKILL.md                          ← v3.0 thin (~110 dòng, refs brain/)
├── 🎯 thumbnail-bible-explainer/         ← SKILL: Thumbnail prompts
│   └── SKILL.md                          ← v3.0 thin (~120 dòng, refs brain/)
│
└── ⚙️ .claude/                           ← CLAUDE CODE CONFIG
    ├── 📄 README.md
    ├── settings.local.json               ← Project settings (no trading hooks)
    └── commands/                         ← 5 custom slash commands
        ├── new-video.md
        ├── generate-images.md
        ├── generate-thumb.md
        ├── export-video.md
        └── competitor-check.md
```

---

## File Count Summary

| Category | Files | Size |
|----------|-------|------|
| System docs | 8 | ~30KB |
| Brain (prompts + templates + workflows) | 12 | ~35KB |
| Skills (3 SKILL.md) | 3 | ~10.5KB |
| Automation scripts | 4 | ~3KB |
| Configs | 2 | ~1KB |
| README (modules) | 11 | ~8KB |
| Channel output | 27 (24 ảnh + 3 thumb) | ~75MB |
| Archive | 39 files | ~90MB |
| Claude config | 7 | ~3KB |
| **TOTAL** | **113 files** | **~170MB** |

---

## Data Flow

```
USER TRIGGER (ví dụ: "viết script về Noah")
    │
    ▼
CLAUDE.md ──pre-load──→ brain/prompts/style-signature.md
                        brain/prompts/competitor-brief.md
    │
    ▼
SKILL.md (script-bible-explainer)
    │ reference: brain/prompts/ + brain/templates/
    ▼
OUTPUT ──→ channels/bible-explainer/scripts/noah_20260521.md
```

---

## Key Design Decisions

1. **Single source of truth** — `brain/prompts/style-signature.md` là authoritative. Mọi skill tham chiếu, không copy.
2. **Thin skills** — SKILL.md chỉ chứa workflow logic unique. Style/colors/templates ở brain/.
3. **Multi-channel by default** — `channels/` structure cho phép scale không giới hạn.
4. **Archive không xoá** — Mọi file cũ được archive, không mất dữ liệu.
5. **Automation first** — Mỗi tác vụ lặp lại có script.
