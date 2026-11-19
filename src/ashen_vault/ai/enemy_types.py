from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class EnemyType:
    id: str
    name: str
    hp: int
    speed: float
    damage: int
    reach: float
    sight: float
    windup: float
    recover: float
    exp: int
    gold: range
    radius: float
    height: float  # top of the body as it dies, in metres: the span the ash dissolve crumbles
    tall: float  # top of the body standing, in metres: a spell flying over it misses
    poise: int = 0
    ranged: bool = False
    hover: float | None = None
    mouth: float | None = None  # height its shots leave from, if not the usual chest height
    boss: bool = False
    drop: str | None = None
    ambush: bool = False  # spawns dormant, disguised, until woken
    once: bool = False  # stays dead: shrine rests don't bring it back
    # Global flag set when this boss dies; while it is set the boss does not respawn.
    dead_flag: str | None = None
    # Message shown when this boss falls.
    epitaph: str | None = None
    # Ranged enemies with a bite: inside this distance they bite instead of shooting.
    bite_reach: float | None = None
    # Color of the projectiles a ranged enemy fires.
    shot_rgb: tuple = (255, 120, 40)
    # What its shots look like when they are not plain bolts of light: "arrow", "thorn", "lance" (a
    # lance of moon-frost, which numbs the legs of whoever it strikes).
    shot: str | None = None
    # Turning speed in rad/s; None turns instantly. Slow turners can be outflanked.
    turn_rate: float | None = None
    # Damage multiplier for blows landed from behind (a weak spot on the back).
    back_mult: float = 1.0
    # Lurkers sit still until you come within `sight`, then give chase for `GIVE_UP` metres.
    lurk: bool = False
    # Special attacks mixed in (see enemy.MOVES): "sweep", "web", "pounce", "cinders", "combo",
    # "slam", "eruption", "hook", "breath", "dive", "exhale", "ashfall", "spadeful", "grasp",
    # "dust_devil", "knell", "fireball", "bile", "engulf", "shed", "tail_lash", "squeal",
    # "frost_lance", "blink", "moonbeam", "moonfall".
    moves: tuple = ()
    # Enemy type a boss calls to its side once, when it drops to half HP.
    brood: str | None = None
    # A boss without a brood that flies into a rage at half HP instead: the message shown.
    rage: str | None = None
    # Enemy type a boss sloughs off with its "shed" move (killed with it when it falls).
    sheds: str | None = None
    # Moves a boss only adds to its mix once it reaches its second phase.
    phase_moves: tuple = ()
    # Plant foes: fire (Pyre) hurts them more and leaves them burning.
    flammable: bool = False
    # Iron foes: lightning hurts them more and jolts them (see world/elements.py).
    conductive: bool = False
    # Forged in fire: fire hurts them half as much and never sets them alight.
    fireproof: bool = False
    # Perched like a statue until you come within `sight`; waking one wakes its twin too.
    perch: bool = False
    # Bosses fought as a pair: the other one's type id. The pair shares a `dead_flag`, which is only
    # set (and the relic only dropped) once both have fallen; when one falls the other flies into its
    # `rage`. They take turns with their special moves.
    twin: str | None = None
    # A boss's entrance: "ash" waits as a smouldering heap in its lair and rises out of the burning
    # ash when you step in (see enemy.ASH_RISE). A `perch` statue cracks and tears free instead.
    rise: str | None = None
    # What a blow on it sounds like: the `hit_<material>` sound (audio/synth.py, MATERIALS).
    material: str = "flesh"
    # Ailments its blows and shots build in you when they get through: (kind, buildup) pairs, the
    # buildup out of `ailments.FULL` (see player/ailments.py).
    inflicts: tuple = ()
    # Splitters: the type it bursts into when slain, and how many (a sludge slime's gobbets). The
    # pieces are no splitters themselves, and as no map places them, no shrine rest brings them back.
    splits: str | None = None
    split_count: int = 2
    # A name of its own ("Mother Gnawl"), never written with "The" before it.
    proper: bool = False
    # How quick it fights: its windups, recovers, move cooldowns and combo gaps are scaled by this
    # (below 1 is faster). Windups never drop below `enemy.MIN_WINDUP`.
    tempo: float = 1.0

    @property
    def rooted(self):
        return self.speed <= 0

    @property
    def called(self):
        """How a message names it: "The Loom Mother", "The Butcher", but plain "Mother Gnawl"."""
        return self.name if self.proper or self.name.startswith("The ") else f"The {self.name}"


# What blows can land on. "spirit" is Vesperholm's moonlit dead: a glassy chime, like struck frost.
MATERIALS = ("flesh", "bone", "iron", "stone", "wood", "ash", "spirit")


class EnemyTypes:
    ALL: ClassVar[dict[str, EnemyType]] = {
        t.id: t
        for t in [
            EnemyType(
                id="bone_walker",
                material="bone",
                name="Bone Walker",
                hp=24,
                speed=1.7,
                damage=8,
                reach=1.9,
                sight=12,
                windup=0.55,
                recover=0.9,
                exp=14,
                gold=range(4, 11),
                radius=0.45,
                height=0.8,
                tall=1.8,
                poise=0,
            ),
            EnemyType(
                id="mire_slime",
                name="Mire Slime",
                hp=16,
                speed=1.1,
                damage=6,
                reach=1.5,
                sight=8,
                windup=0.45,
                recover=0.7,
                exp=7,
                gold=range(1, 6),
                radius=0.5,
                height=0.4,
                tall=0.7,
                poise=0,
                inflicts=(("poison", 30), ("corrosion", 35)),
            ),
            EnemyType(
                id="cinder_wisp",
                material="ash",
                name="Cinder Wisp",
                hp=12,
                speed=1.4,
                damage=7,
                reach=9.0,
                sight=12,
                windup=0.8,
                recover=1.8,
                exp=12,
                gold=range(5, 13),
                radius=0.35,
                height=0.6,
                tall=2.1,
                ranged=True,
                hover=1.3,
                poise=0,
            ),
            EnemyType(
                id="ashen_warden",
                material="iron",
                name="Ashen Warden",
                hp=150,
                speed=2.0,
                damage=16,
                reach=2.6,
                sight=16,
                windup=0.75,
                recover=1.1,
                exp=90,
                gold=range(60, 61),
                radius=0.7,
                height=2.6,
                tall=2.6,
                boss=True,
                drop="ember_sigil",
                dead_flag="boss_dead",
                rise="ash",
                epitaph="The Warden crumbles into ash. Something glows where he fell.",
                poise=14,
                # A cleave all around, a leaping slam, a fan of embers flung from his hand, a
                # three-swing chain and a shockwave slam; at half HP his blade catches fire and he
                # starts calling fire up from the floor.
                moves=("sweep", "pounce", "cinders", "combo", "slam"),
                phase_moves=("eruption",),
                rage="The Warden's blade catches fire!",
                shot_rgb=(255, 140, 50),
            ),
            EnemyType(
                id="butcher",
                name="The Butcher",
                hp=120,
                speed=1.5,
                damage=18,
                reach=2.5,
                sight=12,
                windup=0.95,
                recover=1.3,
                exp=70,
                gold=range(45, 61),
                radius=0.7,
                height=2.6,
                tall=2.7,
                boss=True,
                dead_flag="butcher_dead",
                rise="ash",
                epitaph="The Butcher topples among his hooks, and does not rise.",
                poise=12,
                # The prison's slaughterman, above the Warden's hall: a slow, heavy cleaver that sweeps
                # all round, a lunge across the floor and a chain of hacks. At half HP he tears into a
                # frenzy and adds a two-handed chop that shakes the floor.
                moves=("sweep", "pounce", "combo"),
                phase_moves=("slam",),
                rage="The Butcher roars and hacks wildly!",
                inflicts=(("bleed", 45),),
            ),
            EnemyType(
                id="mimic",
                material="wood",
                name="Mimic",
                hp=60,
                speed=2.0,
                damage=22,
                reach=2.0,
                sight=10,
                windup=0.45,
                recover=1.0,
                exp=60,
                gold=range(40, 61),
                radius=0.55,
                height=0.8,
                tall=0.9,
                poise=10,
                ambush=True,
                once=True,
            ),
            EnemyType(
                id="snare_bloom",
                material="wood",
                flammable=True,
                name="Snare Bloom",
                hp=22,
                speed=0.0,
                damage=9,
                reach=8.0,
                sight=9,
                windup=0.7,
                recover=1.6,
                exp=16,
                gold=range(3, 10),
                radius=0.45,
                height=1.7,
                tall=2.3,
                mouth=1.7,
                ranged=True,
                bite_reach=2.2,
                shot_rgb=(150, 210, 70),
                shot="thorn",
                poise=0,
                inflicts=(("poison", 35),),
            ),
            EnemyType(
                id="bark_husk",
                material="wood",
                flammable=True,
                name="Bark Husk",
                hp=70,
                speed=1.1,
                damage=16,
                reach=2.6,
                sight=10,
                windup=0.95,
                recover=1.3,
                exp=34,
                gold=range(8, 19),
                radius=0.75,
                height=3.0,
                tall=3.0,
                poise=10,
                # A lumbering old tree: circle it and strike the glowing heart-fungus in its back.
                turn_rate=1.3,
                back_mult=2.0,
            ),
            EnemyType(
                id="stump_mimic",
                material="wood",
                flammable=True,
                name="Stump Mimic",
                hp=34,
                speed=1.9,
                damage=12,
                reach=1.8,
                sight=2.8,
                windup=0.4,
                recover=1.0,
                exp=22,
                gold=range(10, 26),
                radius=0.55,
                height=0.9,
                tall=1.0,
                poise=5,
                lurk=True,
            ),
            EnemyType(
                id="loom_mother",
                name="Loom Mother",
                hp=240,
                speed=2.4,
                damage=19,
                reach=3.1,
                sight=16,
                windup=0.7,
                recover=1.0,
                exp=140,
                gold=range(100, 101),
                radius=1.3,
                height=2.5,
                tall=1.8,
                boss=True,
                drop="verdant_sigil",
                dead_flag="spider_dead",
                rise="ash",
                epitaph="The Loom Mother curls up and is still. Something green glows in the silk.",
                poise=16,
                moves=("sweep", "web", "pounce"),
                brood="loom_brood",
                inflicts=(("poison", 25),),
            ),
            EnemyType(
                id="loom_brood",
                name="Loom Brood",
                hp=10,
                speed=2.7,
                damage=5,
                reach=1.3,
                sight=16,
                windup=0.35,
                recover=0.6,
                exp=4,
                gold=range(0, 3),
                radius=0.35,
                height=0.75,
                tall=0.6,
                inflicts=(("poison", 30),),
            ),
            EnemyType(
                id="gaoler",
                material="iron",
                name="Gaoler",
                hp=55,
                speed=1.3,
                damage=13,
                reach=2.2,
                sight=11,
                windup=0.8,
                recover=1.2,
                exp=38,
                gold=range(12, 25),
                radius=0.6,
                height=2.1,
                tall=2.2,
                poise=8,
                # A hulking jailer who hauls you in on a hooked chain, then clubs you.
                moves=("hook",),
                inflicts=(("bleed", 30),),
            ),
            EnemyType(
                id="hollow_inmate",
                name="Hollow Inmate",
                hp=20,
                speed=1.5,
                damage=7,
                reach=1.7,
                sight=7,
                windup=0.75,
                recover=1.0,
                exp=10,
                gold=range(1, 6),
                radius=0.4,
                height=0.8,
                tall=1.7,
                poise=0,
                # A prisoner the prison was shut on, gone hollow: it kneels where it was left until you
                # come near, then shambles after you and brings the chain between its wrists down.
                lurk=True,
            ),
            EnemyType(
                id="bone_crawler",
                material="bone",
                name="Bone Crawler",
                hp=18,
                speed=2.8,
                damage=7,
                reach=1.4,
                sight=3.2,
                windup=0.35,
                recover=0.7,
                exp=11,
                gold=range(2, 8),
                radius=0.45,
                height=0.55,
                tall=0.6,
                # Lies as a heap of bones until you walk up to it, then skitters after you.
                lurk=True,
                inflicts=(("bleed", 30),),
            ),
            EnemyType(
                id="forge_golem",
                material="stone",
                name="Forge Golem",
                hp=90,
                speed=0.9,
                damage=18,
                reach=2.4,
                sight=10,
                windup=1.0,
                recover=1.4,
                exp=48,
                gold=range(14, 30),
                radius=0.8,
                height=2.4,
                tall=2.6,
                poise=14,
                # A walking furnace: slow to turn, with its firebox open on its back.
                turn_rate=1.0,
                back_mult=2.0,
                moves=("slam", "sweep"),
                conductive=True,
                fireproof=True,
                inflicts=(("corrosion", 35),),
            ),
            EnemyType(
                id="iron_bowman",
                material="iron",
                name="Iron Bowman",
                hp=26,
                speed=1.3,
                damage=10,
                reach=13.0,
                sight=15,
                windup=1.0,
                recover=1.6,
                exp=20,
                gold=range(6, 15),
                radius=0.45,
                height=1.8,
                tall=1.9,
                poise=4,
                ranged=True,
                bite_reach=1.8,  # too close and he bashes you with his bow-stave
                shot_rgb=(150, 150, 160),
                shot="arrow",
                conductive=True,
                inflicts=(("bleed", 25),),
            ),
            EnemyType(
                id="slag_hound",
                name="Slag Hound",
                hp=30,
                speed=3.0,
                damage=9,
                reach=1.6,
                sight=11,
                windup=0.4,
                recover=0.8,
                exp=18,
                gold=range(3, 10),
                radius=0.5,
                height=0.9,
                tall=1.0,
                moves=("pounce",),
                fireproof=True,
                inflicts=(("bleed", 30),),
            ),
            EnemyType(
                id="brand",
                material="iron",
                name="Brand",
                hp=260,
                speed=2.1,
                damage=19,
                reach=2.6,
                sight=14,
                windup=0.75,
                recover=1.1,
                exp=170,
                gold=range(70, 71),
                radius=0.9,
                height=2.2,
                tall=2.4,
                boss=True,
                drop="iron_sigil",
                dead_flag="gargoyles_dead",
                epitaph="The iron gargoyles lie still. Something cold and grey gleams on the roof.",
                poise=16,
                # The ground-bound twin: tail sweeps, claw chains, leaps and a crushing landing.
                moves=("sweep", "combo", "pounce", "slam"),
                phase_moves=("eruption",),
                rage="Brand roars over its fallen twin, and the roof begins to smoke!",
                conductive=True,
                fireproof=True,
                perch=True,
                twin="bellows",
                shot_rgb=(255, 150, 60),
            ),
            EnemyType(
                id="bellows",
                material="stone",
                name="Bellows",
                hp=220,
                speed=1.9,
                damage=16,
                reach=2.4,
                sight=14,
                windup=0.8,
                recover=1.2,
                exp=170,
                gold=range(70, 71),
                radius=0.85,
                height=2.0,
                tall=3.0,  # it hovers by its talons: its chest, head and horns ride high above
                hover=1.0,
                boss=True,
                drop="iron_sigil",
                dead_flag="gargoyles_dead",
                epitaph="The iron gargoyles lie still. Something cold and grey gleams on the roof.",
                poise=14,
                # The winged twin: rakes the roof with fire, swoops through you and spits embers.
                moves=("breath", "dive", "cinders"),
                phase_moves=("eruption",),
                rage="Bellows shrieks over its fallen twin, its throat white-hot!",
                conductive=True,
                fireproof=True,
                perch=True,
                twin="brand",
                shot_rgb=(255, 170, 70),
            ),
            # --- the Cemetery of Ashes -----------------------------------------------------------
            EnemyType(
                id="ashen_husk",
                material="ash",
                name="Ashen Husk",
                # One of the Ashen who woke before you and failed: grey, stooped and empty, it
                # shambles at you and claws.
                hp=16,
                speed=1.2,
                damage=6,
                reach=1.6,
                sight=9,
                windup=0.7,
                recover=1.0,
                exp=8,
                gold=range(2, 7),
                radius=0.4,
                height=0.85,
                tall=1.7,
                inflicts=(("rot", 20),),
            ),
            EnemyType(
                id="mourner",
                material="bone",
                name="Shrouded Mourner",
                # Found only in the Cemetery of Ashes: a hooded thing in long dark robes that stands
                # bowed over a grave, still as a stone, until you come close; then it glides at you
                # and stabs with a crooked knife, and from further off kindles a ball of grave-fire in
                # its bony palm and throws it. Left far behind, it gives up and stands still again.
                hp=22,
                speed=2.6,
                damage=9,
                reach=1.5,
                sight=3.5,
                windup=0.45,
                recover=1.1,
                exp=14,
                gold=range(4, 11),
                radius=0.4,
                height=1.0,
                tall=2.2,
                lurk=True,
                moves=("fireball",),
                shot_rgb=(255, 110, 40),
                inflicts=(("rot", 30),),
            ),
            EnemyType(
                id="sexton",
                material="ash",
                name="Ashen Sexton",
                hp=95,
                speed=1.5,
                damage=12,
                reach=2.8,
                sight=14,
                windup=0.95,
                recover=1.3,
                exp=60,
                gold=range(40, 41),
                radius=0.75,
                height=2.0,
                tall=2.6,
                boss=True,
                dead_flag="sexton_dead",
                rise="ash",
                epitaph="The Sexton sinks back into the ash it kept. The gate beyond stands open.",
                poise=10,
                # The first boss, and a gentle one: slow spade chops, and the ash it keeps. Up close it
                # breathes a cone of grave dust at you, or dashes an urn of ashes down so the ash
                # billows out all round; further off it flings a spadeful of grave ash in a fan, calls
                # hands of ash grasping up from the ground in a line, or whirls its spade and raises
                # two whirlwinds of ash that hunt you. Each of them slows you. At half HP the ash in its
                # chest catches the bell's note and kindles, and it tolls the knell: two rings of
                # embers, one after the other.
                moves=("exhale", "ashfall", "spadeful", "grasp", "dust_devil"),
                phase_moves=("knell",),
                rage="The bell's note rings through the Sexton. Its ash catches fire!",
                shot_rgb=(255, 150, 60),
                inflicts=(("rot", 35),),
            ),
            # --- the Harrow Sewers ---------------------------------------------------------------
            EnemyType(
                id="sewer_rat",
                name="Gutter Rat",
                # A rat the size of a cat, grey and scabbed: they come in packs, quick and weak, and
                # their bites carry the sewers' rot.
                hp=7,
                speed=3.3,
                damage=4,
                reach=1.1,
                sight=9,
                windup=0.3,
                recover=0.6,
                exp=3,
                gold=range(0, 3),
                radius=0.28,
                height=0.3,
                tall=0.4,
                inflicts=(("rot", 12),),
            ),
            EnemyType(
                id="giant_rat",
                name="Cistern Rat",
                # As big as a hound and as mangy: it springs from further off than you would think.
                hp=30,
                speed=2.7,
                damage=10,
                reach=1.5,
                sight=11,
                windup=0.5,
                recover=0.9,
                exp=20,
                gold=range(3, 10),
                radius=0.5,
                height=0.75,
                tall=0.9,
                poise=4,
                moves=("pounce",),
                inflicts=(("bleed", 28), ("rot", 15)),
            ),
            EnemyType(
                id="sludge_slime",
                name="Sludge Slime",
                # A heap of the sewers' own filth that crawls: struck down, it bursts into gobbets that
                # crawl on. Its touch poisons and eats at iron.
                hp=24,
                speed=1.0,
                damage=7,
                reach=1.5,
                sight=8,
                windup=0.5,
                recover=0.8,
                exp=10,
                gold=range(1, 6),
                radius=0.55,
                height=0.45,
                tall=0.8,
                inflicts=(("poison", 30), ("corrosion", 30)),
                splits="slimelet",
            ),
            EnemyType(
                id="slimelet",
                name="Sludge Gobbet",
                hp=7,
                speed=1.6,
                damage=4,
                reach=1.1,
                sight=10,
                windup=0.4,
                recover=0.6,
                exp=3,
                gold=range(0, 2),
                radius=0.3,
                height=0.25,
                tall=0.4,
                inflicts=(("poison", 20), ("corrosion", 15)),
            ),
            EnemyType(
                id="drowned",
                name="Drowned Wretch",
                # One of the town's own, years in the sludge: it lies sunk to the shoulders until you
                # wade close, then heaves itself up, bloated and dripping, and claws.
                hp=34,
                speed=1.3,
                damage=11,
                reach=1.7,
                sight=3.4,
                windup=0.75,
                recover=1.1,
                exp=22,
                gold=range(4, 12),
                radius=0.45,
                height=1.0,
                tall=2.0,
                poise=6,
                lurk=True,
                inflicts=(("rot", 30),),
            ),
            EnemyType(
                id="bilge_leech",
                name="Bilge Leech",
                # A leech as long as a man, lying flat in the sludge by the channels: it rears up and
                # lunges from further off than its reach, and its bite bleeds.
                hp=20,
                speed=1.8,
                damage=8,
                reach=1.3,
                bite_reach=2.6,
                sight=3.0,
                windup=0.55,
                recover=1.0,
                exp=14,
                gold=range(1, 7),
                radius=0.4,
                height=0.4,
                tall=0.9,
                lurk=True,
                inflicts=(("bleed", 35),),
            ),
            EnemyType(
                id="rat_matron",
                name="Mother Gnawl",
                proper=True,
                hp=150,
                speed=2.2,
                damage=14,
                reach=2.2,
                sight=12,
                windup=0.7,
                recover=1.0,
                exp=80,
                gold=range(50, 61),
                radius=0.9,
                height=1.3,
                tall=1.6,
                boss=True,
                dead_flag="matron_dead",
                rise="ash",
                epitaph="Mother Gnawl sprawls across her nest. The squeaking in the walls falls still.",
                poise=10,
                # The brood-mother of the sewers' rats, swollen to the size of a cart-horse in a nest
                # of rags and bones: she rakes all round with her claws, springs at you, lashes her
                # tail at whoever slips behind her, squeals fit to split your skull and burrows into
                # the muck to burst up under you; at half HP her old wounds tear open and she fights
                # on in a frenzy.
                moves=("sweep", "pounce", "tail_lash", "squeal", "burrow"),
                rage="Mother Gnawl shrieks, and her old wounds tear open!",
                inflicts=(("rot", 30),),
            ),
            EnemyType(
                id="sodden_pall",
                name="The Sodden Pall",
                hp=280,
                speed=1.0,
                damage=18,
                reach=2.6,
                sight=15,
                windup=0.9,
                recover=1.2,
                exp=180,
                gold=range(90, 101),
                radius=1.3,
                height=2.6,
                tall=3.3,
                boss=True,
                dead_flag="pall_dead",
                rise="ash",
                epitaph="The Sodden Pall sinks into a green, still pool, and the face in it fades away.",
                poise=16,
                # Everything the town ever washed down its drains settled in the deepest cistern and
                # grew a skin: a bell of green ooze twice a man's height that drags itself along on its
                # hem like a pall dragged off a coffin, and the drowned it took show as a face in its
                # folds. It rears up and crashes down so the floor heaves, flings its skirt out all
                # round and spits bile from the mouth in its folds; at half HP the face rises pale in
                # it, and it lurches along the floor to flow over you and sloughs off clots of itself
                # that crawl at you.
                moves=("slam", "sweep", "bile"),
                phase_moves=("engulf", "shed"),
                sheds="pall_clot",
                rage="The Sodden Pall shudders, and a pale face rises in its folds!",
                shot_rgb=(140, 220, 90),
                inflicts=(("poison", 30), ("corrosion", 35)),
            ),
            EnemyType(
                id="pall_clot",
                name="Pall Clot",
                # A clot of the Pall sloughed off its hem, crawling at you on its own.
                hp=7,
                speed=1.6,
                damage=4,
                reach=1.1,
                sight=10,
                windup=0.4,
                recover=0.6,
                exp=3,
                gold=range(0, 2),
                radius=0.3,
                height=0.25,
                tall=0.4,
                inflicts=(("poison", 20), ("corrosion", 15)),
            ),
            # --- Vesperholm, the Moonbound City ----------------------------------------------------
            EnemyType(
                id="pale_sentinel",
                material="iron",
                name="Pale Sentinel",
                # An empty suit of silvered plate filled with moonlight, still keeping the watch its
                # wearer died on: slow to turn, it sweeps a long crescent glaive all round.
                hp=92,
                speed=1.4,
                damage=19,
                reach=2.5,
                sight=12,
                windup=0.9,
                recover=1.2,
                exp=60,
                gold=range(14, 34),
                radius=0.5,
                height=2.1,
                tall=2.3,
                poise=16,
                turn_rate=1.8,
                moves=("sweep",),
                conductive=True,
                inflicts=(("frost", 20),),
            ),
            EnemyType(
                id="lantern_wraith",
                material="spirit",
                name="Lantern Wraith",
                # A lamplighter of the endless night, a hooded shade with no legs under its robe,
                # drifting with a lantern of trapped moonlight: it throws lances of moon-frost from
                # afar, three at once now and then, and its touch keeps you as the moon keeps all.
                hp=38,
                speed=1.2,
                damage=12,
                reach=10.0,
                sight=14,
                windup=0.75,
                recover=1.6,
                exp=45,
                gold=range(9, 23),
                radius=0.4,
                height=1.9,
                tall=2.0,
                ranged=True,
                bite_reach=1.6,
                mouth=1.3,
                shot="lance",
                shot_rgb=(196, 222, 255),
                moves=("frost_lance",),
                inflicts=(("rot", 20), ("frost", 30)),
            ),
            EnemyType(
                id="moonhound",
                name="Moonhound",
                # A gaunt, pale hound of the Duchess's kennels, its coat gone white as frost and its
                # eyes two moons: it hunts in pairs and springs from far off.
                hp=42,
                speed=3.1,
                damage=13,
                reach=1.6,
                sight=12,
                windup=0.4,
                recover=0.8,
                exp=36,
                gold=range(6, 17),
                radius=0.5,
                height=0.9,
                tall=1.1,
                moves=("pounce",),
                inflicts=(("bleed", 30),),
            ),
            EnemyType(
                id="veiled_knight",
                material="spirit",
                name="Veiled Knight",
                # One of the Duchess's honour guard, half of him no longer quite here: under a veil of
                # moon-silk his armour shows through like frost on glass. Keep your distance and he
                # steps through the moonlight to strike from behind you.
                hp=100,
                speed=1.8,
                damage=20,
                reach=2.0,
                sight=12,
                windup=0.7,
                recover=0.8,
                exp=75,
                gold=range(17, 40),
                radius=0.5,
                height=2.0,
                tall=2.1,
                poise=14,
                moves=("blink",),
                inflicts=(("rot", 25), ("frost", 25)),
            ),
            EnemyType(
                id="moon_duchess",
                material="spirit",
                name="Duchess Ilvane",
                proper=True,
                hp=540,
                speed=2.3,
                damage=24,
                reach=2.8,
                sight=16,
                windup=0.8,
                recover=0.7,
                exp=420,
                gold=range(180, 196),
                radius=0.8,
                height=2.9,
                tall=3.3,
                boss=True,
                drop="argent_sigil",
                dead_flag="duchess_dead",
                rise="ash",
                epitaph="Duchess Ilvane kneels in her own light, and it goes out. Silver gleams where she fell.",
                poise=22,
                # The Moonwed, the king's sister and Vesperholm's lady: she wed the moon on the fourth
                # sigil so the night would never end and nothing in her city would die. Tall as two men
                # in a gown of moon-silk and a veil, a crescent glaive in her hands: she sweeps it all
                # round, cuts three times in a row, throws a fan of frost lances and calls shafts of
                # moonlight down where you stand. At half HP she casts off her veil, steps through the
                # moonlight behind you, and the moon rains down round you in rings.
                moves=("sweep", "combo", "frost_lance", "moonbeam"),
                phase_moves=("blink", "moonfall"),
                rage="Duchess Ilvane casts off her veil, and the moon pours its light into her!",
                shot="lance",
                shot_rgb=(210, 230, 255),
                inflicts=(("rot", 30), ("frost", 35)),
                # Quicker than any foe before her: her windups, recovers and combo come a good quarter
                # faster, and faster again in her rage.
                tempo=0.72,
            ),
        ]
    }

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]

    @classmethod
    def has(cls, id_):
        return id_ in cls.ALL
