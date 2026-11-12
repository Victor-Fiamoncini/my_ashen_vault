require "minitest/autorun"
require_relative "../lib/ashen_vault/core"

module TestMaps
  ROOM = <<~MAP.freeze
    [meta]
    name = Test Room
    start = 1 1 0

    [legend]
    # = wall tex=stone_brick top=3
    . = floor h=0 ceil=3
    , = floor h=0.5 ceil=3
    ^ = floor h=1.5 ceil=3
    ~ = water h=-0.4

    [grid]
    ######
    #..,^#
    #.a..#
    #~...#
    ######

    [entities]
    a = bone_walker yaw=90
  MAP

  def self.room = AshenVault::MapLoader.new(ROOM, name: "room").parse
end
