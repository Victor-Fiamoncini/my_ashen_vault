"""What a weapon button's ATK bar shows, as data (`hud.draw_atk_bar` draws it). No raylib.

The bar has two rows: the top shows the ATK gauge (yellow, dim while it refills) and the bottom shows the
heavy charge while the button is held (orange, dim red when you lack the ST for a heavy). When a weapon
with an art (weapons.ARTS) has both rows full and the MP to loose it, the whole bar burns in the art's
colour; short of MP, it looks like any weapon's ready heavy."""

from dataclasses import dataclass

ATK_RGB = (240, 210, 90)
ATK_CHARGING_RGB = (150, 120, 50)
HEAVY_RGB = (255, 140, 50)
WINDED_RGB = (140, 40, 30)
CHARGE_SHOW = 0.08  # ignore the first moments of a hold so plain taps never flash the bar

# What the bar glows with: nothing, a ready heavy or a ready art.
PLAIN, HEAVY, ART = "plain", "heavy", "art"


@dataclass(frozen=True)
class BarState:
    gauge: float  # top row's fill, 0..1
    gauge_rgb: tuple
    charge: float  # bottom row's fill, 0..1
    charge_rgb: tuple
    glow: str = PLAIN
    art_rgb: tuple | None = None  # set when `glow` is ART


def state(player, hand):
    """The ATK bar of `hand`'s weapon button right now."""
    g = player.gauge(hand)
    gauge_rgb = ATK_RGB if g.full else ATK_CHARGING_RGB
    held = player.charge_hand == hand and not player.swinging and player.charge_t >= CHARGE_SHOW
    if not held:
        return BarState(g.value, gauge_rgb, 0.0, HEAVY_RGB)
    if not player.can_heavy(hand):
        return BarState(g.value, gauge_rgb, 1.0, WINDED_RGB)
    k = player.charge_frac
    art = player.art_ready(hand)
    if art:
        return BarState(1.0, art.rgb, 1.0, art.rgb, ART, art.rgb)
    return BarState(g.value, gauge_rgb, k, HEAVY_RGB, HEAVY if k >= 1 else PLAIN)
