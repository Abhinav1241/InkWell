"""
Inkwell — Core Prompts (P1–P6 + Gemma)

All prompts as format-string templates. Placeholder names match
the keys passed by each calling module.
"""

# ── P1: Intake extraction + clarifying questions ─────────────────────────────

P1_INTAKE = """You are the creative director of a comic studio, in conversation with an author.
Read their story input (which may be rough, partial, or messy):
\"\"\"{raw_story}\"\"\"
Return STRICT JSON (no markdown fences, no commentary):
{{
 "logline": "<one sentence>",
 "tone": "<e.g., noir, whimsical, epic>",
 "setting": "<where/when>",
 "characters": [{{"name":"<or a placeholder>","role":"<protagonist/antagonist/supporting>",
   "description":"<distinctive visual + personality details>"}}],
 "questions": ["<2–4 clarifying questions whose answers will change the art or pacing:
   art style, page count, content rating, mood/pacing, point of view — ask only what's
   genuinely undecided>"]
}}
Do not invent plot the author didn't imply. Keep questions short and concrete."""


# ── P2: Character reference sheet ────────────────────────────────────────────

P2_CHARACTER_SHEET = """Character reference sheet for a comic in this art style: {style_phrase}.
Character: {name}. {canonical_prompt_fragment}.
Show the SAME character in one image as a turnaround: front, 3/4, and side views, plus two
expressions (neutral and {key_emotion}). Neutral flat background. Consistent proportions,
consistent outfit and colors across all views. Clean model-sheet layout. No text labels."""


# ── P2b: Location reference sheet ────────────────────────────────────────────

P2B_LOCATION_SHEET = """Location reference sheet for a comic in this art style: {style_phrase}.
Location: {name}. {canonical_prompt_fragment}.
Show establishing environmental and architectural views in one clean reference sheet: wide exterior view, key architectural/geographical features, lighting, textures, and atmospheric details. Consistent colors and mood. Clean model-sheet layout. No characters, no text labels."""


# ── P3: Script → panel plan ──────────────────────────────────────────────────

P3_PANEL_PLAN = """Break this story into EXACTLY {page_count} page(s). Style: {style_phrase}. Rating: {rating}.
CRITICAL CONSTRAINT: You MUST produce EXACTLY {page_count} pages in the "pages" array (indexes 0 to {page_count_minus_1}). Do not produce more or fewer pages.

Story/bible:
{bible_json}

Return STRICT JSON (no markdown fences, no commentary):
{{"pages":[{{"index":<int>,"panels":[
  {{"order":<int>,"shotType":"wide|medium|close|splash",
   "staging":"<camera + who is where + what happens visually>",
   "charactersPresent":["<name>"],
   "action":"<the visual moment to draw; no dialogue here>",
   "dialogue":[{{"speaker":"<name|null>","text":"<line>","bubbleType":"speech|thought|caption"}}],
   "caption":"<narration caption or empty>",
   "beat":"<emotional beat>"}}]}}]}}
Rules: Keep panels-per-page between 1 and 3 for crisp pacing; vary shot types for rhythm; 1 splash max unless story demands; put ALL spoken words in dialogue, never in action; keep each character's name spelled exactly as given so the memory bank matches."""


# ── P4: Panel art ────────────────────────────────────────────────────────────

P4_PANEL_ART = """A single comic panel in this exact art style: {style_phrase}.
Shot: {shot_type}. Composition/staging: {staging}. Action: {action}.
Characters in frame (keep them IDENTICAL to the provided reference images):
{character_descriptions}
Consistent line, palette, environment, and rendering with the reference images. Leave clear negative space
near the top/sides for speech bubbles. Do NOT draw any text, letters, or speech bubbles."""


# ── P5: Character-match critic ───────────────────────────────────────────────

P5_CHARACTER_CRITIC = """You are QA for character consistency. Image 1 is a freshly drawn comic panel. The following
images are the approved reference sheets for the characters who should appear.
For EACH named character, judge whether the panel depicts the SAME character (face, hair,
build, outfit, age). Return STRICT JSON (no markdown fences):
{{"results":[{{"name":"<name>","match":true|false,"note":"<if false, what's wrong in <=15 words>"}}]}}
match=false for any noticeable identity drift.
Characters to check: {character_names}"""


# ── P5b: Style / readability critic ──────────────────────────────────────────

P5B_STYLE_CRITIC = """Image 1 is a comic panel; Image 2 is the house style reference.
Return STRICT JSON (no markdown fences):
{{"styleConsistent":true|false,"compositionReadable":true|false,
"textOk":true|false|null,"notes":"<if any false, what to fix in <=20 words>"}}.
textOk=null if the panel has no text. Judge style match, whether the action reads clearly
at a glance, and (if text present) legibility/spelling."""


# ── P5c: Location / environment critic ───────────────────────────────────────

P5C_LOCATION_CRITIC = """You are QA for location and environment consistency. Image 1 is a freshly drawn comic panel.
The following images are the approved reference sheets for the location/setting where the scene occurs.
For EACH named location, judge whether the panel depicts the SAME environment (architecture, landscape,
lighting, atmospheric mood, key features). Return STRICT JSON (no markdown fences):
{{"results":[{{"name":"<name>","match":true|false,"note":"<if false, what's wrong in <=15 words>"}}]}}
match=false for any noticeable environment/architectural drift.
Locations to check: {location_names}"""


# ── P6: Dialogue polish ─────────────────────────────────────────────────────

P6_DIALOGUE_POLISH = """Tighten this panel's dialogue for a comic bubble: natural, in character, and short enough to
letter. Keep meaning and speaker. Return JSON (no markdown fences):
[{{"speaker":"...", "text":"...", "bubbleType":"..."}}].
{dialogue_json}"""


# ── Style guide generation ───────────────────────────────────────────────────

P_STYLE_GUIDE = """Create a comic art style reference image.
Art style: {style_phrase}.
Show a single sample panel demonstrating the line work, coloring approach, shading style,
and overall mood. Use the color palette: {palette}.
No text, no speech bubbles. This image will be used as a style reference for all panels."""


# ── Gemma: Panel triage ─────────────────────────────────────────────────────

P_GEMMA_TRIAGE = """Panel: shotType={shot_type}, characters={n_chars}, has_dialogue={has_dialogue}, action="{action}".
Classify visual complexity as SIMPLE or COMPLEX, and whether a cheap draft pass is warranted
before a final render. Answer JSON: {{"complexity":"SIMPLE|COMPLEX","useDraft":true|false}}."""


# ── Gemma: Moderation ───────────────────────────────────────────────────────

P_GEMMA_MODERATE = """Rate this image generation prompt for content safety.
Rating target: {rating}.
Prompt: \"{prompt}\"
Return JSON: {{"safe":true|false,"reason":"<if unsafe, brief explanation>"}}."""
