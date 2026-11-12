module AshenVault
  # Thin layer over raylib for uploading our generated data and drawing with the PS1 shader.
  class Gpu
    include Raylib

    SHADER_DIR = File.join(__dir__, "shaders")

    attr_reader :shader, :textures

    def initialize
      @shader = LoadShader(File.join(SHADER_DIR, "ps1.vs"), File.join(SHADER_DIR, "ps1.fs"))
      @locs = Hash.new { |h, name| h[name] = GetShaderLocation(@shader, name) }
      @textures = TextureGen.all.to_h { |name, bytes| [name, upload_texture(bytes, TextureGen::SIZE)] }
      @materials = Hash.new { |h, tex| h[tex] = make_material(@textures.fetch(tex) { @textures["white"] }) }
      @meshes = {}
      @color = Color.from_u8(255, 255, 255, 255)
      @vec3 = FFI::MemoryPointer.new(:float, 3)
      @vec2 = FFI::MemoryPointer.new(:float, 2)
      @float = FFI::MemoryPointer.new(:float, 1)
    end

    # --- uniforms ----------------------------------------------------------

    def set_vec3(name, values)
      @vec3.put_array_of_float(0, values.map(&:to_f))
      SetShaderValue(@shader, @locs[name], @vec3, SHADER_UNIFORM_VEC3)
    end

    def set_vec2(name, values)
      @vec2.put_array_of_float(0, values.map(&:to_f))
      SetShaderValue(@shader, @locs[name], @vec2, SHADER_UNIFORM_VEC2)
    end

    def set_float(name, value)
      @float.put_float(0, value.to_f)
      SetShaderValue(@shader, @locs[name], @float, SHADER_UNIFORM_FLOAT)
    end

    # --- resources ---------------------------------------------------------

    def upload_texture(bytes, size)
      data = MemAlloc(bytes.bytesize)
      data.put_bytes(0, bytes)
      image = Image.new
      image[:data] = data
      image[:width] = size
      image[:height] = size
      image[:mipmaps] = 1
      image[:format] = PIXELFORMAT_UNCOMPRESSED_R8G8B8A8
      tex = LoadTextureFromImage(image)
      UnloadImage(image)
      SetTextureFilter(tex, TEXTURE_FILTER_POINT)
      SetTextureWrap(tex, TEXTURE_WRAP_REPEAT)
      tex
    end

    def make_material(texture)
      mat = LoadMaterialDefault()
      mat[:shader] = @shader
      SetMaterialTexture(mat.to_ptr, MATERIAL_MAP_ALBEDO, texture)
      mat
    end

    def material(tex) = @materials[tex]

    # Uploads a MeshBuilder::Batch. Colors are 0..1 floats.
    def upload_batch(batch)
      n = batch.vertex_count
      mesh = Mesh.new
      mesh[:vertexCount] = n
      mesh[:triangleCount] = n / 3
      mesh[:vertices] = alloc_floats(batch.verts)
      mesh[:texcoords] = alloc_floats(batch.uvs)
      normals = Array.new(n * 3, 0.0)
      (0...n).each { |i| normals[i * 3 + 1] = 1.0 }
      mesh[:normals] = alloc_floats(normals)
      colors = MemAlloc(n * 4)
      colors.put_bytes(0, batch.colors.each_slice(3).map { |r, g, b| [r * 255, g * 255, b * 255, 255] }.flatten.pack("C*"))
      mesh[:colors] = colors
      UploadMesh(mesh.to_ptr, false)
      mesh
    end

    def alloc_floats(values)
      ptr = MemAlloc(values.size * 4)
      ptr.put_array_of_float(0, values)
      ptr
    end

    def unload_mesh(mesh) = UnloadMesh(mesh)

    # Primitive meshes for models, all unit-sized and centered on the origin.
    def primitive(kind)
      @meshes[kind] ||= case kind
                        when :cube then GenMeshCube(1, 1, 1)
                        when :sphere then GenMeshSphere(0.5, 5, 7)
                        when :cyl then centered(GenMeshCylinder(0.5, 1, 7))
                        when :cone then centered(GenMeshCone(0.5, 1, 7))
                        when :quad then GenMeshPlane(1, 1, 1, 1)
                        end
    end

    # Cylinders and cones are generated base-at-origin; shift them to center.
    def centered(mesh)
      count = mesh[:vertexCount]
      verts = mesh[:vertices].get_array_of_float(0, count * 3)
      (0...count).each { |i| verts[i * 3 + 1] -= 0.5 }
      mesh[:vertices].put_array_of_float(0, verts)
      UpdateMeshBuffer(mesh, 0, mesh[:vertices], count * 12, 0)
      mesh
    end

    # --- drawing -----------------------------------------------------------

    def draw_world_batch(mesh, tex)
      set_float("isModel", 0.0)
      mat = material(tex)
      set_color(mat, 255, 255, 255)
      DrawMesh(mesh, mat, MatrixIdentity())
    end

    # Models keep a floor of light so they never vanish into the dark.
    def model_light(rgb)
      @model_light = rgb.map { |c| c + 0.12 }
      set_vec3("modelLight", @model_light)
    end

    def draw_part(kind, matrix, rgb, tex: "white", glow: false)
      mat = material(tex)
      set_color(mat, *rgb)
      set_vec3("modelLight", [1.5, 1.5, 1.5]) if glow
      DrawMesh(primitive(kind), mat, matrix)
      set_vec3("modelLight", @model_light) if glow && @model_light
    end

    def set_color(mat, r, g, b)
      map = MaterialMap.new(mat[:maps])
      map[:color][:r] = r
      map[:color][:g] = g
      map[:color][:b] = b
      map[:color][:a] = 255
    end

    def to_matrix(m)
      mx = Matrix.new
      # m is row-major 4x4; raylib fields mN are column-major indices.
      16.times { |i| mx[:"m#{(i % 4) * 4 + i / 4}"] = m[i] }
      mx
    end
  end
end
