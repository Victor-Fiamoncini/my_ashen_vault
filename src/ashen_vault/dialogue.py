"""NPC conversations. Each entry returns (speaker, lines, after) where `after`
is an optional callable run with the game when the conversation closes."""

from ashen_vault.world import relics

SHOPS = {
    # Pell deals in what came in by boat or up out of the well: scrolls and odd salvage.
    "pell": ["scroll_mend", "leather_whip", "ashblade", "thornlash"],
    # Brannoc forges the rest: honest steel, shields and armour.
    "brannoc": [
        "leather_gloves",
        "oak_cudgel",
        "buckler",
        "hatchet",
        "round_shield",
        "bastard_sword",
        "mace",
        "chain_mitts",
        "ringmail",
        "spiked_club",
        "lamellar_vest",
        "kite_shield",
        "iron_gauntlets",
        "bearded_axe",
        "brigandine",
        "zweihander",
        "tower_shield",
        "blackened_plate",
    ],
    "tamsin": ["red_tonic", "blue_moss"],
    "corvane": ["katana", "moonless_tachi", "nodachi"],
}
SHOP_NAMES = {
    "pell": "Pell's Goods",
    "brannoc": "Brannoc's Forge",
    "tamsin": "Tamsin's Remedies",
    "corvane": "Corvane's Blades",
}
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
    if id_ in GIFTS:
        return gift_giver(id_, flags)
    if id_ == "wren":
        return "Wren", wren_lines(flags), None
    if id_ == "enthroned":
        return "The Enthroned", enthroned_lines(relics.held(inv.has)), None
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


# Villagers who hand a newcomer something once: (speaker, items, first meeting, after the gift, shop).
GIFTS = {
    "brannoc": (
        "Brannoc",
        {"hatchet": 1},
        [
            "Mind the sparks. Brannoc, smith of Harrowmere, for my sins.",
            "You're going down that well with a rusted sword? No. Take this hatchet. It bites.",
            "When you've coin, come back. Everything I sell, I forged on this anvil.",
        ],
        ["Steel doesn't sharpen itself. What'll it be?"],
        "brannoc",
    ),
    "garrick": (
        "Garrick",
        {"buckler": 1},
        [
            "Halt. ...Ah, the one off the boat. Captain Garrick, of what's left of the watch.",
            "Six of us once. Now it's me and Hollis, and Hollis guards the well from the inside.",
            "Here, a buckler from the watch stores. Catch the blow, then answer it.",
        ],
        [
            "The trail east goes green and dark. The road north goes red. Pick your poison.",
            "Raise that buckler before the blow, not after.",
        ],
        None,
    ),
    "tamsin": (
        "Tamsin",
        {"red_tonic": 2, "blue_moss": 1},
        [
            "Careful of the pot, it's half boiled down. I'm Tamsin. I mend what the dark breaks.",
            "Take these, a first dose on the house. Nobody walks out of the well on their own legs twice.",
            "After that, I'm afraid herbs cost coin like anything else.",
        ],
        ["Back in one piece? Mostly? Let's see what you need."],
        "tamsin",
    ),
    "ilse": (
        "Sister Ilse",
        {"scroll_lumen": 1},
        [
            "Be welcome under this roof, traveller. I am Ilse. I tend the candles, and the one who sits above.",
            "The Enthroned was old when the bell was cast. They have not spoken plainly in my lifetime.",
            "Take this scroll. Read it, and a little light will walk with you where none should be.",
        ],
        [
            "The candles burn lower each night the bell is silent.",
            "If the Enthroned speaks to you, remember every word. I will want to hear them.",
        ],
        None,
    ),
}


def _received(items):
    from ashen_vault.player.items import Items

    parts = []
    for item, n in items.items():
        name = Items.get(item).name
        parts.append(f"{{{n} {name}s}}" if n > 1 else f"{{{name}}}")
    return "Received " + " and ".join(parts) + "."


def gift_giver(id_, flags):
    """A villager who gives a newcomer something on first meeting, then sells their wares (if any)."""
    speaker, items, first, later, shop = GIFTS[id_]
    flag = f"gift:{id_}"
    opens = (lambda g: g.open_shop(shop)) if shop else None
    if flag in flags:
        return speaker, later, opens

    def after(g):
        g.flags.add(flag)
        for item, n in items.items():
            g.player.inventory.add(item, n)
        g.message(_received(items))
        if shop:
            g.open_shop(shop)

    return speaker, first, after


def wren_lines(flags):
    if "met_wren" in flags:
        return [
            "The cellar's dry and the ale's wet. That's all an inn can promise these days.",
            "Folk sleep badly since the bell went quiet. They say they dream of a long hall and a chair.",
        ]
    flags.add("met_wren")
    return [
        "Welcome to the Drowned Lantern. I'm Wren. Rooms are cheap, since nobody's travelling.",
        "You'll have seen the bell in the square. The Silent Bell, we call it now. It cracked one still night.",
        "No wind, no storm. Just a sound like a breath let out, and then nothing.",
        "Since then: the keep below wakes, a wood grows in a cave, the old fortress north is lit again.",
        "Three roads out of Harrowmere, and every one of them gone bad.",
    ]


ENTHRONED_LINES = (
    [
        "(The figure on the throne does not move. Dust lies on its hands.)",
        "...a stranger... the tide brings them... as it brought us...",
    ],
    [
        "(Something stirs beneath the cowl. Two cold glints turn toward you.)",
        "...one note... I hear one note again... faint...",
    ],
    [
        "(The Enthroned's fingers tighten on the stone.)",
        "...two... the bell remembers its shape... it remembers us...",
    ],
    [
        "(The air in the nave grows heavy. The candles bend toward the throne.)",
        "...all three... take them to the keeper... and the bell will wake... and so... shall I...",
    ],
)


def enthroned_lines(held):
    """The Enthroned stirs a little more with each sigil you carry."""
    return list(ENTHRONED_LINES[min(len(held), len(ENTHRONED_LINES) - 1)])
