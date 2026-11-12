module AshenVault
  # Enemy state machine. `world` must respond to:
  #   player_x, player_z, player_alive?, can_see?(ax, az, bx, bz),
  #   move_enemy(enemy, dx, dz), enemy_strike(enemy), enemy_fire(enemy)
  class Enemy
    attr_reader :type, :state, :hp, :home_x, :home_z, :marker
    attr_accessor :x, :z, :yaw, :anim_t, :state_t

    def initialize(type, x, z, yaw: 0.0, marker: nil, rng: Random.new)
      @type = type
      @x = x
      @z = z
      @home_x = x
      @home_z = z
      @yaw = yaw
      @hp = type.hp
      @marker = marker
      @rng = rng
      @state = :idle
      @state_t = 0.0
      @anim_t = 0.0
      @wander_dir = nil
      @struck = false
    end

    def alive? = @state != :dead
    def gone? = @state == :dead && @state_t > 1.6
    def radius = @type.radius
    def name = @type.name

    def update(dt, world)
      @anim_t += dt
      @state_t += dt
      return if @state == :dead

      dist = Math.hypot(world.player_x - @x, world.player_z - @z)
      case @state
      when :idle then idle(dt, world, dist)
      when :chase then chase(dt, world, dist)
      when :windup then windup(dt, world, dist)
      when :attack then attack(world, dist)
      when :recover, :hurt then switch(:chase) if @state_t >= (@state == :hurt ? 0.35 : @type.recover)
      end
    end

    # Applies damage and returns true if the hit was fatal.
    def take_hit(amount)
      return false unless alive?

      @hp -= amount
      if @hp <= 0
        @hp = 0
        switch(:dead)
        return true
      end
      switch(:hurt) if amount >= @type.poise
      false
    end

    def face(tx, tz) = @yaw = Math.atan2(tz - @z, tx - @x)

    private

    def switch(state)
      @state = state
      @state_t = 0.0
      @struck = false
    end

    def notices?(world, dist)
      world.player_alive? && dist <= @type.sight && world.can_see?(@x, @z, world.player_x, world.player_z)
    end

    def idle(dt, world, dist)
      return switch(:chase) if notices?(world, dist)

      if @wander_dir.nil? || @state_t > 2.5
        @state_t = 0.0
        far = Math.hypot(@home_x - @x, @home_z - @z) > 3.0
        @wander_dir = far ? Math.atan2(@home_z - @z, @home_x - @x) : (@rng.rand < 0.5 ? nil : @rng.rand * Math::PI * 2)
      end
      return unless @wander_dir

      @yaw = @wander_dir
      step(world, Math.cos(@yaw), Math.sin(@yaw), @type.speed * 0.35 * dt)
    end

    def chase(dt, world, dist)
      return switch(:idle) unless world.player_alive?
      return switch(:idle) if dist > @type.sight * 1.5

      face(world.player_x, world.player_z)
      in_range = dist <= @type.reach
      in_range &&= world.can_see?(@x, @z, world.player_x, world.player_z) if @type.ranged
      return switch(:windup) if in_range && (!@type.ranged || dist >= 2.5)

      dir = @type.ranged && dist < 4.0 ? -1.0 : 1.0
      step(world, Math.cos(@yaw) * dir, Math.sin(@yaw) * dir, @type.speed * dt)
    end

    def windup(_dt, world, _dist)
      face(world.player_x, world.player_z) if @state_t < @type.windup * 0.6
      switch(:attack) if @state_t >= @type.windup
    end

    def attack(world, dist)
      unless @struck
        @struck = true
        if @type.ranged
          world.enemy_fire(self)
        elsif dist <= @type.reach + 0.3 && facing?(world.player_x, world.player_z)
          world.enemy_strike(self)
        end
      end
      switch(:recover) if @state_t >= 0.2
    end

    def facing?(px, pz)
      diff = (Math.atan2(pz - @z, px - @x) - @yaw + Math::PI) % (2 * Math::PI) - Math::PI
      diff.abs < 0.9
    end

    def step(world, dx, dz, amount) = world.move_enemy(self, dx * amount, dz * amount)
  end
end
