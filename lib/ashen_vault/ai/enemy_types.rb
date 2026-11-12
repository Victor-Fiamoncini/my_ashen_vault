module AshenVault
  EnemyType = Struct.new(:id, :name, :hp, :speed, :damage, :reach, :sight, :windup, :recover, :exp, :gold,
                         :radius, :ranged, :hover, :boss, :drop, :poise, :height, keyword_init: true)

  module EnemyTypes
    ALL = [
      EnemyType.new(id: "bone_walker", name: "Bone Walker", hp: 24, speed: 1.7, damage: 8, reach: 1.9, sight: 12,
                    windup: 0.55, recover: 0.9, exp: 14, gold: 4..10, radius: 0.45, height: 1.8, poise: 0),
      EnemyType.new(id: "mire_slime", name: "Mire Slime", hp: 16, speed: 1.1, damage: 6, reach: 1.5, sight: 8,
                    windup: 0.45, recover: 0.7, exp: 7, gold: 1..5, radius: 0.5, height: 0.8, poise: 0),
      EnemyType.new(id: "cinder_wisp", name: "Cinder Wisp", hp: 12, speed: 1.4, damage: 7, reach: 9.0, sight: 12,
                    windup: 0.8, recover: 1.8, exp: 12, gold: 5..12, radius: 0.35, height: 0.6, ranged: true,
                    hover: 1.3, poise: 0),
      EnemyType.new(id: "ashen_warden", name: "Ashen Warden", hp: 150, speed: 2.0, damage: 16, reach: 2.6,
                    sight: 16, windup: 0.75, recover: 1.1, exp: 90, gold: 60..60, radius: 0.7, height: 2.6,
                    boss: true, drop: "ember_sigil", poise: 14)
    ].to_h { |t| [t.id, t] }.freeze

    def self.[](id) = ALL.fetch(id)
    def self.key?(id) = ALL.key?(id)
  end
end
