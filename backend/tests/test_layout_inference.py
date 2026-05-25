"""Tests for layout_inference."""

from app.schemas.architecture import DiagramType, LayoutStyle
from app.services.architecture.layout_inference import infer_layout


def test_pipeline_vertical():
    assert infer_layout(DiagramType.PIPELINE, 5) == LayoutStyle.VERTICAL_PIPELINE


def test_layered_layout():
    assert infer_layout(DiagramType.LAYERED, 8) == LayoutStyle.LAYERED


def test_microservices_mesh_for_large():
    assert infer_layout(DiagramType.MICROSERVICES, 12) == LayoutStyle.MESH
