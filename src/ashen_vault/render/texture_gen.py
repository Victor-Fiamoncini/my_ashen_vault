"""Procedural low-resolution textures. Each generator returns RGBA bytes."""

import math

from ashen_vault.util import rround

SIZE = 64


def all_textures():
    return {
        "stone_brick": stone_brick(),
        "flagstone": flagstone(),
        "rough_stone": rough_stone(),
        "wood_plank": wood_plank(),
        "door_wood": door_wood(),
        "plaster": plaster(),
        "timber": timber(),
        "grass": grass(),
        "dirt": dirt(),
        "cobble": cobble(),
        "cobble_moss": cobble_moss(),
        "setts": setts(),
        "stucco": stucco(),
        "ashlar": ashlar(),
        "terracotta": terracotta(),
        "water": water(),
        "roof": roof(),
        "iron_bars": iron_bars(),
        "mossy_brick": mossy_brick(),
        "vine_wall": vine_wall(),
        "bark": bark(),
        "leaf_litter": leaf_litter(),
        "jungle_floor": jungle_floor(),
        "canopy": canopy(),
        "foliage": foliage(),
        "mud": mud(),
        "bog": bog(),
        "rapids": rapids(),
        "thorns": thorns(),
        "cliff_rock": cliff_rock(),
        "ravine": ravine(),
        "log_wall": log_wall(),
        "ossuary": ossuary(),
        "web_wall": web_wall(),
        "black_brick": black_brick(),
        "iron_plate": iron_plate(),
        "iron_grate": iron_grate(),
        "lava": lava(),
        "slag": slag(),
        "ash_road": ash_road(),
        "slate": slate(),
        "clouds": clouds(),
        "cloud_cap": cloud_cap(),
        "mist": mist(),
        "white": solid(255, 255, 255),
    }


def hash_(x, y, seed):
    """Deterministic hash noise in 0..1."""
    h = (x * 374_761_393 + y * 668_265_263 + seed * 2_147_483_647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1_274_126_177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) / 4_294_967_295.0


def noise(x, y, cell, seed):
    """Tileable value noise at `cell` pixel scale."""
    n = SIZE // cell
    gx = x / cell
    gy = y / cell
    x0 = math.floor(gx)
    y0 = math.floor(gy)
    fx = gx - x0
    fy = gy - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)

    def v(i, j):
        return hash_((x0 + i) % n, (y0 + j) % n, seed)

    a = v(0, 0) + (v(1, 0) - v(0, 0)) * fx
    b = v(0, 1) + (v(1, 1) - v(0, 1)) * fx
    return a + (b - a) * fy


def fbm(x, y, seed):
    return noise(x, y, 16, seed) * 0.5 + noise(x, y, 8, seed + 1) * 0.3 + noise(x, y, 4, seed + 2) * 0.2


def _c(v):
    return 0 if v < 0 else 255 if v > 255 else int(v)


def build(fn):
    out = bytearray(SIZE * SIZE * 4)
    i = 0
    for y in range(SIZE):
        for x in range(SIZE):
            px = fn(x, y)
            out[i] = _c(px[0])
            out[i + 1] = _c(px[1])
            out[i + 2] = _c(px[2])
            out[i + 3] = px[3] if len(px) > 3 else 255
            i += 4
    return bytes(out)


def tint(base, k):
    return [rround(c * k) for c in base]


def _rgb_at(tex, x, y):
    i = (y * SIZE + x) * 4
    return [tex[i], tex[i + 1], tex[i + 2]]


def solid(r, g, b):
    return build(lambda x, y: (r, g, b))


def bricks(base, mortar, seed, rows=4, cols=2, moss=False):
    bh = SIZE // rows
    bw = SIZE // cols

    def px(x, y):
        row = y // bh
        ox = (x + (bw // 2 if row % 2 == 1 else 0)) % SIZE
        col = ox // bw
        edge = y % bh == 0 or ox % bw == 0
        n = fbm(x, y, seed)
        if edge:
            return tint(mortar, 0.8 + n * 0.3)
        k = 0.75 + hash_(col, row, seed) * 0.35 + (n - 0.5) * 0.35
        if y % bh == bh - 1 or ox % bw == bw - 1:
            k *= 0.82
        c = tint(base, k)
        if moss and noise(x, y, 8, seed + 9) > 0.62:
            c = [rround(c[0] * 0.6), rround(c[1] * 0.95 + 20), rround(c[2] * 0.5)]
        return c

    return build(px)


def stone_brick():
    return bricks([118, 110, 100], [48, 44, 40], 11)


def mossy_brick():
    return bricks([100, 104, 90], [40, 44, 36], 12, moss=True)


def flagstone():
    def px(x, y):
        jx = rround(noise(0, y, 16, 5) * 6)
        jy = rround(noise(x, 0, 16, 6) * 6)
        cx = (x + jx) // 32
        cy = (y + jy) // 32
        gap = (x + jx) % 32 < 2 or (y + jy) % 32 < 2
        n = fbm(x, y, 21)
        if gap:
            return tint([40, 38, 36], 0.9 + n * 0.2)
        return tint([104, 98, 90], 0.72 + hash_(cx, cy, 3) * 0.3 + (n - 0.5) * 0.4)

    return build(px)


def rough_stone():
    return build(lambda x, y: tint([84, 80, 76], 0.6 + fbm(x, y, 31) * 0.6))


def dirt():
    return build(lambda x, y: tint([96, 74, 52], 0.65 + fbm(x, y, 41) * 0.5 + (hash_(x, y, 2) - 0.5) * 0.15))


def grass():
    def px(x, y):
        n = fbm(x, y, 51)
        blade = 1.25 if hash_(x, y, 7) > 0.86 else 1.0
        return tint([62, 92, 44], (0.62 + n * 0.5) * blade)

    return build(px)


def wood_plank(base=(112, 78, 48)):
    def px(x, y):
        plank = x // 16
        grain = math.sin((y + hash_(plank, 0, 4) * 64) * 0.35 + noise(x, y, 4, 8) * 3) * 0.08
        k = 0.78 + hash_(plank, 1, 4) * 0.2 + grain + (fbm(x, y, 61) - 0.5) * 0.25
        if x % 16 == 0:
            k *= 0.55
        return tint(base, k)

    return build(px)


def door_wood():
    planks = wood_plank((96, 64, 40))

    def px(x, y):
        if y in (10, 11, 12, 52, 53, 54):
            return (120, 116, 108) if x % 16 == 8 else (54, 52, 50)
        return _rgb_at(planks, x, y)

    return build(px)


def plaster():
    def px(x, y):
        grime = 1.0 - (y - 48) / 40.0 if y > 48 else 1.0
        return tint([186, 176, 150], (0.82 + fbm(x, y, 71) * 0.22) * grime)

    return build(px)


def timber():
    wall = plaster()

    def px(x, y):
        beam = x < 4 or x >= 60 or y < 4 or y >= 60 or abs(x - y) < 3
        if beam:
            return tint([70, 48, 30], 0.8 + fbm(x, y, 81) * 0.3)
        return _rgb_at(wall, x, y)

    return build(px)


def _cobbles(seed, joint, cell=8):
    """Rounded cobbles set close in a tileable Voronoi pattern: each stone domed (lit on its crown,
    darker toward its rim) and of its own shade, the joints between them coloured by `joint(x, y)`."""
    n = SIZE // cell

    def px(x, y):
        cx, cy = x // cell, y // cell
        best, second, owner = 99.0, 99.0, (0, 0)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                hx, hy = (cx + i) % n, (cy + j) % n
                ppx = (cx + i) * cell + (0.2 + hash_(hx, hy, seed) * 0.6) * cell
                ppy = (cy + j) * cell + (0.2 + hash_(hx, hy, seed + 1) * 0.6) * cell
                d = math.hypot(x - ppx, y - ppy)
                if d < best:
                    second, best, owner = best, d, (hx, hy)
                elif d < second:
                    second = d
        edge = second - best
        if edge < 1.4:
            return joint(x, y)
        hue = hash_(*owner, seed + 2)
        base = [128, 122, 112] if hue < 0.55 else [142, 128, 104] if hue < 0.8 else [108, 108, 110]
        dome = 1.08 - min(best / (cell * 0.75), 1.0) ** 2 * 0.35
        rim = 0.82 if edge < 2.4 else 1.0  # the stone rounds down into its joint
        return tint(base, (0.72 + hash_(*owner, seed + 3) * 0.22 + (fbm(x, y, 91) - 0.5) * 0.18) * dome * rim)

    return px


def cobble():
    """Grey-brown cobbles in dark, earthy joints."""
    return build(_cobbles(9, lambda x, y: tint([46, 42, 36], 0.8 + fbm(x, y, 92) * 0.4)))


def cobble_moss():
    """Cobbles going green at the edge of a lawn: grass in the joints, and tufts over some stones."""
    stones = _cobbles(29, lambda x, y: tint([54, 80, 38], 0.6 + fbm(x, y, 93) * 0.4))

    def px(x, y):
        if noise(x, y, 16, 94) > 0.76 and hash_(x, y, 95) > 0.45:
            return tint([62, 96, 44], 0.6 + fbm(x, y, 51) * 0.5)
        return stones(x, y)

    return build(px)


def setts():
    """Squared paving setts laid in courses, joints staggered from row to row: the town's main roads."""
    rows = 8  # px per course (a quarter metre)

    def px(x, y):
        row = y // rows
        shift = (row * 7) % 16
        xx = (x + shift) % SIZE
        col = xx // 16
        if y % rows == 0 or xx % 16 == 0:
            return tint([50, 46, 40], 0.8 + fbm(x, y, 96) * 0.3)
        k = 0.74 + hash_(col, row, 97) * 0.22 + (fbm(x, y, 98) - 0.5) * 0.2
        if y % rows == 1 or xx % 16 == 1:
            k *= 1.12  # the worn upper edge catches the light
        elif y % rows == rows - 1 or xx % 16 == 15:
            k *= 0.82
        return tint([150, 140, 122], k)

    return build(px)


def stucco():
    """Warm ochre render, sun-faded and stained, worn thin here and there over the stones beneath."""

    def px(x, y):
        n = fbm(x, y, 141)
        wear = noise(x, y, 16, 142) * 0.6 + noise(x, y, 8, 145) * 0.4
        if wear > 0.74:  # a worn patch: the coursed rubble shows faintly through
            if y % 8 == 0 or (x + (y // 8) * 5) % 13 == 0:
                return tint([150, 126, 96], 0.9)
            return tint([190, 164, 124], 0.8 + hash_(x // 13, y // 8, 143) * 0.18)
        streak = 0.95 if noise(x, y, 4, 144) > 0.8 else 1.0
        return tint([206, 178, 132], (0.8 + n * 0.25) * streak)

    return build(px)


def ashlar():
    """Dressed tan sandstone in courses of long and short blocks, with pale lime mortar."""

    def px(x, y):
        row = y // 16
        shift = 0 if row % 2 == 0 else 20
        xx = (x + shift) % SIZE
        widths = (24, 40) if row % 2 == 0 else (36, 28)
        col = 0 if xx < widths[0] else 1
        left = 0 if col == 0 else widths[0]
        if y % 16 == 0 or xx == left:
            return tint([196, 186, 160], 0.9)
        k = 0.78 + hash_(col, row, 151) * 0.18 + (fbm(x, y, 152) - 0.5) * 0.22
        if y % 16 == 15 or xx == left + 1:
            k *= 0.85
        return tint([186, 158, 116], k)

    return build(px)


def terracotta():
    """Barrel tiles of fired clay in rows, each tile rounded and overlapping the one below."""

    def px(x, y):
        row = y // 12
        ox = (x + (4 if row % 2 else 0)) % 8
        curve = math.cos((ox - 3.5) / 4.0 * math.pi / 2)
        lap = (y % 12) / 12.0
        if y % 12 == 11:
            return (60, 26, 16)
        k = 0.58 + curve * 0.42 - lap * 0.12 + hash_((x + (4 if row % 2 else 0)) // 8, row, 161) * 0.18
        k += (fbm(x, y, 162) - 0.5) * 0.15
        return tint([182, 86, 52], k)

    return build(px)


def water():
    def px(x, y):
        w = math.sin(x * 0.3 + noise(x, y, 8, 3) * 4) * math.sin(y * 0.2) * 0.12
        return tint([38, 64, 78], 0.8 + w + fbm(x, y, 101) * 0.25)

    return build(px)


def roof():
    def px(x, y):
        row = y // 8
        ox = (x + (4 if row % 2 == 1 else 0)) % 8
        curve = (abs(ox - 4) / 4.0) * 0.25
        if y % 8 == 7:
            return (44, 26, 22)
        k = 0.7 + hash_(x // 8, row, 13) * 0.2 - curve + (fbm(x, y, 111) - 0.5) * 0.2
        return tint([120, 58, 44], k)

    return build(px)


def iron_bars():
    def px(x, y):
        if x % 16 < 4 or y % 32 < 4:
            return [*tint([70, 68, 66], 0.8 + fbm(x, y, 121) * 0.4), 255]
        return (0, 0, 0, 0)

    return build(px)


# --- the Verdant Hollow ------------------------------------------------------


def vine_wall():
    """Dense leaves over dark gaps, crossed by hanging vine strands."""

    def px(x, y):
        n = fbm(x, y, 131)
        leaf = noise(x, y, 4, 132)
        k = 0.45 + n * 0.55
        c = tint([52, 92, 40], k)
        if leaf < 0.32:
            c = tint([18, 30, 16], 0.8 + n * 0.4)
        elif leaf > 0.72:
            c = tint([86, 128, 52], 0.8 + n * 0.3)
        for strand in (5, 22, 41, 57):
            wobble = rround(math.sin(y * 0.25 + strand) * 2 + noise(strand, y, 8, 133) * 3)
            if abs(x - strand - wobble) < 1.5:
                return tint([92, 74, 42], 0.75 + hash_(x, y, 134) * 0.35)
        return c

    return build(px)


def web_wall():
    """A thick sheet of old silk: matted grey-white strands with a few dark tears to see through."""

    def px(x, y):
        n = fbm(x, y, 151)
        if noise(x, y, 8, 152) < 0.22:
            return (0, 0, 0, 0)
        k = 0.55 + n * 0.45
        for i, (a, b) in enumerate(((0.9, 3), (-0.7, 17), (0.25, 40), (-1.4, 52))):
            # Strands at a slant across the sheet; they wrap so the texture tiles.
            if abs((x * a + y - b) % SIZE) < 1.2 + i % 2:
                return [*tint([232, 230, 222], 0.85 + hash_(x, y, 153) * 0.15), 255]
        return [*tint([176, 174, 166], k), 255]

    return build(px)


def bark():
    """Vertical ridged bark with dark furrows."""

    def px(x, y):
        ridge = noise(x, y // 4, 8, 141)
        furrow = math.sin(x * 0.9 + noise(x, y, 16, 142) * 6)
        k = 0.55 + ridge * 0.35 + (fbm(x, y, 143) - 0.5) * 0.3
        if furrow > 0.75:
            k *= 0.5
        return tint([98, 70, 46], k)

    return build(px)


def leaf_litter():
    """Brown forest floor strewn with olive and rust leaves."""

    def px(x, y):
        n = fbm(x, y, 151)
        c = tint([70, 56, 36], 0.6 + n * 0.5)
        cell = hash_(x // 3, y // 3, 152)
        if cell > 0.82:
            c = tint([104, 96, 44], 0.7 + n * 0.4)
        elif cell < 0.12:
            c = tint([118, 64, 34], 0.7 + n * 0.4)
        return c

    return build(px)


def jungle_floor():
    """Dark moss and fern over wet soil."""

    def px(x, y):
        n = fbm(x, y, 161)
        if noise(x, y, 8, 162) < 0.35:
            return tint([62, 50, 34], 0.6 + n * 0.5)
        blade = 1.3 if hash_(x, y, 163) > 0.88 else 1.0
        return tint([46, 82, 36], (0.55 + n * 0.5) * blade)

    return build(px)


def canopy():
    """Leaf canopy seen from below, with a few pale gaps."""

    def px(x, y):
        n = fbm(x, y, 171)
        if noise(x, y, 4, 172) > 0.8 and n > 0.55:
            return tint([150, 170, 120], 0.8 + n * 0.3)
        return tint([30, 56, 28], 0.5 + n * 0.6)

    return build(px)


def foliage():
    """Pale leaf clusters, tinted per tree by the part's colour: bright tufts catching the sun over
    darker hollows, with a few deep gaps."""

    def px(x, y):
        n = fbm(x, y, 191)
        tuft = noise(x, y, 4, 192)
        k = 0.62 + n * 0.45
        if tuft > 0.72:
            k += 0.28  # a sunlit tuft
        elif tuft < 0.2:
            k *= 0.55  # a hollow between clumps
        return tint([210, 216, 200], k)

    return build(px)


def mud():
    def px(x, y):
        n = fbm(x, y, 181)
        wet = 1.15 if noise(x, y, 8, 182) > 0.7 else 1.0
        return tint([66, 52, 34], (0.6 + n * 0.45) * wet)

    return build(px)


def bog():
    """Murky green water with floating scum."""

    def px(x, y):
        w = math.sin(x * 0.25 + noise(x, y, 8, 191) * 4) * math.sin(y * 0.18) * 0.1
        n = fbm(x, y, 192)
        if noise(x, y, 4, 193) > 0.74:
            return tint([78, 96, 40], 0.8 + n * 0.3)
        return tint([34, 54, 34], 0.8 + w + n * 0.25)

    return build(px)


def rapids():
    """Fast shallow water: pale streaks of foam running down the current (+y)."""

    def px(x, y):
        streak = noise(x * 4 % SIZE, y, 8, 201)
        n = fbm(x, y, 202)
        if streak > 0.72:
            return tint([190, 214, 206], 0.8 + n * 0.3)
        return tint([46, 86, 92], 0.8 + n * 0.35 + math.sin(y * 0.5 + x * 0.1) * 0.08)

    return build(px)


def thorns():
    """Leaf litter overgrown with a mat of dark briars and pale thorns."""

    def px(x, y):
        n = fbm(x, y, 211)
        vine = abs(math.sin((x + noise(x, y, 8, 212) * 20) * 0.35)) < 0.18
        vine2 = abs(math.sin((y + noise(x, y, 8, 213) * 20) * 0.3)) < 0.15
        if hash_(x, y, 214) > 0.96:
            return tint([220, 200, 160], 0.9 + n * 0.2)
        if vine or vine2:
            return tint([92, 40, 34], 0.7 + n * 0.4)
        return tint([70, 58, 36], 0.55 + n * 0.35)

    return build(px)


def cliff_rock():
    """Layered grey-brown rock in sloping strata, with moss in the cracks."""

    def px(x, y):
        n = fbm(x, y, 221)
        band = math.sin((y + x * 0.25 + noise(x, y, 16, 222) * 10) * 0.45)
        k = 0.6 + n * 0.35 + band * 0.08
        if band > 0.88:
            return tint([28, 26, 24], 0.9 + n * 0.2)  # a crack between strata
        if band > 0.7 and hash_(x, y, 223) > 0.55:
            return tint([66, 96, 46], 0.7 + n * 0.4)  # moss growing in it
        return tint([108, 100, 88], k)

    return build(px)


def ravine():
    """The chasm floor far below: dark scree half lost in mist."""

    def px(x, y):
        n = fbm(x, y, 231)
        if hash_(x // 2, y // 2, 232) > 0.9:
            return tint([70, 70, 66], 0.6 + n * 0.3)
        return tint([26, 30, 28], 0.6 + n * 0.5)

    return build(px)


def log_wall():
    """Stacked round logs of a woodsman's cabin, chinked with dried mud."""

    def px(x, y):
        row = y // 16
        v = (y % 16) / 15.0
        k = 0.55 + math.sin(v * math.pi) * 0.45  # each log is rounded, lit along its middle
        grain = (noise(x, y, 4, 241 + row) - 0.5) * 0.25
        if y % 16 in (0, 15):
            return tint([78, 66, 48], 0.7 + fbm(x, y, 242) * 0.3)  # mud chinking
        c = tint([110, 78, 48], k + grain)
        if hash_(x // 8, row, 243) > 0.85 and abs(v - 0.5) < 0.2:
            return tint([60, 92, 44], 0.7 + grain)  # moss on the weathered logs
        return c

    return build(px)


def ossuary():
    """A charnel wall: courses of small skulls between courses of long bones stacked end-on,
    all grey-yellow with age, packed in dark mortar."""

    def px(x, y):
        n = fbm(x, y, 51)
        course = y // 8
        if course % 2 == 0:  # a course of skulls
            off = 4 if course % 4 == 0 else 0
            cx = (x + off) % 8 - 3.5
            cy = y % 8 - 3.5
            if (cx / 3.4) ** 2 + (cy / 3.2) ** 2 > 1.0:
                return tint([34, 31, 28], 0.8 + n * 0.4)
            if cy in (-1.5, -0.5) and abs(cx) in (1.5, 2.5):
                return tint([22, 18, 15], 1.0)  # deep eye sockets
            if cy == 1.5 and abs(cx) <= 0.5:
                return tint([40, 34, 28], 1.0)  # the nose hole
            if cy == 2.5 and abs(cx) <= 2.5 and (x % 2 == 0):
                return tint([50, 44, 36], 1.0)  # gaps between the teeth
            k = hash_((x + off) // 8, course, 9)
            return tint([150, 138, 112], 0.6 + k * 0.3 + (n - 0.5) * 0.3 - max(cy, 0) * 0.04)
        # A course of long bones seen end-on and side-on: pale bars with knobbed ends.
        seg = hash_(x // 16, course, 4)
        start = rround(seg * 6)
        local = (x - start) % 16
        if y % 8 in (0, 7) or local in (0, 15):
            return tint([34, 31, 28], 0.8 + n * 0.4)
        knob = local in (1, 2, 13, 14)
        if not knob and y % 8 in (1, 6):
            return tint([34, 31, 28], 0.8 + n * 0.4)
        return tint([140, 128, 104], 0.62 + hash_(x // 16, course, 7) * 0.25 + (n - 0.5) * 0.3)

    return build(px)


# --- the Cinderhold -----------------------------------------------------------------------------


def black_brick():
    """The fortress's soot-black ashlar, with ember-orange glints of slag in the mortar."""
    base = bricks([62, 56, 58], [24, 20, 20], 301, rows=4, cols=2)

    def px(x, y):
        c = _rgb_at(base, x, y)
        if hash_(x, y, 302) > 0.985 and c[0] < 40:
            return [200, 90, 30]
        return c

    return build(px)


def iron_plate():
    """Riveted iron plates, streaked with rust and scorch."""

    def px(x, y):
        n = fbm(x, y, 311)
        seam = x % 32 == 0 or y % 32 == 0
        if seam:
            return tint([30, 28, 30], 0.9 + n * 0.2)
        if (x % 32 in (4, 28)) and (y % 32 in (4, 28)):
            return [130, 126, 130]  # a rivet head
        k = 0.65 + n * 0.4
        c = tint([82, 80, 86], k)
        if noise(x, y, 8, 312) > 0.68:
            c = [rround(c[0] * 1.2 + 20), rround(c[1] * 0.8), rround(c[2] * 0.6)]  # rust
        return c

    return build(px)


def iron_grate():
    """A heavy floor grate over a red glow far below."""

    def px(x, y):
        bar = x % 16 < 4 or y % 16 < 4
        n = fbm(x, y, 321)
        if bar:
            return tint([70, 68, 72], 0.7 + n * 0.4)
        return tint([150, 50, 20], 0.4 + n * 0.5)

    return build(px)


def lava():
    """Molten rock: bright cracks of yellow-white between rafts of dark crust."""

    def px(x, y):
        n = fbm(x, y, 331)
        v = noise(x, y, 8, 332)
        crack = abs(v - 0.5) < 0.07 + n * 0.05
        if crack:
            return [255, rround(200 + n * 50), rround(90 + n * 60)]
        if n > 0.55:
            return [255, rround(110 + n * 60), 30]
        return tint([150, 46, 16], 0.7 + n * 0.6)

    return build(px)


def slag():
    """Cooled slag underfoot: black, glassy, pitted, with a faint red heat in the deepest pits."""

    def px(x, y):
        n = fbm(x, y, 341)
        if hash_(x // 2, y // 2, 342) > 0.94:
            return [110, 34, 14]
        return tint([50, 44, 44], 0.6 + n * 0.6)

    return build(px)


def ash_road():
    """Packed grey ash with cinders trodden into it."""

    def px(x, y):
        n = fbm(x, y, 351)
        if hash_(x, y, 352) > 0.97:
            return [40, 36, 34]
        return tint([104, 98, 94], 0.6 + n * 0.45)

    return build(px)


def slate():
    """Overlapping roof slates, dark blue-grey, edged with soot."""

    def px(x, y):
        row = y // 8
        ox = (x + (8 if row % 2 else 0)) % SIZE
        n = fbm(x, y, 361)
        if y % 8 == 7 or ox % 16 == 0:
            return tint([22, 22, 26], 0.9 + n * 0.2)
        k = 0.7 + hash_(ox // 16, row, 362) * 0.25 + (n - 0.5) * 0.3
        return tint([70, 74, 84], k)

    return build(px)


# A 4x4 ordered-dither matrix (0..15): the sky textures stipple their soft edges with it, the way
# the PS1 faked transparency, since the shader keeps a texel only when its alpha is at least half.
BAYER = (0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5)


def _stipple(x, y, density):
    """Opaque where `density` (0..1) beats this texel's dither threshold."""
    return 255 if density > (BAYER[(y % 4) * 4 + x % 4] + 0.5) / 16 else 0


def clouds():
    """Banks of cloud, tileable left to right: billowing lumps that thin out toward the band's top
    and bottom edges, brighter in their cores. The sky tints them (lit tops, dark undersides)."""

    def px(x, y):
        n = noise(x, y, 16, 402) * 0.55 + noise(x, y, 8, 403) * 0.3 + noise(x, y, 4, 404) * 0.15
        edge = math.sin(math.pi * (y + 0.5) / SIZE)
        density = (n - 0.45) * 7.0 * edge - (1.0 - edge) * 0.5
        k = 0.82 + min(max(density, 0.0), 1.0) * 0.18
        return [rround(255 * k)] * 3 + [_stipple(x, y, density)]

    return build(px)


def cloud_cap():
    """The thin cloud overhead: loose wisps with stippled edges."""

    def px(x, y):
        n = noise(x, y, 16, 412) * 0.6 + noise(x, y, 4, 413) * 0.4
        density = (n - 0.52) * 6.0
        return [240, 240, 240, _stipple(x, y, density)]

    return build(px)


def mist():
    """Horizon haze: long streaks, densest at the bottom and fading to nothing at the top."""

    def px(x, y):
        streak = noise(x, y // 4, 16, 422) * 0.7 + noise(x, y, 8, 423) * 0.3
        density = (y / SIZE) * 1.15 * (0.55 + streak * 0.6)
        return [255, 255, 255, _stipple(x, y, density)]

    return build(px)
