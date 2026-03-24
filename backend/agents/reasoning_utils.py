from __future__ import annotations

from typing import Dict, List, Tuple


def sort_feature_contributions(reasoning: Dict[str, float]) -> List[Tuple[str, float]]:
    items = [(name, float(score)) for name, score in reasoning.items()]
    items.sort(key=lambda x: abs(x[1]), reverse=True)
    return items


def format_feature_contributions(
    reasoning: Dict[str, float],
    top_k: int = 5,
    *,
    bullet: str = "-",
    decimals: int = 3,
    include_direction: bool = False,
) -> str:
    top_items = sort_feature_contributions(reasoning)[:top_k]
    if not top_items:
        return "No reasoning available" if bullet == "-" else "- No significant factors identified."

    lines: list[str] = []
    for name, value in top_items:
        if include_direction:
            direction = "Positive" if value > 0 else "Negative"
            label = name.replace("_", " ").title()
            lines.append(f"{bullet} {label}: {value:+.{decimals}f} ({direction} Impact)")
        else:
            lines.append(f"{bullet} {name}: {value:+.{decimals}f}")

    return "\n".join(lines)
