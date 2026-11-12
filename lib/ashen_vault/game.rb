module AshenVault
  class Game
    include Raylib

    W = 320
    H = 240
    FOV = 62.0
    PREVIEW = 64 # inventory item preview size in pixels

    attr_reader :gpu, :player, :flags, :world, :messages

    def initialize(opts = {})
      @opts = opts
      SetTraceLogLevel(LOG_WARNING)
      SetConfigFlags(FLAG_WINDOW_RESIZABLE | FLAG_VSYNC_HINT)
      InitWindow(W * 3, H * 3, "Ashen Vault")
      SetTargetFPS(60)
      SetExitKey(KEY_NULL)
      @target = LoadRenderTexture(W, H)
      SetTextureFilter(@target[:texture], TEXTURE_FILTER_POINT)
      @preview = LoadRenderTexture(PREVIEW, PREVIEW)
      SetTextureFilter(@preview[:texture], TEXTURE_FILTER_POINT)
      @gpu = Gpu.new
      @rig = Rig.new(@gpu)
      @audio = Audio.new
      @input = Input.new(opts[:script])
      @saves = SaveSystem.new
      @camera = Camera3D.new.with_up(0, 1, 0).with_fovy(FOV).with_projection(CAMERA_PERSPECTIVE)
      @view_camera = Camera3D.new.with_position(0, 0, 0).with_target(1, 0, 0).with_up(0, 1, 0)
                             .with_fovy(55).with_projection(CAMERA_PERSPECTIVE)
      @messages = []
      @flags = Set.new
      @player = Player.new
      @menu_index = 0
      @time = 0.0
      @frames = 0
      @running = true
      if opts[:map]
        new_game(opts[:map], at: opts[:at])
      else
        show_title
      end
    end

    # --- main loop ----------------------------------------------------------

    def run
      while @running && !WindowShouldClose()
        dt = [GetFrameTime(), 0.05].min
        dt = 1.0 / 60 if @opts[:smoke]
        @time += dt
        @frames += 1
        @input.update(dt)
        update(dt)
        render
        smoke_check
      end
    ensure
      shutdown # also on errors, so a Ruby exception doesn't end in a native segfault
    end

    def shutdown
      @world&.unload
      @audio.close
      UnloadRenderTexture(@preview)
      UnloadRenderTexture(@target)
      CloseWindow()
    end

    def smoke_check
      return unless @opts[:smoke] && @frames >= @opts[:smoke]

      shot = @opts[:shot] || "screenshot.png"
      image = LoadImageFromTexture(@target[:texture])
      ImageFlipVertical(image.to_ptr)
      ImageResizeNN(image.to_ptr, W * 3, H * 3)
      ExportImage(image, shot)
      UnloadImage(image)
      puts "smoke: #{@frames} frames, fps=#{GetFPS()}, map=#{@world&.name}, pos=#{@player.x.round(2)},#{@player.z.round(2)} " \
           "hp=#{@player.stats.hp} lv=#{@player.stats.level} exp=#{@player.stats.exp} gold=#{@player.inventory.gold} " \
           "scene=#{@scene} flags=#{@flags.to_a.join(",")} items=#{@player.inventory.counts.to_h} " \
           "enemies=#{@world&.enemies&.map { |e| "#{e.type.id}:#{e.state}:#{e.hp}" }&.join(',')} shot=#{shot}"
      @running = false
    end

    def update(dt)
      @messages.each { |m| m[1] += dt }
      @messages.reject! { |m| m[1] > 5 }
      case @scene
      when :title then update_title
      when :play then update_play(dt)
      when :dialogue then update_dialogue
      when :menu then update_menu
      when :shop then update_shop
      when :pause then update_pause
      when :controls then update_controls
      when :dead then update_dead(dt)
      when :ending then update_ending
      end
    end

    def mouse_look(on)
      return if @opts[:smoke] || on == @mouse_captured

      @mouse_captured = on
      on ? DisableCursor() : EnableCursor()
    end

    # --- scenes: title / new game / travel ----------------------------------

    def show_title
      @scene = :title
      @menu_index = 0
      @flags = Set.new
      @player = Player.new
      load_world("harrowmere")
      mouse_look(false)
    end

    def title_options = @saves.exists? ? ["Continue", "New Game", "Controls", "Quit"] : ["New Game", "Controls", "Quit"]

    def update_title
      opts = title_options
      @menu_index = (@menu_index - 1) % opts.size if @input.pressed?(:up)
      @menu_index = (@menu_index + 1) % opts.size if @input.pressed?(:down)
      return unless @input.pressed?(:confirm)

      case opts[@menu_index]
      when "Continue" then continue_game
      when "New Game"
        new_game("harrowmere")
        @audio.play(:bell, volume: 0.5)
        message("Harrowmere. The bell has gone quiet.")
      when "Controls" then open_controls
      when "Quit" then @running = false
      end
    end

    def new_game(map_name, at: nil)
      @flags = Set.new
      @player = Player.new
      @messages.clear
      load_world(map_name)
      x, z, yaw = at ? spot(at) : @world.start_position
      @player.place(x, z, yaw, @world.map)
      enter_play
    end

    def continue_game
      map_name, player, flags = @saves.load
      return message("The save file could not be read.") unless map_name

      @player = player
      @flags = flags
      @messages.clear
      load_world(map_name)
      @player.place(player.x, player.z, player.yaw, @world.map)
      enter_play
      message("You wake beside the shrine.")
    end

    def spot(at)
      tx, tz, yaw = at.to_s.split(",").map(&:to_f)
      x, z = TileMap.center(tx.to_i, tz.to_i)
      [x, z, (yaw || 0) * Math::PI / 180]
    end

    def load_world(name)
      @world&.unload
      @world = World.new(self, name)
    end

    def travel(map_name, at)
      load_world(map_name)
      x, z, yaw = spot(at)
      @player.place(x, z, yaw, @world.map)
      message(@world.meta.fetch(:name, map_name))
    end

    def enter_play
      @scene = :play
      mouse_look(true)
    end

    # --- play ------------------------------------------------------------------

    def update_play(dt)
      p = @player
      return open_pause if @input.pressed?(:pause)
      return open_menu if @input.pressed?(:menu)

      if @mouse_captured
        md = GetMouseDelta()
        p.turn(md.x * 0.0032)
        p.look(-md.y * 0.0032)
      end
      p.turn((axis(:turn_r, :turn_l)) * Player::TURN_SPEED * dt)
      p.look((axis(:look_up, :look_down)) * 1.2 * dt)
      moved = p.walk(@world.map, axis(:forward, :back), axis(:strafe_r, :strafe_l), dt,
                     blocked: @world.blocker, sprint: @input.down?(:sprint))
      p.settle(@world.map, dt)
      footstep if moved

      p.update_timers(dt)
      if @input.pressed?(:attack) && p.start_swing
        @hit_done = false
        sfx(:swing, 0.6)
      end
      resolve_swing if p.swinging? && !@hit_done && p.swing_t >= Player::SWING_HIT_AT
      cast_spell if @input.pressed?(:cast)
      cycle_spell if @input.pressed?(:cycle)
      quick_use("red_tonic") if @input.pressed?(:quick1)
      quick_use("blue_moss") if @input.pressed?(:quick2)
      interact if @input.pressed?(:interact)

      @world.update(dt)
      @dead_t = 0.0 unless p.alive?
      @scene = :dead unless p.alive?
    end

    def axis(pos, neg) = (@input.down?(pos) ? 1 : 0) - (@input.down?(neg) ? 1 : 0)

    def footstep
      @step_phase ||= 0.0
      phase = (@player.bob_t / Math::PI).floor
      return if phase == @step_phase

      @step_phase = phase
      sfx(:step, 0.35)
    end

    def resolve_swing
      @hit_done = true
      weapon = @player.inventory.weapon_item
      target = @world.melee_targets(weapon.reach).first
      return unless target

      dmg = Combat.damage(base: weapon.power, strength: @player.stats.strength, gauge: @player.swing_power,
                          defense: target.type.boss ? 4 : 0)
      sfx(:hit)
      damage_enemy(target, dmg)
    end

    def damage_enemy(enemy, dmg)
      return unless enemy.take_hit(dmg)

      sfx(:enemy_die)
      t = enemy.type
      gold = rand(t.gold)
      @player.inventory.gold += gold
      message("#{t.name} destroyed. #{t.exp} EXP, #{gold} gold.")
      gained = @player.stats.gain_exp(t.exp)
      if gained.positive?
        sfx(:levelup)
        message("You reached level #{@player.stats.level}!")
      end
      return unless t.boss

      @flags << "boss_dead"
      @world.drop_sigil(enemy.x, enemy.z)
      message("The Warden crumbles into ash. Something glows where he fell.")
    end

    def hurt_player(dmg, source)
      return unless @player.alive?

      @player.stats.hurt(dmg)
      @player.hurt_t = 0.4
      sfx(:hurt)
      message("#{source} hits you for #{dmg}.") if dmg >= 10
    end

    def cast_spell
      spell = @player.current_spell
      return message("You know no spells.") unless spell
      return message("Your focus has not returned.") unless @player.magic_gauge.full?
      return message("Not enough MP.") unless @player.stats.spend_mp(spell.cost)

      gauge = @player.magic_gauge.spend
      sfx(:spell)
      case spell.id
      when "flame" then @world.fire_bolt(Spells.flame_damage(@player.stats.magic, gauge))
      when "mend"
        amount = Spells.mend_amount(@player.stats.magic)
        @player.stats.heal(amount)
        message("Warmth closes your wounds. +#{amount} HP")
      when "lumen"
        @player.lumen_t = Spells::LUMEN_DURATION
        message("A pale light gathers around you.")
      end
    end

    def cycle_spell
      return if @player.spells.size < 2

      @player.spell_index = (@player.spell_index + 1) % @player.spells.size
      message(@player.current_spell.name)
    end

    def quick_use(id)
      return message("You have no #{Items[id].name}.") unless @player.inventory.has?(id)

      use_item(Items[id])
    end

    def use_item(item)
      inv = @player.inventory
      case item.kind
      when :consumable
        inv.remove(item.id)
        @player.stats.heal(item.heal) if item.heal
        @player.stats.restore_mp(item.mana) if item.mana
        sfx(:pickup, 0.6)
        message("Used #{item.name}.")
      when :scroll
        inv.remove(item.id)
        @player.spells << item.spell unless @player.spells.include?(item.spell)
        sfx(:levelup)
        message("You learned #{Spells[item.spell].name}.")
      when :weapon, :armor
        if inv.unequip(item.id)
          message("Unequipped #{item.name}.")
        else
          inv.equip(item.id)
          message("Equipped #{item.name}.")
        end
      else
        message(item.desc)
      end
    end

    def focus_label
      return nil unless @scene == :play && @world && (p = @world.focus)

      case p.kind
      when "npc" then "[E] Talk"
      when "chest" then "[E] Open chest"
      when "door" then "[E] Open door"
      when "lever" then "[E] Pull lever"
      when "save_statue" then "[E] Pray at the shrine"
      when "exit" then "[E] #{p.props.fetch('label', 'Leave').tr('_', ' ')}"
      when "pickup" then "[E] Take"
      end
    end

    def interact
      prop = @world.focus
      return unless prop

      case prop.kind
      when "npc" then start_dialogue(*DialogueData.for(prop.props["id"], self))
      when "chest" then open_chest(prop)
      when "door" then open_door(prop)
      when "lever"
        @world.pull_lever(prop)
        sfx(:door)
        message("Somewhere chains rattle, and iron grinds against stone.")
      when "save_statue"
        @player.stats.heal(@player.stats.max_hp)
        @player.stats.restore_mp(@player.stats.max_mp)
        @saves.save(map: @world.name, player: @player, flags: @flags)
        sfx(:save)
        message("The shrine restores you. Your journey is recorded.")
      when "exit" then travel(prop.props["map"], prop.props["at"])
      when "pickup"
        item = Items[prop.props["item"]]
        @player.inventory.add(item.id)
        @flags << "sigil_taken" if item.id == "ember_sigil"
        @world.remove_prop(prop)
        sfx(:pickup)
        message("Obtained #{item.name}.")
      end
    end

    def open_chest(prop)
      @world.open_prop(prop)
      sfx(:chest)
      item = prop.props["item"]
      count = prop.props.fetch("count", "1").to_i
      gold = prop.props.fetch("gold", "0").to_i
      @player.inventory.add(item, count) if item
      @player.inventory.gold += gold
      parts = []
      parts << "#{Items[item].name}#{count > 1 ? " x#{count}" : ''}" if item
      parts << "#{gold} gold" if gold.positive?
      message("Found #{parts.join(' and ')}.")
    end

    def open_door(prop)
      key = prop.props["key"]
      if key && !@player.inventory.has?(key)
        message("It is locked. You need the #{Items[key].name}.")
        return
      end
      @world.open_prop(prop)
      sfx(:door)
      message(key ? "The #{Items[key].name} turns in the lock." : "The door grinds open.")
    end

    def message(text)
      @messages << [text, 0.0]
      nil
    end

    def sfx(name, volume = 1.0) = @audio.play(name, volume: volume)

    # --- dialogue ------------------------------------------------------------

    def start_dialogue(speaker, lines, after)
      @dialogue = { speaker: speaker, lines: lines, page: 0, after: after }
      @scene = :dialogue
    end

    def update_dialogue
      return unless @input.pressed?(:confirm) || @input.pressed?(:interact) || @input.pressed?(:cancel)

      @dialogue[:page] += 1
      return if @dialogue[:page] < @dialogue[:lines].size

      after = @dialogue[:after]
      @scene = :play
      after&.call(self)
    end

    # --- inventory menu ------------------------------------------------------------

    def open_menu
      @scene = :menu
      @menu_index = 0
      mouse_look(false)
    end

    def menu_items = @player.inventory.items.sort_by { |i| [%i[weapon armor consumable scroll key].index(i.kind), i.name] }

    def update_menu
      items = menu_items
      return enter_play if @input.pressed?(:cancel)
      return if items.empty?

      @menu_index = (@menu_index - 1) % items.size if @input.pressed?(:up)
      @menu_index = (@menu_index + 1) % items.size if @input.pressed?(:down)
      @menu_index = @menu_index.clamp(0, items.size - 1)
      use_item(items[@menu_index]) if @input.pressed?(:confirm)
    end

    # --- shop ----------------------------------------------------------------------

    def open_shop
      @scene = :shop
      @menu_index = 0
      mouse_look(false)
    end

    def shop_stock
      DialogueData::SHOP.reject do |id|
        item = Items[id]
        (item.kind == :scroll && (@player.spells.include?(item.spell) || @player.inventory.has?(id))) ||
          (%i[weapon armor].include?(item.kind) && @player.inventory.has?(id))
      end.map { |id| Items[id] }
    end

    def update_shop
      stock = shop_stock
      return enter_play if @input.pressed?(:cancel) || stock.empty?

      @menu_index = (@menu_index - 1) % stock.size if @input.pressed?(:up)
      @menu_index = (@menu_index + 1) % stock.size if @input.pressed?(:down)
      @menu_index = @menu_index.clamp(0, stock.size - 1)
      return unless @input.pressed?(:confirm)

      item = stock[@menu_index]
      if @player.inventory.buy(item.id)
        sfx(:pickup)
        message("Bought #{item.name}.")
      else
        message("You can't afford that.")
      end
    end

    # --- pause / death / ending ----------------------------------------------------

    PAUSE_OPTIONS = ["Resume", "Controls", "Return to Title", "Quit"].freeze

    def open_pause
      @scene = :pause
      @menu_index = 0
      mouse_look(false)
    end

    def update_pause
      return enter_play if @input.pressed?(:cancel)

      @menu_index = (@menu_index - 1) % PAUSE_OPTIONS.size if @input.pressed?(:up)
      @menu_index = (@menu_index + 1) % PAUSE_OPTIONS.size if @input.pressed?(:down)
      return unless @input.pressed?(:confirm)

      case PAUSE_OPTIONS[@menu_index]
      when "Resume" then enter_play
      when "Controls" then open_controls
      when "Return to Title" then show_title
      when "Quit" then @running = false
      end
    end

    # Controls reference, opened from the title or pause menu; returns to it on cancel.
    def open_controls
      @controls_from = @scene
      @scene = :controls
    end

    def update_controls
      @scene = @controls_from if @input.pressed?(:cancel) || @input.pressed?(:confirm)
    end

    def draw_controls
      Ui.hud(self) if @controls_from == :pause
      DrawRectangle(0, 0, W, H, Ui.color(0, 0, 0, 120))
      Ui.list("Controls", 30, 26, 260, Input::CONTROLS, -1, footer: "Esc / Enter: back")
    end

    def update_dead(dt)
      @dead_t += dt
      @world.update(dt)
      return unless @dead_t > 1.5 && @input.pressed?(:confirm)

      @saves.exists? ? continue_game : show_title
    end

    def finish_game
      @player.inventory.remove("ember_sigil")
      @flags << "ending"
      @audio.play(:bell)
      @scene = :ending
      @ending_t = 0.0
      mouse_look(false)
    end

    def update_ending
      @ending_t += GetFrameTime()
      show_title if @ending_t > 2 && @input.pressed?(:confirm)
    end

    # --- rendering ---------------------------------------------------------------

    def render
      render_preview if @scene == :menu
      BeginTextureMode(@target)
      fog = @world.meta.fetch(:fog, [0, 0, 0])
      ClearBackground(Color.from_u8(*fog.map { |c| (c * 255).round }, 255))
      render_world(fog)
      render_ui
      EndTextureMode()

      BeginDrawing()
      ClearBackground(BLACK)
      sw = GetScreenWidth()
      sh = GetScreenHeight()
      scale = [sw.to_f / W, sh.to_f / H].min
      dw = W * scale
      dh = H * scale
      DrawTexturePro(@target[:texture], Rectangle.create(0, 0, W, -H),
                     Rectangle.create((sw - dw) / 2, (sh - dh) / 2, dw, dh), Vector2.create(0, 0), 0, WHITE)
      EndDrawing()
    end

    def render_world(fog)
      setup_camera
      meta = @world.meta
      @gpu.set_vec2("snapRes", [W / 2, H / 2])
      @gpu.set_vec3("fogColor", fog)
      @gpu.set_vec2("fogRange", meta.fetch(:fog_range, [4, 30]))
      radius, *torch = meta.fetch(:torch, [0, 0, 0, 0])
      if @player.lumen_t.positive?
        radius = [radius, 0].max + 9
        torch = [0.6, 0.65, 0.75]
      end
      @gpu.set_vec3("torchColor", torch)
      @gpu.set_float("torchRadius", radius)

      BeginMode3D(@camera)
      @world.draw(@rig, @gpu)
      EndMode3D()

      return unless %i[play dialogue menu shop].include?(@scene) && @player.alive?

      BeginMode3D(@view_camera)
      rlDisableDepthTest() # BeginMode3D turns depth on; the viewmodel must draw over the world
      @gpu.set_float("isModel", 1.0)
      @gpu.model_light(@world.builder.light_at(@player.x, @player.eye_y, @player.z).map { |c| [c + 0.15, 1.4].min })
      bob = Math.sin(@player.bob_t) * 0.02
      Models.sword_view(@rig, @player.swing_t, bob, @player.inventory.weapon)
      EndMode3D()
    end

    # Spins the selected inventory item in its own little PS1-styled viewport.
    def render_preview
      item = menu_items[@menu_index]
      BeginTextureMode(@preview)
      ClearBackground(Ui.color(16, 12, 9))
      if item
        @preview_camera ||= Camera3D.new.with_position(2.6, 0.5, 0).with_target(0, 0, 0).with_up(0, 1, 0)
                                    .with_fovy(40).with_projection(CAMERA_PERSPECTIVE)
        @gpu.set_vec2("snapRes", [PREVIEW / 2, PREVIEW / 2])
        @gpu.set_vec3("fogColor", [0, 0, 0])
        @gpu.set_vec2("fogRange", [50, 60])
        @gpu.set_vec3("torchColor", [0, 0, 0])
        @gpu.set_float("torchRadius", 0)
        BeginMode3D(@preview_camera)
        @gpu.set_float("isModel", 1.0)
        @gpu.model_light([1.25, 1.15, 1.0])
        @rig.at(0, Math.sin(@time * 2) * 0.04, 0, ry: @time * 1.2) { Models.item(@rig, item.id, @time) }
        EndMode3D()
      end
      EndTextureMode()
    end

    def setup_camera
      if @scene == :title || (@scene == :controls && @controls_from == :title)
        a = @time * 0.08
        cx, cz = TileMap.center(15, 15)
        ex = cx + Math.cos(a) * 9
        ez = cz + Math.sin(a) * 9
        @player.x = ex
        @player.z = ez
        @camera.with_position(ex, 4.5, ez).with_target(cx, 1.5, cz)
        return
      end
      p = @player
      fx, fz = p.forward
      cp = Math.cos(p.pitch)
      eye = p.eye_y
      @camera.with_position(p.x, eye, p.z).with_target(p.x + fx * cp, eye + Math.sin(p.pitch), p.z + fz * cp)
    end

    def render_ui
      case @scene
      when :title then draw_title
      when :play then Ui.hud(self)
      when :dialogue
        Ui.hud(self)
        d = @dialogue
        Ui.dialogue(d[:speaker], d[:lines][d[:page]], d[:page], d[:lines].size) if d[:page] < d[:lines].size
      when :menu then draw_menu
      when :shop then draw_shop
      when :pause
        Ui.hud(self)
        DrawRectangle(0, 0, W, H, Ui.color(0, 0, 0, 120))
        Ui.list("Paused", 100, 80, 120, PAUSE_OPTIONS.map { |o| [o] }, @menu_index)
      when :controls then draw_controls
      when :dead then draw_dead
      when :ending then draw_ending
      end
    end

    def draw_title
      DrawRectangle(0, 0, W, H, Ui.color(0, 0, 0, 90))
      Ui.text_centered("ASHEN VAULT", W / 2, 56, Ui::HIGHLIGHT, size: 20)
      Ui.text_centered("beneath the silent bell", W / 2, 80, Ui::DIM)
      title_options.each_with_index do |o, i|
        Ui.text_centered(i == @menu_index ? "> #{o} <" : o, W / 2, 140 + i * 14, i == @menu_index ? Ui::HIGHLIGHT : Ui::TEXT)
      end
    end

    def draw_menu
      items = menu_items
      inv = @player.inventory
      rows = items.map do |i|
        tag = inv.equipped?(i.id) ? " (E)" : ""
        ["#{i.name}#{tag}", i.kind == :consumable ? "x#{inv.count(i.id)}" : nil]
      end
      Ui.list("Belongings", 6, 6, 170, rows, @menu_index)
      s = @player.stats
      Ui.panel(182, 6, 132, 144)
      [["Level", s.level], ["EXP", "#{s.exp}/#{s.next_level_exp}"], ["HP", "#{s.hp}/#{s.max_hp}"],
       ["MP", "#{s.mp}/#{s.max_mp}"], ["STR", s.strength], ["MAG", s.magic], ["DEF", inv.defense],
       ["Weapon", inv.weapon_item.power], ["Gold", inv.gold]].each_with_index do |(k, v), i|
        Ui.text(k, 190, 12 + i * 11, Ui::DIM)
        Ui.text(v.to_s, 306 - MeasureText(v.to_s, 10), 12 + i * 11)
      end
      spells = @player.spells.map { |id| Spells[id].name }
      Ui.text("Spells", 190, 114, Ui::DIM)
      Ui.wrap(spells.join(", "), 116).first(2).each_with_index { |l, i| Ui.text(l, 190, 125 + i * 11) }

      Ui.panel(6, 156, 308, 78)
      item = items[@menu_index]
      if item
        DrawRectangle(10, 160, PREVIEW + 6, PREVIEW + 6, BLACK)
        DrawTextureRec(@preview[:texture], Rectangle.create(0, 0, PREVIEW, -PREVIEW), Vector2.create(13, 163), WHITE)
        DrawRectangleLines(10, 160, PREVIEW + 6, PREVIEW + 6, Ui::BORDER)
        Ui.text(item.name, 84, 162, Ui::HIGHLIGHT)
        Ui.text(item_detail(item), 84, 174, Ui::DIM)
        Ui.wrap(item.desc, 224).first(3).each_with_index { |l, i| Ui.text(l, 84, 187 + i * 11) }
      end
      msg = @messages.last
      footer = msg && msg[1] < 2.5 ? msg[0] : "Enter: use/equip/unequip   Tab: close"
      Ui.text(footer, 84, 221, msg && msg[1] < 2.5 ? Ui::TEXT : Ui::DIM)
    end

    def item_detail(item)
      case item.kind
      when :weapon then "Weapon   ATK #{item.power}   Reach #{item.reach}"
      when :armor then "Armor   DEF #{item.power}"
      when :consumable then "Consumable   x#{@player.inventory.count(item.id)}"
      when :scroll then "Scroll   #{Spells[item.spell].name}"
      else "Key item"
      end
    end

    def draw_shop
      Ui.hud(self)
      stock = shop_stock
      rows = stock.map { |i| [i.name, "#{i.price}g", i.price > @player.inventory.gold] }
      Ui.list("Pell's Goods  (you have #{@player.inventory.gold}g)", 40, 30, 240, rows, @menu_index,
              footer: "Enter: buy   Esc: leave")
      item = stock[@menu_index]
      Ui.text_centered(item.desc, W / 2, 140) if item
    end

    def draw_dead
      DrawRectangle(0, 0, W, H, Ui.color(40, 0, 0, [(@dead_t || 0) * 120, 200].min.round))
      Ui.text_centered("YOU HAVE FALLEN", W / 2, 100, Ui.color(220, 80, 70), size: 20)
      Ui.text_centered(@saves.exists? ? "Press Enter to wake at the last shrine" : "Press Enter", W / 2, 130, Ui::DIM) if @dead_t.to_f > 1.5
    end

    ENDING = [
      "The bell of Harrowmere rings again.",
      "Its note rolls down through the well and into the drowned halls,",
      "and the old keep settles back into sleep.",
      "",
      "Thank you for playing the Ashen Vault demo."
    ].freeze

    def draw_ending
      DrawRectangle(0, 0, W, H, Ui.color(0, 0, 0, [@ending_t * 100, 230].min.round))
      ENDING.each_with_index { |l, i| Ui.text_centered(l, W / 2, 70 + i * 14) }
      Ui.text_centered("Press Enter", W / 2, 190, Ui::DIM) if @ending_t > 2
    end
  end
end
