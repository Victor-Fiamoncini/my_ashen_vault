require_relative "test_helper"
require "tmpdir"

class TestRpg < Minitest::Test
  include AshenVault

  def test_gauge_refills_and_spend_returns_fill
    g = Gauge.new(2.0)
    assert_in_delta 1.0, g.spend
    g.update(1.0)
    assert_in_delta 0.5, g.value
    g.update(5.0)
    assert g.full?
  end

  def test_low_gauge_swings_are_weak
    full = Combat.damage(base: 8, strength: 6, gauge: 1.0, defense: 0)
    half = Combat.damage(base: 8, strength: 6, gauge: 0.5, defense: 0)
    empty = Combat.damage(base: 8, strength: 6, gauge: 0.0, defense: 0)
    assert_equal 11, full
    assert_operator half, :<, full / 2.0 + 1
    assert_operator empty, :>=, 1
  end

  def test_defense_never_drops_damage_below_one
    assert_equal 1, Combat.damage(base: 1, strength: 0, gauge: 0.1, defense: 50)
  end

  def test_level_up
    s = Stats.new
    gained = s.gain_exp(Stats.exp_for(1) + Stats.exp_for(2))
    assert_equal 2, gained
    assert_equal 3, s.level
    assert_equal s.max_hp, s.hp
    assert_equal 52, s.max_hp
  end

  def test_inventory_equip_and_buy
    inv = Inventory.new(gold: 200)
    assert inv.has?("rusted_sword")
    assert inv.buy("ashblade")
    assert_equal 20, inv.gold
    refute inv.buy("ringmail")
    assert inv.equip("ashblade")
    assert_equal 15, inv.weapon_item.power
    refute inv.equip("red_tonic")
  end

  def test_unequip_falls_back_to_fists_and_no_armor
    inv = Inventory.new
    refute inv.unequip("red_tonic")
    assert inv.unequip("rusted_sword")
    assert inv.unequip("padded_coat")
    assert_nil inv.weapon
    assert_equal Items::FISTS, inv.weapon_item
    assert_equal 0, inv.defense
    assert inv.has?("rusted_sword"), "unequipping keeps the item"
    assert inv.equip("rusted_sword")
    assert inv.equipped?("rusted_sword")

    restored = Inventory.from_h(Inventory.new(weapon: nil, armor: nil).to_h)
    assert_nil restored.weapon
    assert_nil restored.armor
  end

  def test_inventory_remove
    inv = Inventory.new
    inv.add("red_tonic", 2)
    assert inv.remove("red_tonic")
    assert_equal 1, inv.count("red_tonic")
    assert inv.remove("red_tonic")
    refute inv.has?("red_tonic")
    refute inv.remove("red_tonic")
  end

  def test_save_round_trip
    Dir.mktmpdir do |dir|
      saves = SaveSystem.new(File.join(dir, "save.json"))
      player = Player.new
      player.x = 3.5
      player.z = 7.25
      player.stats.gain_exp(100)
      player.inventory.add("red_tonic", 3)
      player.spells << "mend"
      saves.save(map: "harrowmere", player: player, flags: Set["chest:a"])

      map, loaded, flags = saves.load
      assert_equal "harrowmere", map
      assert_in_delta 7.25, loaded.z
      assert_equal player.stats.level, loaded.stats.level
      assert_equal 3, loaded.inventory.count("red_tonic")
      assert_equal %w[flame mend], loaded.spells
      assert_includes flags, "chest:a"
    end
  end

  def test_corrupt_save_returns_nil
    Dir.mktmpdir do |dir|
      path = File.join(dir, "save.json")
      File.write(path, "{nope")
      assert_nil SaveSystem.new(path).load
    end
  end

  def test_sprint_is_faster_and_holds_attack_gauge
    map = TestMaps.room
    x, z = TileMap.center(1, 2)
    walker = Player.new
    runner = Player.new
    [walker, runner].each { |p| p.place(x, z, 0.0, map) }
    walker.walk(map, 1, 0, 0.1)
    runner.walk(map, 1, 0, 0.1, sprint: true)
    assert_in_delta Player::SPRINT, (runner.x - x) / (walker.x - x), 1e-6
    assert runner.sprinting
    refute walker.sprinting

    runner.attack_gauge.spend
    runner.update_timers(0.5)
    assert_in_delta 0.0, runner.attack_gauge.value
    runner.walk(map, 0, 0, 0.1, sprint: true)
    refute runner.sprinting
    runner.update_timers(0.5)
    assert_operator runner.attack_gauge.value, :>, 0
  end
end
