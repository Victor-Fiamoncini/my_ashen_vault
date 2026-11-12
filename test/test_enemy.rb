require_relative "test_helper"

class TestEnemy < Minitest::Test
  include AshenVault

  # Minimal world stub implementing the interface Enemy expects.
  class FakeWorld
    attr_accessor :player_x, :player_z, :visible, :strikes, :shots

    def initialize(px, pz)
      @player_x = px
      @player_z = pz
      @visible = true
      @strikes = 0
      @shots = 0
    end

    def player_alive? = true
    def can_see?(*) = @visible

    def move_enemy(enemy, dx, dz)
      enemy.x += dx
      enemy.z += dz
    end

    def enemy_strike(_enemy) = @strikes += 1
    def enemy_fire(_enemy) = @shots += 1
  end

  def tick(enemy, world, seconds, dt = 0.05)
    (seconds / dt).round.times { enemy.update(dt, world) }
  end

  def walker(x = 0.0, z = 0.0) = Enemy.new(EnemyTypes["bone_walker"], x, z, rng: Random.new(1))

  def test_notices_and_chases
    e = walker
    w = FakeWorld.new(8.0, 0.0)
    e.update(0.05, w)
    assert_equal :chase, e.state
    tick(e, w, 1.0)
    assert_operator e.x, :>, 1.0
  end

  def test_stays_idle_without_sight
    e = walker
    w = FakeWorld.new(5.0, 0.0)
    w.visible = false
    tick(e, w, 1.0)
    assert_equal :idle, e.state
  end

  def test_winds_up_then_strikes_once
    e = walker
    w = FakeWorld.new(1.0, 0.0)
    tick(e, w, 0.1)
    assert_equal :windup, e.state
    assert_equal 0, w.strikes
    tick(e, w, 1.0)
    assert_equal 1, w.strikes
  end

  def test_hit_staggers_and_interrupts_windup
    e = walker
    w = FakeWorld.new(1.0, 0.0)
    tick(e, w, 0.1)
    e.take_hit(3)
    assert_equal :hurt, e.state
    tick(e, w, 0.3)
    assert_equal 0, w.strikes
  end

  def test_boss_has_poise
    boss = Enemy.new(EnemyTypes["ashen_warden"], 0, 0)
    boss.take_hit(5)
    refute_equal :hurt, boss.state
    boss.take_hit(20)
    assert_equal :hurt, boss.state
  end

  def test_death
    e = walker
    assert e.take_hit(999)
    refute e.alive?
    tick(e, FakeWorld.new(1, 0), 2.0)
    assert e.gone?
  end

  def test_ranged_enemy_fires
    e = Enemy.new(EnemyTypes["cinder_wisp"], 0, 0)
    w = FakeWorld.new(6.0, 0.0)
    tick(e, w, 1.5)
    assert_equal 1, w.shots
  end
end
