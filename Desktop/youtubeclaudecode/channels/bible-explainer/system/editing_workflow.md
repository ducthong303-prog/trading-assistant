# Editing Workflow — CapCut / Premiere Pro

**Goal:** Turn 28 images + voiceover into cinematic video in under 4 hours.

---

## RECOMMENDED TOOL: CapCut Desktop

Free, motion presets built-in, subtitle auto-gen, faster than Premiere for image-based videos.

**Use Premiere only if:** You need multi-cam, complex masking, or advanced color grading.

---

## PROJECT STRUCTURE

```
Project: Every-Time-Jesus-Wept
├── Act 1 — Mystery
├── Act 2 — Warning
├── Act 3 — Breaking
├── Act 4 — Cost
├── Act 5 — Peak
├── Act 6 — Resolution
└── Assets (audio, VO, fonts)
```

**One sequence per act** → nest into master sequence. Easier to adjust timing per act without ripple-destroying everything.

---

## TRACK ORGANIZATION

```
Track 1  — Video (images + motion keyframes)
Track 2  — Subtitles
Track 3  — Voiceover (WAV)
Track 4  — Music (ducked)
Track 5  — Ambient SFX
```

**Lock tracks after finalized.** Prevents accidental nudges.

---

## SEQUENCE SETUP (Master)

- Resolution: 1920×1080
- Frame rate: 24 fps
- Pixel aspect: Square (1.0)
- Audio sample rate: 48kHz

---

## MOTION PRESET WORKFLOW

Create 4 reusable presets:

| Preset | Keyframes | Use For |
|--------|-----------|---------|
| **Slow Zoom In** | Scale 100%→115% over duration, ease-in-out | Most images (70% of video) |
| **Slow Zoom Out** | Scale 110%→100% over duration, ease-in-out | Wide establishing shots |
| **Static Hold** | No motion | Peak emotional moments |
| **Parallax Drift** | Foreground scale 100%→108%, background 100%→102% | Images with depth layers |

**In CapCut:** Save as Adjustment Layer presets. In Premiere: Save as Motion Graphics Template (.mogrt).

---

## TRANSITION PRESETS

| Transition | Duration | Use |
|------------|----------|-----|
| Cross Dissolve | 1.5 sec | Within acts (default) |
| Cross Dissolve | 3 sec | Between acts 1→2, 4→5 |
| Dip to Black | 2 sec | Between acts 2→3 (night) |
| Dip to Black | 4 sec | Between acts 5→6 (death→resurrection) |
| Hard Cut | — | Act 4 montage (urgency) |

**Save as preset.** One-click apply. No manual tweaking per cut.

---

## SUBTITLE WORKFLOW

1. CapCut auto-caption (English) → 90% accurate
2. Manual fix: Greek/Hebrew words, punctuation
3. Style: White text, thin black outline/shadow, sans-serif
4. Max 2 lines, max 42 chars per line
5. Position: Bottom-center, 10% margin from bottom edge
6. Duration: Match VO timing exactly. Appear WITH voice, not before.
7. Export SRT as backup

---

## PROXY WORKFLOW

- Use 4K images as source (3840×2160)
- No proxy needed for image-based timeline (no video footage)
- If using CapCut: it auto-proxies large images
- If using Premiere: Create proxies at 1920×1080 PNG sequence

---

## EXPORT PRESETS

**YouTube 1080p:**
- Format: H.264
- Resolution: 1920×1080
- Frame rate: 24 fps
- Bitrate: VBR 2-pass, target 16 Mbps, max 24 Mbps
- Audio: AAC, 320 kbps, 48kHz
- Render: Maximum depth + Maximum render quality ON

**Archive Master:**
- Format: ProRes 422 (or DNxHR HQ on Windows)
- Resolution: 3840×2160 (4K)
- Audio: PCM 24-bit, 48kHz

---

## EDITING ORDER (Fastest)

1. Lay in voiceover track → lock
2. Place all 28 images to VO timing per blueprint → lock
3. Apply motion presets → lock
4. Apply transitions
5. Add music + ambient SFX → duck under VO
6. Generate + fix subtitles
7. Watch full pass, adjust timing
8. Export

**Never go backward in this order.** Each step locked before next begins.
