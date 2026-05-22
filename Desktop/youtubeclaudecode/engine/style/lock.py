"""YouTube AI Factory v4.1 — Style Lock Engine"""
import json
from pathlib import Path
from typing import Optional

PRESETS_DIR = Path(__file__).resolve().parent / "presets"


class StyleLock:
    """Centralized style consistency. Loads preset JSON files and injects
    locked traits into prompts to prevent drift across videos."""

    def __init__(self):
        self._cache = {}

    def _load_json(self, filename: str) -> dict:
        if filename not in self._cache:
            path = PRESETS_DIR / filename
            if path.exists():
                with open(path) as f:
                    self._cache[filename] = json.load(f)
            else:
                self._cache[filename] = {}
        return self._cache[filename]

    # ── Character Locks ───────────────────────────────

    def character(self, name: str) -> dict:
        """Get locked character traits. Supports: jesus, mary, martha, peter, generic_crowd."""
        chars = self._load_json("characters.json")
        return chars.get(f"{name}-portrait-v1") or chars.get(name, {})

    def character_traits_text(self, name: str) -> str:
        """Get character traits as injectable prompt text."""
        c = self.character(name)
        if not c:
            return ""
        traits = c.get("locked_traits", {})
        parts = [f"{k.replace('_',' ')}: {v}" for k, v in traits.items()
                 if k not in ("expression_range", "forbidden_traits", "age", "age_range")]
        if "age" in traits:
            parts.append(f"age: {traits['age']}")
        if "expression_range" in traits:
            parts.append(f"expression must be one of: {', '.join(traits['expression_range'])}")
        return ", ".join(parts)

    def character_forbidden_text(self, name: str) -> str:
        c = self.character(name)
        if not c:
            return ""
        forbidden = c.get("forbidden_traits", [])
        clothing_forbidden = c.get("clothing", {}).get("forbidden", [])
        return ", ".join(forbidden + clothing_forbidden)

    def character_clothing_text(self, name: str) -> str:
        c = self.character(name)
        if not c:
            return ""
        clothing = c.get("clothing", {})
        colors = ", ".join(clothing.get("robe_colors", []))
        style = clothing.get("style", "")
        return f"{style} robes in {colors}"

    # ── Palette Locks ─────────────────────────────────

    def palette(self) -> dict:
        return self._load_json("palette.json")

    def palette_colors_text(self, mood: str = None) -> str:
        """Get palette hex codes as text. If mood given, returns mood-specific palette."""
        p = self.palette()
        if mood and mood in p.get("mood_mappings", {}):
            colors = p["mood_mappings"][mood]
            return ", ".join(colors) + " watercolor on cream paper"
        primary = p.get("primary", {})
        return ", ".join(f"{v['hex']} ({k})" for k, v in primary.items())

    def palette_rules_text(self) -> str:
        """Get palette rules as injectable text."""
        p = self.palette()
        rules = p.get("rules", {})
        return "background is always cream (#F5EBD8), " \
               f"negative space minimum {rules.get('negative_space_min_55_percent', 55)}%, " \
               f"ink outlines in {rules.get('ink_color', 'sepia')}"

    # ── Camera Locks ──────────────────────────────────

    def camera(self) -> dict:
        return self._load_json("camera.json")

    def camera_shot_text(self, shot_type: str) -> str:
        """Get camera framing instructions for a shot type."""
        shots = self.camera().get("cinematic_shots", {})
        shot = shots.get(shot_type, shots.get("close_up_face", {}))
        framing = shot.get("framing", "subject centered")
        neg = shot.get("negative_space", "55% cream background")
        kb = shot.get("ken_burns", "slow_zoom")
        return f"{framing}, {neg}, subject floats on cream background, Ken Burns: {kb}"

    def camera_rules_text(self) -> str:
        rules = self.camera().get("rules", {})
        return "16:9 aspect ratio, subject never touches frame edges, " \
               "ink outlines on subject and foreground only, background is watercolor wash"

    # ── Watercolor DNA ────────────────────────────────

    def watercolor(self) -> dict:
        return self._load_json("watercolor.json")

    def watercolor_dna_text(self, mood: str = None) -> str:
        """Get the full watercolor DNA as injectable prompt text."""
        w = self.watercolor()
        dna = w.get("dna", {})
        descriptors = ", ".join(w.get("quality_descriptors", []))

        # Mood-based intensity
        intensity = "medium"
        if mood and mood in w.get("emotional_wash_intensity", {}):
            intensity = "medium"  # Handled via palette mood

        return f"{descriptors}, {dna.get('lighting', '')}, " \
               f"{dna.get('edge_handling', '')}"

    # ── Forbidden ─────────────────────────────────────

    def forbidden(self) -> dict:
        return self._load_json("forbidden.json")

    def negative_prompt(self) -> str:
        return self.forbidden().get("universal_negative_prompt", "")

    def format_negative_prompt_block(self) -> str:
        """Returns formatted negative prompt text for inclusion in compiled prompts."""
        return f"\n❌ NEGATIVE PROMPT:\n{self.negative_prompt()}"

    # ── Compile Style Injection ───────────────────────

    def compile(self, character: str = None, mood: str = None,
                shot: str = "close_up_face") -> dict:
        """Compile all style locks into a reusable injection block.

        This is the main entry point for prompt compilation.
        Returns dict with keys ready for template injection.
        """
        result = {
            "watercolor_dna": self.watercolor_dna_text(mood),
            "palette_colors": self.palette_colors_text(mood),
            "palette_rules": self.palette_rules_text(),
            "camera_shot": self.camera_shot_text(shot),
            "camera_rules": self.camera_rules_text(),
            "negative_prompt": self.negative_prompt(),
            "mood": mood or "neutral",
            "shot_type": shot,
        }
        if character:
            result["character_traits"] = self.character_traits_text(character)
            result["character_clothing"] = self.character_clothing_text(character)
            result["character_forbidden"] = self.character_forbidden_text(character)
            result["character_name"] = character
        return result


# Singleton
style_lock = StyleLock()
