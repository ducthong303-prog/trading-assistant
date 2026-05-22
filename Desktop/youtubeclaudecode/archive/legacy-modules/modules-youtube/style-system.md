# Style System — Watercolor Bible Illustration

> **Authority:** Module này là nguồn authoritative cho visual style. Mọi prompt ảnh và thumbnail PHẢI tuân theo spec này.
> **Version:** v1.0.0

---

## CORE STYLE SIGNATURE

### Medium (Non-Negotiable)
- **Watercolor painting** — KHÔNG oil painting, KHÔNG photorealistic, KHÔNG digital art, KHÔNG vector
- **Hand-drawn black ink outlines** — thin, sketchy, imperfect lines (như minh họa sách truyện)
- **White/cream background** — subject "floats" on canvas, no full-frame background fill
- **Modern Bible storybook** quality — như sách minh họa xuất bản gần đây

### Color Palette (Limited)
| Color | Hex | Usage |
|-------|-----|-------|
| Burnt Orange | `#B25D29` | Accent, clothing details, warm highlights |
| Deep Navy | `#1E2A4A` | Ink outlines, dark shadows, text |
| Cream | `#F5EBD8` | Background, negative space |
| Sepia | `#8B6B4A` | Secondary shadows, aged elements |
| Soft Grey | `#C4C4C4` | Distant elements, subtle shading |

**Quy tắc màu:**
- 80% palette trên, 20% room cho context-specific colors
- Không neon, không saturated bright colors
- Không gradient hiện đại
- Shadows = watercolor wash (không digital drop shadow)

### Character Design
- **Middle Eastern accurate** — KHÔNG European features
- Olive/tan skin tones
- Dark hair, dark eyes
- Period-appropriate clothing (1st century Middle Eastern, không medieval European)
- Ages appropriate to biblical narrative

### Composition
- **Aspect ratio:** 16:9 (cinematic)
- **Subject placement:** Rule of thirds
- **Depth:** Foreground focal point + atmospheric background wash
- **Negative space:** 30-40% cream/white space

---

## SCENE TYPES

### NARRATIVE
- Biblical event unfolding
- Multiple characters in action
- Environmental context visible
- Example: Jesus teaching crowd, disciples in boat

### EXPLAINER/CONCEPT
- Abstract idea visualized
- Infographic-style elements OK
- Symbols, diagrams, maps
- Example: Trinity diagram, covenant structure

### EMOTIONAL/PORTRAIT
- Single character close-up
- Expression tells the story
- Minimal background
- Example: Mary at tomb, Peter weeping

### HISTORICAL/CONTEXT
- Ancient architecture, maps
- Archaeological elements
- Cultural context
- Example: Temple layout, Jerusalem map

---

## TEXT IN IMAGES

### When YES:
- Bible verse references (e.g., "John 3:16")
- Character names (e.g., "Mary of Magdala")
- Key concepts (e.g., "COVENANT")

### Text Specs:
- Font: Hand-drawn serif (looks like ink on paper)
- Color: Deep navy `#1E2A4A`
- Placement: Bottom 10% or top 10% of frame
- Size: Small enough to not dominate, large enough to read on mobile

### When NO:
- Clean visual only
- Better for editing flexibility
- Text added in post-production if needed

---

## GOOGLE FLOW SPECIFICS

### Imagen 4 (Recommended)
- Best quality watercolor rendering
- Add "watercolor painting" early in prompt
- Use negative prompts: "NOT oil painting, NOT photorealistic, NOT digital art, NOT dark background"

### Nano Banana Pro (Alternative)
- Faster, cheaper
- May need more explicit style instructions
- Add "children's Bible storybook illustration style"

### Consistency Method
1. Generate Image 1 (main character) first
2. Save as "Subject Ingredient" in Flow
3. Upload ingredient for Images 2+
4. Reference: "same character as ingredient image, same watercolor style"

---

## THUMBNAIL TYPOGRAPHY

| Element | Font | Style | Size | Color |
|---------|------|-------|------|-------|
| Main Title | Cinzel Bold | ALL CAPS | 120-180pt | `#1E2A4A` |
| Subtitle | Cinzel/Playfair | Regular | 70-100pt | `#B25D29` |
| Bible Verse | Playfair Display | Italic | 50-70pt | `#1E2A4A` |
| Background | — | Solid/splash | — | `#F5EBD8` or `#FFFFFF` |

**Font source:** Google Fonts (free, no license issues)

---

## ANTI-PATTERNS (Never Use)

- ❌ Dark dramatic backgrounds (full-frame black/dark)
- ❌ Photorealistic 3D renders
- ❌ Neon glow effects
- ❌ Modern sans-serif fonts (Impact, Bebas Neue, Arial)
- ❌ Digital gradient backgrounds
- ❌ European-looking Jesus (blonde hair, blue eyes)
- ❌ AI-generated text on images (gibberish risk)
- ❌ Busy compositions (no focal point)
- ❌ Cartoon/caricature style
