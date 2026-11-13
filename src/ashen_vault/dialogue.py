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


# Odrin on each sigil: how it feels in your hand, where to find it, and where it lies once its
# keeper has fallen (the boss's dead flag) but nobody has picked it up.
SIGIL_HELD = {
    "ember_sigil": "The Ember Sigil! Warm as a hearthstone.",
    "verdant_sigil": "Green glass with a leaf inside... the Verdant Sigil.",
    "iron_sigil": "Black iron, cold as a grave... the Iron Sigil. Even the gargoyles could not keep it.",
}
SIGIL_HINT = {
    "ember_sigil": "The Ember Sigil waits in the Warden's hall. Climb down the well in the square.",
    "verdant_sigil": (
        "The Verdant Sigil is in the hollow. Follow the green trail east of the square to the cave. "
        "Take a light."
    ),
    "iron_sigil": (
        "The Iron Sigil is held in the Cinderhold. Take the north road and cross the long bridge over the fire."
    ),
}
SIGIL_FALLEN = {
    "ember_sigil": (
        "boss_dead",
        "The Warden has fallen? Then the Ember Sigil should be lying in his hall. Bring it to me.",
    ),
    "verdant_sigil": (
        "spider_dead",
        "The thing in the hollow is dead? Then the Verdant Sigil lies in its nest. Fetch it.",
    ),
    "iron_sigil": (
        "gargoyles_dead",
        "The gargoyles are broken? Then the Iron Sigil lies up on the Cinderhold's roof. Fetch it.",
    ),
}


def _sigil_lines(flags, held):
    """For each sigil you still lack: where it lies if its keeper is dead, else how to find it."""
    lines = []
    for item in relics.ENDING_RELICS:
        if item in held:
            continue
        flag, fallen = SIGIL_FALLEN[item]
        lines.append(
            fallen if flag in flags and relics.get(item).taken_flag not in flags else SIGIL_HINT[item]
        )
    return lines


def odrin(game, flags, inv):
    held = relics.held(inv.has)
    if len(held) == len(relics.ENDING_RELICS):
        return (
            "Odrin",
            [
                "Ember, leaf and iron, all three of them. I can feel them from here.",
                "Give them here. The bell will hold its note again.",
                "Listen. The ground has gone quiet already, the roots are still, and the forges are cooling.",
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
                "Last month the bell cracked, and three things began to stir around the town.",
                "Deep in the Sunken Keep the Ember Sigil sits in the Warden's hall. That is one.",
                "The other is the Verdant Sigil. A green trail has crept out of the square's east side.",
                "It ends at a cave, and beyond it a hollow has grown where no wood should be. Something nests there.",
                "The last is the Iron Sigil. Look north at night: the old fortress on the ridge glows again.",
                "They call it the Cinderhold. The north road and its long bridge lead there. Its forges are lit.",
                "The bell needs all three sigils to hold its note. Bring them back and the town will sleep again.",
                "Take these. They are all an old bell-keeper has.",
            ],
            after,
        )
    lines = _sigil_lines(flags, held)
    if held:
        felt = [SIGIL_HELD[i] for i in held]
        return "Odrin", [*felt, "Hold on to it a little longer. The bell still needs the rest.", *lines], None
    dead = [SIGIL_FALLEN[i][1] for i in relics.ENDING_RELICS if SIGIL_FALLEN[i][1] in lines]
    if dead:
        return "Odrin", dead, None
    return (
        "Odrin",
        [
            "The well in the square leads down into the keep. The green trail east leads to the hollow's cave.",
            "The north road climbs to the Cinderhold. Its bridge crosses a gorge of fire.",
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
            "Mind the green trail to the east. The cave at its end opens on a wood that shouldn't be there."
        )
        lines.append("The flowers in there bite, and the trees walk. Don't stand still near either.")
    if "gargoyles_dead" not in flags:
        lines.append("The north road's open again. Folk say the fortress on the ridge has its forges lit.")
        lines.append("Iron men walk its walls, and something on the roof watches the bridge. Bring a shield.")
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
