require "shellwords"

module AshenVault
  # Parses the plain-text .map format:
  #
  #   [meta]     key = value lines
  #   [legend]   <char> = <floor|wall|water> key=value ...
  #   [grid]     rows of legend chars and entity markers
  #   [entities] <marker> = <kind> key=value ... (on=<legend char> picks the tile under it)
  class MapLoader
    class Error < StandardError; end

    TILE_KINDS = %w[floor wall water].freeze

    def self.load_file(path)
      new(File.read(path), name: File.basename(path, ".map")).parse
    end

    def initialize(text, name: "map")
      @text = text
      @name = name
    end

    def parse
      sections = split_sections
      meta = parse_meta(sections.fetch("meta", []))
      legend = parse_legend(sections.fetch("legend", []))
      specs = parse_entities(sections.fetch("entities", []))
      rows = sections.fetch("grid") { raise Error, "#{@name}: missing [grid]" }
      rows = rows.reject { |r| r.strip.empty? }
      raise Error, "#{@name}: empty grid" if rows.empty?

      width = rows.map(&:length).max
      default_char = meta.fetch(:default, ".")
      tiles = []
      entities = []
      rows.each_with_index do |row, tz|
        width.times do |tx|
          ch = row[tx] || " "
          if (spec = specs[ch])
            entities << EntitySpec.new(kind: spec[:kind], tx: tx, tz: tz, props: spec[:props], marker: ch)
            ch = spec[:props].fetch("on", default_char)
          end
          ch = default_char if ch == " " && !legend.key?(" ")
          tile = legend[ch] or raise Error, "#{@name}: unknown tile '#{ch}' at #{tx},#{tz}"
          tiles << tile
        end
      end
      TileMap.new(name: @name, width: width, depth: rows.size, tiles: tiles, meta: meta, entities: entities)
    end

    private

    def split_sections
      sections = {}
      current = nil
      @text.each_line(chomp: true) do |line|
        if (m = line.match(/\A\[(\w+)\]\s*\z/))
          current = sections[m[1]] = []
        elsif current
          current << line
        end
      end
      sections
    end

    def content_lines(lines) = lines.reject { |l| l.strip.empty? || l.strip.start_with?("//") }

    def parse_meta(lines)
      content_lines(lines).to_h do |line|
        key, value = line.split("=", 2).map(&:strip)
        [key.to_sym, coerce_meta(key, value)]
      end
    end

    def coerce_meta(key, value)
      case key
      when "ambient", "fog", "fog_range", "start", "sky", "torch" then value.split.map(&:to_f)
      when "edge_top" then value.to_f
      else value
      end
    end

    def parse_legend(lines)
      content_lines(lines).to_h do |line|
        ch = line[0]
        kind, *pairs = Shellwords.split(line[1..].sub(/\A\s*=\s*/, ""))
        raise Error, "#{@name}: bad tile kind '#{kind}' for '#{ch}'" unless TILE_KINDS.include?(kind)

        [ch, build_tile(kind, kv(pairs))]
      end
    end

    def build_tile(kind, p)
      floor = p.fetch("h", "0").to_f
      ceil = p.key?("ceil") ? p["ceil"].to_f : nil
      case kind
      when "wall"
        Tile.new(solid: true, walkable: false, floor: floor, ceil: nil, top: p.fetch("top", "3").to_f,
                 wall_tex: p.fetch("tex", "stone_brick"), floor_tex: p["cap"] || p.fetch("tex", "stone_brick"))
      when "water"
        Tile.new(solid: false, walkable: false, floor: floor, ceil: ceil, liquid: true,
                 floor_tex: p.fetch("tex", "water"), wall_tex: p.fetch("side", "stone_brick"),
                 ceil_tex: p.fetch("ceil_tex", "rough_stone"))
      else
        Tile.new(solid: false, walkable: true, floor: floor, ceil: ceil,
                 floor_tex: p.fetch("tex", "flagstone"), wall_tex: p.fetch("side", "stone_brick"),
                 ceil_tex: p.fetch("ceil_tex", "rough_stone"))
      end
    end

    def parse_entities(lines)
      content_lines(lines).to_h do |line|
        ch = line[0]
        kind, *pairs = Shellwords.split(line[1..].sub(/\A\s*=\s*/, ""))
        [ch, { kind: kind, props: kv(pairs) }]
      end
    end

    def kv(pairs) = pairs.to_h { |pair| pair.split("=", 2) }
  end
end
