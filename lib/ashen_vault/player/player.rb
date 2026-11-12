module AshenVault
  # First-person body: deliberately slow, King's Field-style movement.
  class Player
    RADIUS = 0.4
    EYE = 1.55
    WALK_SPEED = 2.6
    BACK_SPEED = 1.8
    SPRINT = 1.75 # speed multiplier while sprinting
    TURN_SPEED = 1.7 # rad/s on keys
    LOOK_LIMIT = 0.9

    attr_accessor :x, :z, :y, :yaw, :pitch, :bob_t, :hurt_t, :stats, :inventory, :spells, :spell_index,
                  :attack_gauge, :magic_gauge, :lumen_t, :swing_t, :swing_power
    attr_reader :sprinting

    def initialize(stats: Stats.new, inventory: Inventory.new, spells: ["flame"])
      @stats = stats
      @inventory = inventory
      @spells = spells
      @spell_index = 0
      @x = @z = @y = 0.0
      @yaw = 0.0
      @pitch = 0.0
      @bob_t = 0.0
      @hurt_t = 0.0
      @lumen_t = 0.0
      @swing_t = nil
      @swing_power = 0.0
      @sprinting = false
      @attack_gauge = Gauge.new(inventory.weapon_item.speed)
      @magic_gauge = Gauge.new(2.2)
    end

    def place(x, z, yaw, map)
      @x = x
      @z = z
      @yaw = yaw
      @pitch = 0.0
      @y = map.floor_at(x, z)
    end

    def forward = [Math.cos(@yaw), Math.sin(@yaw)]
    def eye_y = @y + EYE + Math.sin(@bob_t * 2) * 0.035
    def alive? = !@stats.dead?
    def current_spell = @spells.empty? ? nil : Spells[@spells[@spell_index % @spells.size]]

    # Compass heading in degrees, north (-Z) = 0.
    def heading = ((@yaw * 180 / Math::PI) + 90) % 360

    def turn(amount) = @yaw = (@yaw + amount) % (2 * Math::PI)
    def look(amount) = @pitch = (@pitch + amount).clamp(-LOOK_LIMIT, LOOK_LIMIT)

    # fwd/strafe are -1..1 intents. Returns true if the player moved.
    # Sprinting is faster but holds the ATK gauge from refilling.
    def walk(map, fwd, strafe, dt, blocked: nil, sprint: false)
      @sprinting = false
      return false if fwd.zero? && strafe.zero?

      fx, fz = forward
      speed = fwd.negative? ? BACK_SPEED : WALK_SPEED
      speed *= SPRINT if sprint
      dx = (fx * fwd - fz * strafe) * speed * dt
      dz = (fz * fwd + fx * strafe) * speed * dt
      len = Math.hypot(fwd, strafe)
      if len > 1
        dx /= len
        dz /= len
      end
      ox = @x
      oz = @z
      @x, @z = Collision.move(map, @x, @z, dx, dz, radius: RADIUS, blocked: blocked)
      moved = Math.hypot(@x - ox, @z - oz)
      @bob_t += moved * 2.2
      @sprinting = sprint && moved > 1e-4
      moved > 1e-4
    end

    # Eases eye height onto the floor below (stairs, drops).
    def settle(map, dt)
      target = map.floor_at(@x, @z)
      @y += (target - @y) * [dt * 10, 1].min
      @y = target if (target - @y).abs < 0.005
    end

    def update_timers(dt)
      @attack_gauge.refill_time = @inventory.weapon_item.speed
      @attack_gauge.update(dt) unless swinging? || @sprinting
      @magic_gauge.update(dt)
      @hurt_t = [@hurt_t - dt, 0].max
      @lumen_t = [@lumen_t - dt, 0].max
      return unless @swing_t

      @swing_t += dt
      @swing_t = nil if @swing_t > SWING_TIME
    end

    SWING_TIME = 0.45
    SWING_HIT_AT = 0.16

    def swinging? = !@swing_t.nil?

    def start_swing
      return false if swinging?

      @swing_power = @attack_gauge.spend
      @swing_t = 0.0
      true
    end

    def to_h
      { x: @x, z: @z, yaw: @yaw, stats: @stats.to_h, inventory: @inventory.to_h, spells: @spells }
    end
  end
end
