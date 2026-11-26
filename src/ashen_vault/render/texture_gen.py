"""Procedural low-resolution textures. Each generator returns RGBA bytes."""

import math

from ashen_vault.util import rround

SIZE = 64


def all_textures():
    return {
        "stone_brick": stone_brick(),
        "flagstone": flagstone(),
        "cathedral_floor": cathedral_floor(),
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
        "glitter": glitter(),
        "roof": roof(),
        "iron_bars": iron_bars(),
        "vine_wall": vine_wall(),
        "bark": bark(),
        "leaf_litter": leaf_litter(),
        "jungle_floor": jungle_floor(),
        "canopy": canopy(),
        "leaf_card": leaf_card(),
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
        "violet_slate": violet_slate(),
        "clay_tile": clay_tile(),
        "stone_timber": stone_timber(),
        "clouds": clouds(),
        "cloud_cap": cloud_cap(),
        "mist": mist(),
        "ripple": ripple(),
        "ward_net": ward_net(),
        "ash_skin": ash_skin(),
        "ash_rock": ash_rock(),
        "ash_stone": ash_stone(),
        "ash_brick": ash_brick(),
        "ash_ground": ash_ground(),
        "ash_grass": ash_grass(),
        "ash_flagstone": ash_flagstone(),
        "sewer_brick": sewer_brick(),
        "sewer_vault": sewer_vault(),
        "sludge": sludge(),
        "moonstone": moonstone(),
        "moon_paving": moon_paving(),
        "silver_slate": silver_slate(),
        "moon_glass": moon_glass(),
        "sunken_brick": sunken_brick(),
        "ochre_flag": ochre_flag(),
        "cavern_rock": cavern_rock(),
        "crystal_rock": crystal_rock(),
        "sallow_mire": sallow_mire(),
        "fen_mud": fen_mud(),
        "dirt_path": dirt_path(),
        "dirt_hill": dirt_hill(),
        "rotten_wood": rotten_wood(),
        "herran_brick": herran_brick(),
        "herran_ashlar": herran_ashlar(),
        "herran_slate": herran_slate(),
        "encaustic_tile": encaustic_tile(),
        "iron_grating": iron_grating(),
        "lab_tile": lab_tile(),
        "cloud_sea": cloud_sea(),
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


def bricks(base, mortar, seed, rows=4, cols=2):
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
        return tint(base, k)

    return build(px)


def stone_brick():
    return bricks([118, 110, 100], [48, 44, 40], 11)


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


def cathedral_floor():
    """The cathedral's floor: each tile a panel framed in a band of dark red marble with a pale fillet
    inside it, laid in lozenges of cream limestone and grey-violet slate, worn and faintly veined."""

    def px(x, y):
        n = fbm(x, y, 41)
        edge = min(x, y, SIZE - 1 - x, SIZE - 1 - y)
        if edge < 3:  # the border band
            return tint([112, 52, 48], 0.8 + n * 0.3)
        if edge == 3:  # its pale fillet
            return tint([206, 196, 176], 0.9 + n * 0.1)
        u, v = x + y, x - y + SIZE
        if u % 16 == 0 or v % 16 == 0:  # the joints between the lozenges
            return tint([46, 42, 44], 0.9 + n * 0.2)
        vein = 0.08 * math.sin((x * 0.35 + y * 0.12) + noise(x, y, 8, 42) * 6)
        if (u // 16 + v // 16) % 2:
            return tint([198, 188, 168], 0.86 + (n - 0.5) * 0.24 + vein)
        return tint([74, 70, 86], 0.86 + (n - 0.5) * 0.3 + vein)

    return build(px)


def rough_stone():
    return build(lambda x, y: tint([84, 80, 76], 0.6 + fbm(x, y, 31) * 0.6))


def ash_skin():
    """The player's ashen skin: near-white mottled grain (the part's colour sets its grey) shot with
    sparse dark blue-grey streaks running along the limb."""

    def px(x, y):
        k = 0.78 + fbm(x, y, 53) * 0.2 + (hash_(x, y, 54) - 0.5) * 0.16
        if hash_(x, y // 5, 55) < 0.025:  # a faint streak, five pixels long
            return tint([196, 200, 222], 0.72 + hash_(x, y, 56) * 0.1)
        return tint([255, 255, 255], k)

    return build(px)


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


def glitter():
    """The sun's glints on the sea: short bright dashes lying across the swell, cut out against
    nothing (alpha 0 between them), white so the sun's colour tints them."""

    def px(x, y):
        row = y // 4
        if y % 4 > 1 or hash_(x // 6, row, 611) < 0.55:
            return (0, 0, 0, 0)
        if x % 6 == 5:  # a gap between neighbouring dashes
            return (0, 0, 0, 0)
        return (*tint([255, 250, 240], 0.85 + hash_(x // 6, row, 612) * 0.15), 255)

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


def leaf_card():
    """A spray of leaves cut out against nothing (alpha 0 between them), for the town's trees: each
    card is one clump seen side-on, a ragged oval of small leaves with gaps you can see through.
    Pale, so each tree tints it; leaves catch the light toward the spray's top (high rows, which a
    cube's face maps to its top) and darken into its heart."""
    half = SIZE / 2

    def px(x, y):
        dx, dy = (x + 0.5 - half) / half, (y + 0.5 - half) / half
        d = math.sqrt(dx * dx + dy * dy * 1.15)
        edge = noise(x, y, 8, 571) - 0.5  # a ragged outline
        leaf = noise(x, y, 4, 572)  # single leaves, a few texels across
        if d > 0.97 or 1.0 - d * 1.05 + edge * 0.7 + (leaf - 0.5) * 0.45 < 0.12 or leaf < 0.18:
            return (0, 0, 0, 0)
        k = 0.55 + 0.3 * ((y + 0.5) / SIZE) + 0.25 * d  # lit toward the top and the rim
        if leaf > 0.74:
            k += 0.25  # a leaf turned to the sun
        elif leaf < 0.3:
            k *= 0.6  # the shadow at a leaf's edge
        return (*tint([205, 214, 188], k), 255)

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


def _soot(x, y, seed):
    """0..1 how sooty a wall is at (x, y): streaks running down from above, broken by noise."""
    streak = noise(x, 0, 4, seed) * 0.7 + noise(x, y, 16, seed + 1) * 0.3
    return max(streak - 0.55, 0.0) / 0.45


def _ashed(c, k):
    """`c` drifted over with pale ash by `k` (0..1)."""
    return [rround(v + (178 - v) * k) for v in c]


def ash_rock():
    """The cemetery's cliffs: pale grey rock in sloping strata, no moss, soot streaked down from its
    cracks and ash settled on every ledge."""

    def px(x, y):
        n = fbm(x, y, 401)
        band = math.sin((y + x * 0.25 + noise(x, y, 16, 402) * 10) * 0.45)
        if band > 0.88:
            return tint([26, 24, 24], 0.9 + n * 0.2)  # a crack between strata
        c = tint([112, 108, 104], 0.62 + n * 0.35 + band * 0.08)
        if 0.62 < band <= 0.88 and hash_(x, y, 403) > 0.35:
            return _ashed(c, 0.55)  # ash on the ledge below the crack
        return tint(c, 1 - 0.45 * _soot(x, y, 404))

    return build(px)


def ash_stone():
    """Rough blocks of grey-white stone, charred dark where they meet."""
    bh, bw = 16, 32

    def px(x, y):
        row = y // bh
        ox = (x + (bw // 2 if row % 2 else 0)) % SIZE
        n = fbm(x, y, 411)
        dy, dx = min(y % bh, bh - 1 - y % bh), min(ox % bw, bw - 1 - ox % bw)
        edge = min(dx, dy)
        if edge == 0:
            return tint([30, 28, 28], 0.8 + n * 0.3)
        char = max(0.0, 1 - edge / 4) * (0.5 + noise(x, y, 8, 412) * 0.5)
        c = tint([150, 146, 140], 0.7 + hash_(ox // bw, row, 413) * 0.2 + (n - 0.5) * 0.35)
        return tint(c, 1 - 0.6 * char)

    return build(px)


def ash_brick():
    """Cold grey brick in soot-black mortar, the lower courses crusted with pale ash."""
    base = bricks([112, 108, 106], [24, 22, 22], 421)

    def px(x, y):
        i = (y * SIZE + x) * 4
        c = [base[i], base[i + 1], base[i + 2]]
        c = tint(c, 1 - 0.35 * _soot(x, y, 422))
        crust = max(0.0, (y - 40) / 24) * noise(x, y, 8, 423)
        return _ashed(c, min(crust * 1.4, 0.7))

    return build(px)


def ash_ground():
    """Loose pale ash underfoot, with darker cinders and the odd fleck of bone."""

    def px(x, y):
        n = fbm(x, y, 431)
        h = hash_(x, y, 432)
        if h > 0.985:
            return [196, 190, 172]  # a fleck of bone
        if h < 0.03:
            return tint([44, 40, 38], 0.9 + n * 0.3)  # a cinder
        return tint([150, 146, 142], 0.62 + n * 0.4 + (hash_(x, y, 433) - 0.5) * 0.1)

    return build(px)


def ash_grass():
    """Dead grass, grey-brown and thin, with ash drifted between the blades."""

    def px(x, y):
        n = fbm(x, y, 441)
        if noise(x, y, 16, 442) > 0.58:
            return tint([140, 136, 132], 0.66 + n * 0.35)  # ash drifted over it
        blade = 1.25 if hash_(x, y, 443) > 0.84 else 1.0
        return tint([92, 86, 70], (0.6 + n * 0.45) * blade)

    return build(px)


def ash_flagstone():
    """Flagstones under a dusting of ash, thickest in the joints."""
    base = flagstone()

    def px(x, y):
        i = (y * SIZE + x) * 4
        c = tint([base[i], base[i + 1], base[i + 2]], 0.95)
        dark = c[0] < 50  # a joint
        return _ashed(c, 0.55 if dark else 0.25 * noise(x, y, 8, 451))

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


def violet_slate():
    """Fish-scale roof slates of a dusky violet, laid in staggered courses: each scale rounded at its
    foot, lit along its crown and shadowed where it laps the course below, edged with soot."""

    def px(x, y):
        row = y // 4
        ox = (x + (2 if row % 2 else 0)) % 4
        dy = y % 4
        # The scale's rounded foot: the lower edge curves up toward the scale's sides.
        foot = 3 - abs(ox - 1.5) ** 2 / 2.0
        n = fbm(x, y, 371)
        if dy > foot:
            return tint([56, 40, 68], 0.85 + n * 0.25)
        k = 0.72 + hash_((x + (2 if row % 2 else 0)) // 4, row, 372) * 0.22 + (n - 0.5) * 0.3
        k += (1 - dy / 4) * 0.08  # lit along the crown, darker toward the lap
        return tint([92, 66, 118], k)

    return build(px)


def clay_tile():
    """Weathered terracotta barrel tiles in staggered courses (eight across, eight up the slope): each
    tile rounded across its width (lit along its crown, shaded into the pan between), fired its own
    shade from brick-red to warm tan, darkened by soot toward its foot, with a dark lap shadow where
    the course above overhangs it and a few flecks of grey lichen and green moss. Row 0 is the eaves:
    models' faces map their foot to the texture's first row."""

    def px(x, y):
        row = y // 8
        shift = 4 if row % 2 else 0
        ox = (x + shift) % 8
        tile = (x + shift) // 8 % 8
        dy = y % 8  # 0 at the tile's foot (toward the eaves), 7 under the lap of the course above
        n = fbm(x, y, 381)
        if dy == 7:  # the lap: the course above casts its shadow over this one
            moss = hash_(x, row, 387) > 0.86
            return tint([62, 70, 40] if moss else [58, 30, 22], 0.85 + n * 0.3)
        hue = hash_(tile, row, 382)
        base = [150 + 26 * hue, 72 + 20 * hue, 48 + 10 * hue]
        if hash_(tile, row, 383) > 0.86:  # now and then a tile fired darker, or a newer brighter one
            base = tint(base, 0.78 if hash_(tile, row, 384) > 0.5 else 1.12)
        curve = math.cos((ox - 3.5) / 4.0 * math.pi / 2)  # round across its width
        k = 0.5 + curve * 0.6 + (n - 0.5) * 0.22
        k *= 0.78 + 0.22 * dy / 6  # soot gathered toward its foot
        if dy == 6:
            k *= 0.86  # deepening into the lap's shadow
        if ox in (0, 7):
            k *= 0.8  # the pan between two barrels
        k *= 1.0 - 0.12 * (1 - y / 63) ** 2  # rain-blackened along the eaves
        if hash_(x, y, 385) > 0.982 and noise(x, y, 16, 386) > 0.5:  # a fleck of lichen
            return tint([150, 148, 112] if hash_(x, y, 388) > 0.5 else [96, 112, 64], 0.85 + n * 0.25)
        return tint(base, k)

    return build(px)


def stone_timber():
    """A house wall of two storeys in one: a lower half of coursed ashlar (the stone ground floor) and
    an upper half framed in dark oak (sill beam, posts, a top plate and raking braces) over a lime
    plaster infill. Its last row is the wall's foot, as on the map's walls: on a wall it repeats every
    tile's height."""
    stone = ashlar()
    lime = plaster()

    def px(x, y):
        if y >= 32:  # the ground floor's ashlar, two courses of it
            if y == 32:
                return tint([46, 34, 24], 0.9)  # the shadow under the sill beam
            return _rgb_at(stone, x, y)
        sill = y >= 28
        plate = y < 3
        post = x < 3 or x >= 61 or 30 <= x < 34
        lx = x % 32  # each panel's own coordinates
        brace = 3 <= y < 28 and (abs((lx - 3) - (y - 3)) < 2 if x < 32 else abs((60 - x) - (y - 3)) < 2)
        if sill or plate or post or brace:
            k = 0.78 + fbm(x, y, 391) * 0.3
            if (sill and y == 31) or (plate and y == 2):
                k *= 0.8  # a beam's lower arris in shade
            return tint([70, 48, 30], k)
        return _rgb_at(lime, x, y + 32)  # the plaster, its grime toward the beam below

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


def ripple():
    """One thin ring of light on water, its line broken here and there, on nothing."""

    def px(x, y):
        r = math.hypot((x + 0.5) / SIZE - 0.5, (y + 0.5) / SIZE - 0.5) * 2
        if abs(r - 0.92) > 0.05 or hash_(rround(math.atan2(y - 32, x - 32) * 6), 0, 451) < 0.15:
            return (0, 0, 0, 0)
        return (255, 255, 255, 255)

    return build(px)


def ward_net():
    """A ward's dome of light: a lattice of thin glowing diamonds, with knots where they cross,
    see-through between its strands."""

    def px(x, y):
        a, b = (x + y) % 16, (x - y) % 16
        if a == 0 or b == 0:
            return (*tint([255, 255, 255], 0.85 + 0.15 * noise(x, y, 8, 461)), 255)
        if (a in (1, 15) and b in (1, 15)) or hash_(x, y, 462) > 0.985:
            return (255, 255, 255, 255)
        return (0, 0, 0, 0)

    return build(px)


# --- the Harrow Sewers ---------------------------------------------------------------------------


def _slimed(c, k):
    """`c` filmed over with green-brown slime by `k` (0..1)."""
    return [rround(c[0] + (58 - c[0]) * k), rround(c[1] + (76 - c[1]) * k), rround(c[2] + (36 - c[2]) * k)]


def sewer_brick():
    """Old red-brown sewer brick in black mortar, slime streaked down its face from the vault, a dark
    tide line across its lower courses where the sludge has stood."""
    base = bricks([104, 72, 58], [26, 24, 20], 501, rows=5, cols=2)

    def px(x, y):
        c = _rgb_at(base, x, y)
        streak = noise(x, 0, 4, 502) * 0.7 + noise(x, y, 8, 503) * 0.3
        drip = max(streak - 0.5, 0.0) / 0.5 * (1 - y / SIZE * 0.4)
        c = _slimed(c, min(drip * 1.3, 0.85))
        if y > 44:  # below the tide line: stained dark and greened
            c = _slimed(tint(c, 0.7), 0.35 + 0.2 * noise(x, y, 4, 504))
        elif 41 <= y <= 44:
            c = tint([50, 54, 30], 0.8 + 0.3 * noise(x, y, 4, 505))  # the scum the tide left
        if hash_(x, y, 506) > 0.997:
            c = [118, 132, 80]  # a bead of wet light
        return c

    return build(px)


def sewer_vault():
    """The vault overhead: courses of dark wet brick, beaded with drips and furred with pale nitre."""
    base = bricks([84, 62, 52], [20, 18, 16], 511, rows=4, cols=3)

    def px(x, y):
        c = _rgb_at(base, x, y)
        if noise(x, y, 8, 512) > 0.66:
            c = [rround(v + (150 - v) * 0.35) for v in c]  # nitre bloom
        if hash_(x, y, 513) > 0.985:
            c = [120, 140, 96]  # a drip about to fall
        return _slimed(c, 0.2)

    return build(px)


def sludge():
    """Thick brown-green sewage: swirled murk with rafts of yellow scum and the odd bubble."""

    def px(x, y):
        swirl = math.sin(x * 0.2 + noise(x, y, 8, 521) * 5) * math.sin(y * 0.16 + noise(x, y, 16, 522) * 3)
        n = fbm(x, y, 523)
        if noise(x, y, 4, 524) > 0.76:
            return tint([110, 112, 52], 0.8 + n * 0.3)  # scum
        if hash_(x, y, 525) > 0.99:
            return [150, 150, 96]  # a bubble's glint
        return tint([62, 58, 34], 0.75 + swirl * 0.12 + n * 0.3)

    return build(px)


# --- Vesperholm, the Moonbound City ----------------------------------------------------------------


def moonstone():
    """Vesperholm's walls: dressed blocks of pale blue-grey stone in long courses, veined with silver
    that catches the moon, rimed with frost along the joints and darker where the rime has run."""

    def px(x, y):
        row = y // 16
        xx = (x + (0 if row % 2 == 0 else 22)) % SIZE
        widths = (28, 36) if row % 2 == 0 else (40, 24)
        col = 0 if xx < widths[0] else 1
        left = 0 if col == 0 else widths[0]
        if y % 16 == 0 or xx == left:
            return tint([206, 214, 228], 0.82 + noise(x, y, 4, 601) * 0.18)  # frost in the joint
        n = fbm(x, y, 602)
        k = 0.74 + hash_(col, row, 603) * 0.16 + (n - 0.5) * 0.24
        if y % 16 == 15 or xx == left + 1:
            k *= 0.8
        c = tint([138, 146, 164], k)
        vein = abs(math.sin(x * 0.21 + y * 0.09 + noise(x, y, 16, 604) * 6))
        if vein < 0.06:
            c = [min(v + 52, 255) for v in c]  # a silver vein
        if y % 16 > 11 and noise(x, y, 4, 605) > 0.62:
            c = tint(c, 0.86)  # where the rime has run down from the joint above
        return c

    return build(px)


def moon_paving():
    """The streets' paving: big square flags of pale moonstone, worn smooth, a hoar frost settled in
    the gaps between them and glittering here and there on their faces."""

    def px(x, y):
        jx = rround(noise(0, y, 16, 611) * 4)
        jy = rround(noise(x, 0, 16, 612) * 4)
        cx, cy = (x + jx) // 32, (y + jy) // 32
        if (x + jx) % 32 < 2 or (y + jy) % 32 < 2:
            return tint([196, 206, 222], 0.78 + noise(x, y, 4, 613) * 0.2)  # frost in the gaps
        n = fbm(x, y, 614)
        c = tint([122, 130, 148], 0.76 + hash_(cx, cy, 615) * 0.22 + (n - 0.5) * 0.3)
        if hash_(x, y, 616) > 0.992:
            c = [222, 230, 246]  # a glint of frost
        return c

    return build(px)


def silver_slate():
    """Roof slates and the wall walks' flags: thin, square-cut slate of a silvered blue-grey, in
    staggered courses, each slate's lower edge catching the moon in a pale line."""

    def px(x, y):
        row = y // 8
        ox = (x + (4 if row % 2 else 0)) % 8
        dy = y % 8
        n = fbm(x, y, 621)
        if ox == 0:
            return tint([46, 52, 66], 0.9 + n * 0.2)  # the joint between two slates
        if dy == 7:
            return tint([176, 186, 206], 0.85 + n * 0.2)  # the lit lower edge
        k = 0.7 + hash_((x + (4 if row % 2 else 0)) // 8, row, 622) * 0.24 + (n - 0.5) * 0.26
        return tint([96, 104, 124], k + (dy / 8) * 0.08)

    return build(px)


def moon_glass():
    """Frosted moon-glass: leaded panes of pale blue and silver-white, a few of violet, frost feathering
    across them, the lead dark between. Vesperholm's windows, and the glass bridge underfoot."""
    tints = ([168, 190, 226], [204, 214, 236], [150, 172, 214], [176, 158, 214])

    def px(x, y):
        # Diamond quarries: lead runs along both diagonals every 16 texels.
        a, b = (x + y) % 16, (x - y) % 16
        if a == 0 or b == 0:
            return [44, 46, 56]  # the lead
        cell = ((x + y) // 16 + (x - y) // 16 * 3) % 4
        n = fbm(x, y, 631)
        c = tint(tints[cell], 0.8 + n * 0.25)
        feather = abs(math.sin(x * 0.5 + noise(x, y, 8, 632) * 7) * math.cos(y * 0.45))
        if feather > 0.93:
            c = [min(v + 34, 255) for v in c]  # frost feathering across the pane
        return c

    return build(px)


# --- Old Harrowmere, the sunken city ---------------------------------------------------------------


def sunken_brick():
    """The drowned city's warm sandstone brick in long, low courses, worn soft at the edges, a pale
    crust of old silt in the joints and a dark band low down where the water stood for centuries."""
    base = bricks([150, 118, 84], [70, 58, 44], 601, rows=5, cols=2)

    def px(x, y):
        c = _rgb_at(base, x, y)
        if noise(x, y, 8, 602) > 0.7:
            c = [rround(v + (196 - v) * 0.25) for v in c]  # silt crusted on it
        if y > 46:
            c = tint(c, 0.72 + 0.1 * noise(x, y, 4, 603))  # the old water line
        return c

    return build(px)


def ochre_flag():
    """Big ochre paving slabs, cracked and sunk unevenly, silt and grit drifted in the gaps."""

    def px(x, y):
        jx = rround(noise(0, y, 16, 611) * 5)
        jy = rround(noise(x, 0, 16, 612) * 5)
        cx = (x + jx) // 32
        cy = (y + jy) // 32
        gap = (x + jx) % 32 < 2 or (y + jy) % 32 < 2
        n = fbm(x, y, 613)
        if gap:
            return tint([70, 60, 46], 0.85 + n * 0.25)
        crack = abs(math.sin((x * 0.3 + y * 0.7) * 0.2 + noise(x, y, 8, 614) * 4)) < 0.03
        if crack and hash_(cx, cy, 615) > 0.6:
            return tint([78, 66, 52], 0.9)
        return tint([128, 108, 82], 0.72 + hash_(cx, cy, 616) * 0.24 + (n - 0.5) * 0.3)

    return build(px)


def crystal_rock():
    """The rock of the Glimmering Cave under the Vesper Gate: cold blue-grey stone in broken folds,
    flecked with glinting facets of violet moon-crystal and seamed with veins of it."""

    def px(x, y):
        n = fbm(x, y, 631)
        fold = math.sin((y + noise(x, y, 16, 632) * 12) * 0.4)
        if fold > 0.92:
            return tint([20, 20, 34], 0.9 + n * 0.2)  # a cleft
        if hash_(x // 3, y // 3, 633) > 0.965:
            return tint([196, 182, 255], 0.75 + hash_(x, y, 634) * 0.3)  # a glinting facet
        if abs(noise(x, y, 24, 635) - 0.5) < 0.02:
            return tint([128, 112, 214], 0.8 + n * 0.3)  # a vein of crystal
        return tint([74, 78, 102], 0.6 + n * 0.4 + max(fold, 0) * 0.12)

    return build(px)


def sallow_mire():
    """The Sallow Fen's fouled water: murky violet, an oily sheen swirling over it, rafts of pale
    lilac scum and sodden reed-litter floating on it."""

    def px(x, y):
        n = fbm(x, y, 641)
        swirl = math.sin(x * 0.22 + noise(x, y, 8, 642) * 5) * math.sin(y * 0.17 + noise(x, y, 12, 643) * 3)
        if noise(x, y, 4, 644) > 0.76:
            return tint([150, 120, 170], 0.75 + n * 0.3)  # a raft of scum
        if hash_(x // 2, y // 5, 645) > 0.985:
            return tint([86, 92, 52], 0.8 + n * 0.2)  # a floating reed
        if swirl > 0.55:
            return tint([118, 70, 150], 0.8 + n * 0.25)  # the oily sheen
        return tint([56, 30, 74], 0.75 + swirl * 0.12 + n * 0.3)

    return build(px)


def fen_mud():
    """The fen's banks: dark peaty mud stained violet where the mire seeps up through it, with
    trodden reed stalks pressed into it."""

    def px(x, y):
        n = fbm(x, y, 651)
        if noise(x, y, 6, 652) > 0.72:
            return tint([74, 48, 84], 0.65 + n * 0.35)  # a violet seep
        if abs(noise(x, y, 10, 653) - 0.5) < 0.015:
            return tint([110, 104, 64], 0.7 + n * 0.3)  # a pressed reed
        return tint([58, 46, 40], 0.6 + n * 0.45)

    return build(px)


def dirt_path():
    """A packed earth path through the fen: firm brown dirt, slightly raised, with scattered
    pebbles and the faint impression of wagon ruts. No toxic stain here."""

    def px(x, y):
        n = fbm(x, y, 661)
        rut = math.sin(x * 0.3 + noise(x, y, 6, 662) * 0.5) * 0.05
        if noise(x, y, 8, 663) > 0.92:
            return tint([90, 76, 58], 0.55 + n * 0.3)  # a pebble
        if abs(noise(x, y, 12, 664) - 0.5) < 0.008:
            return tint([130, 110, 86], 0.7 + n * 0.2)  # a highlight
        return tint([106, 88, 66], 0.65 + rut + n * 0.35)

    return build(px)


def dirt_hill():
    """A raised mound of firm earth in the fen: a safe island of packed soil and grass roots,
    standing above the toxic mire. Green-brown with tufts of hardy sedge."""

    def px(x, y):
        n = fbm(x, y, 671)
        if noise(x, y, 5, 672) > 0.88:
            return tint([120, 108, 72], 0.7 + n * 0.25)  # a grass tuft
        if noise(x, y, 7, 673) > 0.95:
            return tint([72, 60, 44], 0.6 + n * 0.3)  # a root
        return tint([98, 84, 58], 0.65 + n * 0.4)

    return build(px)


def rotten_wood():
    """The bridge's deck: ancient blackened timber, warped and cracked by decades of violet mist.
    Deep grey-brown with mossy green stains and violet slime in the cracks."""

    def px(x, y):
        n = fbm(x, y, 681)
        grain = math.sin(x * 0.45 + noise(x, y, 10, 682) * 0.3)
        crack = noise(x, y, 4, 683) > 0.98
        if crack:
            return tint([50, 38, 30], 0.5 + n * 0.3)  # a deep crack
        if grain > 0.85:
            return tint([68, 58, 46], 0.7 + n * 0.2)  # a raised grain
        if noise(x, y, 8, 684) > 0.93:
            return tint([82, 90, 68], 0.6 + n * 0.3)  # moss stain
        if noise(x, y, 12, 685) > 0.97:
            return tint([110, 70, 140], 0.4 + n * 0.2)  # violet slime
        return tint([60, 50, 40], 0.65 + n * 0.35)

    return build(px)


def cavern_rock():
    """The walls of the great cavern the old city sank into: warm brown rock in steep, broken folds,
    lit amber at the ridges, black in the clefts."""

    def px(x, y):
        n = fbm(x, y, 621)
        fold = math.sin((x + noise(x, y, 16, 622) * 14) * 0.35)
        if fold > 0.9:
            return tint([30, 24, 20], 0.9 + n * 0.2)  # a cleft
        k = 0.55 + n * 0.4 + max(fold, 0) * 0.15
        return tint([120, 96, 70], k)

    return build(px)


# --- Herran's Castle, above the clouds -------------------------------------------------------------


def herran_brick():
    """The castle's walls: hard red brick in Flemish bond, every fifth course a band of dun brick, the
    mortar black with soot, soot streaking the faces, the headers a shade darker than the stretchers."""

    def px(x, y):
        row = y // 6
        dy = y % 6
        shift = 0 if row % 2 == 0 else 6
        xx = (x + shift) % SIZE
        unit = xx // 12  # Flemish bond: a stretcher (8) then a header (4) along each course
        within = xx % 12
        header = within >= 8
        if dy == 5 or within in (0, 8):
            return tint([24, 22, 22], 0.8 + noise(x, y, 4, 701) * 0.3)  # the sooted mortar
        n = fbm(x, y, 702)
        if row % 5 == 2:  # the cream band
            return tint([112, 100, 82], 0.7 + hash_(unit, row, 703) * 0.14 + (n - 0.5) * 0.2)
        base = [84, 32, 26] if header else [102, 40, 30]
        soot = 0.55 + 0.45 * noise(x, y, 12, 705)  # soot streaks darken the face
        k = (0.66 + hash_(unit * 2 + header, row, 704) * 0.2 + (n - 0.5) * 0.24) * soot
        return tint(base, k + (0.05 if dy == 0 else 0))

    return build(px)


def herran_ashlar():
    """Dressed limestone gone grey with soot and rain: the quoins, cornices and the paving, in square-cut
    blocks with fine dark joints."""

    def px(x, y):
        row = y // 16
        xx = (x + (0 if row % 2 == 0 else 16)) % SIZE
        col = xx // 32
        if y % 16 == 0 or xx % 32 == 0:
            return tint([44, 42, 40], 0.8 + noise(x, y, 4, 711) * 0.16)
        n = fbm(x, y, 712)
        k = 0.8 + hash_(col, row, 713) * 0.14 + (n - 0.5) * 0.22
        c = tint([86, 82, 76], k)
        if hash_(x, y, 714) > 0.985:
            c = tint(c, 0.82)  # a pit in the stone
        return c

    return build(px)


def herran_slate():
    """Fish-scale slates of the mansard roofs and conical caps: rounded tails in staggered rows, blue-black
    with a violet cast, each tail's rim catching the lamplight."""

    def px(x, y):
        row = y // 8
        ox = (x + (4 if row % 2 else 0)) % 8
        dy = y % 8
        n = fbm(x, y, 721)
        # A rounded tail: the bottom of each scale is an arc.
        edge = 7 - rround(((ox - 3.5) / 4.0) ** 2 * 3)
        if dy > edge:
            return tint([10, 10, 16], 0.9 + n * 0.2)  # shadow under the tail
        if dy == edge:
            return tint([70, 74, 100], 0.85 + n * 0.2)  # the lamplit rim
        k = 0.72 + hash_((x + (4 if row % 2 else 0)) // 8, row, 722) * 0.22 + (n - 0.5) * 0.24
        return tint([34, 36, 52], k + (dy / 8) * 0.1)

    return build(px)


def encaustic_tile():
    """The halls' floors: encaustic tiles in a four-tile pattern, dull terracotta and blue-black, a
    dun eight-pointed star in each, worn darker where the drakes' claws have dragged."""

    def px(x, y):
        tx, ty = x % 16, y % 16
        if tx == 0 or ty == 0:
            return tint([16, 14, 14], 0.9 + noise(x, y, 4, 731) * 0.1)  # the grout
        cx, cy = abs(tx - 8), abs(ty - 8)
        n = fbm(x, y, 732)
        quarter = ((x // 16) + (y // 16)) % 2
        if cx + cy <= 4 or ((cx <= 1 or cy <= 1) and cx + cy <= 6):  # the star
            c = [128, 108, 70]
        elif max(cx, cy) >= 6:  # the border
            c = [22, 24, 34] if quarter else [86, 28, 26]
        else:
            c = [86, 28, 26] if quarter else [22, 24, 34]
        k = 0.7 + (n - 0.5) * 0.26
        if noise(x, y, 8, 733) > 0.72:
            k *= 0.7  # worn
        return tint(c, k)

    return build(px)


def iron_grating():
    """The skybridges' decks: cast-iron plates in a lattice of diamonds, painted a dark green long since
    flaked to rust, the gaps between them black."""

    def px(x, y):
        a, b = (x + y) % 8, (x - y) % 8
        n = fbm(x, y, 741)
        if a < 2 or b < 2:
            c = [52, 66, 56] if noise(x, y, 8, 742) > 0.42 else [112, 64, 40]  # paint, or rust
            k = 0.82 + (n - 0.5) * 0.3 + (0.12 if a == 0 or b == 0 else 0)
            return tint(c, k)
        return tint([14, 14, 16], 0.9 + n * 0.2)  # the gap

    return build(px)


def lab_tile():
    """The laboratories' walls and floors: grimy grey-green glazed tiles in a square grid, crazed, with
    black grout, stained green and brown where something has spilt and dried."""

    def px(x, y):
        if x % 8 == 0 or y % 8 == 0:
            return tint([22, 24, 20], 0.85 + noise(x, y, 4, 751) * 0.15)
        n = fbm(x, y, 752)
        c = tint([104, 112, 96], 0.7 + hash_(x // 8, y // 8, 753) * 0.1 + (n - 0.5) * 0.12)
        stain = noise(x, y, 16, 754)
        if stain > 0.66:
            c = tint([50, 74, 40] if noise(x, y, 32, 755) > 0.5 else [70, 52, 34], 0.9 + stain * 0.1)
        if hash_(x, y, 756) > 0.97:
            c = tint(c, 0.8)  # the crazing
        return c

    return build(px)


def cloud_sea():
    """The sea of cloud far below the castle: soft billows lit gold from the low sun on one side and
    shadowed blue-grey on the other."""

    def px(x, y):
        n = fbm(x, y, 761)
        m = noise(x, y, 16, 762)
        k = 0.6 + n * 0.5
        lit = [236, 224, 206]
        shade = [150, 156, 180]
        mix = min(max((m - 0.3) * 1.6, 0.0), 1.0)
        c = [rround(s + (l - s) * mix) for s, l in zip(shade, lit, strict=True)]
        return tint(c, min(k, 1.0))

    return build(px)
