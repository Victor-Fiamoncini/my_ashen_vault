module AshenVault
  # Procedural low-resolution textures. Each generator returns an RGBA byte string.
  module TextureGen
    SIZE = 64

    module_function

    def all
      {
        "stone_brick" => stone_brick, "flagstone" => flagstone, "rough_stone" => rough_stone,
        "wood_plank" => wood_plank, "door_wood" => door_wood, "plaster" => plaster, "timber" => timber,
        "grass" => grass, "dirt" => dirt, "cobble" => cobble, "water" => water, "roof" => roof,
        "iron_bars" => iron_bars, "mossy_brick" => mossy_brick, "white" => solid(255, 255, 255)
      }
    end

    # Deterministic hash noise in 0..1.
    def hash(x, y, seed)
      h = (x * 374_761_393 + y * 668_265_263 + seed * 2_147_483_647) & 0xFFFFFFFF
      h = ((h ^ (h >> 13)) * 1_274_126_177) & 0xFFFFFFFF
      (h ^ (h >> 16)) / 4_294_967_295.0
    end

    # Tileable value noise at `cell` pixel scale.
    def noise(x, y, cell, seed)
      n = SIZE / cell
      gx = x.to_f / cell
      gy = y.to_f / cell
      x0 = gx.floor
      y0 = gy.floor
      fx = gx - x0
      fy = gy - y0
      fx = fx * fx * (3 - 2 * fx)
      fy = fy * fy * (3 - 2 * fy)
      v = ->(i, j) { hash((x0 + i) % n, (y0 + j) % n, seed) }
      a = v.(0, 0) + (v.(1, 0) - v.(0, 0)) * fx
      b = v.(0, 1) + (v.(1, 1) - v.(0, 1)) * fx
      a + (b - a) * fy
    end

    def fbm(x, y, seed) = noise(x, y, 16, seed) * 0.5 + noise(x, y, 8, seed + 1) * 0.3 + noise(x, y, 4, seed + 2) * 0.2

    def build
      bytes = String.new(capacity: SIZE * SIZE * 4, encoding: Encoding::BINARY)
      SIZE.times do |y|
        SIZE.times do |x|
          r, g, b, a = yield(x, y)
          bytes << [r.clamp(0, 255), g.clamp(0, 255), b.clamp(0, 255), (a || 255)].pack("C4")
        end
      end
      bytes
    end

    def tint(base, k) = base.map { |c| (c * k).round }

    def solid(r, g, b) = build { [r, g, b] }

    def bricks(base, mortar, seed, rows: 4, cols: 2, moss: false)
      bh = SIZE / rows
      bw = SIZE / cols
      build do |x, y|
        row = y / bh
        ox = (x + (row.odd? ? bw / 2 : 0)) % SIZE
        col = ox / bw
        edge = (y % bh).zero? || (ox % bw).zero?
        n = fbm(x, y, seed)
        if edge
          tint(mortar, 0.8 + n * 0.3)
        else
          k = 0.75 + hash(col, row, seed) * 0.35 + (n - 0.5) * 0.35
          k *= 0.82 if (y % bh) == bh - 1 || (ox % bw) == bw - 1
          c = tint(base, k)
          if moss && noise(x, y, 8, seed + 9) > 0.62
            c = [c[0] * 0.6, c[1] * 0.95 + 20, c[2] * 0.5].map(&:round)
          end
          c
        end
      end
    end

    def stone_brick = bricks([118, 110, 100], [48, 44, 40], 11)
    def mossy_brick = bricks([100, 104, 90], [40, 44, 36], 12, moss: true)

    def flagstone
      build do |x, y|
        jx = (noise(0, y, 16, 5) * 6).round
        jy = (noise(x, 0, 16, 6) * 6).round
        cx = (x + jx) / 32
        cy = (y + jy) / 32
        gap = ((x + jx) % 32) < 2 || ((y + jy) % 32) < 2
        n = fbm(x, y, 21)
        gap ? tint([40, 38, 36], 0.9 + n * 0.2) : tint([104, 98, 90], 0.72 + hash(cx, cy, 3) * 0.3 + (n - 0.5) * 0.4)
      end
    end

    def rough_stone = build { |x, y| tint([84, 80, 76], 0.6 + fbm(x, y, 31) * 0.6) }
    def dirt = build { |x, y| tint([96, 74, 52], 0.65 + fbm(x, y, 41) * 0.5 + (hash(x, y, 2) - 0.5) * 0.15) }

    def grass
      build do |x, y|
        n = fbm(x, y, 51)
        blade = hash(x, y, 7) > 0.86 ? 1.25 : 1.0
        tint([62, 92, 44], (0.62 + n * 0.5) * blade)
      end
    end

    def wood_plank(base = [112, 78, 48])
      build do |x, y|
        plank = x / 16
        grain = Math.sin((y + hash(plank, 0, 4) * 64) * 0.35 + noise(x, y, 4, 8) * 3) * 0.08
        k = 0.78 + hash(plank, 1, 4) * 0.2 + grain + (fbm(x, y, 61) - 0.5) * 0.25
        k *= 0.55 if (x % 16).zero?
        tint(base, k)
      end
    end

    def door_wood
      planks = wood_plank([96, 64, 40])
      build do |x, y|
        i = (y * SIZE + x) * 4
        r, g, b = planks.byteslice(i, 3).unpack("C3")
        if [10, 11, 12, 52, 53, 54].include?(y)
          stud = (x % 16) == 8
          stud ? [120, 116, 108] : [54, 52, 50]
        else
          [r, g, b]
        end
      end
    end

    def plaster
      build do |x, y|
        grime = y > 48 ? 1.0 - (y - 48) / 40.0 : 1.0
        tint([186, 176, 150], (0.82 + fbm(x, y, 71) * 0.22) * grime)
      end
    end

    def timber
      wall = plaster
      build do |x, y|
        beam = x < 4 || x >= 60 || y < 4 || y >= 60 || (x - y).abs < 3
        if beam
          tint([70, 48, 30], 0.8 + fbm(x, y, 81) * 0.3)
        else
          wall.byteslice((y * SIZE + x) * 4, 3).unpack("C3")
        end
      end
    end

    def cobble
      build do |x, y|
        cx = x / 10
        cy = y / 10
        best = 99.0
        second = 99.0
        (-1..1).each do |i|
          (-1..1).each do |j|
            px = (cx + i) * 10 + hash((cx + i) % 7, (cy + j) % 7, 9) * 10
            py = (cy + j) * 10 + hash((cx + i) % 7, (cy + j) % 7, 10) * 10
            d = Math.hypot(x - px, y - py)
            if d < best
              second = best
              best = d
            elsif d < second
              second = d
            end
          end
        end
        edge = second - best < 1.6
        edge ? tint([52, 50, 46], 1.0) : tint([128, 122, 112], 0.7 + fbm(x, y, 91) * 0.4 - best * 0.015)
      end
    end

    def water
      build do |x, y|
        w = Math.sin(x * 0.3 + noise(x, y, 8, 3) * 4) * Math.sin(y * 0.2) * 0.12
        tint([38, 64, 78], 0.8 + w + fbm(x, y, 101) * 0.25)
      end
    end

    def roof
      build do |x, y|
        row = y / 8
        ox = (x + (row.odd? ? 4 : 0)) % 8
        curve = ((ox - 4).abs / 4.0) * 0.25
        edge = (y % 8) == 7
        k = 0.7 + hash(x / 8, row, 13) * 0.2 - curve + (fbm(x, y, 111) - 0.5) * 0.2
        edge ? [44, 26, 22] : tint([120, 58, 44], k)
      end
    end

    def iron_bars
      build do |x, y|
        bar = (x % 16) < 4 || (y % 32) < 4
        bar ? tint([70, 68, 66], 0.8 + fbm(x, y, 121) * 0.4) + [255] : [0, 0, 0, 0]
      end
    end
  end
end
