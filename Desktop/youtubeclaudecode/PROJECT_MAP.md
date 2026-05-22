# PROJECT_MAP.md — Architecture & Dependency Map

> **Version:** v3.0.0
> **Last updated:** 2026-05-21

---

## Architecture Philosophy

```
CONSTITUTION (brain/prompts/)     ← Single source of truth
    ↓
TEMPLATES (brain/templates/)      ← Reusable structures
    ↓
SKILLS (3 SKILL.md files)         ← Execution engines (thin, reference ↑)
    ↓
WORKFLOWS (brain/workflows/)      ← Multi-step orchestration
    ↓
OUTPUT (channels/)                ← Per-channel deliverables
```

---

## File Dependency Graph

```
style-signature.md ◄──── color-palette.md
       ◄──────────────── script-template.md
       ◄──────────────── image-prompt-template.md
       ◄──────────────── thumbnail-brief.md
       ◄──────────────── competitor-brief.md
       ◄──────────────── script-bible-explainer/SKILL.md
       ◄──────────────── image-bible-explainer/SKILL.md
       ◄──────────────── thumbnail-bible-explainer/SKILL.md

competitor-brief.md ◄─── script-bible-explainer/SKILL.md
                    ◄─── thumbnail-bible-explainer/SKILL.md

full-production.md ◄─── ALL 3 SKILLs
script-only.md     ◄─── script-bible-explainer
visual-only.md     ◄─── image + thumbnail skills
rapid-thumbnail.md ◄─── thumbnail-bible-explainer
```

---

## Loading Order (Claude Code Session)

```
1. CLAUDE.md                          ← Project identity + auto-rules
2. brain/prompts/style-signature.md   ← Visual constitution (pre-loaded)
3. brain/prompts/competitor-brief.md  ← Market context (pre-loaded)
4. [Triggered Skill SKILL.md]         ← Loaded on demand
   └── References brain/prompts/ + brain/templates/
```

---

## Single Source of Truth Map

| Concept | Authoritative File | DO NOT Duplicate In |
|---------|-------------------|---------------------|
| Color hex codes | `brain/prompts/color-palette.md` | Skills, templates |
| Watercolor specs | `brain/prompts/style-signature.md` | Skills |
| Typography | `brain/prompts/style-signature.md` | Skills |
| Negative prompts | `brain/prompts/style-signature.md` | Skills |
| Competitor data | `brain/prompts/competitor-brief.md` | Skills |
| Script structure | `brain/templates/script-template.md` | Skills |
| Image prompt format | `brain/templates/image-prompt-template.md` | Skills |
| Thumbnail patterns | `brain/templates/thumbnail-brief.md` | Skills |
| 9-step pipeline | `brain/workflows/full-production.md` | README, CLAUDE.md |

---

## Channel Data Flow

```
brain/ (shared logic)
    ↓
[Skill execution]
    ↓
channels/[channel-name]/
    ├── scripts/      ← .md files
    ├── images/       ← prompts.md + .jpeg
    ├── thumbnails/   ← prompts.md + .jpeg
    ├── audio/        ← .mp3
    ├── video/        ← .mp4
    └── publishing/   ← _log.md
```

---

## Multi-Channel Scaling

```
channels/
├── bible-explainer/       ← Active
├── [christian-history]/   ← Future
├── [bible-biographies]/   ← Future
└── [theology-explained]/  ← Future
```

Mỗi channel:
- Dùng chung `brain/prompts/` (style, colors, competitors)
- Có thể có template riêng trong `brain/templates/[channel]/`
- Output riêng trong `channels/[name]/`
