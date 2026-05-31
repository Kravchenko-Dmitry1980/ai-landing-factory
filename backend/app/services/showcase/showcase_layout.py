"""Deterministic 3D card placement for showcase layouts.

Positions are pure functions of the project index and count, so tests can
assert exact coordinates. Coordinates use the A-Frame/three.js convention:
+X right, +Y up, -Z into the screen. The default camera sits at ``0 1.6 5``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.services.showcase.showcase_schema import ShowcaseLayout

CARD_Y = 1.6
CARD_WIDTH = 1.6
CARD_HEIGHT = 1.1


@dataclass(frozen=True)
class CardPlacement:
    """Position + rotation (degrees) of a single card in the scene."""

    x: float
    y: float
    z: float
    rotation_y: float

    def position_attr(self) -> str:
        return f"{self.x:.3f} {self.y:.3f} {self.z:.3f}"

    def rotation_attr(self) -> str:
        return f"0 {self.rotation_y:.3f} 0"


def _round(value: float) -> float:
    # Avoid -0.0 and noisy floats so the output is stable across platforms.
    rounded = round(value, 3)
    return 0.0 if rounded == 0 else rounded


def _gallery_arc(count: int) -> list[CardPlacement]:
    if count <= 0:
        return []
    radius = 4.0
    # Total arc spread grows with count but is capped to keep cards readable.
    spread = min(math.radians(28 * max(count - 1, 1)), math.radians(150))
    start = -spread / 2
    step = spread / (count - 1) if count > 1 else 0.0
    placements: list[CardPlacement] = []
    for i in range(count):
        angle = start + step * i
        x = math.sin(angle) * radius
        z = -math.cos(angle) * radius
        rotation_y = math.degrees(angle)
        placements.append(
            CardPlacement(
                x=_round(x),
                y=CARD_Y,
                z=_round(z),
                rotation_y=_round(rotation_y),
            )
        )
    return placements


def _grid_hall(count: int) -> list[CardPlacement]:
    if count <= 0:
        return []
    columns = min(count, 4)
    col_gap = 2.0
    row_gap = 1.6
    placements: list[CardPlacement] = []
    for i in range(count):
        col = i % columns
        row = i // columns
        x = (col - (columns - 1) / 2) * col_gap
        y = CARD_Y - row * row_gap
        z = -4.5
        placements.append(
            CardPlacement(x=_round(x), y=_round(y), z=z, rotation_y=0.0)
        )
    return placements


def _circle_booths(count: int) -> list[CardPlacement]:
    if count <= 0:
        return []
    radius = 4.5
    placements: list[CardPlacement] = []
    for i in range(count):
        angle = (2 * math.pi / count) * i
        x = math.sin(angle) * radius
        z = -math.cos(angle) * radius
        # Face the center (camera origin area).
        rotation_y = math.degrees(angle)
        placements.append(
            CardPlacement(
                x=_round(x),
                y=CARD_Y,
                z=_round(z),
                rotation_y=_round(rotation_y),
            )
        )
    return placements


def compute_placements(layout: ShowcaseLayout, count: int) -> list[CardPlacement]:
    """Return deterministic placements for the given layout and project count."""

    if layout == ShowcaseLayout.GRID_HALL:
        return _grid_hall(count)
    if layout == ShowcaseLayout.CIRCLE_BOOTHS:
        return _circle_booths(count)
    return _gallery_arc(count)
