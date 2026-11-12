module AshenVault
  # One grid cell. Heights are in meters; ceil nil means open sky.
  Tile = Struct.new(:solid, :walkable, :floor, :ceil, :top,
                    :floor_tex, :wall_tex, :ceil_tex, :liquid, keyword_init: true) do
    def open_sky? = ceil.nil?
  end

  # Marker placed in the grid, resolved to an entity at load time.
  EntitySpec = Struct.new(:kind, :tx, :tz, :props, :marker, keyword_init: true)

  class TileMap
    TILE = 2.0

    attr_reader :width, :depth, :meta, :entities, :name

    def initialize(name:, width:, depth:, tiles:, meta:, entities:)
      @name = name
      @width = width
      @depth = depth
      @tiles = tiles
      @meta = meta
      @entities = entities
      @edge = Tile.new(solid: true, walkable: false, floor: 0.0, ceil: nil,
                       top: meta.fetch(:edge_top, 4.0), wall_tex: meta.fetch(:edge_tex, "stone_brick"))
    end

    def [](tx, tz)
      return @edge if tx.negative? || tz.negative? || tx >= @width || tz >= @depth

      @tiles[tz * @width + tx]
    end

    def each_tile
      @depth.times { |tz| @width.times { |tx| yield tx, tz, self[tx, tz] } }
    end

    def self.tile_coord(world) = (world / TILE).floor

    def tile_at(wx, wz) = self[TileMap.tile_coord(wx), TileMap.tile_coord(wz)]

    def floor_at(wx, wz) = tile_at(wx, wz).floor

    def self.center(tx, tz) = [(tx + 0.5) * TILE, (tz + 0.5) * TILE]
  end
end
