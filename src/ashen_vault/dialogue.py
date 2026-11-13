"""NPC conversations. Each entry returns (speaker, lines, after) where `after`
is an optional callable run with the game when the conversation closes."""

from ashen_vault.world import relics

SHOPS = {
    "pell": [
        "red_tonic",
        "blue_moss",
        "scroll_mend",
        "leather_gloves",
        "oak_cudgel",
        "buckler",
        "hatchet",
        "leather_whip",
        "round_shield",
        "bastard_sword",
        "mace",
        "chain_mitts",
        "ringmail",
        "spiked_club",
        "ashblade",
        "lamellar_vest",
        "thornlash",
        "kite_shield",
        "iron_gauntlets",
        "bearded_axe",
        "brigandine",
        "zweihander",
        "tower_shield",
        "blackened_plate",
    ],
    "corvane": ["katana", "moonless_tachi", "nodachi"],
}
SHOP_NAMES = {"pell": "Pell's Goods", "corvane": "Corvane's Blades"}
CORVANE_LEVEL = 5  # the swordsmith won't speak to anyone greener than this


def for_npc(id_, game):
    flags = game.flags
    inv = game.player.inventory
    if id_ == "odrin":
        return odrin(game, flags, inv)
    if id_ == "pell":
        return "Pell", pell_lines(flags), lambda g: g.open_shop("pell")
    if id_ == "hollis":
        return "Hollis", hollis_lines(flags), None
    if id_ == "maeve":
        return maeve(game, flags)
    if id_ == "corvane":
        return corvane(game.player.stats.level, flags)
    return "Stranger", ["..."], None


def odrin(game, flags, inv):
    held = relics.held(inv.has)
    if len(held) == len(relics.ENDING_RELICS):
        return (
            "Odrin",
            [
                "Ember and leaf, both of them. I can feel the pair of them from here.",
                "Give them here. The bell will hold its note again.",
                "Listen. The ground has gone quiet already, and the roots are still.",
                "Harrowmere owes you more than it can pay. Rest now, wanderer.",
            ],
            lambda g: g.finish_game(),
        )
    if "quest" not in flags:

        def after(g):
            g.flags.add("quest")
            g.player.inventory.gold += 60
            g.player.inventory.add("red_tonic", 2)
            g.message("Received {60 gold} and {2 Red Tonics}.")

        return (
            "Odrin",
            [
                "A traveller off the morning boat? Then the tide has not taken all our luck.",
                "I keep the bell of Harrowmere. For three hundred years it has sung over the old keep below us.",
                "Last month the bell cracked, and two things began to stir beneath the town.",
                "Deep in the Sunken Keep the Ember Sigil sits in the Warden's hall. That is one.",
                "The other is the Verdant Sigil. Roots burst up through the house east of the square.",
                "Beneath it a green hollow has grown, and something large nests at the bottom of it.",
                "The bell needs both sigils to hold its note. Bring them back and the town will sleep again.",
                "Take these. They are all an old bell-keeper has.",
            ],
            after,
        )
    if held == ["ember_sigil"]:
        return (
            "Odrin",
            [
                "The Ember Sigil! Warm as a hearthstone. Hold on to it a little longer.",
                "The bell still needs its twin. Go through the overgrown house east of the square.",
                "The Verdant Sigil waits somewhere in the hollow beneath it.",
            ],
            None,
        )
    if held == ["verdant_sigil"]:
        return (
            "Odrin",
            [
                "Green glass with a leaf inside... the Verdant Sigil. Keep it close.",
                "Now the Ember Sigil. Climb down the well in the square and find the Warden's hall.",
            ],
            None,
        )
    lines = []
    if "boss_dead" in flags and "sigil_taken" not in flags:
        lines.append(
            "The Warden has fallen? Then the Ember Sigil should be lying in his hall. Bring it to me."
        )
    if "spider_dead" in flags and relics.get("verdant_sigil").taken_flag not in flags:
        lines.append("The thing in the hollow is dead? Then the Verdant Sigil lies in its nest. Fetch it.")
    if lines:
        return "Odrin", lines, None
    return (
        "Odrin",
        [
            "The well in the square leads down into the keep. The overgrown house leads down into the hollow.",
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
        lines = [
            "You opened the north gate? Then the stairs to the upper hall are clear.",
            "Watch for the floating embers up there. Keep moving and they'll miss.",
        ]
    else:
        lines = [
            "I'm meant to guard this well. Mostly I guard it from the inside.",
            "Down there a portcullis seals the stairs going north. There's a lever in the east cells.",
            "The cell door's locked, though. My brother dropped the key in the flooded cellar, west side.",
        ]
    if "spider_dead" not in flags:
        lines.append(
            "Mind the overgrown house to the east. Its door opens on a wood that shouldn't be there."
        )
        lines.append("The flowers in there bite, and the trees walk. Don't stand still near either.")
    return lines


def maeve(game, flags):
    if "maeve_gift" in flags:
        return "Maeve", ["The fish won't bite while the bell is quiet. Go on, then."], None

    def after(g):
        g.flags.add("maeve_gift")
        g.player.inventory.add("blue_moss", 2)
        g.message("Received {2 Blue Moss}.")

    return (
        "Maeve",
        [
            "You smell of dust and lamp oil. Going under, are you?",
            "My father told me the keep sank in a single night, with its knights still at their posts.",
            "Here, take some moss from the cliffs. Chew it when your spirit runs thin.",
        ],
        after,
    )


def corvane(level, flags):
    """A swordsmith from across the sea who lives apart from the town. Below CORVANE_LEVEL they will
    not even look up; after that they sell the curved blades of their homeland."""
    if level < CORVANE_LEVEL:
        return (
            "Hooded figure",
            [
                "...",
                "(They turn back to the whetstone. You are beneath their notice.)",
            ],
            None,
        )
    if "met_corvane" in flags:
        return "Corvane", ["You again. The steel is where it was. Choose."], lambda g: g.open_shop("corvane")

    def after(g):
        g.flags.add("met_corvane")
        g.open_shop("corvane")

    return (
        "Corvane",
        [
            "So. The one who walks in the keep and comes back up the well.",
            "I am Corvane. I left my island with three blades and a debt. The debt is paid.",
            "The blades are not for anyone with a purse. They are for hands that have learned to wait.",
            "A word, since you have earned one: hold the draw. Stand still, and let the blade decide.",
        ],
        after,
    )
