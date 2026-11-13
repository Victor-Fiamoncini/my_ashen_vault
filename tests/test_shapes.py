from ashen_vault.render import shapes


def _tris(verts, normals):
    for i in range(0, len(verts), 9):
        yield [tuple(verts[i + k : i + k + 3]) for k in (0, 3, 6)], tuple(normals[i : i + 3])


def test_shapes_are_unit_sized_centred_and_face_outward():
    for name, build in shapes.SHAPES.items():
        verts, normals, uvs = build()
        assert len(verts) % 9 == 0 and len(verts) == len(normals) and len(uvs) == len(verts) // 3 * 2
        for axis in range(3):
            coords = verts[axis::3]
            assert min(coords) >= -0.5 - 1e-9 and max(coords) <= 0.5 + 1e-9, (name, axis)
            assert abs(min(coords) + max(coords)) < 1e-9, f"{name} is centred on axis {axis}"
        for (a, b, c), n in _tris(verts, normals):
            assert abs(shapes._dot(n, n) - 1) < 1e-6
            centre = tuple((a[i] + b[i] + c[i]) / 3 for i in range(3))
            assert shapes._dot(n, centre) > 0, f"{name}: a face looks inward"
            wound = shapes._cross(shapes._sub(b, a), shapes._sub(c, a))
            assert shapes._dot(wound, n) > 0, f"{name}: a face is wound clockwise from outside"


def test_the_blade_comes_to_a_point():
    verts, _, _ = shapes.blade()
    top = max(verts[1::3])
    at_top = {tuple(verts[i : i + 3]) for i in range(0, len(verts), 3) if verts[i + 1] == top}
    assert at_top == {(0.0, 0.5, 0.0)}
