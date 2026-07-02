#!/usr/bin/env python3
"""Generate a GitHub-dark contribution snake SVG from public contribution data."""

from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

USERNAME = "jobcode003"
API_URL = f"https://github-contributions-api.deno.dev/{USERNAME}.json"
OUTPUT = Path(__file__).resolve().parents[1] / "profile" / "github-snake-dark.svg"

# GitHub dark contribution palette (low -> high)
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
SNAKE_COLOR = "#ff6b35"
CELL = 13
GAP = 3
PITCH = CELL + GAP
PAD = 16


def fetch_contributions() -> list[list[dict]]:
    with urllib.request.urlopen(API_URL, timeout=30) as response:
        payload = json.load(response)
    return payload["contributions"]


def level_to_color(level: str, count: int) -> str:
    if count <= 0:
        return COLORS[0]
    mapping = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }
    idx = mapping.get(level, min(4, max(1, count)))
    return COLORS[idx]


def build_snake_path(grid: list[list[dict]]) -> list[tuple[float, float]]:
    """Walk the grid in row-major order through cells with contributions."""
    points: list[tuple[float, float]] = []
    weeks = len(grid)
    for week_idx, week in enumerate(grid):
        for day_idx, day in enumerate(week):
            if day.get("contributionCount", 0) <= 0:
                continue
            x = PAD + week_idx * PITCH + CELL / 2
            y = PAD + day_idx * PITCH + CELL / 2
            points.append((x, y))

    if not points:
        # Fallback path across center row so animation still renders.
        mid = 3
        for week_idx in range(weeks):
            x = PAD + week_idx * PITCH + CELL / 2
            y = PAD + mid * PITCH + CELL / 2
            points.append((x, y))
    return points


def points_to_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    parts = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for x, y in points[1:]:
        parts.append(f"L {x:.1f} {y:.1f}")
    return " ".join(parts)


def main() -> None:
    grid = fetch_contributions()
    weeks = len(grid)
    days = len(grid[0]) if grid else 7
    width = PAD * 2 + weeks * PITCH - GAP
    height = PAD * 2 + days * PITCH - GAP

    rects: list[str] = []
    for week_idx, week in enumerate(grid):
        for day_idx, day in enumerate(week):
            x = PAD + week_idx * PITCH
            y = PAD + day_idx * PITCH
            color = level_to_color(day.get("contributionLevel", "NONE"), day.get("contributionCount", 0))
            rects.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
            )

    snake_points = build_snake_path(grid)
    path_d = points_to_path(snake_points)
    path_length = max(200, len(snake_points) * 18)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#0d1117"/>
  <g>
    {''.join(rects)}
  </g>
  <path id="snake-trail" d="{path_d}" fill="none" stroke="{SNAKE_COLOR}" stroke-width="4"
        stroke-linecap="round" stroke-linejoin="round" opacity="0.85"
        stroke-dasharray="{path_length}" stroke-dashoffset="{path_length}">
    <animate attributeName="stroke-dashoffset" from="{path_length}" to="0" dur="8s" repeatCount="indefinite"/>
  </path>
  <circle r="5" fill="{SNAKE_COLOR}">
    <animateMotion dur="8s" repeatCount="indefinite" path="{path_d}"/>
  </circle>
</svg>
"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(svg)} bytes, {weeks}x{days} grid, {len(snake_points)} snake points)")


if __name__ == "__main__":
    main()
