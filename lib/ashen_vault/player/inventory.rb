module AshenVault
  class Inventory
    attr_reader :counts, :weapon, :armor
    attr_accessor :gold

    def initialize(counts: {}, weapon: "rusted_sword", armor: "padded_coat", gold: 0)
      @counts = Hash.new(0).merge(counts)
      @weapon = weapon
      @armor = armor
      @gold = gold
      add(weapon) if weapon && !has?(weapon)
      add(armor) if armor && !has?(armor)
    end

    def add(id, n = 1) = @counts[Items[id].id] += n
    def has?(id) = @counts[id].positive?
    def count(id) = @counts[id]

    def remove(id, n = 1)
      return false if @counts[id] < n

      @counts[id] -= n
      @counts.delete(id) if @counts[id].zero?
      true
    end

    def items = @counts.keys.map { |id| Items[id] }

    def equip(id)
      item = Items[id]
      return false unless has?(id)

      case item.kind
      when :weapon then @weapon = id
      when :armor then @armor = id
      else return false
      end
      true
    end

    def equipped?(id) = [@weapon, @armor].include?(id)

    # Takes off the weapon or armor `id`; returns false if it wasn't equipped.
    def unequip(id)
      if @weapon == id then @weapon = nil
      elsif @armor == id then @armor = nil
      else return false
      end
      true
    end

    def weapon_item = @weapon ? Items[@weapon] : Items::FISTS
    def armor_item = @armor && Items[@armor]
    def defense = armor_item&.power || 0

    def buy(id)
      price = Items[id].price
      return false if @gold < price

      @gold -= price
      add(id)
      true
    end

    def to_h = { counts: @counts.to_h, weapon: @weapon, armor: @armor, gold: @gold }

    def self.from_h(h)
      h = h.transform_keys(&:to_sym)
      new(counts: h[:counts].to_h, weapon: h[:weapon], armor: h[:armor], gold: h[:gold])
    end
  end
end
