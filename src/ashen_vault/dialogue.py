"""NPC conversations. Each entry returns (speaker, lines, after) where `after`
is an optional callable run with the game when the conversation closes."""

from ashen_vault.player import stash
from ashen_vault.world import loot, relics

SHOPS = {
    # Pell deals in what came in by boat or up out of the well: scrolls and odd salvage.
    "pell": ["scroll_mend", "leather_whip", "ashblade", "thornlash"],
    # Brannoc forges the rest: honest steel, shields and armour.
    "brannoc": [
        "menders_kit",
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
    "tamsin": ["red_tonic", "blue_moss", "bitter_root", "clotting_salve", "grave_lily", "ember_draught"],
    "corvane": ["katana", "moonless_tachi", "nodachi"],
    # Ysolde Vane, in the Oubliette under Old Harrowmere: the two spells she copied off the vault's rift.
    "ysolde": ["scroll_rift_lance", "scroll_bellward", "blue_moss"],
}
SHOP_NAMES = {
    "pell": "Pell's Goods",
    "brannoc": "Brannoc's Forge",
    "tamsin": "Tamsin's Remedies",
    "corvane": "Corvane's Blades",
    "ysolde": "Ysolde's Copies",
}
REPAIRERS = {"brannoc"}  # smiths whose shop opens with a "Mend gear" row (`Game` scene "repair")
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
    if id_ in WATCH:
        name, lines = WATCH[id_]
        return name, lines(flags), None
    if id_ == "maeve":
        return maeve(game, flags)
    if id_ == "corvane":
        return corvane(game.player.stats.level, flags)
    if id_ == "marrow":
        return marrow(flags)
    if id_ in GIFTS:
        return gift_giver(id_, flags)
    if id_ == "wren":
        return "Wren", wren_lines(flags), None
    if id_ == "aubel":
        return "Aubel the Ringer", aubel_lines(flags), None
    if id_ == "coldry":
        return "Sister Coldry", coldry_lines(flags), None
    if id_ == "ysolde":
        return ysolde(flags)
    if id_ == "enthroned":
        return "The Enthroned", enthroned_lines(relics.held(inv.has)), None
    return "Stranger", ["..."], None


# Odrin on each sigil: how it feels in your hand, where to find it, and where it lies once its
# keeper has fallen (the boss's dead flag) but nobody has picked it up.
SIGIL_HELD = {
    "ember_sigil": "The Ember Sigil! Warm as a hearthstone.",
    "verdant_sigil": "Green glass with a leaf inside... the Verdant Sigil.",
    "iron_sigil": "Black iron, cold as a grave... the Iron Sigil. Even the gargoyles could not keep it.",
    "argent_sigil": "Silver, and cold as moonlight on frost... the Argent Sigil. So Ilvane let it go at last.",
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
    "argent_sigil": (
        "The Argent Sigil is in Vesperholm. Climb the cathedral steps: the Vesper Gate at their head stands open."
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
    "argent_sigil": (
        "duchess_dead",
        "The Duchess has fallen? Then the Argent Sigil lies in her choir, under the moon. Bring it home.",
    ),
}


def _sigil_lines(flags, held):
    """For each sigil you still lack: where it lies if its keeper is dead, else how to find it."""
    lines = []
    for item in relics.ENDING_RELICS:
        if item in held:
            continue
        flag, fallen = SIGIL_FALLEN[item]
        if flag in flags and relics.get(item).taken_flag not in flags:
            lines.append(fallen)
        else:
            lines.append(SIGIL_HINT[item])
    return lines


def odrin(game, flags, inv):
    held = relics.held(inv.has)
    if len(held) == len(relics.ENDING_RELICS):
        return (
            "Odrin",
            [
                "Ember, leaf, iron... and silver. All four. I never thought to hold them in these hands.",
                "Give them here. Listen: the ground is quiet, the roots are still, the forges are cooling.",
                "And over Vesperholm the moon is going down, for the first time since the king turned to stone.",
                "His sister Ilvane wed the moon on the fourth sigil, so that her city would never see a death.",
                "But the moon keeps all it shines on as it is: her people as shades, her brother as stone.",
                "It was him at the rope, wasn't it? From inside the stone. The moon keeps the living. Not ash.",
                "Up on the hill the stone is cracking open. Harrowmere owes you more than it can pay. Rest now, Ashen.",
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
                "Grey as hearth-ash, and walking. So the bell has called another of you.",
                "You heard it in the grave, didn't you? One toll over the town. No hand was on the rope.",
                "Who rang it, I cannot tell you. No one in Harrowmere has touched that rope in years.",
                "I am Odrin. I kept that bell, once. Now I keep a prophecy older than the bell.",
                "Whoever wakes to the bell must win the four sigils, and the king on the stone throne shall rise.",
                "The Enthroned. Our king, turned to stone in his chair in the cathedral, longer than anyone remembers.",
                "You are not the first to wake. The cemetery you climbed out of is full of the ones who failed.",
                "Deep in the Abandoned Prison the Ember Sigil sits in the Warden's hall. That is one.",
                "The next is the Verdant Sigil. A green trail has crept out of the square's east side.",
                "It ends at a cave, and beyond it a hollow has grown where no wood should be. Something nests there.",
                "Then the Iron Sigil. Look north at night: the old fortress on the ridge glows again.",
                "They call it the Cinderhold. The north road and its long bridge lead there. Its forges are lit.",
                "The fourth is the Argent Sigil. At the head of the cathedral steps the Vesper Gate stands open.",
                "Beyond it lies Vesperholm, the Moonbound City. Nobody remembers the gate shut, nor who opened it.",
                "Take these. They are all an old bell-keeper has.",
            ],
            after,
        )
    lines = _sigil_lines(flags, held)
    if held:
        felt = [SIGIL_HELD[i] for i in held]
        return "Odrin", [*felt, "Keep it close. The king will need every one of them.", *lines], None
    dead = [SIGIL_FALLEN[i][1] for i in relics.ENDING_RELICS if SIGIL_FALLEN[i][1] in lines]
    if dead:
        return "Odrin", dead, None
    return (
        "Odrin",
        [
            "The well in the square leads down into the old prison. The green trail east leads to the hollow's cave.",
            "The north road climbs to the Cinderhold. Its bridge crosses a gorge of fire.",
            "The cathedral steps climb to the Vesper Gate. It stands open on Vesperholm, under the moon.",
            "Save your strength at the stone shrines. The old wardens built them for the Ashen. Many knelt there.",
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


def north_gate_lines(flags):
    if "gargoyles_dead" in flags:
        return [
            "The fires on the ridge burn low now. Carters are asking about the road again.",
            "I tell them to wait. Iron men don't always know when they're beaten.",
        ]
    return [
        "The north road. It climbs to the Cinderhold, the fortress on the ridge.",
        "Past the long bridge the ground runs with fire. Mind your feet and keep off the edges.",
        "Iron bowmen walk the walls. Close on them fast, or bring a shield.",
    ]


def north_gate_second_lines(flags):
    if "gargoyles_dead" in flags:
        return ["Sergeant says we can stand easy. I'll stand easy when the smoke stops."]
    return [
        "Nobody's come back down that road since the forges were lit again.",
        "If you're going up, go before the smoke thickens. It's worse after dark.",
    ]


def east_gap_lines(flags):
    if "spider_dead" in flags:
        return [
            "The trail's quiet. No more silk in the hedges, and the flowers keep to themselves.",
            "Whatever you killed in that hollow, the whole wood breathed out when it died.",
        ]
    return [
        "The green trail. It wasn't there when I was a girl. Now it runs to a cave full of jungle.",
        "Take a light. Past the cave mouth the dark is thick enough to lose your hand in.",
    ]


def west_gate_lines(flags):
    lines = [
        "The cemetery gate. It opens one way only: out. Nobody's walked back in.",
        "You came through it, didn't you? Grey as the ash. You're not the first I've seen.",
    ]
    if "quest" not in flags:
        lines.append("Old Odrin by the bell will want a word with you. Up the lane, in the square.")
    return lines


WATCH = {  # the town watch at its gates: (name, lines)
    "aldous": ("Sergeant Aldous", north_gate_lines),
    "tobin": ("Tobin", north_gate_second_lines),
    "reyna": ("Reyna", east_gap_lines),
    "fenn": ("Old Fenn", west_gate_lines),
}


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
            "My father told me the prison was shut in a single night, with its gaolers and its prisoners still inside.",
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
            "So. The one who walks in the prison and comes back up the well.",
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
        {"hatchet": 1, "menders_kit": 2},
        [
            "Mind the sparks. Brannoc, smith of Harrowmere, for my sins.",
            "You're going down that well with a rusted sword? No. Take this hatchet. It bites.",
            "And two mender's kits. Steel dulls, straps tear, plate splits. Mend it before it fails you.",
            "When you've coin, come back. Everything I sell, I forged on this anvil, and I mend what I sell.",
        ],
        ["Steel doesn't sharpen itself. What'll it be? A blade, or one mended?"],
        "brannoc",
    ),
    "garrick": (
        "Garrick",
        {"buckler": 1},
        [
            "Halt. ...Grey skin, ash on your boots. Another one up from the cemetery. Captain Garrick, of the watch.",
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
    "marrow": (
        "Brother Marrow",
        {"red_tonic": 2},
        [
            "The bars... they're up. You came back for an old man. The old gods never once did.",
            "I kept these under the straw. Tonics, from a gaoler who still had a conscience. Take them.",
            "I'll stay a while. Someone should pray in this place who isn't made to.",
        ],
        [
            "The Warden walks the hall above the antechamber. He was a man once. Remember that, and strike.",
            "Their chapel is quiet now. Mind the ones still kneeling in it.",
        ],
        None,
    ),
    "ilse": (
        "Sister Ilse",
        {"scroll_lumen": 1},
        [
            "Be welcome under this roof, traveller. I am Ilse. I tend the candles, and the one who sits above.",
            "The Enthroned, our king, was old when the bell was cast. Not a plain word from the throne in my life.",
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
        spare = 0
        for item, n in items.items():
            kept, gold = loot.claim(g.player.inventory, stash.known_spells(g.player), item, g.player.stash)
            if kept:
                g.player.inventory.add(kept, n)
            spare += gold
        g.player.inventory.gold += spare
        g.message(_received(items))
        if spare:
            g.message(loot.spare_message(spare))
        if shop:
            g.open_shop(shop)

    return speaker, first, after


MARROW_FREED = "lever:marrow_cell"  # his cell's lever, in the warders' quarters


def marrow(flags):
    """Brother Marrow, a lay brother of the prison's chapel jailed for refusing its rites. Through the
    bars he tells you where the Warden's Key lies and where his cell's lever is; once you have let him
    out, he gives what he hid in his cell (a gift, like the villagers')."""
    if MARROW_FREED in flags:
        return gift_giver("marrow", flags)
    return (
        "Brother Marrow",
        [
            "...A light. Not a gaoler's. You are one of the Ashen, then. Come closer. These bars won't bite.",
            "I am Marrow. I was a brother of this prison's chapel, until I would not make them kneel.",
            "The wardens gave the prisoners to the old gods: no names, no faces, only hands held out.",
            "The Warden's Key lies on their altar, past the end of this corridor. Their chapel keeps it now.",
            "My cell's lever is in the warders' quarters, beyond the locked door. If you find a way in...",
        ],
        None,
    )


# --- the Bell-keepers' Oubliette, under Old Harrowmere --------------------------------------------

OUBLIETTE_OPEN = "lever:oubliette"  # the gaoler's lever, at the end of the Oubliette's hall
KEYSTONE_DEAD = "keystone_dead"


def aubel_lines(flags):
    """Aubel the Ringer, who rang the old city's third bell: he tells how the first Harrowmere was raised
    on the sleeping Keystone and sank when its bells fell silent, and, once you have opened his cell,
    how the two roads of light below the plaza work."""
    if KEYSTONE_DEAD in flags:
        return [
            "The Keystone lies still. I felt it in my teeth, like the last toll of a bell.",
            "Whatever woke you, Ashen, it rang from up above. Down here there is nothing left to ring.",
        ]
    if OUBLIETTE_OPEN in flags:
        return [
            "Free legs, after all these years. They still remember the way to the bell.",
            "Below the plaza the masons left two roads of light over the chasm. Only one stands at a time.",
            "Strike a ward-stone and the road you walk on fades while the other wakes. Mind your feet.",
            "Find the order and the Keystone's court is yours. Choose badly and the chasm keeps you.",
        ]
    return [
        "Ah... footsteps that don't drag. You're no sexton. Come to the bars, Ashen.",
        "I am Aubel. I rang the third bell of the old city, before the city went down into the dark.",
        "They raised Harrowmere on a sleeping giant. The Keystone, we called him. Our bells kept him dreaming.",
        "When the bells fell silent the ground shrugged, and the whole city slid into this cavern.",
        "The gaoler keeps the cell lever at the end of the hall. Pull it, and I'll tell you of the roads.",
    ]


def coldry_lines(flags):
    """Sister Coldry, the last of the masons who laid the first city and spelled its ward-stones: she
    chose her chains, and tells why the roads to the Keystone were built to stand one at a time."""
    if KEYSTONE_DEAD in flags:
        return [
            "So the stone is broken. The mortar can rest, and so can I.",
            "Take nothing from his court you would not carry up the lift. The gallery is long and dark.",
        ]
    if "met_coldry" in flags:
        return [
            "The roads remember the masons' craft. They do not remember mercy.",
            "Two roads, three stones. Walk one, wake the other. That is all the craft there is.",
        ]
    flags.add("met_coldry")
    return [
        "Do not pity the chains. I asked for them.",
        "I am Coldry, of the Sisters of the Mortar. We laid every stone the first city stood on.",
        "We cut the ward-stones too, and spelled two roads, so no army could cross to the Keystone in one march.",
        "When the city sank, the gaolers locked away everyone who knew the way. I am the last of us.",
        "The sextons still ring for him. Every toll a little louder. He is waking, and he is angry.",
    ]


def ysolde(flags):
    """Ysolde Vane, a scholar jailed for copying what the daylight writes on the vault round its rift.
    Through the bars she only talks; once the gaoler's lever has opened her cell she sells her copies."""
    if OUBLIETTE_OPEN not in flags:
        return (
            "Ysolde Vane",
            [
                "Careful. The light in here is mine, and I had to steal it.",
                "Ysolde Vane, scholar of the rift. They jailed me for copying what the daylight writes on the vault.",
                "Pull the gaoler's lever and I'll sell you what I copied. Two spells, and nobody else alive knows them.",
            ],
            None,
        )
    if "met_ysolde" in flags:
        return "Ysolde Vane", ["The rift writes, I copy. Choose."], lambda g: g.open_shop("ysolde")

    def after(g):
        g.flags.add("met_ysolde")
        g.open_shop("ysolde")

    return (
        "Ysolde Vane",
        [
            "Free, and nowhere to go but further into the dark. Very well: business.",
            "A lance of the rift's own daylight, and a bell that nobody rings. Both copied true.",
        ],
        after,
    )


def wren_lines(flags):
    if "met_wren" in flags:
        return [
            "The cellar's dry and the ale's wet. That's all an inn can promise these days.",
            "Folk sleep badly since the bell rang. They say they dream of a long hall and a chair.",
        ]
    flags.add("met_wren")
    return [
        "Welcome to the Drowned Lantern. I'm Wren. Rooms are cheap, since nobody's travelling.",
        "You'll have seen the bell in the square. The Silent Bell, we call it. Cracked, and dumb for years.",
        "Then one still night it rang. Once. No wind, no storm, and nobody at the rope.",
        "Since then: the prison below wakes, a wood grows in a cave, the old fortress north is lit again.",
        "Three roads out of Harrowmere, and every one of them gone bad.",
    ]


# The Enthroned, one stage for each sigil you carry. The story they come to: the four sigils were the
# realm's four seals, and the king held them. His sister, Duchess Ilvane of Vesperholm, wed the moon on
# the fourth so her city would never see a dawn or a death; the moon keeps whatever it shines on as it
# is, and it kept her brother too, as stone on his throne. With the fourth bent to the moon the other
# three fell to keepers who went bad. The bell is the king's own voice: from inside the stone he rang it
# once, to wake the Ashen, the dead the moon cannot keep, to win the sigils back.
ENTHRONED_LINES = (
    [
        "(The king on the throne is stone, grey and cracked. Dust lies thick on his hands and his crown.)",
        "...ash again... the bell calls them... as it called the others...",
    ],
    [
        "(A hairline crack runs through the stone face. Something whispers from within it.)",
        "...one... I feel one... warm, far below the stone...",
    ],
    [
        "(Grit trickles from the stone fingers, as if they had tried to tighten on the arms.)",
        "...two... the bell remembers its shape... it remembers its king...",
    ],
    [
        "(The air in the nave grows heavy. The candles bend toward the statue, and the stone is warm.)",
        "...three... and the fourth... beyond the pale gate... my sister... she would not let the night end...",
        "...the moon keeps what it shines on... it kept her city... and it kept me...",
    ],
    [
        "(A shard of stone falls from the king's cheek. Under it the skin is grey and warm.)",
        "...four... the moon lets go... it was I who rang the bell... the only voice the stone left me...",
        "...the moon keeps the living... it cannot keep ash... take them to the bell-keeper... and I shall wake...",
    ],
)


def enthroned_lines(held):
    """The petrified Enthroned whispers from the stone, and stirs a little more with each sigil you
    carry."""
    return list(ENTHRONED_LINES[min(len(held), len(ENTHRONED_LINES) - 1)])
