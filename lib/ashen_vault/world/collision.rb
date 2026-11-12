module AshenVault
  # Grid collision for circles moving over tiles with floor heights.
  module Collision
    STEP_HEIGHT = 0.6
    BODY_HEIGHT = 1.7

    module_function

    # Can a body standing at `from_floor` occupy tile (tx, tz)?
    # `blocked` is an optional proc for dynamic blockers such as closed doors.
    def passable?(map, tx, tz, from_floor, blocked: nil)
      tile = map[tx, tz]
      return false unless tile.walkable
      return false if tile.floor - from_floor > STEP_HEIGHT
      return false if tile.ceil && tile.ceil - tile.floor < BODY_HEIGHT
      return false if blocked&.call(tx, tz)

      true
    end

    # Moves a circle by (dx, dz), sliding along blocked tiles axis by axis.
    # Returns the new [x, z].
    def move(map, x, z, dx, dz, radius:, blocked: nil)
      from_floor = map.floor_at(x, z)
      x = slide(map, x, z, dx, 0, radius, from_floor, blocked)[0]
      z = slide(map, x, z, 0, dz, radius, from_floor, blocked)[1]
      [x, z]
    end

    def slide(map, x, z, dx, dz, radius, from_floor, blocked)
      nx = x + dx
      nz = z + dz
      home = [TileMap.tile_coord(x), TileMap.tile_coord(z)]
      return [nx, nz] if circle_clear?(map, nx, nz, radius, from_floor, blocked, home)

      t = TileMap::TILE
      eps = 0.001
      if dx != 0
        nx = dx.positive? ? ((TileMap.tile_coord(x + radius) + 1) * t - radius - eps) : (TileMap.tile_coord(x - radius) * t + radius + eps)
        nx = x unless circle_clear?(map, nx, nz, radius, from_floor, blocked, home)
      else
        nz = dz.positive? ? ((TileMap.tile_coord(z + radius) + 1) * t - radius - eps) : (TileMap.tile_coord(z - radius) * t + radius + eps)
        nz = z unless circle_clear?(map, nx, nz, radius, from_floor, blocked, home)
      end
      [nx, nz]
    end

    # Treats the circle as its bounding box against the tile grid.
    # The tile we started in never counts as blocking, so a body can't get trapped.
    def circle_clear?(map, x, z, radius, from_floor, blocked, home = nil)
      (TileMap.tile_coord(x - radius)..TileMap.tile_coord(x + radius)).all? do |tx|
        (TileMap.tile_coord(z - radius)..TileMap.tile_coord(z + radius)).all? do |tz|
          [tx, tz] == home || passable?(map, tx, tz, from_floor, blocked: blocked)
        end
      end
    end

    # True if nothing solid lies between two points (eye-level sight line).
    def line_of_sight?(map, ax, az, bx, bz, eye: 1.4, blocked: nil)
      dist = Math.hypot(bx - ax, bz - az)
      steps = (dist / 0.25).ceil
      eye_y = map.floor_at(ax, az) + eye
      (1...steps).each do |i|
        t = i.to_f / steps
        px = ax + (bx - ax) * t
        pz = az + (bz - az) * t
        tx = TileMap.tile_coord(px)
        tz = TileMap.tile_coord(pz)
        tile = map[tx, tz]
        return false if tile.solid
        return false if tile.floor > eye_y || (tile.ceil && tile.ceil < eye_y - 0.5)
        return false if blocked&.call(tx, tz)
      end
      true
    end

    # Pushes circle a out of circle b; returns the corrected [x, z] for a.
    def separate(ax, az, ar, bx, bz, br)
      dx = ax - bx
      dz = az - bz
      d = Math.hypot(dx, dz)
      min = ar + br
      return [ax, az] if d >= min
      return [ax + min, az] if d < 1e-5

      push = (min - d) / d
      [ax + dx * push, az + dz * push]
    end
  end
end
