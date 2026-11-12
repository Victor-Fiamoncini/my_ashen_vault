module AshenVault
  # 2D drawing at the 320x240 internal resolution.
  module Ui
    include Raylib
    extend Raylib

    module_function

    def color(r, g, b, a = 255) = Color.from_u8(r, g, b, a)

    TEXT = Color.from_u8(220, 210, 180, 255)
    DIM = Color.from_u8(140, 130, 110, 255)
    SHADOW = Color.from_u8(0, 0, 0, 200)
    PANEL = Color.from_u8(10, 8, 6, 210)
    BORDER = Color.from_u8(120, 100, 70, 255)
    HIGHLIGHT = Color.from_u8(255, 220, 140, 255)

    def text(str, x, y, col = TEXT, size: 10)
      DrawText(str, x + 1, y + 1, size, SHADOW)
      DrawText(str, x, y, size, col)
    end

    def text_centered(str, cx, y, col = TEXT, size: 10) = text(str, cx - MeasureText(str, size) / 2, y, col, size: size)

    def panel(x, y, w, h)
      DrawRectangle(x, y, w, h, PANEL)
      DrawRectangleLines(x, y, w, h, BORDER)
    end

    def bar(x, y, w, h, frac, rgb)
      DrawRectangle(x - 1, y - 1, w + 2, h + 2, color(0, 0, 0, 220))
      DrawRectangle(x, y, (w * frac.clamp(0, 1)).round, h, color(*rgb))
    end

    # Word-wraps `str` to `width` pixels.
    def wrap(str, width, size: 10)
      lines = [+""]
      str.split.each do |word|
        trial = lines.last.empty? ? word : "#{lines.last} #{word}"
        if MeasureText(trial, size) > width && !lines.last.empty?
          lines << word.dup
        else
          lines[-1] = trial
        end
      end
      lines
    end

    def hud(game)
      p = game.player
      s = p.stats
      w = Game::W
      h = Game::H

      # Vitals: a small block in the bottom-left corner.
      DrawRectangle(4, h - 31, 108, 27, color(0, 0, 0, 110))
      text("HP", 8, h - 28, color(230, 120, 110))
      bar(26, h - 26, 54, 4, s.hp.to_f / s.max_hp, [190, 40, 40])
      text(s.hp.to_s, 84, h - 28, DIM)
      text("MP", 8, h - 16, color(120, 150, 230))
      bar(26, h - 14, 54, 4, s.mp.to_f / s.max_mp, [50, 80, 200])
      text(s.mp.to_s, 84, h - 16, DIM)

      # Gauges flank the compass ball in the bottom-right corner.
      cx = w - 25
      cy = h - 25
      gauge(cx - 31, cy - 12, p.attack_gauge.value, [240, 210, 90], [150, 120, 50])
      gauge(cx - 25, cy - 12, p.magic_gauge.value, [120, 220, 240], [60, 110, 130])
      compass(p.heading, cx, cy)
      spell = p.current_spell
      label = spell ? "#{spell.name} #{spell.cost}" : "No spell"
      text(label, w - 8 - MeasureText(label, 10), cy - 34, spell ? DIM : color(90, 84, 72))
      text("SPRINT", 8, h - 42, DIM) if p.sprinting

      boss_bar(game)
      messages(game)
      prompt(game)
      flash(p)
    end

    # Thin vertical gauge that brightens when full (gold = ATK, cyan = MAG).
    def gauge(x, y, frac, full_rgb, fill_rgb)
      DrawRectangle(x - 1, y - 1, 5, 26, color(0, 0, 0, 220))
      fill = (24 * frac.clamp(0, 1)).round
      DrawRectangle(x, y + 24 - fill, 3, fill, color(*(frac >= 1 ? full_rgb : fill_rgb)))
    end

    # King's Field style compass: a shaded ball that rolls with your heading.
    # The direction you face sits at the front-center of the ball.
    COMPASS_TILT = 0.5 # how far we look down onto the ball (radians)

    def compass(heading, cx, cy, r: 17)
      DrawCircle(cx, cy, r + 2, color(0, 0, 0, 210))
      # Fake sphere shading: stacked discs drifting toward the light (upper left).
      7.times do |i|
        k = i / 6.0
        DrawCircle(cx - (k * r * 0.35).round, cy - (k * r * 0.4).round, r * (1 - k * 0.8),
                   color((70 + k * 120).round, (58 + k * 105).round, (40 + k * 80).round))
      end

      ct = Math.cos(COMPASS_TILT)
      st = Math.sin(COMPASS_TILT)
      project = lambda do |az, lat|
        a = (az - heading) * Math::PI / 180
        x = Math.cos(lat) * Math.sin(a)
        y = Math.sin(lat)
        z = Math.cos(lat) * Math.cos(a) # toward the viewer
        [cx + x * r, cy - (y * ct - z * st) * r, z * ct + y * st]
      end
      line = lambda do |a, b|
        ax, ay, ad = a
        bx, by, bd = b
        next if ad < 0 || bd < 0

        DrawLine(ax.round, ay.round, bx.round, by.round, color(40, 28, 16, (90 + [ad, bd].min * 150).round.clamp(0, 230)))
      end

      # Meridians every 45 degrees plus the equator, front hemisphere only.
      (0...360).step(45) do |az|
        (-75..60).step(15) { |lat| line.call(project.call(az, lat * Math::PI / 180), project.call(az, (lat + 15) * Math::PI / 180)) }
      end
      (0...360).step(15) { |az| line.call(project.call(az, 0), project.call(az + 15, 0)) }

      { "N" => 0, "E" => 90, "S" => 180, "W" => 270 }.each do |label, az|
        px, py, depth = project.call(az, 0)
        next if depth < -0.05

        alpha = (60 + depth * 260).clamp(0, 255).round
        rgb = label == "N" ? [200, 30, 24] : [36, 24, 12]
        DrawText(label, px.round - MeasureText(label, 10) / 2, py.round - 5, 10, color(*rgb, alpha))
      end

      # Fixed pointer under the ball marks the facing.
      DrawTriangle(Vector2.create(cx, cy + r), Vector2.create(cx - 3, cy + r + 5),
                   Vector2.create(cx + 3, cy + r + 5), HIGHLIGHT)
    end

    def boss_bar(game)
      boss = game.world&.enemies&.find { |e| e.type.boss && e.alive? && e.state != :idle }
      return unless boss

      text_centered(boss.name, Game::W / 2, 20, color(230, 180, 150))
      bar(Game::W / 2 - 80, 32, 160, 4, boss.hp.to_f / boss.type.hp, [170, 40, 30])
    end

    def messages(game)
      lines = game.messages.last(3)
      lines.each_with_index do |(msg, age), i|
        alpha = age > 4 ? (255 * (5 - age)).clamp(0, 255).round : 255
        next if alpha <= 0

        text_centered(msg, Game::W / 2, Game::H - 58 - (lines.size - 1 - i) * 11, color(230, 220, 190, alpha))
      end
    end

    def prompt(game)
      label = game.focus_label
      text_centered(label, Game::W / 2, 140, HIGHLIGHT) if label
    end

    def flash(player)
      return unless player.hurt_t.positive?

      DrawRectangle(0, 0, Game::W, Game::H, color(160, 0, 0, (player.hurt_t * 300).clamp(0, 120).round))
    end

    def dialogue(speaker, line, page, pages)
      panel(10, 150, 300, 56)
      text(speaker, 18, 155, HIGHLIGHT)
      wrap(line, 284).each_with_index { |l, i| text(l, 18, 168 + i * 11) }
      text("#{page + 1}/#{pages}", 284, 195, DIM)
    end

    def list(title, x, y, w, rows, selected, footer: nil)
      height = 22 + [rows.size, 1].max * 11 + (footer ? 12 : 0)
      panel(x, y, w, height)
      text(title, x + 8, y + 5, HIGHLIGHT)
      text("(empty)", x + 12, y + 20, DIM) if rows.empty?
      rows.each_with_index do |(label, right, dim), i|
        col = i == selected ? HIGHLIGHT : (dim ? DIM : TEXT)
        text(i == selected ? ">" : " ", x + 4, y + 20 + i * 11, col)
        text(label, x + 12, y + 20 + i * 11, col)
        text(right.to_s, x + w - 8 - MeasureText(right.to_s, 10), y + 20 + i * 11, col) if right
      end
      text(footer, x + 8, y + height - 13, DIM) if footer
    end
  end
end
