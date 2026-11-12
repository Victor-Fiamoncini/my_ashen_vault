module AshenVault
  class Stats
    attr_accessor :level, :exp, :hp, :max_hp, :mp, :max_mp, :strength, :magic

    def initialize(level: 1, exp: 0, hp: 40, max_hp: 40, mp: 16, max_mp: 16, strength: 6, magic: 4)
      @level = level
      @exp = exp
      @hp = hp
      @max_hp = max_hp
      @mp = mp
      @max_mp = max_mp
      @strength = strength
      @magic = magic
    end

    def self.exp_for(level) = (30 * (level**1.6)).round

    def next_level_exp = Stats.exp_for(@level)
    def dead? = @hp <= 0

    # Adds experience; returns the number of levels gained.
    def gain_exp(amount)
      @exp += amount
      gained = 0
      while @exp >= next_level_exp
        @exp -= next_level_exp
        @level += 1
        @max_hp += 6
        @max_mp += 3
        @strength += 1
        @magic += 1
        @hp = @max_hp
        @mp = @max_mp
        gained += 1
      end
      gained
    end

    def heal(amount) = @hp = [@hp + amount, @max_hp].min
    def restore_mp(amount) = @mp = [@mp + amount, @max_mp].min
    def hurt(amount) = @hp = [@hp - amount, 0].max

    def spend_mp(cost)
      return false if @mp < cost

      @mp -= cost
      true
    end

    def to_h = { level:, exp:, hp:, max_hp:, mp:, max_mp:, strength:, magic: }
    def self.from_h(h) = new(**h.transform_keys(&:to_sym))
  end
end
