"""Profil için "BİLGİSAYAR MÜHENDİSİ" yazılı katkı grafiği + yılan animasyonu.

GitHub'ın katkı grafiğine benzeyen bir ızgarada yazı yeşil kutucuklarla
çizilir; mor yılan ızgarayı sırayla dolaşıp kutucukları yer, sonra döngü
baştan başlar. Çıktı: assets/snake-text-dark.svg ve assets/snake-text-light.svg

Çalıştırma: python tools/gen_text_snake.py
"""
import os
import random

# 5 satırlık piksel yazı tipi ('#' dolu). Türkçe noktalar ayrıca eklenir.
FONT = {
    "B": ["###.", "#..#", "###.", "#..#", "###."],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "L": ["#...", "#...", "#...", "#...", "####"],
    "G": [".###", "#...", "#.##", "#..#", ".###"],
    "S": [".###", "#...", ".##.", "...#", "###."],
    "A": [".##.", "#..#", "####", "#..#", "#..#"],
    "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."],
    "R": ["###.", "#..#", "###.", "#.#.", "#..#"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "U": ["#..#", "#..#", "#..#", "#..#", ".##."],
    "H": ["#..#", "#..#", "####", "#..#", "#..#"],
    "E": ["####", "#...", "###.", "#...", "####"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "D": ["###.", "#..#", "#..#", "#..#", "###."],
}
# harf -> (temel harf, üst noktaların sütunları)
TR = {"İ": ("I", [1]), "Ü": ("U", [0, 3])}

COLS, ROWS = 45, 18

# Profilde yazılan iki satır ve başladıkları ızgara satırı.
LINES = [("SUEDA", 1), ("TEKİN", 9)]

# 7 satırlık büyük piksel yazı tipi (ad için).
FONT7 = {
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "N": ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"],
}
TR7 = {"İ": ("I", [2])}
CELL, GAP = 12, 3
PITCH = CELL + GAP
STEP = 0.028  # yılanın bir kutu ilerleme süresi (sn)
PAUSE = 2.0  # tur sonunda bekleme
SNAKE_LEN = 7

THEMES = {
    "dark": {
        "empty": "#161b22",
        "greens": ["#0e4429", "#006d32", "#26a641", "#39d353"],
        "text": ["#26a641", "#39d353", "#2ea043"],
        "snake": "#b45cff",
        "head": "#d6a6ff",
    },
    "light": {
        "empty": "#ebedf0",
        "greens": ["#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "text": ["#30a14e", "#216e39", "#40c463"],
        "snake": "#8a2be2",
        "head": "#b45cff",
    },
}


def glyph(ch):
    if ch in TR:
        base, dots = TR[ch]
        rows = FONT[base]
        top = "".join("#" if i in dots else "." for i in range(len(rows[0])))
        return [top] + rows
    return ["." * len(FONT[ch][0])] + FONT[ch]


def glyph7(ch, dotted_line):
    """Büyük harf; satırda noktalı harf varsa hepsine üstte bir satır eklenir."""
    if ch in TR7:
        base, dots = TR7[ch]
        rows = FONT7[base]
        top = "".join("#" if i in dots else "." for i in range(len(rows[0])))
        return [top] + rows
    rows = FONT7[ch]
    return (["." * len(rows[0])] + rows) if dotted_line else rows


def text_cells7(word, top_row, gap=2):
    dotted = any(c in TR7 for c in word)
    gl = [glyph7(c, dotted) for c in word]
    width = sum(len(g[0]) for g in gl) + gap * (len(gl) - 1)
    x = (COLS - width) // 2
    cells = set()
    for g in gl:
        for r, line in enumerate(g):
            for c, v in enumerate(line):
                if v == "#":
                    cells.add((top_row + r, x + c))
        x += len(g[0]) + gap
    return cells


def text_cells(word, top_row):
    gl = [glyph(c) for c in word]
    width = sum(len(g[0]) for g in gl) + len(gl) - 1
    x = (COLS - width) // 2
    cells = set()
    for g in gl:
        for r, line in enumerate(g):
            for c, v in enumerate(line):
                if v == "#":
                    cells.add((top_row + r, x + c))
        x += len(g[0]) + 1
    return cells


def build(theme_name):
    t = THEMES[theme_name]
    rnd = random.Random(42)
    letters = set()
    for word, top in LINES:
        letters |= text_cells7(word, top)
    # yılanın yolu: satır satır zikzak
    path = []
    for r in range(ROWS):
        cols = range(COLS) if r % 2 == 0 else range(COLS - 1, -1, -1)
        path += [(r, c) for c in cols]
    index = {cell: i for i, cell in enumerate(path)}
    move = len(path) * STEP
    total = move + PAUSE

    def center(cell):
        r, c = cell
        return (c * PITCH + CELL / 2, r * PITCH + CELL / 2)

    w, h = COLS * PITCH - GAP, ROWS * PITCH - GAP
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 {w + 4} {h + 4}" '
        f'width="{w + 4}" height="{h + 4}">',
        "<style>",
    ]
    rects = []
    for r in range(ROWS):
        for c in range(COLS):
            x, y = c * PITCH, r * PITCH
            if (r, c) in letters:
                i = index[(r, c)]
                p = 100 * i * STEP / total
                col = rnd.choice(t["text"])
                out.append(
                    f"@keyframes e{i}{{0%,{p:.2f}%{{fill:{col}}}"
                    f"{p + 0.4:.2f}%,98.5%{{fill:{t['empty']}}}100%{{fill:{col}}}}}"
                )
                rects.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{col}" style="animation:e{i} {total:.2f}s linear infinite"/>'
                )
            else:
                # yazı dışındaki kutular: boş; sadece en dış satır/sütunlarda
                # ara sıra soluk yeşil (yazının okunurluğunu bozmasın)
                edge = r in (0, ROWS - 1) or c < 3 or c >= COLS - 3
                fill = (
                    t["greens"][0]
                    if edge and rnd.random() < 0.12
                    else t["empty"]
                )
                rects.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{fill}"/>'
                )
    out.append("</style>")
    out += rects

    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in map(center, path))
    out.append(f'<defs><path id="p" d="{d}"/></defs>')
    for k in range(SNAKE_LEN):
        a = k * STEP / total
        b = (k * STEP + move) / total
        size = CELL - 1 - k * 0.6
        color = t["head"] if k == 0 else t["snake"]
        op = 1 - k * 0.08
        out.append(
            f'<rect x="{-size / 2:.1f}" y="{-size / 2:.1f}" width="{size:.1f}" '
            f'height="{size:.1f}" rx="{size / 3:.1f}" fill="{color}" opacity="{op:.2f}">'
            f'<animateMotion dur="{total:.2f}s" repeatCount="indefinite" '
            f'calcMode="linear" keyPoints="0;0;1;1" '
            f'keyTimes="0;{a:.5f};{min(b, 0.9999):.5f};1">'
            f'<mpath href="#p"/></animateMotion></rect>'
        )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(__file__), "..", "assets")
    for name in THEMES:
        with open(os.path.join(root, f"snake-text-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(build(name))
    print("ok")
