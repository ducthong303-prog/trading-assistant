# Migration Plan — YouTube AI Project Isolation

> **Ngày:** 2026-05-21
> **Mục tiêu:** Tách hoàn toàn YouTube AI Production Studio khỏi trading-system
> **Nguy��n tắc:** KHÔNG delete, chỉ analyze + propose + migrate safely

---

## 1. DEPENDENCY MAP

### Trước migration (current state)

```
~/.claude/                              ← GLOBAL (dùng chung)
├── commands → trading-system/brain/commands    ❌ 34 trading commands
├── modules  → trading-system/brain/modules     ❌ 10 trading modules
├── shared   → trading-system/brain/shared      ❌ 22 trading schemas
├── .mcp.json (TradingView MCP)                 ❌ TV server config
├── settings.json (API key + trading hooks)     ⚠️  Shared config
└── projects/-Users-ttcenter/memory/            ❌ 24 trading memories

/Users/ttcenter/CLAUDE.md                       ❌ 18KB trading instructions

/Users/ttcenter/Desktop/youtubeclaudecode/      ← PROJECT (no isolation)
├── KHÔNG có CLAUDE.md                          ❌ Falls back to global
├── KHÔNG có .claude/                           ❌ Falls back to global
├── script-bible-explainer/SKILL.md             ✅ YouTube-specific
├── image-bible-explainer/SKILL.md               ✅ YouTube-specific
└── thumbnail-bible-explainer/SKILL.md           ✅ YouTube-specific
```

### Sau migration (target state)

```
/Users/ttcenter/Desktop/youtubeclaudecode/      ← PROJECT (fully isolated)
├── CLAUDE.md                                   ✅ Project identity
├── .claude/                                    ✅ Project config
│   ├── settings.local.json                     ✅ No trading hooks
│   ├── commands-youtube/ (5 files)             ✅ YouTube commands
│   ├── modules-youtube/ (3 files)              ✅ YouTube knowledge
│   └── workflows-youtube/ (2 files)            ✅ YouTube workflows
├── script-bible-explainer/SKILL.md             ✅ (unchanged)
├── image-bible-explainer/SKILL.md               ✅ (unchanged)
├── thumbnail-bible-explainer/SKILL.md           ✅ (unchanged)
├── scripts/cleanup_output.sh                   ✅ NEW
└── output/                                     ✅ NEW organized output

~/.claude/projects/-Users-ttcenter-Desktop-youtubeclaudecode/memory/
├── MEMORY.md                                   ✅ Project memory index
├── project_architecture.md                     ✅
├── reference_style_quick.md                    ✅
├── reference_script_rules.md                   ✅
└── reference_competitors.md                    ✅
```

---

## 2. WHAT WAS CREATED

| File | Purpose | Size |
|------|---------|------|
| `CLAUDE.md` | Project identity, auto-rules, style system, workflow | ~5KB |
| `.claude/settings.local.json` | Project settings (no trading hooks) | ~0.3KB |
| `.claude/commands-youtube/new-video.md` | `/new-video` command | ~0.8KB |
| `.claude/commands-youtube/generate-images.md` | `/generate-images` command | ~0.9KB |
| `.claude/commands-youtube/generate-thumb.md` | `/generate-thumb` command | ~1.0KB |
| `.claude/commands-youtube/export-video.md` | `/export-video` command | ~1.2KB |
| `.claude/commands-youtube/competitor-check.md` | `/competitor-check` command | ~0.8KB |
| `.claude/modules-youtube/style-system.md` | Watercolor style specs | ~3.5KB |
| `.claude/modules-youtube/script-architecture.md` | Script structure & rules | ~4.5KB |
| `.claude/modules-youtube/publishing-pipeline.md` | Publishing workflow | ~3.0KB |
| `.claude/workflows-youtube/full-video-production.md` | End-to-end workflow | ~2.5KB |
| `.claude/workflows-youtube/rapid-thumbnail.md` | Thumbnail-only workflow | ~1.0KB |
| `scripts/cleanup_output.sh` | Output organizer | ~0.3KB |
| Memory: MEMORY.md + 4 files | Project-specific memory | ~2KB |
| **TOTAL** | **18 files created** | **~26KB** |

---

## 3. WHAT REMAINS SHARED (Non-Controversial)

| Item | Why it's OK to share |
|------|---------------------|
| `~/.claude/settings.json` API key | Cùng 1 user, key dùng cho Claude API calls |
| `~/.claude/history.jsonl` | Conversation history per-user |
| `~/.claude/sessions/` | Session management |
| `~/.claude/file-history/` | File edit history |
| `~/.claude/ide/` | IDE integration |
| `~/.claude/plugins/` | Shared plugins (harmless) |

---

## 4. STILL NEEDS ATTENTION (Optional Improvements)

### 4.1 Conditional: Multi-project workflow
Nếu sau này user thường xuyên switch giữa trading và YouTube trong cùng session:
- Cần project-aware context switching
- Giải pháp: luôn `cd` vào đúng thư mục project trước khi bắt đầu

### 4.2 Conditional: Separate API keys
Nếu muốn tách chi phí API giữa 2 projects:
- Tạo API key riêng cho YouTube project
- Config trong `.claude/settings.local.json`

### 4.3 Optional: Git repository
Hiện tại youtubeclaudecode chưa có git repo riêng:
```bash
cd /Users/ttcenter/Desktop/youtubeclaudecode
git init
echo "server.log" > .gitignore
echo "img/" >> .gitignore
echo "thumb/" >> .gitignore
git add -A
git commit -m "init: YouTube AI Production Studio v3.0.0-standalone"
```

### 4.4 Optional: Remove global trading symlinks
Nếu trading-system không còn dùng thường xuyên, có thể unlink:
```bash
# CHỈ LÀM NẾU không còn dùng trading system qua Claude Code
unlink ~/.claude/commands
unlink ~/.claude/modules
unlink ~/.claude/shared
```
**Cảnh báo:** Làm vậy sẽ disable toàn bộ trading commands trong Claude Code.

---

## 5. HOW TO USE (Quick Start)

### Bắt đầu session YouTube:
```bash
cd /Users/ttcenter/Desktop/youtubeclaudecode
# Mở Claude Code — tự động load CLAUDE.md + YouTube commands
```

### Bắt đầu session Trading:
```bash
cd /Users/ttcenter/trading-system
# Mở Claude Code — load CLAUDE.md trading + trading commands
```

### Switch giữa 2 projects:
- Thoát Claude Code session hiện tại
- `cd` sang thư mục project kia
- Mở Claude Code mới

---

## 6. VERIFICATION CHECKLIST

Sau khi migration hoàn tất, verify:

- [ ] Mở Claude Code trong `/Users/ttcenter/Desktop/youtubeclaudecode/`
- [ ] CLAUDE.md YouTube được load (không thấy trading instructions)
- [ ] Gõ `/` → chỉ thấy YouTube commands (/new-video, /generate-images...)
- [ ] KHÔNG thấy trading commands (/open, /close, /scalp-sniper...)
- [ ] Nói "viết script về Noah" → script-bible-explainer được kích hoạt
- [ ] Nói "tạo ảnh" → image-bible-explainer được kích hoạt
- [ ] Memory chỉ chứa YouTube context
- [ ] Mở Claude Code trong `/Users/ttcenter/trading-system/`
- [ ] Trading commands vẫn hoạt động bình thường
- [ ] Trading memory vẫn intact

---

> **Status:** Migration hoàn tất 2026-05-21. 18 files mới được tạo. 0 files bị xóa/sửa.
> **Next step:** User verify hoạt động trong session tiếp theo.
