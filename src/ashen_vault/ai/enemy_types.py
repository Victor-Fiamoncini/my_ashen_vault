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
    height: float
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
    # Turning speed in rad/s; None turns instantly. Slow turners can be outflanked.
    turn_rate: float | None = None
    # Damage multiplier for blows landed from behind (a weak spot on the back).
    back_mult: float = 1.0
    # Lurkers sit still until you come within `sight`, then give chase for `GIVE_UP` metres.
    lurk: bool = False
    # Special attacks a boss mixes in (see Enemy.MOVES): "sweep", "web", "pounce".
    moves: tuple = ()
    # Enemy type a boss calls to its side once, when it drops to half HP.
    brood: str | None = None

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
                height=1.8,
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
                height=0.8,
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
                boss=True,
                drop="ember_sigil",
                dead_flag="boss_dead",
                epitaph="The Warden crumbles into ash. Something glows where he fell.",
                poise=14,
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
                height=1.0,
                poise=10,
                ambush=True,
                once=True,
            ),
            EnemyType(
                id="snare_bloom",
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
                ranged=True,
                bite_reach=2.2,
                shot_rgb=(150, 210, 70),
                poise=0,
            ),
            EnemyType(
                id="bark_husk",
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
                height=2.8,
                poise=10,
                # A lumbering old tree: circle it and strike the glowing heart-fungus in its back.
                turn_rate=1.3,
                back_mult=2.0,
            ),
            EnemyType(
                id="stump_mimic",
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
                height=1.1,
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
                height=1.9,
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
                height=0.5,
            ),
        ]
    }

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]

    @classmethod
    def has(cls, id_):
        return id_ in cls.ALL
