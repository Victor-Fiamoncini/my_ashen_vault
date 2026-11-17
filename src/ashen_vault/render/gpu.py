"""Thin layer over raylib for uploading our generated data and drawing with the PS1 shader."""

import os
from array import array

import raylib as rl
from raylib import ffi

from ashen_vault.render import shapes, texture_gen

SHADER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shaders")


class Gpu:
    def __init__(self):
        self.shader = rl.LoadShader(
            os.path.join(SHADER_DIR, "ps1.vs").encode(), os.path.join(SHADER_DIR, "ps1.fs").encode()
        )
        self._locs = {}
        self.textures = {
            name: self.upload_texture(data, texture_gen.SIZE)
            for name, data in texture_gen.all_textures().items()
        }
        self._materials = {}
        self._meshes = {}
        self._tris = {}
        self._model_light = None
        self._vec3 = ffi.new("float[3]")
        self._vec2 = ffi.new("float[2]")
        self._float = ffi.new("float[1]")
        self._identity = rl.MatrixIdentity()
        self._matrix = ffi.new("Matrix *")  # every part's transform passes through this one buffer

    # --- uniforms ----------------------------------------------------------

    def _loc(self, name):
        loc = self._locs.get(name)
        if loc is None:
            loc = self._locs[name] = rl.GetShaderLocation(self.shader, name.encode())
        return loc

    def set_vec3(self, name, values):
        self._vec3[0], self._vec3[1], self._vec3[2] = (float(v) for v in values)
        rl.SetShaderValue(self.shader, self._loc(name), self._vec3, rl.SHADER_UNIFORM_VEC3)

    def set_vec2(self, name, values):
        self._vec2[0], self._vec2[1] = (float(v) for v in values)
        rl.SetShaderValue(self.shader, self._loc(name), self._vec2, rl.SHADER_UNIFORM_VEC2)

    def set_float(self, name, value):
        self._float[0] = float(value)
        rl.SetShaderValue(self.shader, self._loc(name), self._float, rl.SHADER_UNIFORM_FLOAT)

    # --- resources ---------------------------------------------------------

    def upload_texture(self, data, size):
        buf = ffi.new("unsigned char[]", data)
        image = ffi.new(
            "Image *",
            {
                "data": buf,
                "width": size,
                "height": size,
                "mipmaps": 1,
                "format": rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8,
            },
        )
        tex = rl.LoadTextureFromImage(image[0])
        rl.SetTextureFilter(tex, rl.TEXTURE_FILTER_POINT)
        rl.SetTextureWrap(tex, rl.TEXTURE_WRAP_REPEAT)
        return tex

    def material(self, tex):
        mat = self._materials.get(tex)
        if mat is None:
            mat = rl.LoadMaterialDefault()
            mat.shader = self.shader
            mat.maps[rl.MATERIAL_MAP_ALBEDO].texture = self.textures.get(tex, self.textures["white"])
            self._materials[tex] = mat
        return mat

    @staticmethod
    def _alloc(ctype, raw):
        """Copies bytes into raylib-owned memory so UnloadMesh can free it."""
        ptr = rl.MemAlloc(len(raw))
        ffi.memmove(ptr, raw, len(raw))
        return ffi.cast(ctype, ptr)

    def upload_batch(self, batch):
        """Uploads a MeshBuilder Batch. Colors are 0..1 floats."""
        n = batch.vertex_count
        mesh = ffi.new("Mesh *")
        mesh.vertexCount = n
        mesh.triangleCount = n // 3
        mesh.vertices = self._alloc("float *", array("f", batch.verts).tobytes())
        mesh.texcoords = self._alloc("float *", array("f", batch.uvs).tobytes())
        # A baked prop's light rides in the normals (`Batch.light`); the world needs none.
        normals = (
            array("f", light) if (light := getattr(batch, "light", None)) else array("f", [0.0, 1.0, 0.0]) * n
        )
        mesh.normals = self._alloc("float *", normals.tobytes())
        rgb = bytes(int(c * 255) for c in batch.colors)
        rgba = bytearray(b"\xff") * (n * 4)
        for ch in range(3):
            rgba[ch::4] = rgb[ch::3]
        mesh.colors = self._alloc("unsigned char *", bytes(rgba))
        rl.UploadMesh(mesh, False)
        return mesh

    def unload_mesh(self, mesh):
        rl.UnloadMesh(mesh[0])

    def primitive(self, kind):
        """Primitive meshes for models, all unit-sized and centered on the origin."""
        mesh = self._meshes.get(kind)
        if mesh is None:
            if kind == "cube":
                mesh = rl.GenMeshCube(1, 1, 1)
            elif kind == "sphere":
                mesh = rl.GenMeshSphere(0.5, 5, 7)
            elif kind == "cyl":
                mesh = self._centered(rl.GenMeshCylinder(0.5, 1, 7))
            elif kind == "cone":
                mesh = self._centered(rl.GenMeshCone(0.5, 1, 7))
            elif kind == "quad":
                mesh = rl.GenMeshPlane(1, 1, 1, 1)
            elif kind in shapes.SHAPES:
                mesh = self._upload_shape(*shapes.SHAPES[kind]())[0]
            self._meshes[kind] = mesh
        return mesh

    def primitive_tris(self, kind):
        """A primitive's triangles as flat (vertices, normals, uvs) lists, unindexed: what
        `prop_bake.PropBaker` transforms into a baked batch, exactly the mesh `draw_part` draws."""
        tris = self._tris.get(kind)
        if tris is None:
            mesh = self.primitive(kind)
            n = mesh.vertexCount
            verts = ffi.unpack(mesh.vertices, n * 3)
            normals = ffi.unpack(mesh.normals, n * 3)
            uvs = ffi.unpack(mesh.texcoords, n * 2)
            if mesh.indices != ffi.NULL:
                order = ffi.unpack(mesh.indices, mesh.triangleCount * 3)
                verts = [verts[i * 3 + k] for i in order for k in range(3)]
                normals = [normals[i * 3 + k] for i in order for k in range(3)]
                uvs = [uvs[i * 2 + k] for i in order for k in range(2)]
            tris = self._tris[kind] = (list(verts), list(normals), list(uvs))
        return tris

    @staticmethod
    def _centered(mesh):
        """Cylinders and cones are generated base-at-origin; shift them to center."""
        count = mesh.vertexCount
        for i in range(count):
            mesh.vertices[i * 3 + 1] -= 0.5
        rl.UpdateMeshBuffer(mesh, 0, mesh.vertices, count * 12, 0)
        return mesh

    def _upload_shape(self, verts, normals, uvs):
        """Uploads a triangle soup from render/shapes.py as a model primitive."""
        mesh = ffi.new("Mesh *")
        mesh.vertexCount = len(verts) // 3
        mesh.triangleCount = len(verts) // 9
        mesh.vertices = self._alloc("float *", array("f", verts).tobytes())
        mesh.normals = self._alloc("float *", array("f", normals).tobytes())
        mesh.texcoords = self._alloc("float *", array("f", uvs).tobytes())
        rl.UploadMesh(mesh, False)
        return mesh

    # --- drawing -----------------------------------------------------------

    def draw_world_batch(self, mesh, tex):
        self.set_float("isModel", 0.0)
        mat = self.material(tex)
        self.set_color(mat, 255, 255, 255)
        rl.DrawMesh(mesh[0], mat, self._identity)

    def draw_baked_batch(self, mesh, tex):
        """Props baked by `prop_bake`: world-space, lit in their (halved) vertex colours."""
        self.set_float("isModel", -1.0)
        mat = self.material(tex)
        self.set_color(mat, 255, 255, 255)
        rl.DrawMesh(mesh[0], mat, self._identity)

    def draw_sky_batch(self, mesh, tex, matrix):
        """A sky layer: baked vertex colours like the world, placed around the eye by `matrix`."""
        self.set_float("isModel", 0.0)
        mat = self.material(tex)
        self.set_color(mat, 255, 255, 255)
        rl.DrawMesh(mesh[0], mat, matrix)

    def model_light(self, rgb):
        """Models keep a floor of light so they never vanish into the dark."""
        self._model_light = [c + 0.12 for c in rgb]
        self.set_vec3("modelLight", self._model_light)

    def draw_part(self, kind, matrix, rgb, tex="white", glow=False):
        mat = self._materials.get(tex) or self.material(tex)
        c = mat.maps[0].color
        r, g, b = rgb
        c.r = 0 if r < 0 else 255 if r > 255 else int(r)
        c.g = 0 if g < 0 else 255 if g > 255 else int(g)
        c.b = 0 if b < 0 else 255 if b > 255 else int(b)
        if glow:
            self.set_vec3("modelLight", (1.5, 1.5, 1.5))
        rl.DrawMesh(self.primitive(kind), mat, matrix)
        if glow and self._model_light:
            self.set_vec3("modelLight", self._model_light)

    @staticmethod
    def set_color(mat, r, g, b):
        c = mat.maps[0].color
        c.r = max(0, min(255, int(r)))
        c.g = max(0, min(255, int(g)))
        c.b = max(0, min(255, int(b)))
        c.a = 255

    def to_matrix(self, m):
        """`m` as a raylib Matrix, valid until the next call (the buffer is reused). It is row-major
        4x4, which is exactly raylib's Matrix field order (m0, m4, m8, m12, ...)."""
        ffi.memmove(self._matrix, array("f", m), 64)
        return self._matrix[0]
