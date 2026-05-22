# NAMING_CONVENTIONS.md

> **Version:** v1.0.0 | **Applies to:** All channels, all projects

---

## File Naming

| Type | Convention | Example |
|------|-----------|---------|
| Script | `[topic-slug]_[YYYYMMDD].md` | `fear-not_20260521.md` |
| Image prompts | `img-prompts_[topic-slug].md` | `img-prompts_fear-not.md` |
| Thumbnail prompts | `thumb-prompts_[topic-slug].md` | `thumb-prompts_fear-not.md` |
| Publishing log | `[topic-slug]_publish-log.md` | `fear-not_publish-log.md` |
| Audio | `[topic-slug]_[YYYYMMDD].mp3` | `fear-not_20260521.mp3` |
| Final video | `[topic-slug]_final_[YYYYMMDD].mp4` | `fear-not_final_20260521.mp4` |

---

## Directory Naming

| Type | Convention | Example |
|------|-----------|---------|
| Channel | `kebab-case` | `bible-explainer`, `christian-history` |
| Topic/project | `kebab-case` | `fear-not`, `every-letter-paul` |
| Archive | `YYYY-MM-DD-[topic-slug]` | `2026-05-14-fear-not` |

---

## Image File Naming (from Google Flow)

```
Format: Watercolor_[description]_[YYMMDDHHMM].jpeg
Example: Watercolor_illustration_of_Jesus_Christ_202605141307.jpeg

Sort by: timestamp (last 12 digits)
```

---

## Thumbnail File Naming

```
Format: thumb_[pattern]_v[1-3]_[with-text|no-text]_[YYMMDDHHMM].jpeg
Example: thumb_a_v1_with-text_202605211733.jpeg
         thumb_b_v2_no-text_202605211733.jpeg

A/B test tracking: YouTube auto-logs which thumbnail wins
```

---

## Channel Slug Rules

```
- Lowercase alphanumeric + hyphens
- No spaces, no underscores (underscores for file dates only)
- Keep under 32 characters
- Examples:
  ✅ bible-explainer
  ✅ christian-history
  ✅ theology-explained
  ❌ Bible Explainer
  ❌ christian_history
  ❌ this-is-a-very-long-channel-name-that-is-too-long
```

---

## Topic Slug Rules

```
- Lowercase, hyphens for spaces
- Strip articles (the, a, an)
- Remove special characters
- Examples:
  "Every Time God Said Fear Not" → fear-not
  "Every Letter the Apostle Paul Wrote" → every-letter-paul
  "How Passover Became Easter" → passover-to-easter
```

---

## Versioning

```
SKILL.md files: vMAJOR.MINOR.PATCH
  MAJOR: Breaking workflow changes
  MINOR: New feature (new pattern, new phase)
  PATCH: Bug fix, clarification

System files (CLAUDE.md, README.md, etc.): vMAJOR.MINOR.PATCH
  Follow project version
```
