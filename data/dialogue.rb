module AshenVault
  # NPC conversations. Each entry returns [speaker, lines, after] where `after`
  # is an optional lambda run when the conversation closes.
  module DialogueData
    module_function

    def for(id, game)
      flags = game.flags
      inv = game.player.inventory
      case id
      when "odrin" then odrin(game, flags, inv)
      when "pell" then ["Pell", pell_lines(flags), ->(g) { g.open_shop }]
      when "hollis" then ["Hollis", hollis_lines(flags), nil]
      when "maeve" then maeve(game, flags)
      else ["Stranger", ["..."], nil]
      end
    end

    def odrin(game, flags, inv)
      if inv.has?("ember_sigil")
        ["Odrin", [
          "That warmth... you carry the Ember Sigil.",
          "Give it here. The bell will hold its note again.",
          "Listen. The ground has gone quiet already.",
          "Harrowmere owes you more than it can pay. Rest now, wanderer."
        ], ->(g) { g.finish_game }]
      elsif !flags.include?("quest")
        ["Odrin", [
          "A traveller off the morning boat? Then the tide has not taken all our luck.",
          "I keep the bell of Harrowmere. For three hundred years it has sung over the old keep below us.",
          "Last month the bell cracked, and something under the well began to stir.",
          "Deep in the Sunken Keep the Ember Sigil sits in the Warden's hall. It is what tunes the bell.",
          "Bring the Sigil back and the keep will sleep again.",
          "Take these. They are all an old bell-keeper has."
        ], lambda { |g|
          g.flags << "quest"
          g.player.inventory.gold += 60
          g.player.inventory.add("red_tonic", 2)
          g.message("Received 60 gold and 2 Red Tonics.")
        }]
      elsif flags.include?("boss_dead")
        ["Odrin", ["The Warden has fallen? Then the Sigil should be lying in his hall. Bring it to me."], nil]
      else
        ["Odrin", [
          "The well in the square leads down into the keep.",
          "Save your strength at the stone shrines. The old wardens built them for travellers like you."
        ], nil]
      end
    end

    def pell_lines(flags)
      if flags.include?("met_pell")
        ["Back again? Take a look."]
      else
        flags << "met_pell"
        ["Pell's goods. Most of it came in by boat, and the rest came up out of the well.",
         "Coin up front, mind you. Nobody hands out credit to folk going down that hole."]
      end
    end

    def hollis_lines(flags)
      if flags.include?("lever:north_lever")
        ["You opened the north gate? Then the stairs to the upper hall are clear.",
         "Watch for the floating embers up there. Keep moving and they'll miss."]
      else
        ["I'm meant to guard this well. Mostly I guard it from the inside.",
         "Down there a portcullis seals the stairs going north. There's a lever in the east cells.",
         "The cell door's locked, though. My brother dropped the key in the flooded cellar, west side."]
      end
    end

    def maeve(game, flags)
      if flags.include?("maeve_gift")
        ["Maeve", ["The fish won't bite while the bell is quiet. Go on, then."], nil]
      else
        ["Maeve", [
          "You smell of dust and lamp oil. Going under, are you?",
          "My father told me the keep sank in a single night, with its knights still at their posts.",
          "Here, take some moss from the cliffs. Chew it when your spirit runs thin."
        ], lambda { |g|
          g.flags << "maeve_gift"
          g.player.inventory.add("blue_moss", 2)
          g.message("Received 2 Blue Moss.")
        }]
      end
    end

    SHOP = %w[red_tonic blue_moss scroll_mend ashblade ringmail].freeze
  end
end
