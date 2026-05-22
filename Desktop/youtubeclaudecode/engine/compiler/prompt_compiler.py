"""YouTube AI Factory v4.1 — Prompt Compiler

Takes scene data + style locks → compiles production-ready prompt.
Token-optimized: scene data ~50 tokens → compiled prompt ~150 tokens.
Style boilerplate auto-injected, never duplicated in scene data.
"""
import json
from pathlib import Path
from engine.style.lock import style_lock

PRESETS_DIR = Path(__file__).resolve().parent / "presets"


class PromptCompiler:
    def __init__(self):
        self.emotions = self._load("emotions.json")
        self.shots = self._load("shots.json")

    def _load(self, fname: str) -> dict:
        p = PRESETS_DIR / fname
        if p.exists():
            return json.loads(p.read_text())
        return {}

    # ── Public API ────────────────────────────────────

    def compile(self, scene: dict) -> dict:
        """
        Compile a single scene into a production-ready prompt + metadata.

        scene = {
            "id": "img_001",
            "character": "jesus",
            "emotion": "controlled_sorrow",
            "shot": "extreme_close_up_face",
            "setting": "outside stone tomb in Bethany, late afternoon",
            "action": "a single tear rolls silently down his cheek",
            "bible_verse": "Jesus wept. — John 11:35",
            "text_position": "top_right",
            "mood_override": null,          # optional
            "character_secondary": null,    # optional
            "crowd_context": null,          # optional
            "extra_context": null,          # optional extra detail
        }

        Returns:
        {
            "id": "img_001",
            "prompt": "Full compiled English prompt...",
            "negative": "Universal negative prompt...",
            "metadata": { emotion, shot, mood, character, ... }
        }
        """
        mood = scene.get("mood_override") or self._emotion_mood(scene.get("emotion"))
        shot = scene.get("shot", "close_up_face")
        character = scene.get("character")
        character2 = scene.get("character_secondary")
        emotion = scene.get("emotion", "neutral")

        # Compile style injection
        style = style_lock.compile(
            character=character,
            mood=mood,
            shot=shot,
        )

        # Build prompt
        prompt = self._build_prompt(scene, style)

        return {
            "id": scene["id"],
            "prompt": prompt,
            "negative": style["negative_prompt"],
            "metadata": {
                "character": character,
                "emotion": emotion,
                "shot": shot,
                "mood": mood,
                "bible_verse": scene.get("bible_verse"),
            },
        }

    def compile_batch(self, scenes: list[dict]) -> list[dict]:
        """Compile a batch of scenes."""
        return [self.compile(s) for s in scenes]

    # ── Internal ──────────────────────────────────────

    def _emotion_mood(self, emotion_name: str) -> str:
        e = self.emotions.get(emotion_name, {})
        return e.get("palette_mood", "contemplation")

    def _build_prompt(self, scene: dict, style: dict) -> str:
        """Assemble the final English prompt."""
        parts = []

        # 1. Style anchor
        emotion_name = scene.get("emotion", "neutral")
        emotion_data = self.emotions.get(emotion_name, {})
        shot_type = scene.get("shot", "close_up_face")

        # 2. Subject + action
        character = scene.get("character")
        if character:
            parts.append(f"Watercolor illustration of {character.replace('_',' ').title()}"
                         f" — {style.get('character_traits','')}")
        else:
            parts.append("Watercolor illustration")

        # 3. Action
        action = scene.get("action")
        if action:
            parts.append(f"{action}")

        # 4. Emotion description
        if emotion_data:
            parts.append(f"Expression: {emotion_data.get('face','')}")
            if emotion_data.get("body"):
                parts.append(f"Body language: {emotion_data['body']}")

        # 5. Setting
        setting = scene.get("setting")
        if setting:
            parts.append(f"Setting: {setting}")

        # 6. Character 2 (if two-shot)
        if scene.get("character_secondary"):
            c2 = scene["character_secondary"]
            parts.append(f"With {c2.replace('_',' ').title()} in the scene")

        # 7. Crowd context
        crowd = scene.get("crowd_context")
        if crowd:
            parts.append(f"Background: {crowd}")

        # 8. Clothing
        if character:
            parts.append(f"Clothing: {style.get('character_clothing','')}")

        # 9. Composition
        parts.append(f"Composition: {style.get('camera_shot','')}")
        parts.append(f"Color palette: {style.get('palette_colors','')}")

        # 10. Extra context
        extra = scene.get("extra_context")
        if extra:
            parts.append(f"{extra}")

        # 11. Bible verse text (if any)
        verse = scene.get("bible_verse")
        if verse:
            pos = scene.get("text_position", "bottom_right")
            parts.append(f"Elegant small serif text at {pos.replace('_',' ')} reads \"{verse}\" in deep navy (#1E2A4A)")

        # 12. Style signature
        parts.append(f"{style.get('watercolor_dna','')}")
        parts.append(f"{style.get('palette_rules','')}")
        parts.append(f"{style.get('camera_rules','')}")
        parts.append("16:9, subject centered on cream background")

        prompt = ". ".join(parts) + "."
        # Clean up double spaces and double periods
        prompt = prompt.replace("..", ".").replace("  ", " ").replace(". .", ".")
        return prompt

    # ── Quick Compile (from existing prompt + style injection) ──

    def enrich_existing_prompt(self, prompt: str, character: str = None,
                               mood: str = None) -> str:
        """Enrich an existing hand-written prompt with style lock traits.
        Useful for upgrading legacy prompts to v4.1 consistency.
        """
        style = style_lock.compile(character=character, mood=mood)
        # Append negative prompt
        enriched = prompt.strip()
        if not enriched.endswith("."):
            enriched += "."
        enriched += f"\n\n❌ NEGATIVE PROMPT:\n{style['negative_prompt']}"
        return enriched


# Singleton
prompt_compiler = PromptCompiler()
