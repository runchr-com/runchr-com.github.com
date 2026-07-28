#!/usr/bin/env python3
"""Generate the runchr 8-bit robot mascot as an animated GIF.

Animation loop: idle bounce -> blink -> wave hello -> walk in place -> jump.

Usage:  python3 tools/make_mascot.py
Output: assets/runchr-bot.gif (animated) + assets/runchr-bot.png (poster frame)
"""
from pathlib import Path

from PIL import Image

OUT_DIR = Path(__file__).resolve().parent.parent / "assets"

# Palette ('.' = transparent)
COLORS = {
    "K": (14, 12, 1),      # --border  near-black outline
    "O": (255, 179, 71),   # --accent-warm light orange body
    "W": (255, 255, 255),  # white face
    "G": (105, 214, 167),  # --accent-alt mint green
}

# Character is 16px wide x 20px tall (rows 0-16 head/body, rows 17-19 legs).
FACE = ".KO" + "W" * 10 + "OK."
HEAD_BODY = [
    ".......GG.......",                        # 0  antenna bulb
    ".......GG.......",                        # 1
    ".......KK.......",                        # 2  antenna stem
    ".....KKKKKK.....",                        # 3  head top
    "...KKOOOOOOKK...",                        # 4
    "..K" + "O" * 11 + "K.",                  # 5
    FACE,                                     # 6  face top
    ".KOW" + "@E@" + "W" * 4 + "@E@" + "WOK.",  # 7  eyes (@E@ swapped per frame)
    FACE,                                     # 8
    ".KO" + "W" * 3 + "K" * 4 + "W" * 3 + "OK.",  # 9  mouth
    FACE,                                     # 10
    "..K" + "O" * 10 + "K..",                # 11
    "...KKOOOOOOKK...",                        # 12
    ".....KKKKKK.....",                        # 13 head bottom
    "....KOOOOOOK....",                        # 14 body
    "....KOGOGOOK....",                        # 15 body w/ green buttons
    "....KOOOOOOK....",                        # 16 body bottom
]

# Leg variants, 3 rows each (char rows 17-19). CROUCH is anchored to the
# ground (feet stay put while the body drops); all others follow the body.
LEGS = {
    "A": [  # standing
        ".....KK..KK.....",
        ".....KK..KK.....",
        "....KKK..KKK....",
    ],
    "WL": [  # walk: left foot planted, right foot lifted
        ".....KK.........",
        ".....KK..KKK....",
        "....KKK.........",
    ],
    "WR": [  # walk: right foot planted, left foot lifted
        ".........KK.....",
        "....KKK..KK.....",
        ".........KKK....",
    ],
    "CROUCH": [  # jump crouch/land: body drops, only feet on the ground
        "................",
        "................",
        "....KKK..KKK....",
    ],
    "TUCK": [  # mid-air: legs pulled up one pixel
        "................",
        ".....KK..KK.....",
        "....KKK..KKK....",
    ],
}

# Arm overlays in char coords: (x, y, color). Drawn at body offset.
ARMS = {
    "down": [(3, 15, "K"), (3, 16, "K"),
             (12, 15, "K"), (12, 16, "K")],
    "waveA": [(3, 15, "K"), (3, 16, "K"),
              (12, 15, "K"), (13, 14, "K"), (14, 13, "K"),
              (15, 12, "K"), (15, 11, "K"), (15, 10, "G")],   # hand tipped right
    "waveB": [(3, 15, "K"), (3, 16, "K"),
              (12, 15, "K"), (13, 14, "K"), (14, 13, "K"),
              (14, 12, "K"), (14, 11, "G")],                  # hand up
    "up": [(3, 15, "K"), (2, 14, "K"), (2, 13, "G"),
           (12, 15, "K"), (13, 14, "K"), (13, 13, "G")],      # both arms up (jump)
}

CHAR_W, CHAR_H = 16, 20
CANVAS_W, CANVAS_H = 20, 24   # side room for the raised arm, head room for jumps
OX, OY = 2, 3                 # char origin inside the canvas (resting pose)
GROUND_ROW = OY + CHAR_H - 1  # absolute canvas row the feet rest on
SCALE = 10

# (eyes, legs, dy, arms, duration_ms) — dy is the body offset from resting pose.
SCRIPT = [
    # idle bounce + blink
    ("open",   "A",      0,  "down",  220),
    ("open",   "A",     -1,  "down",  220),
    ("open",   "A",      0,  "down",  200),
    ("closed", "A",      0,  "down",  130),
    ("open",   "A",      0,  "down",  260),
    # wave hello
    ("open",   "A",      0,  "waveA", 180),
    ("open",   "A",      0,  "waveB", 180),
    ("open",   "A",      0,  "waveA", 180),
    ("open",   "A",      0,  "waveB", 180),
    # walk in place (bob up between steps)
    ("open",   "WL",     0,  "down",  150),
    ("open",   "A",     -1,  "down",  150),
    ("open",   "WR",     0,  "down",  150),
    ("open",   "A",     -1,  "down",  150),
    ("open",   "WL",     0,  "down",  150),
    ("open",   "A",     -1,  "down",  150),
    ("open",   "WR",     0,  "down",  150),
    ("open",   "A",      0,  "down",  120),
    # jump: crouch -> air -> land -> rebound
    ("open",   "CROUCH", 2,  "down",  170),
    ("open",   "TUCK",  -3,  "up",    320),
    ("open",   "CROUCH", 2,  "down",  130),
    ("open",   "A",     -1,  "down",  130),
    ("open",   "A",      0,  "down",  500),
]


def build_head_body(eyes):
    rows = []
    for r in HEAD_BODY:
        r = r.replace("@E@", "GG" if eyes == "open" else "KK")
        assert len(r) == CHAR_W, f"row len {len(r)}: {r!r}"
        rows.append(r)
    return rows


def render(eyes, legs, dy, arms):
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    px = img.load()

    body_y = OY + dy
    for y, row in enumerate(build_head_body(eyes)):
        for x, ch in enumerate(row):
            if ch != ".":
                px[OX + x, body_y + y] = (*COLORS[ch], 255)

    # CROUCH legs are anchored to the ground; other legs follow the body.
    legs_y = GROUND_ROW - 2 if legs == "CROUCH" else body_y + 17
    for i, row in enumerate(LEGS[legs]):
        assert len(row) == CHAR_W, f"leg len {len(row)}: {row!r}"
        for x, ch in enumerate(row):
            if ch != ".":
                px[OX + x, legs_y + i] = (*COLORS[ch], 255)

    for x, y, ch in ARMS[arms]:
        px[OX + x, body_y + y] = (*COLORS[ch], 255)

    return img.resize((CANVAS_W * SCALE, CANVAS_H * SCALE), Image.NEAREST)


def main():
    frames = [render(e, l, d, a) for e, l, d, a, _ in SCRIPT]
    durations = [ms for *_, ms in SCRIPT]

    gif_path = OUT_DIR / "runchr-bot.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, disposal=2, transparency=0,
                   optimize=True)
    frames[0].save(OUT_DIR / "runchr-bot.png")
    print(f"saved {gif_path} ({len(frames)} frames, {sum(durations)} ms loop)")


if __name__ == "__main__":
    main()
