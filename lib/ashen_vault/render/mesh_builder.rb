module AshenVault
  # Turns a TileMap into triangle soup grouped by texture, with lighting baked
  # into vertex colors. Pure Ruby: the GPU upload lives in GpuMesh.
  class MeshBuilder
    Light = Struct.new(:x, :y, :z, :radius, :color)
    Batch = Struct.new(:verts, :uvs, :colors) do
      def vertex_count = verts.size / 3
    end

    SEG = 1.0 # max quad size in meters, keeps affine warping tolerable
    DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]].freeze

    attr_reader :batches

    def initialize(map, lights: [])
      @map = map
      @lights = lights
      ambient = map.meta.fetch(:ambient, [0.2, 0.2, 0.2])
      @ambient = ambient
      @batches = Hash.new { |h, k| h[k] = Batch.new([], [], []) }
    end

    def self.lights_for(map)
      map.entities.filter_map do |e|
        next unless %w[torch brazier light].include?(e.kind)

        x, z = TileMap.center(e.tx, e.tz)
        y = map[e.tx, e.tz].floor + e.props.fetch("y", e.kind == "light" ? "2.0" : "1.6").to_f
        color = e.props.fetch("color", "1.0,0.62,0.32").split(",").map(&:to_f)
        Light.new(x, y, z, e.props.fetch("radius", "7").to_f, color)
      end
    end

    # Light reaching a point, without shadows. Used for models too.
    def light_at(x, y, z, nx = 0.0, ny = 1.0, nz = 0.0)
      r, g, b = @ambient
      @lights.each do |l|
        dx = l.x - x
        dy = l.y - y
        dz = l.z - z
        d = Math.sqrt(dx * dx + dy * dy + dz * dz)
        next if d >= l.radius

        f = (1.0 - d / l.radius)**2
        facing = d < 1e-3 ? 1.0 : [(dx * nx + dy * ny + dz * nz) / d, 0.0].max * 0.7 + 0.3
        k = f * facing * 1.4
        r += l.color[0] * k
        g += l.color[1] * k
        b += l.color[2] * k
      end
      [r, g, b]
    end

    def build
      @map.each_tile do |tx, tz, tile|
        tile.solid ? build_solid(tx, tz, tile) : build_open(tx, tz, tile)
      end
      self
    end

    private

    def t = TileMap::TILE

    def build_open(tx, tz, tile)
      x0 = tx * t
      z0 = tz * t
      horizontal(tile.floor_tex, x0, z0, tile.floor, 1, tile.liquid ? 0.85 : 1.0)
      horizontal(tile.ceil_tex, x0, z0, tile.ceil, -1, 0.75) if tile.ceil

      DIRS.each do |dx, dz|
        nb = @map[tx + dx, tz + dz]
        if nb.solid
          top = tile.ceil || nb.top
          wall(nb.wall_tex, tx, tz, dx, dz, tile.floor, top) if top > tile.floor
        elsif nb.floor < tile.floor
          # Step face: drawn by the higher tile, facing down into the neighbor.
          wall(tile.wall_tex, tx, tz, dx, dz, nb.floor, tile.floor, face_out: true)
        end
        next if nb.solid

        if tile.ceil && nb.ceil && nb.ceil > tile.ceil
          wall(tile.wall_tex, tx, tz, dx, dz, tile.ceil, nb.ceil, face_out: true)
        elsif tile.ceil && nb.ceil.nil?
          wall(tile.wall_tex, tx, tz, dx, dz, tile.ceil, tile.ceil + 0.6, face_out: true)
        end
      end
    end

    def build_solid(tx, tz, tile)
      exposed = DIRS.any? do |dx, dz|
        nb = @map[tx + dx, tz + dz]
        !nb.solid && nb.ceil.nil?
      end
      return unless exposed

      horizontal(tile.floor_tex, tx * t, tz * t, tile.top, 1, 0.9)
      DIRS.each do |dx, dz|
        nb = @map[tx + dx, tz + dz]
        next unless nb.solid && nb.top < tile.top

        wall(tile.wall_tex, tx, tz, dx, dz, nb.top, tile.top, face_out: true)
      end
    end

    # Floor (up = 1) or ceiling (up = -1) of one tile, split into SEG squares.
    def horizontal(tex, x0, z0, y, up, shade)
      n = (t / SEG).round
      n.times do |i|
        n.times do |j|
          ax = x0 + i * SEG
          az = z0 + j * SEG
          pts = [[ax, y, az], [ax, y, az + SEG], [ax + SEG, y, az + SEG], [ax + SEG, y, az]]
          uvs = pts.map { |p| [p[0] / t, p[2] / t] }
          quad(tex, pts, uvs, [0.0, up.to_f, 0.0], shade)
        end
      end
    end

    # Vertical face on the edge of tile (tx, tz) toward direction (dx, dz).
    # Faces into the tile unless face_out.
    def wall(tex, tx, tz, dx, dz, y0, y1, face_out: false)
      cx = (tx + 0.5) * t
      cz = (tz + 0.5) * t
      ex = cx + dx * t / 2
      ez = cz + dz * t / 2
      # Edge endpoints run perpendicular to the direction.
      ax = ex - dz.abs * t / 2
      az = ez - dx.abs * t / 2
      bx = ex + dz.abs * t / 2
      bz = ez + dx.abs * t / 2
      normal = face_out ? [dx.to_f, 0.0, dz.to_f] : [-dx.to_f, 0.0, -dz.to_f]
      shade = dx.zero? ? 0.9 : 0.78
      cols = (t / SEG).round
      rows = ((y1 - y0) / SEG).ceil
      cols.times do |i|
        u0 = i.to_f / cols
        u1 = (i + 1).to_f / cols
        px0 = ax + (bx - ax) * u0
        pz0 = az + (bz - az) * u0
        px1 = ax + (bx - ax) * u1
        pz1 = az + (bz - az) * u1
        rows.times do |r|
          ya = y0 + (y1 - y0) * r / rows
          yb = y0 + (y1 - y0) * (r + 1) / rows
          pts = [[px0, ya, pz0], [px1, ya, pz1], [px1, yb, pz1], [px0, yb, pz0]]
          uvs = pts.map { |p| [(p[0] + p[2]) / t, -p[1] / t] }
          quad(tex, pts, uvs, normal, shade, ao_floor: y0)
        end
      end
    end

    def quad(tex, pts, uvs, normal, shade, ao_floor: nil)
      a, b, c = pts
      cross = cross(sub(b, a), sub(c, a))
      if dot(cross, normal).negative?
        pts = pts.reverse
        uvs = uvs.reverse
      end
      batch = @batches[tex]
      colors = pts.map do |p|
        k = shade
        k *= 0.7 + 0.3 * [(p[1] - ao_floor) / 0.8, 1.0].min if ao_floor
        light_at(p[0], p[1], p[2], *normal).map { |ch| (ch * k).clamp(0.0, 1.0) }
      end
      [0, 1, 2, 0, 2, 3].each do |i|
        batch.verts.concat(pts[i])
        batch.uvs.concat(uvs[i])
        batch.colors.concat(colors[i])
      end
    end

    def sub(a, b) = [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
    def dot(a, b) = a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
    def cross(a, b) = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
  end
end
