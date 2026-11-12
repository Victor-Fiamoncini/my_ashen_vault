module AshenVault
  Item = Struct.new(:id, :name, :kind, :price, :desc, :power, :reach, :speed, :heal, :mana, :spell,
                    keyword_init: true)

  module Items
    ALL = [
      Item.new(id: "rusted_sword", name: "Rusted Sword", kind: :weapon, price: 0, power: 8, reach: 2.1, speed: 1.4,
               desc: "Pitted and dull, but it still cuts."),
      Item.new(id: "ashblade", name: "Ashblade", kind: :weapon, price: 180, power: 15, reach: 2.4, speed: 1.7,
               desc: "Forged from the grey iron of the old keep."),
      Item.new(id: "padded_coat", name: "Padded Coat", kind: :armor, price: 0, power: 2,
               desc: "Quilted wool. Better than nothing."),
      Item.new(id: "ringmail", name: "Ringmail", kind: :armor, price: 140, power: 6,
               desc: "Linked iron rings, heavy on the shoulders."),
      Item.new(id: "red_tonic", name: "Red Tonic", kind: :consumable, price: 20, heal: 30,
               desc: "Bitter red draught. Restores 30 HP."),
      Item.new(id: "blue_moss", name: "Blue Moss", kind: :consumable, price: 25, mana: 15,
               desc: "Glowing moss from the cliffs. Restores 15 MP."),
      Item.new(id: "scroll_mend", name: "Scroll of Mend", kind: :scroll, price: 90, spell: "mend",
               desc: "Teaches the healing rite of Mend."),
      Item.new(id: "scroll_lumen", name: "Scroll of Lumen", kind: :scroll, price: 0, spell: "lumen",
               desc: "Teaches Lumen, a light that pushes back the dark."),
      Item.new(id: "cell_key", name: "Cell Key", kind: :key, price: 0, desc: "A small iron key, flaked with rust."),
      Item.new(id: "warden_key", name: "Warden's Key", kind: :key, price: 0, desc: "A heavy key stamped with a tower."),
      Item.new(id: "ember_sigil", name: "Ember Sigil", kind: :key, price: 0,
               desc: "A warm stone disc. The bell-keeper is waiting for it.")
    ].to_h { |i| [i.id, i] }.freeze

    # What you fight with when no weapon is equipped. Not an inventory item.
    FISTS = Item.new(id: "fists", name: "Bare Hands", kind: :weapon, price: 0, power: 3, reach: 1.6, speed: 0.9,
                     desc: "Your own two fists.")

    def self.[](id) = ALL.fetch(id)
  end
end
