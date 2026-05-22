# CLEANUP_PLAN.md — Migration & Cleanup Roadmap

> **Date:** 2026-05-21
> **Principle:** KHÔNG delete ngay — analyze → move → archive → confirm → delete

---

## 1. AUDIT RESULTS

### Duplicate Content (đã merge)

| Before | After | Savings |
|--------|-------|---------|
| Style specs in 5 files | `brain/prompts/style-signature.md` (1 file) | -4 duplicates |
| Color palette in 3 files | `brain/prompts/color-palette.md` (1 file) | -2 duplicates |
| Competitor data in 3 files | `brain/prompts/competitor-brief.md` (1 file) | -2 duplicates |
| Negative prompts in 2 files | `brain/prompts/style-signature.md` | -1 duplicate |
| Typography specs in 2 files | `brain/prompts/style-signature.md` | -1 duplicate |
| SKILL.md file sizes | 69KB → 10.5KB total | **85% reduction** |

### Obsolete Files (cần archive/delete)

| File | Issue | Action |
|------|-------|--------|
| `image-bible-explainer.zip` | Stale backup (May 13) | → `archive/` |
| `script-bible-explainer.zip` | Stale backup (May 13) | → `archive/` |
| `thumbnail-bible-explainer.zip` | Stale backup (May 14) | → `archive/` |
| `MIGRATION_PLAN.md` | Old plan from isolation task | → `archive/` |
| `server.log` (18MB) | Trading system log | **DELETE** (trading contamination) |
| `scripts/cleanup_output.sh` | Replaced by automation/ scripts | → `archive/` |

### Redundant Directories (đã migrate sang channels/)

| Directory | Status | Action |
|-----------|--------|--------|
| `img/` (23 files, 68MB) | Migrated to `archive/2026-05-14-fear-not/images/` | Keep as reference, delete after confirm |
| `thumb/` (3 files, 8.6MB) | Migrated to `archive/2026-05-14-fear-not/thumbnails/` | Keep as reference, delete after confirm |
| `output/` (empty) | Never used | Delete now |
| `scripts/` | Replaced by `automation/` | Delete after confirming automation/ works |
| `.claude/commands-youtube/` | Legacy v2 structure | Merge into slash commands or delete |
| `.claude/modules-youtube/` | Replaced by `brain/prompts/` | Delete (content migrated) |
| `.claude/workflows-youtube/` | Replaced by `brain/workflows/` | Delete (content migrated) |

### Color Inconsistency (đã fix)

| File | Old Value | New Value | Status |
|------|-----------|-----------|--------|
| image-bible-explainer SKILL.md | `#C97A3B` (burnt orange) | `#B25D29` | ✅ Fixed |
| thumbnail-bible-explainer SKILL.md | `#B25D29` (correct) | `#B25D29` | ✅ Consistent |

---

## 2. CLEANUP EXECUTION (3 Phases)

### Phase 1: Safe Archive (DO NOW)

```bash
# Move stale backups
mv image-bible-explainer.zip archive/
mv script-bible-explainer.zip archive/
mv thumbnail-bible-explainer.zip archive/
mv MIGRATION_PLAN.md archive/
mv scripts/cleanup_output.sh archive/

# Move legacy .claude content (already migrated)
mv .claude/modules-youtube archive/legacy-modules/
mv .claude/workflows-youtube archive/legacy-workflows/
```

### Phase 2: Delete After Confirmation (WAIT 1 WEEK)

```bash
# Only after confirming new structure works:
rm server.log                          # 18MB trading contamination
rm -rf img/                            # Already in archive + channels
rm -rf thumb/                          # Already in archive + channels
rm -rf output/                         # Never used, replaced by channels/
rm -rf scripts/                        # Replaced by automation/
rm -rf .claude/commands-youtube/       # Note: keep if slash commands work
```

### Phase 3: Verify (AFTER DELETION)

```bash
# Verify skills still work:
# "viết script về Noah" → script-bible-explainer triggers
# "tạo ảnh" → image-bible-explainer triggers
# "thumbnail" → thumbnail-bible-explainer triggers

# Verify new workflows:
# "video mới" → full production workflow loads
```

---

## 3. MIGRATION MAP

```
BEFORE (v2)                          AFTER (v3)
─────────                            ─────────
style-system.md (4.2KB)       →     brain/prompts/style-signature.md
script-architecture.md (4.5KB) →     brain/templates/script-template.md
publishing-pipeline.md (3.4KB) →     brain/workflows/full-production.md
                                    + WORKFLOW.md

SKILL.md (69KB total)          →     SKILL.md (10.5KB total, thin refs)
    Duplicated style info      →     References brain/prompts/
    Duplicated color info      →     References brain/prompts/
    Duplicated competitor info →     References brain/prompts/

img/ (68MB)                    →     archive/2026-05-14-fear-not/images/
                                    channels/bible-explainer/images/

thumb/ (8.6MB)                 →     archive/2026-05-14-fear-not/thumbnails/
                                    channels/bible-explainer/thumbnails/

No system docs                 →     README.md + WORKFLOW.md + PROJECT_MAP.md
                                    + STYLE_GUIDE.md + NAMING_CONVENTIONS.md
                                    + AUTOMATION_PLAN.md + CLEANUP_PLAN.md

No automation                  →     automation/new-video.sh
                                    automation/organize-output.sh
                                    automation/publish-checklist.sh

No channel structure           →     channels/bible-explainer/
                                    (multi-channel ready)
```

---

## 4. VERIFICATION CHECKLIST

Sau cleanup, verify:

- [ ] `claude` trong thư mục project load CLAUDE.md mới
- [ ] Nói "viết script về Noah" → script-bible-explainer hoạt động
- [ ] Nói "tạo ảnh" → image-bible-explainer hỏi 4 config questions
- [ ] Nói "thumbnail" → thumbnail-bible-explainer hỏi Title + Script
- [ ] Nói "video mới" → load full production workflow
- [ ] `brain/prompts/style-signature.md` được tham chiếu đúng
- [ ] KHÔNG còn file trading contamination (server.log)
- [ ] `archive/` chứa đầy đủ backup
- [ ] `channels/bible-explainer/` sẵn sàng nhận output mới

---

## 5. ROLLBACK PLAN

Nếu có vấn đề:
```bash
# Restore từ archive
cp archive/image-bible-explainer.zip ../
cp archive/script-bible-explainer.zip ../
cp archive/thumbnail-bible-explainer.zip ../

# Restore SKILL.md từ git (nếu có)
git checkout -- script-bible-explainer/SKILL.md
git checkout -- image-bible-explainer/SKILL.md
git checkout -- thumbnail-bible-explainer/SKILL.md
```

---

> **Status:** Audit complete. Migration ready. Awaiting user confirmation for Phase 2 deletions.
> **Next step:** Run Phase 1 (safe archive), verify, then Phase 2 (delete after 1 week).
