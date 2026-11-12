"""NPC conversations. Each entry returns (speaker, lines, after) where `after`
is an optional callable run with the game when the conversation closes."""

SHOP = ["red_tonic", "blue_moss", "scroll_mend", "ashblade", "ringmail"]


def for_npc(id_, game):
    flags = game.flags
    inv = game.player.inventory
    if id_ == "odrin":
        return odrin(game, flags, inv)
    if id_ == "pell":
        return "Pell", pell_lines(flags), lambda g: g.open_shop()
    if id_ == "hollis":
        return "Hollis", hollis_lines(flags), None
    if id_ == "maeve":
        return maeve(game, flags)
    return "Stranger", ["..."], None


def odrin(game, flags, inv):
    if inv.has("ember_sigil"):
        return (
            "Odrin",
            [
                "That warmth... you carry the Ember Sigil.",
                "Give it here. The bell will hold its note again.",
                "Listen. The ground has gone quiet already.",
                "Harrowmere owes you more than it can pay. Rest now, wanderer.",
            ],
            lambda g: g.finish_game(),
        )
    if "quest" not in flags:

        def after(g):
            g.flags.add("quest")
            g.player.inventory.gold += 60
            g.player.inventory.add("red_tonic", 2)
            g.message("Received 60 gold and 2 Red Tonics.")

        return (
            "Odrin",
            [
                "A traveller off the morning boat? Then the tide has not taken all our luck.",
                "I keep the bell of Harrowmere. For three hundred years it has sung over the old keep below us.",
                "Last month the bell cracked, and something under the well began to stir.",
                "Deep in the Sunken Keep the Ember Sigil sits in the Warden's hall. It is what tunes the bell.",
                "Bring the Sigil back and the keep will sleep again.",
                "Take these. They are all an old bell-keeper has.",
            ],
            after,
        )
    if "boss_dead" in flags:
        return (
            "Odrin",
            ["The Warden has fallen? Then the Sigil should be lying in his hall. Bring it to me."],
            None,
        )
    return (
        "Odrin",
        [
            "The well in the square leads down into the keep.",
            "Save your strength at the stone shrines. The old wardens built them for travellers like you.",
        ],
        None,
    )


def pell_lines(flags):
    if "met_pell" in flags:
        return ["Back again? Take a look."]
    flags.add("met_pell")
    return [
        "Pell's goods. Most of it came in by boat, and the rest came up out of the well.",
        "Coin up front, mind you. Nobody hands out credit to folk going down that hole.",
    ]


def hollis_lines(flags):
    if "lever:north_lever" in flags:
        return [
            "You opened the north gate? Then the stairs to the upper hall are clear.",
            "Watch for the floating embers up there. Keep moving and they'll miss.",
        ]
    return [
        "I'm meant to guard this well. Mostly I guard it from the inside.",
        "Down there a portcullis seals the stairs going north. There's a lever in the east cells.",
        "The cell door's locked, though. My brother dropped the key in the flooded cellar, west side.",
    ]


def maeve(game, flags):
    if "maeve_gift" in flags:
        return "Maeve", ["The fish won't bite while the bell is quiet. Go on, then."], None

    def after(g):
        g.flags.add("maeve_gift")
        g.player.inventory.add("blue_moss", 2)
        g.message("Received 2 Blue Moss.")

    return (
        "Maeve",
        [
            "You smell of dust and lamp oil. Going under, are you?",
            "My father told me the keep sank in a single night, with its knights still at their posts.",
            "Here, take some moss from the cliffs. Chew it when your spirit runs thin.",
        ],
        after,
    )
