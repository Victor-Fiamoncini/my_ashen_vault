module AshenVault
  # Runtime state of one loaded map: GPU meshes, props, enemies and projectiles.
  class World
    include Raylib

    Prop = Struct.new(:kind, :x, :z, :y, :tx, :tz, :props, :key, :yaw, :open_t, :axis, keyword_init: true)
    Projectile = Struct.new(:x, :y, :z, :dx, :dz, :life, :damage, :hostile, :rgb, keyword_init: true)

    INTERACT_RANGE = 2.6

    attr_reader :map, :name, :enemies, :props, :projectiles, :builder

    def initialize(game, name)
      @game = game
      @name = name
      @map = MapLoader.load_file(AshenVault.map_path(name))
      @builder = MeshBuilder.new(@map, lights: MeshBuilder.lights_for(@map)).build
      @meshes = @builder.batches.map { |tex, batch| [game.gpu.upload_batch(batch), tex] }
      @props = []
      @enemies = []
      @projectiles = []
      @time = 0.0
      spawn_entities
    end

    def unload = @meshes.each { |mesh, _| @game.gpu.unload_mesh(mesh) }

    def meta = @map.meta
    def player = @game.player
    def flags = @game.flags

    def start_position
      tx, tz, yaw = meta.fetch(:start)
      x, z = TileMap.center(tx.to_i, tz.to_i)
      [x, z, yaw * Math::PI / 180]
    end

    # --- setup ---------------------------------------------------------------

    def spawn_entities
      @map.entities.each do |spec|
        x, z = TileMap.center(spec.tx, spec.tz)
        y = @map[spec.tx, spec.tz].floor
        yaw = spec.props.fetch("yaw", "0").to_f * Math::PI / 180
        if EnemyTypes.key?(spec.kind)
          type = EnemyTypes[spec.kind]
          next if type.boss && flags.include?("boss_dead")

          @enemies << Enemy.new(type, x, z, yaw: yaw, marker: spec.marker)
        else
          key = "#{spec.kind}:#{@name}:#{spec.tx},#{spec.tz}"
          prop = Prop.new(kind: spec.kind, x: x, z: z, y: y, tx: spec.tx, tz: spec.tz, props: spec.props,
                          key: key, yaw: yaw, open_t: 0.0)
          prop.open_t = 1.0 if opened?(prop)
          prop.axis = door_axis(spec.tx, spec.tz) if %w[door gate].include?(spec.kind)
          next if spec.kind == "pickup" && flags.include?(key)

          @props << prop
        end
      end
      return unless flags.include?("boss_dead") && @name == "sunken_keep" && !player.inventory.has?("ember_sigil") &&
                    !flags.include?("sigil_taken")

      drop_sigil(*TileMap.center(15, 4))
    end

    def opened?(prop)
      case prop.kind
      when "door", "chest", "lever" then flags.include?(prop.key)
      when "gate" then flags.include?("lever:#{prop.props['lever']}")
      else false
      end
    end

    # A door blocks the axis it is not aligned with: corridor walls tell us which.
    def door_axis(tx, tz) = @map[tx, tz - 1].solid && @map[tx, tz + 1].solid ? :x : :z

    # --- queries used by collision and AI ------------------------------------

    def blocked_tile?(tx, tz)
      @props.any? do |p|
        p.tx == tx && p.tz == tz && (
          (%w[door gate].include?(p.kind) && p.open_t < 0.9) ||
          %w[well save_statue npc].include?(p.kind) ||
          (p.kind == "exit" && p.props["model"] == "well")
        )
      end
    end

    def blocker = @blocker ||= method(:blocked_tile?).to_proc

    def player_x = player.x
    def player_z = player.z
    def player_alive? = player.alive?

    def can_see?(ax, az, bx, bz) = Collision.line_of_sight?(@map, ax, az, bx, bz, blocked: blocker)

    def move_enemy(enemy, dx, dz)
      nx, nz = Collision.move(@map, enemy.x, enemy.z, dx, dz, radius: enemy.radius, blocked: blocker)
      nx, nz = Collision.separate(nx, nz, enemy.radius, player.x, player.z, Player::RADIUS)
      @enemies.each do |other|
        next if other.equal?(enemy) || !other.alive?

        nx, nz = Collision.separate(nx, nz, enemy.radius, other.x, other.z, other.radius)
      end
      tile = @map.tile_at(nx, nz)
      return unless tile.walkable && !blocked_tile?(TileMap.tile_coord(nx), TileMap.tile_coord(nz))
      return if (tile.floor - @map.floor_at(enemy.x, enemy.z)).abs > Collision::STEP_HEIGHT

      enemy.x = nx
      enemy.z = nz
    end

    def enemy_strike(enemy)
      dmg = [(enemy.type.damage * (0.85 + rand * 0.3) - player.inventory.defense * 0.5).round, 1].max
      @game.hurt_player(dmg, enemy.name)
    end

    def enemy_fire(enemy)
      y = enemy_y(enemy) + (enemy.type.hover || 1.2)
      dx = player.x - enemy.x
      dz = player.z - enemy.z
      d = Math.hypot(dx, dz)
      @projectiles << Projectile.new(x: enemy.x, y: y, z: enemy.z, dx: dx / d * 6, dz: dz / d * 6, life: 4.0,
                                     damage: enemy.type.damage, hostile: true, rgb: [255, 120, 40])
      @game.sfx(:spell)
    end

    def enemy_y(enemy) = @map.floor_at(enemy.x, enemy.z)

    # --- update --------------------------------------------------------------

    def update(dt)
      @time += dt
      @enemies.each { |e| e.update(dt, self) }
      @enemies.reject!(&:gone?)
      @props.each do |p|
        p.open_t = [p.open_t + dt * 0.8, 1.0].min if p.open_t.positive? && p.open_t < 1.0
      end
      update_projectiles(dt)
      push_player_out_of_bodies
    end

    def push_player_out_of_bodies
      @enemies.each do |e|
        next unless e.alive?

        nx, nz = Collision.separate(player.x, player.z, Player::RADIUS, e.x, e.z, e.radius)
        tile = @map.tile_at(nx, nz)
        next unless Collision.passable?(@map, TileMap.tile_coord(nx), TileMap.tile_coord(nz), player.y, blocked: blocker) ||
                    tile.equal?(@map.tile_at(player.x, player.z))

        player.x = nx
        player.z = nz
      end
    end

    def update_projectiles(dt)
      @projectiles.each do |pr|
        pr.x += pr.dx * dt
        pr.z += pr.dz * dt
        pr.life -= dt
        tile = @map.tile_at(pr.x, pr.z)
        if tile.solid || tile.floor > pr.y || (tile.ceil && tile.ceil < pr.y) ||
           blocked_tile?(TileMap.tile_coord(pr.x), TileMap.tile_coord(pr.z))
          pr.life = 0
        elsif pr.hostile
          if Math.hypot(pr.x - player.x, pr.z - player.z) < 0.6
            @game.hurt_player([(pr.damage - player.inventory.defense * 0.3).round, 1].max, "Cinder Wisp")
            pr.life = 0
          end
        elsif (target = @enemies.find { |e| e.alive? && Math.hypot(pr.x - e.x, pr.z - e.z) < e.radius + 0.3 })
          @game.damage_enemy(target, pr.damage)
          pr.life = 0
        end
      end
      @projectiles.reject! { |pr| pr.life <= 0 }
    end

    # --- player actions --------------------------------------------------------

    def melee_targets(reach)
      fx, fz = player.forward
      @enemies.select do |e|
        next false unless e.alive?

        dx = e.x - player.x
        dz = e.z - player.z
        d = Math.hypot(dx, dz)
        next false if d > reach + e.radius
        next true if d < e.radius + 0.2

        (dx * fx + dz * fz) / d > 0.6 && can_see?(player.x, player.z, e.x, e.z)
      end.sort_by { |e| Math.hypot(e.x - player.x, e.z - player.z) }
    end

    def fire_bolt(damage)
      fx, fz = player.forward
      @projectiles << Projectile.new(x: player.x + fx * 0.5, y: player.eye_y - 0.25, z: player.z + fz * 0.5,
                                     dx: fx * 9, dz: fz * 9, life: 3.0, damage: damage, hostile: false,
                                     rgb: [255, 160, 60])
    end

    # Closest interactable prop in front of the player.
    def focus
      fx, fz = player.forward
      @props.select do |p|
        next false unless interactable?(p)

        dx = p.x - player.x
        dz = p.z - player.z
        d = Math.hypot(dx, dz)
        d < INTERACT_RANGE && (d < 0.8 || (dx * fx + dz * fz) / d > 0.55)
      end.min_by { |p| Math.hypot(p.x - player.x, p.z - player.z) }
    end

    def interactable?(p)
      case p.kind
      when "npc", "save_statue", "exit", "pickup" then true
      when "chest", "lever" then p.open_t.zero?
      when "door" then p.open_t.zero?
      else false
      end
    end

    def open_prop(p)
      p.open_t = 0.01
      flags << p.key
    end

    def drop_sigil(x, z)
      tx = TileMap.tile_coord(x)
      tz = TileMap.tile_coord(z)
      @props << Prop.new(kind: "pickup", x: x, z: z, y: @map[tx, tz].floor, tx: tx, tz: tz,
                         props: { "item" => "ember_sigil" }, key: "sigil", yaw: 0, open_t: 0)
    end

    def remove_prop(p) = @props.delete(p)

    def pull_lever(p)
      open_prop(p)
      flags << "lever:#{p.props['id']}"
      @props.each { |g| g.open_t = 0.01 if g.kind == "gate" && g.props["lever"] == p.props["id"] }
    end

    # --- rendering ---------------------------------------------------------------

    def draw(rig, gpu)
      @meshes.each { |mesh, tex| gpu.draw_world_batch(mesh, tex) }
      gpu.set_float("isModel", 1.0)
      far = meta.fetch(:fog_range, [0, 40])[1] + 2
      @props.each do |p|
        next if Math.hypot(p.x - player.x, p.z - player.z) > far

        model_light(gpu, p.x, p.y + 1.0, p.z)
        rig.entity(p.x, p.y, p.z, p.yaw) { draw_prop(rig, p) }
      end
      @enemies.each do |e|
        next if Math.hypot(e.x - player.x, e.z - player.z) > far

        y = enemy_y(e)
        sink = e.state == :dead ? -e.state_t * 1.1 : 0
        model_light(gpu, e.x, y + 1.0, e.z, flash: e.state == :hurt)
        rig.entity(e.x, y + sink, e.z, e.yaw) { Models.enemy(rig, e) }
      end
      @projectiles.each do |pr|
        gpu.model_light([1.6, 1.4, 1.2])
        rig.at(pr.x, pr.y, pr.z, ry: @time * 6) { Models.bolt(rig, pr.rgb) }
      end
    end

    def model_light(gpu, x, y, z, flash: false)
      light = flash ? [2.0, 1.6, 1.6] : @builder.light_at(x, y, z).map { |c| [c, 1.6].min }
      gpu.model_light(light)
    end

    def draw_prop(rig, p)
      t = @time
      case p.kind
      when "torch" then Models.torch(rig, t)
      when "brazier" then Models.brazier(rig, t)
      when "chest" then Models.chest(rig, p.open_t.positive?)
      when "door" then Models.door(rig, p.open_t, p.axis)
      when "gate" then Models.door(rig, p.open_t, p.axis, tex: "iron_bars")
      when "lever" then Models.lever(rig, p.open_t.positive?)
      when "save_statue" then Models.save_statue(rig, t)
      when "tree" then Models.tree(rig, p.tx * 7 + p.tz)
      when "pickup" then Models.pickup(rig, t)
      when "npc"
        look = NPC_LOOKS.fetch(p.props["id"], {})
        Models.npc(rig, look.fetch(:robe, [110, 110, 110]), hair: look.fetch(:hair, [70, 54, 40]), t: t + p.tx)
      when "exit" then p.props["model"] == "well" ? Models.well(rig) : Models.rope(rig, t)
      end
    end

    NPC_LOOKS = {
      "odrin" => { robe: [70, 60, 90], hair: [200, 200, 200] },
      "pell" => { robe: [120, 90, 40] },
      "hollis" => { robe: [80, 84, 90], hair: [40, 30, 22] },
      "maeve" => { robe: [60, 90, 100], hair: [140, 70, 40] }
    }.freeze
  end
end
