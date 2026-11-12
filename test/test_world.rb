require_relative "test_helper"

class TestWorld < Minitest::Test
  include AshenVault

  def setup
    @map = TestMaps.room
  end

  def test_parses_grid_and_meta
    assert_equal 6, @map.width
    assert_equal 5, @map.depth
    assert_equal "Test Room", @map.meta[:name]
    assert_equal [1.0, 1.0, 0.0], @map.meta[:start]
    assert @map[0, 0].solid
    assert_in_delta 0.5, @map[3, 1].floor
    assert @map[1, 3].liquid
  end

  def test_out_of_bounds_is_solid
    assert @map[-1, 2].solid
    assert @map[99, 2].solid
  end

  def test_entity_markers_become_specs_on_default_floor
    spec = @map.entities.first
    assert_equal "bone_walker", spec.kind
    assert_equal [2, 2], [spec.tx, spec.tz]
    assert_equal "90", spec.props["yaw"]
    assert @map[2, 2].walkable
  end

  def test_unknown_tile_raises
    bad = TestMaps::ROOM.sub("#..,^#", "#..?^#")
    assert_raises(MapLoader::Error) { MapLoader.new(bad).parse }
  end

  def test_shipped_maps_load
    Dir[File.join(AshenVault::MAP_DIR, "*.map")].each do |path|
      map = MapLoader.load_file(path)
      sx, sz = map.meta.fetch(:start)
      assert map[sx.to_i, sz.to_i].walkable, "#{path}: start tile must be walkable"
      torch = map.meta.fetch(:torch, [0, 0, 0, 0])
      assert_equal 4, torch.size, "#{path}: torch is radius r g b"
      assert torch.all?(Numeric), "#{path}: torch values must be numbers"
    end
  end

  def test_walls_stop_movement
    x, z = TileMap.center(1, 1)
    nx, _nz = Collision.move(@map, x, z, -5.0, 0, radius: 0.4)
    assert_in_delta 2.0 + 0.4, nx, 0.01
  end

  def test_small_step_is_climbable_but_tall_step_is_not
    x, z = TileMap.center(2, 1)
    nx, = Collision.move(@map, x, z, 2.0, 0, radius: 0.4)
    assert TileMap.tile_coord(nx) == 3, "should step up 0.5m"

    x, z = TileMap.center(3, 1)
    nx, = Collision.move(@map, x, z, 2.0, 0, radius: 0.4)
    assert_equal 3, TileMap.tile_coord(nx + 0.4 - 0.01), "1.0m step blocks"
  end

  def test_water_blocks
    x, z = TileMap.center(1, 2)
    _, nz = Collision.move(@map, x, z, 0, 2.0, radius: 0.4)
    assert_equal 2, TileMap.tile_coord(nz)
  end

  def test_dynamic_blocker
    x, z = TileMap.center(1, 2)
    blocked = ->(tx, tz) { tx == 2 && tz == 2 }
    nx, = Collision.move(@map, x, z, 2.0, 0, radius: 0.4, blocked: blocked)
    assert_equal 1, TileMap.tile_coord(nx)
  end

  def test_line_of_sight
    ax, az = TileMap.center(1, 1)
    bx, bz = TileMap.center(3, 2)
    assert Collision.line_of_sight?(@map, ax, az, bx, bz)
    cx, cz = TileMap.center(1, 1)
    refute Collision.line_of_sight?(@map, cx, cz, cx, cz - 6)
  end

  def test_separate_pushes_apart
    x, z = Collision.separate(0.0, 0.0, 0.5, 0.5, 0.0, 0.5)
    assert_in_delta(-0.5, x)
    assert_in_delta 0.0, z
  end
end
