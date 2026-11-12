# Game logic with no raylib dependency, so it can be tested headlessly.
require "set"

require_relative "world/tile_map"
require_relative "world/map_loader"
require_relative "world/collision"
require_relative "player/combat"
require_relative "player/stats"
require_relative "player/items"
require_relative "player/inventory"
require_relative "player/spells"
require_relative "player/player"
require_relative "ai/enemy_types"
require_relative "ai/enemy"
require_relative "save/save_system"

module AshenVault
  ROOT = File.expand_path("../..", __dir__)
  MAP_DIR = File.join(ROOT, "data", "maps")

  def self.map_path(name) = File.join(MAP_DIR, "#{name}.map")
end
