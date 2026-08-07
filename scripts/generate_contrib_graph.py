#!/usr/bin/env python3
"""Build assets/contrib-gantry-{dark,light}.svg — the contribution graph.

A gantry robot travels the top rail, lowers its claw onto every contribution
cell and sorts each one into a bin by intensity. Pure SMIL, so it animates
natively in a README with no external service involved.

Run: python3 scripts/generate_contrib_graph.py --user Adyansh04
Data: https://github-contributions-api.jogruber.de/v4/<user>?y=last
"""
import argparse
import datetime as dt
import json
import urllib.request

CELL, GAP = 12, 3
PITCH = CELL + GAP
MARGIN, TOP = 16, 34
SCAN = 0.92               # fraction of loop spent working; rest = pause/recharge
DUR = 26                  # seconds per loop

# GitHub Primer palette — looks native on github.com
THEMES = {
    "dark": dict(
        bg="#0d1117", border="#30363d", text="#e6edf3", muted="#8b949e",
        empty="#161b22", fog="#131a22", accent="#58a6ff", accent2="#3fb950",
        warn="#d29922", flash="#eaf3ff",
        raw=["#0e4429", "#006d32", "#26a641", "#39d353"],
        mapped=["#1f6feb", "#388bfd", "#58a6ff", "#79c0ff"],
        body="#21262d", dark="#0b0e14", steel="#8b949e",
    ),
    "light": dict(
        bg="#ffffff", border="#d0d7de", text="#24292f", muted="#57606a",
        empty="#ebedf0", fog="#eef0f3", accent="#0969da", accent2="#1a7f37",
        warn="#9a6700", flash="#0a3069",
        raw=["#9be9a8", "#40c463", "#30a14e", "#216e39"],
        mapped=["#54aeff", "#218bff", "#0969da", "#033d8b"],
        body="#d0d7de", dark="#57606a", steel="#6e7781",
    ),
}


def fetch(user, input_file):
    if input_file:
        data = json.load(open(input_file))
    else:
        url = f"https://github-contributions-api.jogruber.de/v4/{user}?y=last"
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
    return data["contributions"], sum(data["total"].values())


def build_grid(days):
    first = dt.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7
    cells = [None] * lead + days
    cells += [None] * (-len(cells) % 7)
    return [cells[i:i + 7] for i in range(0, len(cells), 7)]


def xy(col, row):
    return MARGIN + col * PITCH, TOP + row * PITCH


def cxy(col, row):
    x, y = xy(col, row)
    return x + CELL / 2, y + CELL / 2


def serpentine(ncols):
    out = []
    for c in range(ncols):
        rows = range(7) if c % 2 == 0 else range(6, -1, -1)
        out += [(c, r) for r in rows]
    return out


def fmt(x):
    return f"{x:.4g}"


def anim(attr, pairs, calc="linear", transform=None, dur=None):
    """SMIL animate from [(t, value)] pairs; t in [0,1], first 0, last 1."""
    vals = ";".join(str(v) for _, v in pairs)
    kts = ";".join(fmt(t) for t, _ in pairs)
    d = dur or DUR
    if transform:
        return (f'<animateTransform attributeName="transform" type="{transform}" '
                f'dur="{d}s" repeatCount="indefinite" calcMode="{calc}" '
                f'values="{vals}" keyTimes="{kts}"/>')
    return (f'<animate attributeName="{attr}" dur="{d}s" repeatCount="indefinite" '
            f'calcMode="{calc}" values="{vals}" keyTimes="{kts}"/>')


def flash_hold(raw, flash, mapped, tv):
    """fill timeline: raw -> flash at tv -> mapped, hold to loop end."""
    a = max(tv - 0.005, 0.002)
    b = a + 0.003
    e = min(b + 0.015, 0.985)
    return anim("fill", [(0, raw), (a, raw), (b, flash), (e, mapped), (1, mapped)])


def pop(tv, peak=1.4):
    """centered scale pop at tv (element must live in a g centered at its cell)."""
    a = max(tv - 0.004, 0.002)
    b = a + 0.004
    e = min(b + 0.014, 0.985)
    return anim(None, [(0, 1), (a, 1), (b, peak), (e, 1), (1, 1)], transform="scale")


def svg_open(w, h, t, title, cmd, total, css=""):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        f'<title>{title}</title>',
        f'<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}{css}</style>',
        f'<rect width="{w}" height="{h}" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<text x="{MARGIN}" y="21" font-size="10" fill="{t["muted"]}">{cmd}</text>',
        f'<text x="{w - MARGIN}" y="21" text-anchor="end" font-size="10" font-weight="bold" '
        f'fill="{t["accent"]}">{total} contributions</text>',
    ]


def legend(t, w, y, note):
    s = [f'<text x="{MARGIN}" y="{y}" font-size="9" fill="{t["muted"]}">raw</text>']
    lx = MARGIN + 26
    for c in t["raw"] + t["mapped"]:
        s.append(f'<rect x="{lx}" y="{y - 8}" width="9" height="9" rx="2" fill="{c}"/>')
        lx += 12
    s.append(f'<text x="{lx + 4}" y="{y}" font-size="9" fill="{t["muted"]}">mapped</text>')
    s.append(f'<text x="{w - MARGIN}" y="{y}" text-anchor="end" font-size="9" fill="{t["muted"]}">{note}</text>')
    return s


def battery(t, x, y, drain_end=SCAN):
    """HUD battery that drains during work and recharges in the pause."""
    return (
        f'<g transform="translate({x},{y})">'
        f'<rect x="0" y="0" width="30" height="11" rx="2.5" fill="none" stroke="{t["muted"]}"/>'
        f'<rect x="31" y="3" width="2.5" height="5" rx="1" fill="{t["muted"]}"/>'
        f'<rect x="2" y="2" width="26" height="7" rx="1.5" fill="{t["accent"]}">'
        + anim("width", [(0, 26), (drain_end, 4), (0.985, 26), (1, 26)])
        + '</rect>'
        f'<text x="-5" y="9" text-anchor="end" font-size="8" fill="{t["muted"]}">BAT</text>'
        f'<text x="15" y="9" text-anchor="middle" font-size="7" font-weight="bold" fill="{t["bg"]}" opacity="0">CHG'
        + anim("opacity", [(0, 0), (drain_end, 0), (drain_end + 0.01, 1), (0.99, 1), (1, 0)])
        + '</text></g>'
    )


def grid_cells(cols, t, consumed=None, fog=False):
    """Static + animated cells. consumed: {(c,r): tv} -> flash+pop to mapped.
    fog: all cells hidden until reveal time in consumed (incl. empties)."""
    s = []
    for c, col in enumerate(cols):
        for r, day in enumerate(col):
            if day is None:
                continue
            x, y = xy(c, r)
            cx, cy = cxy(c, r)
            lvl = day["level"]
            tv = consumed.get((c, r)) if consumed else None
            if fog:
                real = t["empty"] if lvl == 0 else t["raw"][lvl - 1]
                real = t["mapped"][lvl - 1] if lvl else t["empty"]
                inner = (f'<rect x="{-CELL/2}" y="{-CELL/2}" width="{CELL}" height="{CELL}" rx="3" fill="{t["fog"]}">'
                         + flash_hold(t["fog"], t["flash"] if lvl else real, real, tv) + '</rect>')
                if lvl:
                    s.append(f'<g transform="translate({cx},{cy})"><g>{pop(tv, 1.35)}{inner}</g></g>')
                else:
                    s.append(f'<g transform="translate({cx},{cy})">{inner}</g>')
                continue
            if lvl == 0:
                s.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{t["empty"]}"/>')
                continue
            raw, mapped = t["raw"][lvl - 1], t["mapped"][lvl - 1]
            if tv is None:
                s.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{raw}"/>')
            else:
                s.append(
                    f'<g transform="translate({cx},{cy})"><g>{pop(tv)}'
                    f'<rect x="{-CELL/2}" y="{-CELL/2}" width="{CELL}" height="{CELL}" rx="3" fill="{raw}">'
                    + flash_hold(raw, t["flash"], mapped, tv) + '</rect></g></g>')
    return s


def v_gantry(user, cols, total, t):
    ncols = len(cols)
    grid_w = 2 * MARGIN + ncols * PITCH - GAP
    bins_w = 86
    w = grid_w + bins_w
    rail_y = TOP - 8
    h = TOP + 7 * PITCH + 26 + 10
    s = svg_open(w, h, t, f"{user} — gantry pick &amp; sort",
                 f"$ ros2 run gantry_sort pick_place --input contributions", total)
    s.append('<g transform="translate(0,10)">')   # drop work area below the header line

    picks = [(c, r) for c, r in serpentine(ncols) if cols[c][r] and cols[c][r]["level"] > 0]
    np_ = len(picks)
    tp = {cr: SCAN * (i + 0.5) / np_ for i, cr in enumerate(picks)}

    # cells: picked ones shrink away at pick time
    for c, col in enumerate(cols):
        for r, day in enumerate(col):
            if day is None:
                continue
            x, y = xy(c, r)
            cx, cy = cxy(c, r)
            lvl = day["level"]
            if lvl == 0:
                s.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{t["empty"]}"/>')
                continue
            tv = tp[(c, r)]
            a = max(tv - 0.004, 0.002)
            s.append(f'<g transform="translate({cx},{cy})"><g>'
                     + anim(None, [(0, 1), (a, 1), (min(a + 0.008, 0.98), 0), (1, 0)], transform="scale")
                     + f'<rect x="{-CELL/2}" y="{-CELL/2}" width="{CELL}" height="{CELL}" rx="3" '
                     f'fill="{t["raw"][lvl - 1]}"/></g></g>')

    # gantry frame: side posts + crossbeam with inner rail
    foot = TOP + 7 * PITCH - GAP + 4
    for px in (7, grid_w - 11):
        s.append(f'<rect x="{px}" y="{rail_y - 2}" width="4" height="{foot - rail_y + 2}" rx="1" '
                 f'fill="{t["body"]}" stroke="{t["steel"]}" stroke-width="0.8"/>'
                 f'<rect x="{px - 2.5}" y="{foot}" width="9" height="3" rx="1" fill="{t["steel"]}"/>')
    s.append(f'<rect x="{5}" y="{rail_y - 4}" width="{grid_w - 10}" height="6" rx="2" '
             f'fill="{t["body"]}" stroke="{t["steel"]}" stroke-width="0.8"/>')
    s.append(f'<line x1="{7}" y1="{rail_y - 1}" x2="{grid_w - 7}" y2="{rail_y - 1}" '
             f'stroke="{t["accent"]}" stroke-width="1" opacity="0.55"/>')

    carr = [(0, MARGIN + 12)] + [(tv, cxy(c, r)[0]) for (c, r), tv in tp.items()] + [(1, MARGIN + 12)]
    delta = min(0.012, 0.45 * SCAN / np_)   # keep extend/retract windows of adjacent picks disjoint
    arm, sleeve, grip, fingL, fingR = [(0, 0)], [(0, 0)], [(0, 0)], [], []
    py = rail_y + 16                        # finger pivot y (wrist local, before grip translate)
    for (c, r), tv in tp.items():
        depth = cxy(c, r)[1] - rail_y - 14
        a, b, e = max(tv - delta, 0.002), tv, min(tv + delta, 0.985)
        arm += [(a, 0), (b, depth), (e, 0)]
        sleeve += [(a, 0), (b, depth * 0.55), (e, 0)]
        grip += [(a, 0), (b, depth), (e, 0)]
        fingL += [(a, 0), (a + 0.002, 26), (b - 0.002, 26), (b, 0)]   # open on descent, snap shut on pick
    arm.append((1, 0))
    sleeve.append((1, 0))
    grip.append((1, 0))
    fingL = [(0, 0)] + fingL + [(1, 0)]
    fingR = [(tt, -v) for tt, v in fingL]
    hazard = "".join(f'<rect x="{-11 + i * 5.5}" y="{rail_y + 6.5}" width="5.5" height="2.5" '
                     f'fill="{t["warn"] if i % 2 == 0 else t["dark"]}"/>' for i in range(4))
    s.append(
        '<g>' + anim(None, [(tt, f"{v},0") for tt, v in carr], transform="translate")
        # rail rollers with spinning spokes
        + "".join(f'<g transform="translate({rx},{rail_y - 1})"><circle r="2.6" fill="{t["dark"]}" '
                  f'stroke="{t["steel"]}" stroke-width="0.9"/>'
                  f'<g><animateTransform attributeName="transform" type="rotate" from="0" to="360" '
                  f'dur="0.9s" repeatCount="indefinite"/>'
                  f'<line x1="-2" y1="0" x2="2" y2="0" stroke="{t["steel"]}" stroke-width="0.7"/></g></g>'
                  for rx in (-7, 7))
        # carriage housing + hazard stripes + status LED + bolts
        + f'<rect x="-11" y="{rail_y + 1.5}" width="22" height="9" rx="1.5" fill="{t["body"]}" '
        f'stroke="{t["accent"]}" stroke-width="1.1"/>'
        + hazard
        + f'<circle cx="8" cy="{rail_y + 4.5}" r="1.3" fill="{t["accent2"]}">'
        f'<animate attributeName="opacity" values="1;0.15;1" dur="1s" repeatCount="indefinite"/></circle>'
        f'<circle cx="-8" cy="{rail_y + 4.5}" r="0.9" fill="{t["steel"]}"/>'
        # telescopic arm: outer sleeve + inner rod
        + f'<rect x="-2.6" y="{rail_y + 10}" width="5.2" height="0" rx="1" fill="{t["steel"]}" opacity="0.95">'
        + anim("height", sleeve) + '</rect>'
        + f'<rect x="-1.2" y="{rail_y + 10}" width="2.4" height="0" fill="{t["accent"]}" opacity="0.9">'
        + anim("height", arm) + '</rect>'
        # wrist + articulated 2-finger claw (opens on descent, closes on pick)
        + '<g>' + anim(None, [(tt, f"0,{v}") for tt, v in grip], transform="translate")
        + f'<rect x="-5" y="{rail_y + 10}" width="10" height="4" rx="1.2" fill="{t["body"]}" '
        f'stroke="{t["steel"]}" stroke-width="0.9"/>'
        f'<circle cx="0" cy="{rail_y + 12}" r="0.9" fill="{t["accent"]}"/>'
        + f'<g>{anim(None, [(tt, f"{v} -4 {py}") for tt, v in fingL], transform="rotate")}'
        f'<path d="M-4,{py - 2} v6.5 h2.6" fill="none" stroke="{t["steel"]}" stroke-width="1.7"/></g>'
        + f'<g>{anim(None, [(tt, f"{v} 4 {py}") for tt, v in fingR], transform="rotate")}'
        f'<path d="M4,{py - 2} v6.5 h-2.6" fill="none" stroke="{t["steel"]}" stroke-width="1.7"/></g>'
        + f'<circle cx="0" cy="{py + 4}" r="2.6" fill="{t["warn"]}" opacity="0">'
        + anim("opacity", [(0, 0)] + [(x, v) for tv in tp.values() for x, v in
                                      [(max(tv - 0.003, 0.001), 0), (tv, 0.9), (min(tv + 0.006, 0.98), 0)]] + [(1, 0)])
        + '</circle></g></g>')

    # bins by level, filling as picks land
    bx = grid_w + 6
    bin_h, bin_w2 = 7 * PITCH - 14, 16
    by = TOP + 8
    counts = [0, 0, 0, 0]
    steps = [[(0, 0)] for _ in range(4)]
    for (c, r), tv in tp.items():
        lvl = cols[c][r]["level"]
        counts[lvl - 1] += 1
        steps[lvl - 1].append((min(tv + 0.004, 0.985), counts[lvl - 1]))
    for i in range(4):
        tot = counts[i] or 1
        full = [(tt, fmt(bin_h * v / max(counts[i], 1))) for tt, v in steps[i]] + [(1, fmt(bin_h * counts[i] / tot if counts[i] else 0))]
        x0 = bx + i * (bin_w2 + 4)
        s.append(f'<rect x="{x0}" y="{by}" width="{bin_w2}" height="{bin_h}" rx="3" fill="none" '
                 f'stroke="{t["border"]}" stroke-width="1"/>')
        s.append(f'<g transform="translate({x0},{by + bin_h}) scale(1,-1)">'
                 f'<rect x="1.5" y="0" width="{bin_w2 - 3}" height="0" rx="2" fill="{t["mapped"][i]}" opacity="0.9">'
                 + anim("height", full, calc="discrete") + '</rect></g>')
        s.append(f'<text x="{x0 + bin_w2 / 2}" y="{by + bin_h + 11}" text-anchor="middle" font-size="7.5" '
                 f'fill="{t["muted"]}">L{i + 1}·{counts[i]}</text>')
    s.append(f'<text x="{bx + 2 * (bin_w2 + 4) - 2}" y="{by - 6}" text-anchor="middle" font-size="8" '
             f'fill="{t["muted"]}">SORT BINS</text>')
    s.append('</g>')
    s += legend(t, w, h - 8, f"{np_} picks · sorted by intensity level")
    s.append('</svg>')
    return "\n".join(s)




def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user", required=True)
    p.add_argument("--out-dir", default="assets")
    p.add_argument("--input", help="local contributions JSON, for offline runs")
    args = p.parse_args()

    days, total = fetch(args.user, args.input)
    cols = build_grid(days)
    for theme in THEMES:
        path = f"{args.out_dir}/contrib-gantry-{theme}.svg"
        with open(path, "w") as f:
            f.write(v_gantry(args.user, cols, total, THEMES[theme]))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
