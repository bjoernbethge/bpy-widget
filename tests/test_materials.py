"""Tests for materials module"""
import pytest
import bpy

from bpy_widget.core.materials import create_material, create_preset_material, assign_material


def test_create_material_basic(clean_scene):
    """Test creating a basic material"""
    mat = create_material(
        name="TestMaterial",
        base_color=(1.0, 0.0, 0.0, 1.0),
        metallic=0.5,
        roughness=0.3
    )

    assert mat is not None
    assert mat.name == "TestMaterial"
    assert mat.use_nodes is True

    # Check principled BSDF exists
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    assert principled is not None


def test_create_preset_material_gold(clean_scene):
    """Test creating gold preset material"""
    mat = create_preset_material("GoldMaterial", "gold")

    assert mat is not None
    assert mat.name == "GoldMaterial"

    # Gold should be metallic
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    assert principled.inputs["Metallic"].default_value > 0.9


def test_create_preset_material_glass(clean_scene):
    """Test creating glass preset material"""
    mat = create_preset_material("GlassMaterial", "glass")

    assert mat is not None
    # Glass should have transmission
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    assert principled.inputs["Transmission Weight"].default_value > 0.8


def test_assign_material(test_cube):
    """Test assigning material to object"""
    mat = create_material("TestMat", base_color=(0.0, 1.0, 0.0, 1.0))
    assign_material(test_cube, mat)

    assert len(test_cube.data.materials) == 1
    assert test_cube.data.materials[0] == mat


def test_material_with_emission(clean_scene):
    """Test material with emission"""
    mat = create_material(
        name="EmissiveMat",
        base_color=(1.0, 0.5, 0.0, 1.0),
        emission_strength=2.0
    )

    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    assert principled.inputs["Emission Strength"].default_value == 2.0
