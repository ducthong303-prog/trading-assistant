# AI Voiceover Workflow — ElevenLabs

**Goal:** Natural, cinematic narration indistinguishable from human.

---

## VOICE SELECTION

**Recommended voices:**

| Voice | Character | Best For |
|-------|-----------|----------|
| Adam | Warm male baritone, natural pauses | Primary narrator |
| Josh | Deeper, more gravitas | Alternative |
| Antoni | Slightly accented, intimate | Contemplative tone |

**Test:** Generate 60 sec sample with each. Listen on phone speakers — that's how most viewers hear it.

---

## VOICE SETTINGS

```
Model: Eleven Multilingual v2
Stability: 45-55%       ← Lower = more emotional variation
Clarity + Similarity: 70-80%  ← Higher = more natural
Style Exaggeration: 20-30%    ← Keep subtle. Over-acting kills trust.
Speaker Boost: OFF            ← Makes voice harsh on long form
```

**Stability tuning:**
- Acts 1, 6 (calm): Stability 55%
- Acts 2, 4 (tension): Stability 45%
- Acts 3, 5 (peak emotion): Stability 35-40%

---

## PRONUNCIATION DICTIONARY

Create in ElevenLabs settings:

```
edakrusen     → eh-DAH-kroo-sen
dakruo        → DAH-kroo-oh
eklausten     → ek-LAO-sten
klaio         → KLAI-oh
kraugēs ischyras → krow-GACE ISS-khee-ras
hoshia na     → ho-SHEE-ah nah
enebrimēsato  → en-eb-ree-MAY-sah-to
perilypos     → pe-REE-loo-pos
Gethsemane    → geth-SEM-ah-nee
Bethany       → BETH-ah-nee
Caiaphas      → KAI-ah-fus
hematidrosis  → hee-mat-ih-DRO-sis
```

**Upload before generating.** Mispronounced Greek = credibility killer.

---

## PACING CONTROLS

ElevenLabs doesn't have direct pacing controls. Use these techniques:

1. **Add punctuation pauses:** "..." = ~0.8 sec pause. Double space = ~0.5 sec.
2. **Break long sentences:** Shorter sentences = Eleven reads slower naturally.
3. **Use SSML (if API):** `<break time="1.5s"/>` for deliberate pauses.
4. **Post-edit in DAW:** Stretch silences manually. Most reliable method.

---

## EMOTIONAL CONSISTENCY

- **Generate per Act, not per line.** ElevenLabs voice model drifts across short clips.
- **Each Act = 1 generation.** If you break mid-Act, re-generate the whole Act.
- **Listen for "AI flatness":** If a line feels emotionally dead, re-generate with more punctuation (commas = micro-pauses, which tricks the model into more natural cadence).

---

## AUDIO CLEANUP CHAIN (DAW: Audacity / Reaper / Audition)

```
1. Noise gate: -45dB threshold (remove breath noise)
2. Light compression: 2:1 ratio, -18dB threshold, 3ms attack, 50ms release
3. EQ: High-pass 80Hz (remove rumble), slight dip at 2-4kHz (reduce AI harshness), slight boost at 100-200Hz (warmth)
4. De-esser: Target 6-8kHz if sibilance present
5. Reverb send: Room reverb, 15-20% wet, 1.2s decay
6. Limit: -3dB peak ceiling
```

**Master output:** -14 LUFS integrated (YouTube standard).

---

## WORKFLOW ORDER

1. Generate VO per Act (6 generations total)
2. Import into DAW
3. Trim silences between acts to match blueprint timings
4. Apply cleanup chain
5. Insert deliberate silences (8 total per blueprint)
6. Export as 48kHz WAV, 24-bit
7. Spot-check: listen on phone, laptop, headphones

---

## QUICK TEST (Before Full Generation)

Generate just Act 1 (~7 min). Listen end-to-end. If voice sounds:
- **Robotic** → Lower Stability to 40%
- **Over-acting** → Lower Style Exaggeration to 15%
- **Rushed** → Add more commas and line breaks to script
- **Flat** → Raise Stability to 55%, add more punctuation

Fix settings → then generate all 6 Acts.
