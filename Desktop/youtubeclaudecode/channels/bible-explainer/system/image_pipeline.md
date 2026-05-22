# Image Generation Pipeline — Bible Explainer

**Target:** 28 images, watercolor Bible illustration, 16:9, consistent style.

---

## TOOL CHOICE

Use **Midjourney** (best watercolor consistency). Fallback: **Flux Pro** via Replicate.

---

## STYLE LOCK (Seed Strategy)

```
Step 1: Generate base image with full prompt. Get seed.
Step 2: Use --seed {base_seed} for ALL subsequent images.
Step 3: If style drifts, re-lock with new seed from best image.
```

**Why:** Same seed = same "artist hand." Watercolor wash pattern, brush stroke density, and paper texture remain consistent.

---

## PROMPT PREFIX (Prepend to EVERY prompt)

```
watercolor illustration, hand-drawn thin black ink outlines, Middle Eastern characters, warm olive skin, cream white background, modern Bible storybook style, deep navy and burnt orange palette, 16:9 aspect ratio, visible paper texture, soft watercolor wash, editorial watercolor --ar 16:9 --style raw --stylize 250
```

**Append to EVERY prompt:**

```
--no photorealistic, oil painting, dark background, full-frame, CGI, 3D, anime, cartoon, European features, neon, saturated colors, text, letters, words
```

---

## BATCH ORDER (3 Phases)

| Phase | Prompts | Batch Size | Reason |
|-------|---------|------------|--------|
| 1 — Lock | #1, #9, #23 | 3 | Cover emotional range (calm/agony/peak) to verify seed works across tones |
| 2 — Core | #2–8, #10–14 | 12 | Main narrative. Run in 2 batches of 6. |
| 3 — Finish | #15–22, #24–28 | 13 | Resolution. Run in 2 batches (7 + 6). |

**Rule:** Never generate all 28 in one batch. If style breaks, you lose everything. Phased = fix early.

---

## UPSCALING

- Midjourney: Use built-in upscaler (U1-U4). Then Topaz Gigapixel to 4K.
- Flux: Generate at max native res. Upscale to 4K via Topaz.
- Final deliverable: 3840×2160 PNG (gives room for Ken Burns zoom without pixelation).

---

## CONSISTENCY CHECK (After Each Batch)

- [ ] Watercolor texture visible (not vector-flat)
- [ ] Cream/white background (not grey/dark)
- [ ] Thin black ink outlines present
- [ ] Middle Eastern features correct
- [ ] Deep navy + burnt orange palette dominant
- [ ] No text, letters, or gibberish in image
- [ ] Subject not touching frame edges
- [ ] 16:9 composition correct

**Fail ≥2 checks** → re-roll that image with adjusted prompt.

---

## FILE NAMING

```
{project}/img_{NN}_{scene-slug}_{YYYYMMDD}.png

Example:
every-time-jesus-wept/img_01_two-words-tease_20260521.png
every-time-jesus-wept/img_14_rooster-crows_20260521.png
```

**NN:** Zero-padded 2-digit (01-28). Matches prompt number.

---

## FOLDER STRUCTURE

```
channels/bible-explainer/images/{project}/
├── prompts/
│   ├── part1_prompts.md
│   ├── part2_prompts.md
│   └── ...
├── raw/              ← Midjourney/Flux outputs (unprocessed)
├── upscaled/         ← 4K PNG finals
├── rejected/         ← Failed consistency check images
└── seed_log.md       ← Record seed per image
```

---

## SEED LOG FORMAT

```markdown
| Img | Seed | Tool | Upscaled | Notes |
|-----|------|------|----------|-------|
| 01 | 8472 | MJ 6.1 | ✅ | Base lock seed |
| 02 | 8472 | MJ 6.1 | ✅ | |
| 03 | 8472 | MJ 6.1 | ⚠️ | Re-rolled — ink too thick |
```

---

## PROMPT DELIVERY FORMAT

Each prompt goes to Midjourney/Flux as:

```
{prompt_prefix}
{prompt_body}
{prompt_suffix}
```

Never send without prefix + suffix. Consistency > creative freedom.
