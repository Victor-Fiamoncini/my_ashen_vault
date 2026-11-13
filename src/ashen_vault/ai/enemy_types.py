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
    # Global flag set when this boss dies; while it is set the boss does not respawn.
    dead_flag: str | None = None
    # Message shown when this boss falls.
    epitaph: str | None = None
    # Ranged enemies with a bite: inside this distance they bite instead of shooting.
    bite_reach: float | None = None
    # Color of the projectiles a ranged enemy fires.
    shot_rgb: tuple = (255, 120, 40)

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
                hp=60,
                speed=1.0,
                damage=14,
                reach=2.4,
                sight=10,
                windup=0.95,
                recover=1.3,
                exp=30,
                gold=range(8, 19),
                radius=0.6,
                height=2.5,
                poise=9,
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
            ),
        ]
    }

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]

    @classmethod
    def has(cls, id_):
        return id_ in cls.ALL
