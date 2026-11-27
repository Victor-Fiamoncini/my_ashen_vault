"""NPC conversations. Each entry returns (speaker, lines, after) where `after`
is an optional callable run with the game when the conversation closes."""

from ashen_vault.player import stash
from ashen_vault.world import loot, relics

SHOPS = {
    # Pell deals in what came in by boat or up out of the gaol's pit: scrolls and odd salvage.
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
    "tamsin": [
        "red_tonic",
        "blue_moss",
        "bitter_root",
        "clotting_salve",
        "grave_lily",
        "ember_draught",
        "hearth_ash",
    ],
    "corvane": ["katana", "moonless_tachi", "nodachi"],
    # Ysolde Vane, in the Oubliette under Old Harrowmere: the two spells she copied off the vault's rift.
    "ysolde": ["scroll_rift_lance", "scroll_bellward", "blue_moss"],
    # Gaoler Brannick, in the Under-Cells below it: the gaolers' stores, heavy things for breaking stone.
    "brannick": ["mace", "spiked_club", "war_hammer", "red_tonic", "clotting_salve", "menders_kit"],
}
SHOP_NAMES = {
    "pell": "Pell's Goods",
    "brannoc": "Brannoc's Forge",
    "tamsin": "Tamsin's Remedies",
    "corvane": "Corvane's Blades",
    "ysolde": "Ysolde's Copies",
    "brannick": "Brannick's Stores",
}
# Stock a shop adds once a save flag is set: shop -> (flag, items). Once the mortar-light is quenched
# the gaolers' frozen stores open, and Ysolde shelves what she finds there beside her copies.
SHOP_EXTRAS = {
    "tamsin": ("visited_sallow_fen", ["fenbane"]),
    "ysolde": ("core_quenched:old_harrowmere", ["menders_kit", "red_tonic", "clotting_salve", "grave_lily"]),
}
REPAIRERS = {"brannoc"}  # smiths whose shop opens with a "Mend gear" row (`Game` scene "repair")
CORVANE_LEVEL = 5  # the swordsmith won't speak to anyone greener than this


def shop_stock(shop_id, flags):
    """Every item a shop offers with these save flags: its stock, plus any extras it has earned."""
    stock = list(SHOPS[shop_id])
    if shop_id in SHOP_EXTRAS:
        flag, extras = SHOP_EXTRAS[shop_id]
        if flag in flags:
            stock += [i for i in extras if i not in stock]
    return stock


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
    if id_ in TOWNSFOLK:
        name, lines = TOWNSFOLK[id_]
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
        return aubel(flags)
    if id_ == "coldry":
        return coldry(flags)
    if id_ == "ysolde":
        return ysolde(flags)
    if id_ == "brannick":
        return brannick(flags)
    if id_ == "sister_vell":
        return sister_vell(flags)
    if id_ == "enthroned":
        return "The Enthroned", enthroned_lines(relics.held(inv.has)), None
    return "Stranger", ["..."], None


# Odrin on each sigil: how it feels in your hand, where to find it, and where it lies once its
# keeper has fallen (the boss's dead flag) but nobody has picked it up.
SIGIL_HELD = {
    "ember_sigil": "The Ember Sigil! Warm as a hearthstone.",
    "verdant_sigil": "Green glass with a leaf inside... the Verdant Sigil.",
    "iron_sigil": "Black iron, cold as a grave... the Iron Sigil. Even the gargoyles could not keep it.",
    "argent_sigil": "Silver, and cold as moonlight on frost... the Argent Sigil. Out of the old god's own hands, was it?",
    "auric_sigil": "Gold, and warm as a living hand... the Auric Sigil. That one was never the king's.",
}
SIGIL_HINT = {
    "ember_sigil": "The Ember Sigil waits in the Warden's hall. Climb down through the gaol's grate, in its yard off the west avenue.",
    "verdant_sigil": (
        "The Verdant Sigil is in the hollow. Go out by the east gate and follow the green trail to the cave. "
        "Take a light."
    ),
    "iron_sigil": (
        "The Iron Sigil is held in the Cinderhold. Take the north road and cross the long bridge over the fire."
    ),
    "argent_sigil": (
        "The Argent Sigil is in Vesperholm. Go up the Vesper street: the Vesper Gate at its head stands open."
    ),
    "auric_sigil": (
        "The Auric Sigil is on the Hollow Peak, with Herran. Lift the Argent Sigil from Lyra's hands "
        "in Vesperholm, and pass the portal behind her."
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
        (
            "The Duchess has fallen? Then the Argent Sigil lies on Lyra's altar, up past her choir. "
            "Bring it home."
        ),
    ),
    "auric_sigil": (
        "herran_dead",
        "Herran has fallen? Then the Auric Sigil lies in his theatre, at the top of his keep. Bring it down.",
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


# Set once Odrin has seen every sigil of the prophecy in your hands: the Silent Bell is unsealed, and
# ringing it (`bell`) ends the game. You keep the sigils until then: the Enthroned and Odrin both count
# the ones you carry. TODO(story): the descent below the bell will take the ending's place.
BELL_UNSEALED = "bell_unsealed"


def bell(flags, held):
    """What touching the Silent Bell says, and whether it rings out and ends the game: only once Odrin
    has unsealed it and you still carry every sigil."""
    if BELL_UNSEALED in flags and len(held) == len(relics.ENDING_RELICS):
        return ["The sigils burn in your hands, and the cracked bronze swings at your touch."], True
    if BELL_UNSEALED in flags:
        return ["The bell will not swing. It wants every sigil in the hand that rings it."], False
    return [
        "The cracked bronze is cold, yet it hums under your palm.",
        "A whisper rises from the stones: {the secret lies below}.",
    ], False


def odrin(game, flags, inv):
    held = relics.held(inv.has)
    if len(held) == len(relics.ENDING_RELICS):
        if BELL_UNSEALED in flags:
            return (
                "Odrin",
                ["Go on, Ashen. The bell is waiting on the plaza. Ring it with the sigils in your hand."],
                None,
            )
        return (
            "Odrin",
            [
                "Ember, leaf, iron, silver... and gold. All five. I never thought to see them in one hand.",
                "Listen: the ground is quiet, the roots are still, the forges are cooling.",
                "And over Vesperholm the moon is going down, for the first time since the king turned to stone.",
                "His sister Ilvane wed the moon on the fourth sigil, so that her city would never see a death.",
                "And Herran, her brother, bent the fifth to his own flesh. Lyra's children, the both of them.",
                "But the moon keeps all it shines on as it is: her people as shades, the king as stone.",
                "It was him at the rope, wasn't it? From inside the stone. The moon keeps the living. Not ash.",
                "Keep them. The prophecy never said to give them to me. The bell was sealed with all five.",
                "Go down to the plaza and ring the Silent Bell with the sigils in your hand.",
            ],
            lambda g: g.flags.add(BELL_UNSEALED),
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
                "Whoever wakes to the bell must win the five sigils, and the king on the stone throne shall rise.",
                "The Enthroned. Our king, turned to stone in his chair in the cathedral, longer than anyone remembers.",
                "You are not the first to wake. The cemetery you climbed out of is full of the ones who failed.",
                "Deep in the Abandoned Prison the Ember Sigil sits in the Warden's hall. That is one.",
                "The next is the Verdant Sigil. A green trail has crept up to the east gate.",
                "It ends at a cave, and beyond it a hollow has grown where no wood should be. Something nests there.",
                "Then the Iron Sigil. Look north at night: the old fortress on the ridge glows again.",
                "They call it the Cinderhold. The north road and its long bridge lead there. Its forges are lit.",
                "The fourth is the Argent Sigil. At the head of the Vesper street the Vesper Gate stands open.",
                "Beyond it lies Vesperholm, the Moonbound City. Nobody remembers the gate shut, nor who opened it.",
                "The fifth, the Auric Sigil, was never the king's. Herran keeps it, in his castle on the Hollow Peak.",
                "Lyra's altar in Vesperholm holds the Argent Sigil. Take it up, and the way to him will show itself.",
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
            "The grate in the gaol yard leads down into the old prison. The green trail east leads to the hollow's cave.",
            "The north road climbs to the Cinderhold. Its bridge crosses a gorge of fire.",
            "The Vesper street runs up to the Vesper Gate. It stands open on Vesperholm, under the moon.",
            "In Lyra's chapel above Vesperholm, a portal opens to Herran's castle on the mountain.",
            "Save your strength at the stone shrines. The old wardens built them for the Ashen. Many knelt there.",
        ],
        None,
    )


def pell_lines(flags):
    if "met_pell" in flags:
        return ["Back again? Take a look."]
    flags.add("met_pell")
    return [
        "Pell's goods. Most of it came in by boat, and the rest came up out of the gaol's pit.",
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
            "I'm meant to guard this grate. Mostly I guard it from the inside.",
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
        lines.append("Old Odrin by the bell will want a word with you. Down the avenue, on the plaza.")
    return lines


def vesper_gate_lines(flags):
    """Corporal Wynn, at the Vesper Gate: the cold road beyond it, and how many of the three
    sigils this side of the wall you have won back."""
    if "duchess_dead" in flags:
        return [
            "No frost on the gate's sill tonight. First time in all my watches I've not had to chip it off.",
            "Whatever you did in Vesperholm, the moon sits lower over the wall. I'd swear to it.",
        ]
    lines = [
        "The Vesper Gate. Nobody in the watch remembers it shut, and nobody remembers who opened it.",
        "The road past it runs cold all the way to Vesperholm. The moon hangs over that city and never sets.",
    ]
    won = sum(relics.RELICS[i].taken_flag in flags for i in relics.FIRST_THREE)
    if won == len(relics.FIRST_THREE):
        lines += [
            "Three sockets in its lintel, and you've won back all three sigils this side of the wall.",
            "Then the fourth's the one beyond. Mind the frost on that road. It takes your legs first.",
        ]
    elif won:
        lines += [
            "You've a sigil or two on you, by the look of you. There are three to win this side of the wall.",
            "The fourth lies past this gate. I'd bring the others home before you go after it.",
        ]
    else:
        lines += [
            "Three sockets in its lintel, one for each sigil this side of the wall. The fourth lies beyond it.",
            "Win the three first. The cold over there has stopped better than you, and it never sleeps.",
        ]
    return lines


WATCH = {  # the town watch at its gates: (name, lines)
    "aldous": ("Sergeant Aldous", north_gate_lines),
    "tobin": ("Tobin", north_gate_second_lines),
    "reyna": ("Reyna", east_gap_lines),
    "fenn": ("Old Fenn", west_gate_lines),
    "wynn": ("Corporal Wynn", vesper_gate_lines),
}


# --- the townsfolk of Harrowmere ------------------------------------------------------------------
# Folk with no shop and no gift: a few lines of their own, some of which turn as the roads out are won.


def _cleared(flags):
    """How many of the three old roads out of town (the prison, the hollow, the fortress) are quiet."""
    return sum(flag in flags for flag in ("boss_dead", "spider_dead", "gargoyles_dead"))


def hedda_lines(flags):
    lines = [
        "Hush. I come to pray for my Aldo. Forty years he worked the quay, and the sea kept him.",
        "The Enthroned never answers. But it never sends me away, either.",
    ]
    if _cleared(flags) >= 2:
        lines.append("The candles burn steadier these nights. Is that your doing, grey one?")
    return lines


def aubrey_lines(flags):
    return [
        "I trim the candles and sweep the nave. Sister Ilse says the work is the prayer.",
        "Don't stare too long at the throne. Folk who do go quiet for days after.",
    ]


def lisbet_lines(flags):
    if "spider_dead" in flags:
        return [
            "Flowers for the bell? I pick them by the east gate now the trail's gone quiet.",
            "Strange blooms, mind. Lovely, though. Nothing in them bites any more.",
        ]
    return [
        "Flowers! Flowers for the bell! Nobody buys, but I like to say it.",
        "I used to pick by the east gate. Not since the green came out of that cave.",
    ]


def osric_lines(flags):
    lines = ["Hear ye! By order of the watch: no one is to touch the bell's rope. Not that it has one."]
    if "gargoyles_dead" in flags:
        lines.append("Hear ye! The north road is reopened to carters, at their own peril. Mostly peril.")
    else:
        lines.append("Hear ye! The north road is closed to carters. The fortress on the ridge burns again.")
    if "duchess_dead" in flags:
        lines.append("And hear ye: the Vesper Gate has thawed. First notice I've had to write about frost.")
    return lines


def merrit_lines(flags):
    return [
        "A coin for old Merrit? No? Then a word for free: the bell rang once, and I was the only one awake.",
        "Never you mind what I saw on the plaza that night. Grey, it was. Grey like you.",
    ]


def tilde_lines(flags):
    return [
        "Mind the loom. I weave sailcloth, though there's few enough sails to mend these days.",
        "The watch buys my wool for tabards. Captain Garrick pays late, but he pays.",
    ]


def barnaby_lines(flags):
    return [
        "Casks for the inn, tubs for the fish. Nobody's fishing, so I make casks.",
        "Wren takes all I can make. Folk drink more when the roads go bad.",
    ]


def ottilie_lines(flags):
    lines = [
        "I've brought half this street into the world. Three born the week the bell rang, all grey-eyed.",
    ]
    if _cleared(flags) == 3:
        lines.append("Since the roads went quiet the babes sleep through. You'll not tell me that's chance.")
    else:
        lines.append("They cry at night, every one of them, facing north. Babes know things.")
    return lines


def hamund_lines(flags):
    return [
        "Forty years at sea and I come home to a town that's walled itself in from it.",
        "Go out by the sea gate if you want air. Maeve's on the pier, always is. Tell her old Hamund says hello.",
    ]


def sefa_lines(flags):
    return [
        "Bread's for the watch first, the cathedral second, and the rest of us after.",
        "Flour comes up the north road. When it comes. Until then, it's barley and hope.",
    ]


def jorun_lines(flags):
    return [
        "My man's boat sits on the quay. He won't take her out while the bell's quiet.",
        "He says the fish won't bite. I say he won't bait the hook.",
    ]


def cobb_lines(flags):
    return [
        "Every lamp in town, lit by dusk. That's my charge. Dusk never seems to end, lately.",
        "There's a grate in every corner of the wall. I'd keep my lamp out of them if I were you.",
    ]


TOWNSFOLK = {  # the townsfolk of Harrowmere: (name, lines)
    "hedda": ("Old Hedda", hedda_lines),
    "aubrey": ("Aubrey", aubrey_lines),
    "lisbet": ("Lisbet", lisbet_lines),
    "osric": ("Osric the Crier", osric_lines),
    "merrit": ("Merrit", merrit_lines),
    "tilde": ("Tilde", tilde_lines),
    "barnaby": ("Barnaby", barnaby_lines),
    "ottilie": ("Ottilie", ottilie_lines),
    "hamund": ("Old Hamund", hamund_lines),
    "sefa": ("Sefa", sefa_lines),
    "jorun": ("Jorun", jorun_lines),
    "cobb": ("Cobb", cobb_lines),
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
            "So. The one who walks in the prison and comes back up through the grate.",
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
            "You're going down that pit with a rusted sword? No. Take this hatchet. It bites.",
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
            "Six of us once. Now it's me and Hollis, and Hollis guards the gaol's grate from the inside.",
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
            "Take these, a first dose on the house. Nobody climbs out of that pit on their own legs twice.",
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


def _received(items, gold=0):
    from ashen_vault.player.items import Items

    parts = ["{" + f"{gold} gold" + "}"] if gold else []
    for item, n in items.items():
        name = Items.get(item).name
        parts.append(f"{{{n} {name}s}}" if n > 1 else f"{{{name}}}")
    return "Received " + " and ".join(parts) + "."


def _hand_over(g, items, gold=0):
    """Give the player items (and gold): a scroll or gear they already own pays gold instead."""
    spare = 0
    for item, n in items.items():
        kept, paid = loot.claim(g.player.inventory, stash.known_spells(g.player), item, g.player.stash)
        if kept:
            g.player.inventory.add(kept, n)
        spare += paid
    g.player.inventory.gold += spare + gold
    g.message(_received(items, gold))
    if spare:
        g.message(loot.spare_message(spare))


def gift_giver(id_, flags):
    """A villager who gives a newcomer something on first meeting, then sells their wares (if any)."""
    speaker, items, first, later, shop = GIFTS[id_]
    flag = f"gift:{id_}"
    opens = (lambda g: g.open_shop(shop)) if shop else None
    if flag in flags:
        return speaker, later, opens

    def after(g):
        g.flags.add(flag)
        _hand_over(g, items)
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
            "The wardens gave the prisoners to Lyra the Embracer, the old god: no face, only hands held out.",
            "The Warden's Key lies on their altar, past the end of this corridor. Their chapel keeps it now.",
            "My cell's lever is in the warders' quarters, beyond the locked door. If you find a way in...",
        ],
        None,
    )


# --- the Bell-keepers' Oubliette, under Old Harrowmere --------------------------------------------
#
# The first city's stone was laid with the mortar-light: a teal light the Sisters of the Mortar mixed
# into their mortar. It binds the old city, it woke the Stone Golems, and it is the Keystone's heart; it
# pools in the energy core on the Drowned Plaza's fountain, and while the core burns the golems mend.
# Quenching it (CORE_QUENCHED) weakens them all. The Oubliette's three prisoners and the two in the
# Under-Cells below them talk of it, of the roads of light, and of each other, and each gives something
# once at a turn of the story (STORY_GIFTS).

OUBLIETTE_OPEN = "lever:oubliette"  # the gaoler's lever, at the end of the Oubliette's hall
KEYSTONE_DEAD = "keystone_dead"
CORE_QUENCHED = "core_quenched:old_harrowmere"  # the energy core on the plaza's fountain, put out
WARD_KEY = "ward:old_harrowmere"  # set (or `WARD_KEY:<set>`) once a ward-stone has changed the roads
UNDERCELLS = "visited_undercells"  # you have been down in the Under-Cells, below the Oubliette

# What each of them gives at a turn of the story, once: id -> (the flag that earns it, items, gold).
STORY_GIFTS = {
    "aubel": (KEYSTONE_DEAD, {"red_tonic": 2, "menders_kit": 1}, 600),
    "coldry": (CORE_QUENCHED, {"menders_kit": 2}, 0),
    "ysolde": (UNDERCELLS, {"blue_moss": 3}, 250),
    "sister_vell": (CORE_QUENCHED, {"scroll_mortar_shard": 1}, 0),
}


def gifted_items():
    """Every item a villager or prisoner gives away, once each (for the find-it-once checks)."""
    found = [i for _, items, *_ in GIFTS.values() for i in items]
    return found + [i for _, items, _ in STORY_GIFTS.values() for i in items]


def roads_changed(flags):
    """Whether a ward-stone has changed which road of light stands (the save remembers it)."""
    return any(f == WARD_KEY or f.startswith(WARD_KEY + ":") for f in flags)


def _story_gift(id_, flags):
    """The after-callable that gives an NPC their story gift if it is due (earned and not yet given), else None."""
    earned_by, items, gold = STORY_GIFTS[id_]
    flag = f"gift:{id_}"
    if earned_by not in flags or flag in flags:
        return None

    def after(g):
        g.flags.add(flag)
        _hand_over(g, items, gold)

    return after


def _then(*afters):
    """One after-callable that runs each of these (skipping None) in turn; None if there are none."""
    afters = [a for a in afters if a]
    if not afters:
        return None
    return lambda g: [a(g) for a in afters] and None


def aubel(flags):
    """Aubel the Ringer, the last of the nine bell-keepers who rang the old city's bells: he tells how
    the first Harrowmere was raised on the sleeping Keystone and sank when its bells fell silent, and,
    once you have opened his cell, how the roads of light below the plaza work and who sold his brothers
    to the Under-Cells. When the Keystone falls he gives the keepers' tithe."""
    speaker = "Aubel the Ringer"
    gift = _story_gift("aubel", flags)
    if gift:
        return (
            speaker,
            [
                "The Keystone lies still. I felt it in my teeth, like the last toll of a bell.",
                "Nine of us kept the bells. Eight went down to the Under-Cells. I kept their tithe for them.",
                "Hidden in the hollow of my bell-rope, forty winters. Take it up into the daylight. Spend it.",
            ],
            gift,
        )
    if KEYSTONE_DEAD in flags:
        lines = [
            "The Keystone lies still. I felt it in my teeth, like the last toll of a bell.",
            "Whatever woke you, Ashen, it rang from up above. Down here there is nothing left to ring.",
        ]
        if CORE_QUENCHED in flags:
            lines.append(
                "And the teal light is out of the fountain. Let the old city sleep, with no one to wake it."
            )
        else:
            lines.append("Only the mortar-light still burns in the plaza, with no giant left to hold up.")
        return speaker, lines, None
    if OUBLIETTE_OPEN not in flags:
        lines = [
            "Ah... footsteps that don't drag. You're no sexton. Come to the bars, Ashen.",
            "I am Aubel. I rang the third bell of the old city, before the city went down into the dark.",
            "They raised Harrowmere on a sleeping giant. The Keystone, we called him. Our bells kept him dreaming.",
            "When the bells fell silent the ground shrugged, and the whole city slid into this cavern.",
        ]
        if UNDERCELLS in flags:
            lines.append(
                "You smell of the Under-Cells. My brothers rang their last down there. Did you see them?"
            )
        lines.append(
            "The gaoler keeps the cell lever at the end of the hall. Pull it, and I'll tell you of the roads."
        )
        return speaker, lines, None
    lines = ["Free legs, after all these years. They still remember the way to the bell."]
    if UNDERCELLS in flags:
        lines += [
            "You've been below, then. You'll have met Brannick. He kept our keys, and he turned them on us.",
            "Eight keepers he walked down those stairs, to save his own neck. Buy from him if you must.",
        ]
    else:
        lines.append(
            "There were nine bell-keepers. The gaolers took the other eight to the Under-Cells, below."
        )
    if CORE_QUENCHED in flags:
        lines.append("The teal glow has gone from the plaza. The golems drag like old men now. So will he.")
    else:
        lines += [
            "That teal glow in the plaza's fountain is the mortar-light. It holds up the giants, him too.",
            "Sister Coldry knows the roads to it better than I do. Ask her how its shield is dropped.",
        ]
    if roads_changed(flags):
        lines.append(
            "I heard you at the ward-stones, ringing all the way down here. Mind which road you stand on."
        )
    else:
        lines += [
            "Below the plaza the masons left roads of light over the chasm. Only one stands at a time.",
            "Strike a ward-stone and the road you walk on fades while the next one wakes. Mind your feet.",
        ]
    return speaker, lines, None


def coldry(flags):
    """Sister Coldry, of the masons who laid the first city and carved its ward-stones with her own
    chisel: she chose her chains. She tells of the mortar-light, of the third, teal road it raised,
    and that the core's shield drops only while that road stands; once the core is quenched she gives
    two mender's kits, plain mortar for plain stone."""
    speaker = "Sister Coldry"
    gift = _story_gift("coldry", flags)
    if KEYSTONE_DEAD in flags:
        lines = ["So the stone is broken. The mortar can rest, and so can I."]
        if CORE_QUENCHED in flags:
            lines.append("And the light went with him. Vell will grieve it. I will not.")
        else:
            lines.append(
                "Only the light still burns in the plaza, with nothing left to hold up. Let it gutter."
            )
        lines.append(
            "Take nothing from his court you would not carry up the lift. The gallery is long and dark."
        )
    elif "met_coldry" not in flags:
        flags.add("met_coldry")
        lines = [
            "Do not pity the chains. I asked for them.",
            "I am Coldry, of the Sisters of the Mortar. We laid every stone the first city stood on.",
            "Our mortar was never only lime. We mixed a light into it, teal as deep water: the mortar-light.",
            "It binds the old city still. When the bells fell silent, it stood up in the stone and walked.",
            "I carved the ward-stones, and spelled the roads, so no army could cross to the Keystone in one march.",
            "When the city sank, the gaolers locked away everyone who knew the way. I thought myself the last.",
            "The sextons still ring for him. Every toll a little louder. He is waking, and he is angry.",
        ]
    elif CORE_QUENCHED in flags:
        lines = [
            "You broke the core. I felt it in my knees: every stone in the city settling at once.",
            "The golems will mend no more, and he wakes weaker. The teal road is only a road now.",
        ]
    else:
        lines = [
            "Three roads, not two. The two my sisters spelled, and a third, teal road the light raised itself.",
            "Each ward-stone you strike wakes the next road: the first, the second, then the teal. Then round.",
            "The core on the plaza's fountain wears a shield of its own light. It drops only while the teal road stands.",
            "So wake the teal road, then strike the core while it stands. Bring something heavy. An edge won't bite.",
        ]
        if roads_changed(flags):
            lines.append("I hear you at my stones. Good. Never strike one from the road you need under you.")
    if UNDERCELLS in flags and KEYSTONE_DEAD not in flags:
        lines.append(
            "Vell lives, down in the Under-Cells? Then I was never the last. She kept the light. I would not."
        )
    if gift:
        lines.append("Take these. Mender's kits: plain mortar, that holds without a light in it.")
    return speaker, lines, gift


def ysolde(flags):
    """Ysolde Vane, once a copyist of the old city's archive, jailed for copying what the daylight
    writes on the vault round its rift. Through the bars she only talks; once the gaoler's lever has
    opened her cell she sells her copies, gives you moss and coin once you have seen the Under-Cells, and
    shelves the gaolers' thawed stores beside her copies once the mortar-light is out (SHOP_EXTRAS)."""
    speaker = "Ysolde Vane"
    if OUBLIETTE_OPEN not in flags:
        return (
            speaker,
            [
                "Careful. The light in here is mine, and I had to steal it.",
                "Ysolde Vane, scholar of the rift. They jailed me for copying what the daylight writes on the vault.",
                "Pull the gaoler's lever and I'll sell you what I copied. Two spells, and nobody else alive knows them.",
            ],
            None,
        )

    def shop(g):
        g.flags.add("met_ysolde")
        g.open_shop("ysolde")

    if "met_ysolde" not in flags:
        lines = [
            "Free, and nowhere to go but further into the dark. Very well: business.",
            "I copied the archive's ledgers for thirty years. Then I looked up, and copied the vault instead.",
            "A lance of the rift's own daylight, and a bell that nobody rings. Both copied true.",
        ]
    else:
        lines = ["The rift writes, I copy. Choose."]
    if CORE_QUENCHED in flags:
        lines.append("With the mortar-light out, the gaolers' stores thawed open. I've shelved what I found.")
    if KEYSTONE_DEAD in flags:
        lines.append("The vault has gone quiet. I'll copy its last lines before the dust settles on them.")
    gift = _story_gift("ysolde", flags)
    if gift:
        lines += [
            "You went down to the Under-Cells? The prisoners there scratched the rift's lines on the walls.",
            "From memory, and all of them wrong. Still, someone tried. Take these, for carrying the news.",
        ]
    return speaker, lines, _then(gift, shop)


def brannick(flags):
    """Gaoler Brannick, in a cell of the Under-Cells he once kept: when the city sank he turned the key
    on eight bell-keepers to save his own neck. He tells where the deep cells' key ring hangs and sells
    the gaolers' stores: heavy, blunt things, since the stone down here shrugs off an edge."""
    speaker = "Gaoler Brannick"
    opens = lambda g: g.open_shop("brannick")  # noqa: E731
    if "met_brannick" in flags:
        if KEYSTONE_DEAD in flags:
            lines = ["He's down? Then there's nothing left to guard but my own shame. Buy something."]
        elif CORE_QUENCHED in flags:
            lines = [
                "The light's out in the plaza. The golems down here dragged their feet all night. Buy, or go."
            ]
        else:
            lines = [
                "The ring's in the warden's office, past the interrogation hall. Mind the water.",
                "Heavy things for the stone. What'll it be?",
            ]
        return speaker, lines, opens

    def after(g):
        g.flags.add("met_brannick")
        g.open_shop("brannick")

    return (
        speaker,
        [
            "Don't look at me like that. I know what they say of me up there. Aubel's said it to the wall for years.",
            "Brannick. I kept the keys of these cells. When the city sank, the warden gave me a choice.",
            "The keepers, or my own neck. I chose my neck, and walked eight bell-keepers down those stairs.",
            "I hear them ringing in my sleep. Now I'm in a cell of my own, and nobody left to keep the keys.",
            "The deep cells open on a key ring in the warden's office, past the interrogation hall. Water's high.",
            "I've the gaolers' stores, too. Heavy things. The stone shrugs off an edge, and down here it's all stone.",
        ],
        after,
    )


def sister_vell(flags):
    """Sister Vell, the last Sister of the Mortar who kept its light, jailed in the Under-Cells: she
    tells what the mortar-light is (the teal light that binds the old city and animates its giants)
    and begs you to quench the core she could never put out herself. Once it is out she gives her
    order's last rite, Mortar Shard; her lines differ whether the core still burns or not."""
    speaker = "Sister Vell"
    gift = _story_gift("sister_vell", flags)
    if gift:
        return (
            speaker,
            [
                "It's out. I felt it go, like a breath I had held for a thousand years.",
                "Thank you. It was a mercy, and one I could never have done myself.",
                "Take the last rite of our order. It throws what is left of the light, and it breaks stone.",
            ],
            gift,
        )
    if CORE_QUENCHED in flags:
        lines = ["The stones are only stones now. Strange, how quiet they are."]
        if KEYSTONE_DEAD in flags:
            lines.append("And he sleeps at last. No light, no bells. Only stone, the way we found it.")
        else:
            lines.append("He wakes weaker without his heart's light. Break him with something heavy.")
        return speaker, lines, None
    if KEYSTONE_DEAD in flags:
        return (
            speaker,
            [
                "He has fallen, and still the mortar-light burns, with nothing left to hold up.",
                "Quench it, Ashen, before it finds another giant in the stone to wake.",
            ],
            None,
        )
    if "met_vell" in flags:
        return (
            speaker,
            [
                "The core still burns. Every golem you break, it mends. Quench it, Ashen.",
                "Wake the teal road, then strike the core with something heavy while its shield is down.",
            ],
            None,
        )
    flags.add("met_vell")
    return (
        speaker,
        [
            "Hush. Can you hear it? The hum in the stones. That is the mortar-light, and it is all that's left of us.",
            "I am Vell, last Sister of the Mortar who still keeps the light. We mixed it into the first city's mortar.",
            "Teal as deep water, it bound every stone. When the bells fell silent, it woke the giants in the stone.",
            "The golems are only mortar-light walking. The Keystone is the oldest of them, and the light is his heart.",
            "It pools in the core, on the fountain in the plaza. While it burns, the golems mend all you break.",
            "Quench it. A heavy blow will do it, once its shield is down. Coldry knows the road that drops it.",
            "I kept that light a thousand nights. I cannot be the one to put it out. You can.",
        ],
        None,
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
        "You'll have seen the bell on the plaza. The Silent Bell, we call it. Cracked, and dumb for years.",
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
        "(The stone of the king's brow splits, and light the colour of noon shows in the crack.)",
        "...four... and the fifth... never mine... the sun's... kept on the mountain...",
        "...by one who wished for more hands than he was born with...",
    ],
    [
        "(A shard of stone falls from the king's cheek. Under it the skin is grey and warm.)",
        "...five... the moon lets go... it was I who rang the bell... the only voice the stone left me...",
        "...the moon keeps the living... it cannot keep ash... take them to the bell-keeper... and I shall wake...",
    ],
)


def enthroned_lines(held):
    """The petrified Enthroned whispers from the stone, and stirs a little more with each sigil you
    carry."""
    return list(ENTHRONED_LINES[min(len(held), len(ENTHRONED_LINES) - 1)])
