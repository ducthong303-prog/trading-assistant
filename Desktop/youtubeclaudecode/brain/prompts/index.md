# Shared Prompt Library Index

> **Load order:** CLAUDE.md pre-loads mục này. Mỗi skill tham chiếu file liên quan.

---

## Prompt Fragment Map

### Khi cần WATERCOLOR STYLE:

→ Load: `style-signature.md` — Đoạn "CORE DNA" + "WATERCOLOR DESCRIPTOR BANK"
→ Dùng: chèn `watercolor illustration` + `hand-drawn black ink outlines` + `on white paper background` vào mọi prompt

### Khi cần COLOR:

→ Load: `color-palette.md`
→ Dùng: palette `#1E2A4A` navy, `#B25D29` burnt orange, `#F5EBD8` cream, `#8B6F47` sepia

### Khi cần NEGATIVE PROMPT:

→ Load: `style-signature.md` — Đoạn "NEGATIVE PROMPTS (Universal)"
→ Dùng: copy-paste nguyên block vào cuối mọi prompt ảnh/thumbnail

### Khi cần COMPETITOR INTEL:

→ Load: `competitor-brief.md`
→ Dùng: pattern viral rates, CTR benchmarks, đối thủ specs

### Khi cần TYPOGRAPHY:

→ Load: `style-signature.md` — Đoạn "TYPOGRAPHY (Thumbnail)"
→ Dùng: Cinzel Bold #1E2A4A 120-180pt ALL CAPS + Playfair #B25D29 70-100pt

### Khi cần CHARACTER DESIGN:

→ Load: `style-signature.md` — Đoạn "CHARACTER DESIGN"
→ Dùng: Middle Eastern accurate, watercolor figure + ink outlines

---

## Reusable Prompt Blocks

### BLOCK W: Watercolor Style Anchor

```
A watercolor illustration in modern Bible storybook style. 
Hand-painted watercolor with visible paper texture. 
Thin hand-drawn black ink outlines. 
The entire scene sits on a white paper background with watercolor splash 
extending naturally around the central composition, leaving generous 
white space around the edges. 
Soft watercolor washes in a limited palette of warm sepia brown, 
deep navy blue (#1E2A4A), and burnt orange (#B25D29) accents.
Friendly storybook illustration quality, 16:9 horizontal composition.
```

### BLOCK N: Universal Negative Prompt

```
no photorealistic, no oil painting, no dark cinematic atmosphere, 
no full-frame edge-to-edge composition, no black background, no CGI, 
no 3D render, no anime, no Disney cartoon style, no anachronisms, 
no modern objects, no European-featured Middle Eastern characters, 
no extra fingers, no distorted hands, no over-saturated colors, 
no gibberish text
```

### BLOCK T: Thumbnail Text Specs

```
Primary title: Cinzel Bold, ALL CAPS, 120-180pt, deep navy #1E2A4A
Subheader "EXPLAINED": Cinzel/Playfair, lighter weight, 70-100pt, burnt orange #B25D29
Small text: Same family, regular, 30-50pt, navy or sepia
Background: Cream #F5EBD8 or white #FFFFFF
Font source: Google Fonts (free)
```

### BLOCK C: Consistency Method

```
1. Generate Image 1 (main character) FIRST
2. Save Image 1 — upload as "Subject Ingredient" for Image 2+
3. Keep ingredient loaded across all images with same character
4. Use Imagen 4 in Google Flow for highest quality
```
