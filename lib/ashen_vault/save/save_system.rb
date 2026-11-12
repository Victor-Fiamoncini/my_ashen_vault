require "json"
require "fileutils"

module AshenVault
  # Persists the run to a single JSON slot.
  class SaveSystem
    DEFAULT_PATH = File.join(Dir.home, ".local", "share", "ashen_vault", "save.json")

    attr_reader :path

    def initialize(path = ENV.fetch("ASHEN_VAULT_SAVE", DEFAULT_PATH))
      @path = path
    end

    def exists? = File.exist?(@path)

    def save(map:, player:, flags:)
      FileUtils.mkdir_p(File.dirname(@path))
      data = { version: 1, map: map, player: player.to_h, flags: flags.to_a.sort }
      File.write(@path, JSON.pretty_generate(data))
    end

    # Returns [map_name, player, flags] or nil.
    def load
      return nil unless exists?

      data = JSON.parse(File.read(@path), symbolize_names: true)
      p = data[:player]
      inv = p[:inventory]
      inventory = Inventory.from_h(counts: inv[:counts].transform_keys(&:to_s), weapon: inv[:weapon],
                                   armor: inv[:armor], gold: inv[:gold])
      player = Player.new(stats: Stats.from_h(p[:stats]), inventory: inventory, spells: p[:spells])
      player.x = p[:x]
      player.z = p[:z]
      player.yaw = p[:yaw]
      [data[:map], player, Set.new(data[:flags])]
    rescue JSON::ParserError, KeyError, NoMethodError
      nil
    end
  end
end
