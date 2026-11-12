module AshenVault
  # Original low-poly models assembled from primitives. All face +X.
  module Models
    BONE = [214, 204, 178].freeze
    RUST = [120, 70, 44].freeze
    IRON = [92, 92, 98].freeze
    ASH = [96, 92, 88].freeze
    EMBER = [255, 140, 50].freeze

    module_function

    def enemy(r, e)
      t = e.anim_t
      case e.type.id
      when "bone_walker" then bone_walker(r, e, t)
      when "mire_slime" then mire_slime(r, e, t)
      when "cinder_wisp" then cinder_wisp(r, e, t)
      when "ashen_warden" then ashen_warden(r, e, t)
      end
    end

    # Arm swing for melee enemies: raised during windup, slammed down on attack.
    def strike_angle(e)
      case e.state
      when :windup then -2.2 * [e.state_t / e.type.windup, 1].min
      when :attack then -2.2 + 3.0 * [e.state_t / 0.2, 1].min
      when :recover then 0.8 * (1 - [e.state_t / e.type.recover, 1].min)
      else 0
      end
    end

    def walk_cycle(e, t) = %i[chase idle].include?(e.state) ? Math.sin(t * 7) * 0.5 : 0

    def bone_walker(r, e, t)
      swing = walk_cycle(e, t)
      hit = strike_angle(e)
      lean = e.state == :hurt ? -0.3 : 0
      r.at(0, 0, 0, rz: lean) do
        [[-0.14, swing], [0.14, -swing]].each do |side, a|
          r.at(0, 0.9, side, rz: a) do
            r.part(:cube, 0, -0.22, 0, 0.08, 0.45, 0.08, BONE)
            r.part(:cube, 0, -0.66, 0, 0.07, 0.45, 0.07, BONE)
            r.part(:cube, 0.06, -0.88, 0, 0.18, 0.05, 0.1, BONE)
          end
        end
        r.part(:cube, 0, 0.95, 0, 0.18, 0.12, 0.34, BONE)
        r.part(:cyl, 0, 1.18, 0, 0.08, 0.4, 0.08, BONE)
        4.times { |i| r.part(:cube, 0.02, 1.08 + i * 0.1, 0, 0.16, 0.03, 0.36 - i * 0.02, BONE) }
        r.part(:cube, 0, 1.42, 0, 0.14, 0.06, 0.46, BONE)
        r.at(0.02, 1.6, 0, rz: Math.sin(t * 2) * 0.1) do
          r.part(:sphere, 0, 0, 0, 0.26, 0.28, 0.24, BONE)
          r.part(:cube, 0.11, -0.03, -0.05, 0.05, 0.06, 0.06, [30, 10, 10])
          r.part(:cube, 0.11, -0.03, 0.05, 0.05, 0.06, 0.06, [30, 10, 10])
          r.part(:cube, 0.08, -0.15, 0, 0.12, 0.06, 0.16, BONE)
        end
        r.at(0, 1.4, -0.27, rz: swing * 0.6) { r.part(:cube, 0, -0.3, 0, 0.06, 0.6, 0.06, BONE) }
        r.at(0, 1.4, 0.27, rz: hit) do
          r.part(:cube, 0, -0.3, 0, 0.06, 0.6, 0.06, BONE)
          r.at(0.05, -0.6, 0, rz: 1.4) do
            r.part(:cube, 0.4, 0, 0, 0.8, 0.07, 0.03, RUST)
            r.part(:cube, 0.0, 0, 0, 0.05, 0.05, 0.2, IRON)
          end
        end
      end
    end

    def mire_slime(r, e, t)
      squash = 1 + Math.sin(t * (e.state == :chase ? 9 : 4)) * 0.12
      squash = 1.35 if e.state == :windup
      squash = 0.7 if e.state == :attack
      green = e.state == :hurt ? [200, 220, 160] : [70, 120, 60]
      r.part(:sphere, 0, 0.32 / squash, 0, 0.95 * squash, 0.7 / squash, 0.95 * squash, green)
      r.part(:sphere, 0.05, 0.14, 0, 1.05 * squash, 0.28, 1.05 * squash, [50, 90, 44])
      r.part(:sphere, 0.3, 0.45 / squash, -0.14, 0.12, 0.12, 0.12, [230, 220, 120])
      r.part(:sphere, 0.3, 0.45 / squash, 0.14, 0.12, 0.12, 0.12, [230, 220, 120])
    end

    def cinder_wisp(r, e, t)
      bob = Math.sin(t * 3) * 0.15
      glow = e.state == :windup ? [255, 230, 140] : EMBER
      r.at(0, e.type.hover + bob, 0) do
        r.part(:sphere, 0, 0, 0, 0.45, 0.45, 0.45, glow)
        r.part(:sphere, 0, 0, 0, 0.62, 0.3, 0.62, [180, 60, 30])
        3.times do |i|
          a = t * 4 + i * 2.1
          r.part(:cube, Math.cos(a) * 0.5, Math.sin(t * 5 + i) * 0.15, Math.sin(a) * 0.5, 0.1, 0.1, 0.1, [255, 200, 90], glow: true)
        end
        r.part(:cone, 0, 0.42, 0, 0.3, 0.45, 0.3, [255, 120, 40], glow: true)
      end
    end

    def ashen_warden(r, e, t)
      swing = walk_cycle(e, t) * 0.7
      hit = strike_angle(e)
      r.at(0, 0, 0, s: 1.35) do
        [[-0.18, swing], [0.18, -swing]].each do |side, a|
          r.at(0, 0.95, side, rz: a) do
            r.part(:cube, 0, -0.45, 0, 0.2, 0.9, 0.18, ASH)
            r.part(:cube, 0.05, -0.92, 0, 0.32, 0.1, 0.2, [60, 58, 56])
          end
        end
        r.part(:cube, 0, 1.0, 0, 0.36, 0.24, 0.5, [70, 66, 62])
        r.part(:cube, 0, 1.35, 0, 0.4, 0.55, 0.62, ASH)
        r.part(:cube, 0, 1.68, 0, 0.44, 0.14, 0.86, [76, 72, 68])
        r.at(0.02, 1.88, 0) do
          r.part(:cube, 0, 0, 0, 0.3, 0.32, 0.28, [70, 66, 62])
          r.part(:cube, 0.15, 0.02, 0, 0.02, 0.05, 0.2, EMBER, glow: true)
          r.part(:cone, 0, 0.26, 0, 0.12, 0.3, 0.12, [60, 58, 56])
        end
        r.at(0, 1.6, -0.47) { r.part(:cube, 0, -0.35, 0, 0.16, 0.7, 0.16, ASH) }
        r.at(0, 1.6, 0.47, rz: hit) do
          r.part(:cube, 0, -0.35, 0, 0.16, 0.7, 0.16, ASH)
          r.at(0.05, -0.72, 0, rz: 1.45) do
            r.part(:cube, 0.6, 0, 0, 1.4, 0.08, 0.08, [60, 44, 30])
            r.part(:cube, 1.2, 0.0, 0, 0.36, 0.5, 0.05, IRON)
          end
        end
      end
    end

    def npc(r, robe, skin: [196, 158, 120], hair: [70, 54, 40], t: 0)
      sway = Math.sin(t * 1.5) * 0.03
      r.at(0, 0, 0, rz: sway) do
        r.part(:cyl, 0, 0.55, 0, 0.55, 1.1, 0.6, robe)
        r.part(:cube, 0, 1.2, 0, 0.32, 0.35, 0.5, robe)
        r.part(:cube, 0, 1.15, -0.3, 0.14, 0.5, 0.12, robe)
        r.part(:cube, 0, 1.15, 0.3, 0.14, 0.5, 0.12, robe)
        r.part(:sphere, 0, 1.55, 0, 0.3, 0.32, 0.28, skin)
        r.part(:sphere, -0.03, 1.64, 0, 0.32, 0.18, 0.3, hair)
        r.part(:cube, 0.14, 1.56, -0.06, 0.02, 0.04, 0.04, [20, 16, 14])
        r.part(:cube, 0.14, 1.56, 0.06, 0.02, 0.04, 0.04, [20, 16, 14])
      end
    end

    def chest(r, open)
      r.part(:cube, 0, 0.25, 0, 0.6, 0.5, 0.9, [255, 255, 255], tex: "wood_plank")
      r.part(:cube, 0, 0.26, 0, 0.62, 0.06, 0.92, IRON)
      r.at(-0.3, 0.5, 0, rz: open ? 1.9 : 0) do
        r.part(:cube, 0.3, 0.08, 0, 0.6, 0.16, 0.9, [255, 255, 255], tex: "wood_plank")
      end
      r.part(:cube, 0.31, 0.42, 0, 0.04, 0.12, 0.1, [200, 170, 80]) unless open
    end

    # Door slab spanning the tile; `axis` :x means it blocks movement along X.
    def door(r, open_t, axis, tex: "door_wood")
      lift = open_t * 2.4
      ry = axis == :x ? 0 : Math::PI / 2
      r.at(0, 0, 0, ry: ry) do
        r.part(:cube, 0, 1.25 + lift, 0, 0.18, 2.5, 2.0, [255, 255, 255], tex: tex)
      end
    end

    def brazier(r, t)
      r.part(:cyl, 0, 0.45, 0, 0.12, 0.9, 0.12, IRON)
      r.part(:cyl, 0, 0.95, 0, 0.6, 0.2, 0.6, IRON)
      flicker = 1 + Math.sin(t * 13) * 0.12
      r.part(:cone, 0, 1.2, 0, 0.4 * flicker, 0.45 * flicker, 0.4 * flicker, [255, 150, 50], glow: true)
      r.part(:cone, 0, 1.2, 0, 0.22, 0.6 * flicker, 0.22, [255, 230, 140], glow: true)
    end

    def torch(r, t)
      r.part(:cyl, 0, 0.8, 0, 0.08, 1.6, 0.08, [80, 56, 36])
      flicker = 1 + Math.sin(t * 11) * 0.15
      r.part(:cone, 0, 1.72, 0, 0.2 * flicker, 0.3 * flicker, 0.2 * flicker, [255, 170, 60], glow: true)
    end

    def save_statue(r, t)
      r.part(:cube, 0, 0.15, 0, 0.9, 0.3, 0.9, [255, 255, 255], tex: "rough_stone")
      r.part(:cube, 0, 0.9, 0, 0.5, 1.2, 0.5, [255, 255, 255], tex: "rough_stone")
      r.at(0, 1.75 + Math.sin(t * 2) * 0.06, 0, ry: t) do
        r.part(:cube, 0, 0, 0, 0.3, 0.4, 0.3, [120, 200, 255], rx: 0.6, rz: 0.6, glow: true)
      end
    end

    def lever(r, pulled)
      r.part(:cube, 0, 0.5, 0, 0.3, 1.0, 0.3, [255, 255, 255], tex: "rough_stone")
      r.at(0.16, 0.8, 0, rz: pulled ? -0.8 : 0.8) do
        r.part(:cube, 0, 0.3, 0, 0.06, 0.6, 0.06, IRON)
        r.part(:sphere, 0, 0.62, 0, 0.12, 0.12, 0.12, [140, 30, 30])
      end
    end

    def pickup(r, t)
      r.at(0, 0.3 + Math.sin(t * 3) * 0.05, 0, ry: t * 1.5) do
        r.part(:sphere, 0, 0, 0, 0.3, 0.26, 0.3, [130, 100, 70])
        r.part(:cube, 0, 0.15, 0, 0.12, 0.1, 0.12, [200, 170, 80])
      end
    end

    def well(r)
      8.times do |i|
        a = i * Math::PI / 4
        r.part(:cube, Math.cos(a) * 0.75, 0.4, Math.sin(a) * 0.75, 0.3, 0.8, 0.62, [255, 255, 255], tex: "cobble", ry: -a)
      end
      r.part(:cube, -0.85, 1.3, 0, 0.12, 1.8, 0.12, [90, 64, 40])
      r.part(:cube, 0.85, 1.3, 0, 0.12, 1.8, 0.12, [90, 64, 40])
      r.part(:cube, 0, 2.2, 0, 2.0, 0.12, 0.12, [90, 64, 40])
      r.part(:cube, 0, 2.45, 0, 2.2, 0.08, 1.2, [255, 255, 255], tex: "roof", rx: 0)
      r.part(:cube, 0, 0.05, 0, 1.2, 0.05, 1.2, [10, 12, 14])
    end

    def tree(r, seed)
      h = 2.6 + (seed % 5) * 0.3
      r.part(:cyl, 0, h * 0.35, 0, 0.32, h * 0.7, 0.32, [84, 60, 40])
      r.part(:cone, 0, h * 0.75, 0, 2.4, h * 0.7, 2.4, [44, 74, 40])
      r.part(:cone, 0, h * 1.1, 0, 1.7, h * 0.55, 1.7, [52, 86, 46])
    end

    def rope(r, t)
      r.at(0, 3.2, 0, rz: Math.sin(t * 0.8) * 0.04) do
        r.part(:cyl, 0, -1.6, 0, 0.07, 3.2, 0.07, [150, 120, 80])
        r.part(:cube, 0, -3.0, 0, 0.16, 0.12, 0.16, [130, 100, 70])
      end
      r.part(:cyl, 0, 0.05, 0, 1.0, 0.1, 1.0, [40, 40, 44])
    end

    def bolt(r, rgb)
      r.part(:sphere, 0, 0, 0, 0.3, 0.3, 0.3, rgb, glow: true)
      r.part(:sphere, 0, 0, 0, 0.5, 0.18, 0.18, [255, 230, 160], glow: true)
    end

    # First-person sword. Camera-space: +X forward, +Y up, +Z right.
    def sword_view(r, swing_t, bob, item_id)
      return fist_view(r, swing_t, bob) unless item_id

      phase = swing_t ? [swing_t / Player::SWING_TIME, 1.0].min : nil
      rz = -0.35
      rx = 0.25
      lift = 0.0
      if phase
        arc = Math.sin(phase * Math::PI)
        rz = -0.35 - arc * 1.3
        rx = 0.25 - (phase - 0.3) * 1.6
        lift = arc * 0.12
      end
      r.at(0.9, -0.5 + bob + lift, 0.36, rx: rx, ry: 0.7, rz: rz, s: 0.7) { sword(r, item_id) }
    end

    # Bare-handed: a fist that jabs straight forward.
    def fist_view(r, swing_t, bob)
      phase = swing_t ? [swing_t / Player::SWING_TIME, 1.0].min : nil
      jab = phase ? Math.sin(phase * Math::PI) * 0.3 : 0.0
      skin = [196, 158, 120]
      r.at(0.95 + jab, -0.46 + bob + jab * 0.2, 0.34 - jab * 0.5, ry: 0.25, rz: 0.2, s: 0.6) do
        r.part(:cube, -0.25, -0.05, 0, 0.5, 0.13, 0.13, [96, 80, 60])
        r.part(:cube, 0.05, 0, 0, 0.16, 0.15, 0.17, skin)
        r.part(:cube, 0.12, 0.03, 0, 0.06, 0.08, 0.18, skin.map { |c| c - 20 })
        r.part(:cube, 0.04, -0.06, -0.09, 0.1, 0.05, 0.05, skin)
      end
    end

    # Sword with the grip at the origin and the blade pointing up +Y.
    def sword(r, item_id)
      blade = item_id == "ashblade" ? [200, 200, 215] : [170, 150, 130]
      r.part(:cube, 0, 0, 0, 0.06, 0.2, 0.06, [70, 46, 30])
      r.part(:cube, 0, 0.12, 0, 0.07, 0.04, 0.3, [150, 130, 80])
      r.part(:cube, 0, 0.6, 0, 0.03, 0.9, 0.12, blade)
      r.part(:cube, 0.016, 0.6, 0, 0.01, 0.86, 0.025, blade.map { |c| [c + 40, 255].min })
      r.part(:cube, 0, 1.08, 0, 0.025, 0.08, 0.07, blade)
      r.part(:cube, 0, -0.12, 0, 0.08, 0.06, 0.08, [150, 130, 80])
    end

    # Inventory preview models, roughly 1 unit tall and centered on the origin.
    def item(r, id, t)
      case id
      when "rusted_sword", "ashblade"
        r.at(0, -0.8, 0, rx: 0.3, s: 1.45) { sword(r, id) }
      when "padded_coat", "ringmail" then garment(r, id == "ringmail")
      when "red_tonic"
        r.part(:sphere, 0, -0.18, 0, 0.5, 0.5, 0.5, [170, 30, 30])
        r.part(:cyl, 0, 0.18, 0, 0.14, 0.32, 0.14, [150, 40, 36])
        r.part(:cyl, 0, 0.38, 0, 0.12, 0.12, 0.12, [120, 90, 60])
      when "blue_moss"
        [[0, -0.1, 0, 0.5], [0.12, 0.08, 0.1, 0.34], [-0.1, 0.05, -0.12, 0.3], [0.05, 0.2, -0.05, 0.24]]
          .each { |x, y, z, d| r.part(:sphere, x, y, z, d, d * 0.8, d, [60, 140, 190], glow: true) }
        r.part(:cyl, 0, -0.32, 0, 0.6, 0.06, 0.6, [70, 60, 44])
      when "scroll_mend", "scroll_lumen"
        ribbon = id == "scroll_mend" ? [170, 40, 40] : [210, 200, 120]
        r.at(0, 0, 0, rx: Math::PI / 2) do
          r.part(:cyl, 0, 0, 0, 0.3, 0.9, 0.3, [210, 196, 160])
          r.part(:cyl, 0, 0, 0, 0.32, 0.1, 0.32, ribbon)
          r.part(:cyl, 0, 0.5, 0, 0.08, 0.14, 0.08, [110, 80, 50])
          r.part(:cyl, 0, -0.5, 0, 0.08, 0.14, 0.08, [110, 80, 50])
        end
      when "cell_key", "warden_key" then key(r, id == "warden_key" ? [120, 120, 128] : [150, 84, 50], id == "warden_key" ? 1.9 : 1.6)
      when "ember_sigil"
        glow = 1 + Math.sin(t * 4) * 0.08
        r.at(0, 0, 0, rz: Math::PI / 2) do
          r.part(:cyl, 0, 0, 0, 0.7, 0.12, 0.7, [110, 80, 70])
          r.part(:cyl, 0, 0, 0, 0.36 * glow, 0.14, 0.36 * glow, EMBER, glow: true)
        end
      else
        r.part(:cube, 0, 0, 0, 0.5, 0.5, 0.5, [130, 100, 70])
      end
    end

    def garment(r, mail)
      col = mail ? [130, 132, 140] : [120, 104, 80]
      r.part(:cube, 0, 0, 0, 0.3, 0.8, 0.62, col)
      r.part(:cube, 0, 0.34, 0, 0.32, 0.14, 0.86, col)
      r.part(:cube, 0, 0.0, -0.42, 0.22, 0.6, 0.18, col, rx: -0.15)
      r.part(:cube, 0, 0.0, 0.42, 0.22, 0.6, 0.18, col, rx: 0.15)
      # Ring rows on the mail, quilting seams on the coat.
      4.times { |i| r.part(:cube, 0, 0.2 - i * 0.14, 0, 0.32, 0.03, 0.64, mail ? [70, 72, 80] : [90, 76, 56]) }
      r.part(:cube, 0, -0.18, 0, 0.33, 0.06, 0.65, [70, 50, 34])
    end

    def key(r, rgb, size)
      r.at(0, 0, 0, rx: -0.6, s: size) do
        r.part(:cyl, 0, 0.32, 0, 0.32, 0.06, 0.32, rgb, rz: Math::PI / 2)
        r.part(:cube, 0, -0.08, 0, 0.06, 0.6, 0.06, rgb)
        r.part(:cube, 0, -0.3, 0.08, 0.05, 0.06, 0.12, rgb)
        r.part(:cube, 0, -0.18, 0.07, 0.05, 0.05, 0.1, rgb)
      end
    end
  end
end
