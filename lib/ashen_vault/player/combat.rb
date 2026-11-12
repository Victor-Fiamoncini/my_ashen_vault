module AshenVault
  # A stamina gauge that empties on use and refills over `refill_time` seconds.
  class Gauge
    attr_reader :value
    attr_accessor :refill_time

    def initialize(refill_time)
      @refill_time = refill_time
      @value = 1.0
    end

    def update(dt) = @value = [@value + dt / @refill_time, 1.0].min
    def full? = @value >= 1.0

    # Empties the gauge and returns how full it was.
    def spend
      used = @value
      @value = 0.0
      used
    end

    def fill! = @value = 1.0
  end

  module Combat
    module_function

    # A swing with a half-empty gauge is weak; a full one hits hardest.
    def power(gauge) = 0.15 + 0.85 * (gauge**1.5)

    def damage(base:, strength:, gauge:, defense:)
      raw = (base + strength * 0.5) * power(gauge)
      [(raw - defense * 0.5).round, 1].max
    end
  end
end
