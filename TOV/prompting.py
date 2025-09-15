"""
prompting.py — minimal prompt builder and parameter mapping for the Streamlit LLM Copy POC.

Responsibilities:
- Map UI controls (tone strength, length) to LLM parameters.
- Build system & user prompts using current guidelines + inputs.
- Keep it small and explicit for a POC.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, Literal, Optional

ToneLevel = Literal[0, 1, 2, 3]  # 0 Subtle, 1 Balanced, 2 Firm, 3 Strong
LengthCode = Literal["short", "medium", "long"]
TaskCode = Literal["rewrite", "create"]


# -------------------------
# Parameter mappings
# -------------------------

TONE_TO_PARAMS: Dict[ToneLevel, Dict[str, float]] = {
    0: {"temperature": 0.3, "frequency_penalty": 0.0, "presence_penalty": 0.0},  # minimal guidelines
    1: {"temperature": 0.4, "frequency_penalty": 0.1, "presence_penalty": 0.0}, # light guidelines
    2: {"temperature": 0.5, "frequency_penalty": 0.2, "presence_penalty": 0.1},  # moderate guidelines
    3: {"temperature": 0.6, "frequency_penalty": 0.3, "presence_penalty": 0.1},  # strict guidelines
}

LENGTH_TO_INSTRUCTIONS: Dict[LengthCode, str] = {
    "short": "Keep it very concise and to the point. Use short sentences and avoid unnecessary details.",
    "medium": "Provide a balanced amount of detail. Be clear and informative without being overly brief or verbose.",
    "long": "Expand with more detail and context. Provide comprehensive information while maintaining clarity."
}


@dataclass
class PromptSpec:
    system: str
    user: str
    params: Dict[str, float]
    task: TaskCode
    length: LengthCode
    tone: ToneLevel


# -------------------------
# Builders
# -------------------------

def _compile_guidelines(guidelines: str) -> str:
    """For POC: return guidelines verbatim.
    In production, compact tables into bullets to cut tokens.
    """
    return (guidelines or "").strip()


def _task_for(source_text: Optional[str], requested: Optional[TaskCode]) -> TaskCode:
    if requested in ("rewrite", "create"):
        return requested
    return "rewrite" if (source_text or "").strip() else "create"


def build_prompts(
    *,
    guidelines: str,
    source_text: str,
    instructions: Optional[str],
    tone_level: ToneLevel,
    length_code: LengthCode,
    task: Optional[TaskCode] = None,
) -> PromptSpec:
    task_code = _task_for(source_text, task)

    tone_labels = {0: "minimal guidelines", 1: "light guidelines", 2: "moderate guidelines", 3: "strict guidelines"}

    # Create different system prompts based on tone level
    if tone_level == 0:
        # Minimal guidelines - keep original text mostly intact
        system_prompt = f"""
You are a text editor. Make minimal changes to improve clarity while preserving the original meaning and style.

Guidelines (apply lightly):
---
{_compile_guidelines(guidelines)}
---

Only make small improvements for clarity. Keep the original structure and most of the original wording.
Only output the final copytext (no preambles, no bullet summaries, no Markdown unless the user text clearly contains Markdown that should be preserved).
""".strip()
    elif tone_level == 1:
        # Light guidelines - some brand voice application
        system_prompt = f"""
You are a brand voice editor. Apply the guidelines moderately while preserving the core message.

Guidelines (apply moderately):
---
{_compile_guidelines(guidelines)}
---

Improve the text with some brand voice elements, but don't completely rewrite it.
Only output the final copytext (no preambles, no bullet summaries, no Markdown unless the user text clearly contains Markdown that should be preserved).
""".strip()
    elif tone_level == 2:
        # Moderate guidelines - clear brand voice application
        system_prompt = f"""
You are a brand voice engine. Apply the guidelines clearly while maintaining the message.

Guidelines (apply clearly):
---
{_compile_guidelines(guidelines)}
---

Rewrite the text to clearly reflect the brand voice while keeping the core message intact.
Only output the final copytext (no preambles, no bullet summaries, no Markdown unless the user text clearly contains Markdown that should be preserved).
""".strip()
    else:  # tone_level == 3
        # Strict guidelines - full brand voice transformation
        system_prompt = f"""
You are a brand voice engine. Follow the provided guidelines *strictly*.
Key rules to enforce at all times:
- One idea per sentence; lead with action and value.
- Prioritise clarity over cleverness; avoid hype and generic slogans.
- Use precise, human language; avoid jargon and buzzwords.
- Use sentence case in headings/CTAs; keep punctuation clean; avoid exclamation marks.
- Respect vocabulary and the "payment vs payments" rules.

Guidelines (canonical, authoritative - apply strictly):
---
{_compile_guidelines(guidelines)}
---
Transform the text completely to match the brand voice. Only output the final copytext (no preambles, no bullet summaries, no Markdown unless the user text clearly contains Markdown that should be preserved).
""".strip()

    # A concise, structured user message. We do not switch to JSON mode to avoid brittle parsing.
    user_prompt = f"""
Task: {task_code}
Guideline adherence: {tone_labels[tone_level]}
Length: {LENGTH_TO_INSTRUCTIONS[length_code]}
Instructions: {(instructions or '').strip() or 'N/A'}

Source text:
>>>\n{(source_text or '').strip()}\n<<<

Constraints:
- If Task is rewrite: preserve meaning, improve clarity, remove hype.
- If Task is create: draft directly to the point; do not invent fake stats or names.
- Prefer short sentences and concrete verbs (set, choose, adjust, track).
""".strip()

    params = {
        **TONE_TO_PARAMS[tone_level],
    }

    return PromptSpec(system=system_prompt, user=user_prompt, params=params, task=task_code, length=length_code, tone=tone_level)
