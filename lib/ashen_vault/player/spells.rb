module AshenVault
  Spell = Struct.new(:id, :name, :cost, :desc, keyword_init: true)

  module Spells
    ALL = [
      Spell.new(id: "flame", name: "Flame Bolt", cost: 5, desc: "Hurl a bolt of fire."),
      Spell.new(id: "mend", name: "Mend", cost: 8, desc: "Close your wounds."),
      Spell.new(id: "lumen", name: "Lumen", cost: 4, desc: "Light the dark around you for a while.")
    ].to_h { |s| [s.id, s] }.freeze

    def self.[](id) = ALL.fetch(id)

    def self.flame_damage(magic, gauge) = Combat.damage(base: 10, strength: magic * 2, gauge: gauge, defense: 0)
    def self.mend_amount(magic) = 20 + magic * 3
    LUMEN_DURATION = 45.0
  end
end
