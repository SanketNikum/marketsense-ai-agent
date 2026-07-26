"""
Guardrail checks: inspect a generated story AFTER the LLM writes it,
and decide whether it's safe to show. Prompt instructions are requests;
these checks are the actual enforcement.
"""

import re

FORBIDDEN_PHRASES = [
    "should buy", "should sell", "buy now", "sell now",
    "good time to buy", "good time to sell",
    "recommend buying", "recommend selling",
    "strong buy", "strong sell",
    "buying opportunity", "consider buying", "consider selling",
    "you should invest", "worth investing",
]


def check_advice_language(story_text: str) -> list[str]:
    """Flags any buy/sell/hold advice language in the story."""
    lowered = story_text.lower()
    violations = []

    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            violations.append(f"Contains advice-like language: '{phrase}'")

    return violations


def check_numeric_claims(story_text: str, mover: dict) -> list[str]:
    """Flags percentage figures in the story that don't match the real price move."""
    violations = []
    found_percentages = re.findall(r"(-?\d+(?:\.\d+)?)\s?%", story_text)
    actual_pct = abs(mover["pct_change"])

    for raw_number in found_percentages:
        claimed_pct = abs(float(raw_number))
        if abs(claimed_pct - actual_pct) > 0.5:
            violations.append(
                f"Story claims a {claimed_pct}% figure, but actual price change was {mover['pct_change']}%"
            )

    return violations


def check_guardrails(story_text: str, mover: dict) -> dict:
    """Runs all guardrail checks. Returns {"passed": bool, "violations": list[str]}."""
    violations = check_advice_language(story_text) + check_numeric_claims(story_text, mover)

    return {"passed": len(violations) == 0, "violations": violations}


if __name__ == "__main__":
    good_story = "HDFC Bank fell 2.8% today amid weak Q1 earnings."
    bad_story = "HDFC Bank fell 2.8% today - this looks like a great buying opportunity."
    wrong_number_story = "HDFC Bank fell 9.4% today amid weak Q1 earnings."

    test_mover = {"ticker": "HDFCBANK.NS", "pct_change": -2.8}

    for label, story in [
        ("good_story", good_story),
        ("bad_story (advice)", bad_story),
        ("wrong_number_story", wrong_number_story),
    ]:
        result = check_guardrails(story, test_mover)
        print(f"{label}: {result}")
