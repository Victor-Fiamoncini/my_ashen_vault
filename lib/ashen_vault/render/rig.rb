module AshenVault
  # Row-major 4x4 matrix stack for building hierarchical low-poly models.
  # Models face +X, up is +Y.
  class Rig
    IDENTITY = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0].freeze

    def initialize(gpu)
      @gpu = gpu
      @stack = [IDENTITY]
    end

    def self.mul(a, b)
      out = Array.new(16, 0.0)
      4.times do |r|
        4.times do |c|
          out[r * 4 + c] = a[r * 4] * b[c] + a[r * 4 + 1] * b[4 + c] + a[r * 4 + 2] * b[8 + c] + a[r * 4 + 3] * b[12 + c]
        end
      end
      out
    end

    def self.translate(x, y, z) = [1.0, 0, 0, x, 0, 1.0, 0, y, 0, 0, 1.0, z, 0, 0, 0, 1.0]
    def self.scale(x, y, z) = [x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0, 0, 0, 0, 1.0]

    def self.rot_x(a)
      c = Math.cos(a)
      s = Math.sin(a)
      [1.0, 0, 0, 0, 0, c, -s, 0, 0, s, c, 0, 0, 0, 0, 1.0]
    end

    def self.rot_y(a)
      c = Math.cos(a)
      s = Math.sin(a)
      [c, 0, s, 0, 0, 1.0, 0, 0, -s, 0, c, 0, 0, 0, 0, 1.0]
    end

    def self.rot_z(a)
      c = Math.cos(a)
      s = Math.sin(a)
      [c, -s, 0, 0, s, c, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]
    end

    def top = @stack.last
    def apply(m) = @stack[-1] = Rig.mul(top, m)

    # Runs the block with a nested transform: translate, then rotate (x, y, z radians).
    def at(x = 0, y = 0, z = 0, rx: 0, ry: 0, rz: 0, s: nil)
      @stack.push(top)
      apply(Rig.translate(x, y, z))
      apply(Rig.rot_y(ry)) unless ry.zero?
      apply(Rig.rot_z(rz)) unless rz.zero?
      apply(Rig.rot_x(rx)) unless rx.zero?
      apply(Rig.scale(s, s, s)) if s
      yield
    ensure
      @stack.pop
    end

    # Places an entity in the world: position plus heading (yaw toward +X at 0).
    def entity(x, y, z, yaw, &) = at(x, y, z, ry: -yaw, &)

    # Draws a primitive centered at (x, y, z) in the current frame.
    def part(kind, x, y, z, sx, sy, sz, rgb, tex: "white", rx: 0, ry: 0, rz: 0, glow: false)
      at(x, y, z, rx: rx, ry: ry, rz: rz) do
        m = Rig.mul(top, Rig.scale(sx, sy, sz))
        @gpu.draw_part(kind, @gpu.to_matrix(m), rgb, tex: tex, glow: glow)
      end
    end
  end
end
