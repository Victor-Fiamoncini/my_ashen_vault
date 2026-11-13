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
    # What its shots look like when they are not plain bolts of light: "arrow".
    shot: str | None = None
    # Turning speed in rad/s; None turns instantly. Slow turners can be outflanked.
    turn_rate: float | None = None
    # Damage multiplier for blows landed from behind (a weak spot on the back).
    back_mult: float = 1.0
    # Lurkers sit still until you come within `sight`, then give chase for `GIVE_UP` metres.
    lurk: bool = False
    # Special attacks mixed in (see enemy.MOVES): "sweep", "web", "pounce", "cinders", "combo",
    # "slam", "eruption", "hook", "breath", "dive".
    moves: tuple = ()
    # Enemy type a boss calls to its side once, when it drops to half HP.
    brood: str | None = None
    # A boss without a brood that flies into a rage at half HP instead: the message shown.
    rage: str | None = None
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

    @property
    def rooted(self):
        return self.speed <= 0


class EnemyTypes:
    ALL: ClassVar[dict[str, EnemyType]] = {
        t.id: t
        for t in [
            EnemyType(
                id="bone_walker",
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
            ),
            EnemyType(
                id="cinder_wisp",
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
                tall=1.6,
                ranged=True,
                hover=1.3,
                poise=0,
            ),
            EnemyType(
                id="ashen_warden",
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
                id="mimic",
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
                height=1.6,
                tall=1.8,
                ranged=True,
                bite_reach=2.2,
                shot_rgb=(150, 210, 70),
                poise=0,
            ),
            EnemyType(
                id="bark_husk",
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
                epitaph="The Loom Mother curls up and is still. Something green glows in the silk.",
                poise=16,
                moves=("sweep", "web", "pounce"),
                brood="loom_brood",
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
            ),
            EnemyType(
                id="gaoler",
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
            ),
            EnemyType(
                id="bone_crawler",
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
            ),
            EnemyType(
                id="forge_golem",
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
            ),
            EnemyType(
                id="iron_bowman",
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
            ),
            EnemyType(
                id="brand",
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
                tall=2.4,
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
        ]
    }

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]

    @classmethod
    def has(cls, id_):
        return id_ in cls.ALL
