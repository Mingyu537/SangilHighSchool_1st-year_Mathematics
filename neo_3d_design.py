"""Create a neo 3D poster-style render in Blender.

Run from the repository root:
    blender --background --python neo_3d_design.py -- --output render/neo_3d_design.png
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Render a neo 3D glass design with Blender.")
    parser.add_argument("--output", default="render/neo_3d_design.png", help="Output PNG path.")
    parser.add_argument("--size", type=int, default=1600, help="Square render size in pixels.")
    parser.add_argument("--samples", type=int, default=128, help="Cycles sample count.")
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def set_socket(node, names: list[str], value) -> None:
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def make_iridescent_material(
    name: str,
    alpha: float = 0.55,
    roughness: float = 0.05,
    transmission: float = 0.7,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    mat.diffuse_color = (0.54, 0.38, 1.0, alpha)

    try:
        mat.use_screen_refraction = True
        mat.show_transparent_back = True
    except AttributeError:
        pass

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        return mat

    layer = nodes.new("ShaderNodeLayerWeight")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.08
    ramp.color_ramp.elements[0].color = (0.00, 0.95, 1.00, 1.0)
    mid = ramp.color_ramp.elements.new(0.52)
    mid.color = (1.00, 0.22, 0.82, 1.0)
    ramp.color_ramp.elements[1].position = 1.00
    ramp.color_ramp.elements[1].color = (1.00, 0.82, 0.28, 1.0)

    links.new(layer.outputs["Facing"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    set_socket(bsdf, ["Alpha"], alpha)
    set_socket(bsdf, ["Roughness"], roughness)
    set_socket(bsdf, ["Metallic"], 0.0)
    set_socket(bsdf, ["Transmission Weight", "Transmission"], transmission)
    set_socket(bsdf, ["IOR"], 1.45)
    set_socket(bsdf, ["Emission Strength"], 0.08)
    set_socket(bsdf, ["Emission Color"], (0.20, 0.45, 1.0, 1.0))
    return mat


def make_basic_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = color
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        set_socket(bsdf, ["Base Color"], color)
        set_socket(bsdf, ["Roughness"], 0.35)
    return mat


def create_curve_tube(
    name: str,
    points: list[tuple[float, float, float]],
    radius: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 32
    curve.bevel_depth = radius
    curve.bevel_resolution = 10

    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = Vector(co)
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"

    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def create_soft_star(material: bpy.types.Material) -> bpy.types.Object:
    segments = 160
    rings = 34
    verts: list[tuple[float, float, float]] = [(0.0, -0.28, 0.0)]
    faces: list[tuple[int, ...]] = []

    for ring in range(1, rings + 1):
        u = ring / rings
        for i in range(segments):
            theta = (2.0 * math.pi * i / segments) + math.radians(45)
            edge = 1.0 + 0.34 * math.cos(4.0 * theta)
            x = 1.35 * u * edge * math.cos(theta)
            z = 1.35 * u * edge * math.sin(theta)
            dome = -0.30 * (1.0 - u**1.8)
            verts.append((x, dome, z))

    for i in range(segments):
        faces.append((0, 1 + i, 1 + ((i + 1) % segments)))

    for ring in range(1, rings):
        start = 1 + (ring - 1) * segments
        next_start = 1 + ring * segments
        for i in range(segments):
            faces.append(
                (
                    start + i,
                    start + ((i + 1) % segments),
                    next_start + ((i + 1) % segments),
                    next_start + i,
                )
            )

    mesh = bpy.data.meshes.new("soft_star_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("soft_four_point_star", mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (1.05, 0.10, 0.30)
    obj.rotation_euler = (math.radians(0), math.radians(0), math.radians(-10))
    obj.data.materials.append(material)

    solidify = obj.modifiers.new("soft thickness", "SOLIDIFY")
    solidify.thickness = 0.22
    solidify.offset = 0.0

    subsurf = obj.modifiers.new("smooth surface", "SUBSURF")
    subsurf.levels = 1
    subsurf.render_levels = 2

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    return obj


def create_text(body: str, location: tuple[float, float, float], size: float, material: bpy.types.Material) -> None:
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90), 0.0, 0.0))
    text = bpy.context.object
    text.name = body.replace(" ", "_").lower()
    text.data.body = body
    text.data.align_x = "CENTER"
    text.data.align_y = "CENTER"
    text.data.size = size
    text.data.extrude = 0.01
    text.data.materials.append(material)


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_lighting() -> None:
    lights = [
        ("AREA", (-3.4, -4.2, 4.8), 520.0, (0.55, 0.90, 1.00), 4.0),
        ("AREA", (3.2, -3.2, 2.2), 320.0, (1.00, 0.35, 0.80), 3.0),
        ("POINT", (0.0, -2.8, -1.5), 160.0, (1.00, 0.75, 0.25), 1.0),
    ]
    for light_type, location, energy, color, size in lights:
        bpy.ops.object.light_add(type=light_type, location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.color = color
        if hasattr(light.data, "size"):
            light.data.size = size


def setup_camera() -> None:
    bpy.ops.object.camera_add(location=(0.0, -6.7, 2.25))
    camera = bpy.context.object
    look_at(camera, (0.0, 0.0, 0.35))
    camera.data.lens = 58
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 6.0
    camera.data.dof.aperture_fstop = 5.6
    bpy.context.scene.camera = camera


def setup_render(output: Path, size: int, samples: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.film_transparent = False
    scene.render.filepath = str(output)

    scene.world.color = (0.006, 0.006, 0.007)

    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "Medium High Contrast"
    except TypeError:
        scene.view_settings.view_transform = "Filmic"
        scene.view_settings.look = "High Contrast"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0


def build_scene() -> None:
    glass = make_iridescent_material("holographic_jelly", alpha=0.62, transmission=0.72)
    tube_glass = make_iridescent_material("clear_color_glass", alpha=0.48, transmission=0.86)
    white = make_basic_material("soft_white", (0.94, 0.94, 0.92, 1.0))
    black = make_basic_material("matte_black", (0.005, 0.005, 0.005, 1.0))

    bpy.ops.mesh.primitive_plane_add(size=7.0, location=(0.0, 1.05, 0.25), rotation=(math.radians(90), 0.0, 0.0))
    backdrop = bpy.context.object
    backdrop.name = "matte_black_backdrop"
    backdrop.data.materials.append(black)

    create_text("Neo 3D Design", (0.0, -0.65, 2.35), 0.36, white)
    create_text("soft glass form / holographic color", (0.0, -0.65, 2.02), 0.095, white)

    create_soft_star(glass)

    paths = [
        [(-2.05, -0.18, -0.95), (-1.35, -0.78, 0.45), (-0.30, -0.22, -0.20), (0.55, -0.70, 0.85), (1.62, -0.15, -0.22)],
        [(-1.72, -0.25, 0.92), (-1.02, -0.82, -0.45), (0.16, -0.35, 0.16), (0.92, -0.74, -0.70), (1.85, -0.16, 0.72)],
        [(-1.92, -0.05, -0.12), (-1.10, -0.56, -0.74), (0.24, -0.16, -1.02), (1.38, -0.48, -0.42), (2.04, -0.10, 0.18)],
    ]
    for index, points in enumerate(paths, start=1):
        create_curve_tube(f"glass_ribbon_{index}", points, 0.045 + index * 0.006, tube_glass)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.48,
        minor_radius=0.055,
        major_segments=128,
        minor_segments=18,
        location=(-1.48, -0.22, -0.42),
        rotation=(math.radians(78), math.radians(18), math.radians(-28)),
    )
    torus = bpy.context.object
    torus.name = "floating_glass_loop"
    torus.data.materials.append(tube_glass)
    bpy.ops.object.shade_smooth()

    for location, radius in [((-2.02, -0.16, -0.95), 0.15), ((1.82, -0.12, 0.72), 0.12), ((0.54, -0.74, 0.86), 0.10)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=radius, location=location)
        sphere = bpy.context.object
        sphere.name = "glass_drop"
        sphere.data.materials.append(tube_glass)
        bpy.ops.object.shade_smooth()


def main() -> None:
    args = parse_args()
    output = Path(args.output).expanduser().resolve()

    clear_scene()
    setup_render(output, args.size, args.samples)
    build_scene()
    setup_lighting()
    setup_camera()
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
