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
        ]
    }

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]

    @classmethod
    def has(cls, id_):
        return id_ in cls.ALL
