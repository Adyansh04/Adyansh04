#!/usr/bin/env python3
"""Build assets/header-banner.svg — the header banner with an autonomous
material-handling cell animating in the L-shaped region.

Closed loop, one master cycle C:
    conveyor (left -> right)  ->  6-DOF arm picks  ->  places on a rising shelf
    ->  shelf lifts it to the top  ->  carrier drone flies it back around
    ->  drops it at the start of the conveyor  ->  repeat.

Arm poses come from real 2-link inverse kinematics, so the gripper actually
lands on the crate and on the shelf. Pure SMIL/CSS — animates on GitHub.

Run: python3 scripts/generate_banner.py
"""
import math

W, H = 900, 270
G, B, P_, A = "#3FB950", "#58A6FF", "#A371F7", "#D29922"
TEXT, MUTED, LINE, PANEL, DARK = "#E6EDF3", "#8B949E", "#30363D", "#21262D", "#0B0E14"
STEEL = "#7D8590"

C = 4.6                       # master cycle: one crate handled per C seconds
N_DRONES = 3                  # drones share the loop, so each flies 3x slower
N_CRATES = 6                  # crates riding the belt at any time
# phases derived from the shelf geometry below (see PHASES note)
PICK_P, PLACE_P, GRAB_P = 0.1628, 0.5745, 0.7128

BASE = (778, 250)             # arm base
L1, L2 = 70.0, 62.0           # link lengths
BELT_X0, BELT_X1, BELT_Y = 24, 700, 238          # conveyor
CRATE_W, CRATE_H = 26, 20
LIFT_X, LIFT_TOP, LIFT_BOT = 852, 120, 214       # shelf column
SHELF_PLACE_Y = 196                              # shelf surface at arm hand-off
SHELF_GRAB_Y = 129                               # shelf height at drone hand-off
DRONE_HOVER_Y, DRONE_LIFT_OFF = 96, 20           # grab altitude, crate hang offset


def ik(tx, ty):
    """Two-link IK. Returns (shoulder, elbow) degrees; links drawn along -y."""
    d = math.hypot(tx, ty)
    d = min(d, L1 + L2 - 0.5)
    ca2 = (d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    a2 = -math.acos(max(-1.0, min(1.0, ca2)))
    phi = math.atan2(tx, -ty)
    a1 = phi - math.atan2(L2 * math.sin(a2), L1 + L2 * math.cos(a2))
    return math.degrees(a1), math.degrees(a2)


# arm choreography: (phase, gripper target in absolute coords, gripper closed)
POSES = [
    (0.00, (706, 186), False),   # approaching the belt
    (PICK_P, (690, 209), True),  # down on the crate, grip closes
    (0.26, (694, 168), True),    # lift clear of the belt
    (0.42, (786, 142), True),    # swing across
    (PLACE_P, (852, 165), False),  # set it on the shelf, grip opens
    (0.68, (842, 132), False),   # retract
    (0.86, (790, 126), False),   # home / idle
    (1.00, (706, 186), False),
]


def arm_tracks():
    sh, el, wr, grip, kt = [], [], [], [], []
    for ph, (gx, gy), closed in POSES:
        a1, a2 = ik(gx - BASE[0], gy - BASE[1])
        sh.append(f"{a1:.2f}")
        el.append(f"{a2:.2f}")
        wr.append(f"{-(a1 + a2):.2f}")          # keep the wrist level
        grip.append("0" if closed else "1")
        kt.append(f"{ph:.4g}")
    return ";".join(sh), ";".join(el), ";".join(wr), ";".join(grip), ";".join(kt)


def crate(w=CRATE_W, h=CRATE_H, col=B, dark="#10243a"):
    """A crate drawn centred on its own origin."""
    x, y = -w / 2, -h / 2
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5" fill="{dark}" stroke="{col}" stroke-width="1.3"/>'
            f'<path d="M{x},{y + h * 0.34} h{w}" stroke="{col}" stroke-width="0.8" opacity="0.55"/>'
            f'<path d="M{x + w * 0.5},{y} v{h}" stroke="{col}" stroke-width="0.7" opacity="0.3"/>'
            f'<rect x="{x + 3.5}" y="{y + 3}" width="{w * 0.34}" height="2.4" rx="1.2" fill="{col}" opacity="0.7"/>'
            f'<path d="M{x},{y + h} l2.5,-2.5 h{w - 5} l2.5,2.5" fill="#000" opacity="0.25"/></g>')


def defs():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" height="100%">
<defs>
  <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#080C14"/><stop offset="50%" stop-color="#0F172A"/><stop offset="100%" stop-color="#05080F"/>
  </linearGradient>
  <linearGradient id="brd" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="{G}" stop-opacity="0.9"/><stop offset="50%" stop-color="{B}" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="{P_}" stop-opacity="0.9"/>
  </linearGradient>
  <linearGradient id="tg" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="{G}"><animate attributeName="stop-color" values="{G};{B};{P_};{G}" dur="6s" repeatCount="indefinite"/></stop>
    <stop offset="50%" stop-color="{B}"><animate attributeName="stop-color" values="{B};{P_};{G};{B}" dur="6s" repeatCount="indefinite"/></stop>
    <stop offset="100%" stop-color="{P_}"><animate attributeName="stop-color" values="{P_};{G};{B};{P_}" dur="6s" repeatCount="indefinite"/></stop>
  </linearGradient>
  <linearGradient id="steel" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#2B3440"/><stop offset="45%" stop-color="#3A4553"/><stop offset="100%" stop-color="#1C232C"/>
  </linearGradient>
  <linearGradient id="armg" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#1B2530"/><stop offset="38%" stop-color="#37424F"/><stop offset="100%" stop-color="#131A22"/>
  </linearGradient>
  <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
    <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#1E293B" stroke-width="0.8" opacity="0.5"/>
  </pattern>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="frame"><rect x="6" y="6" width="888" height="258" rx="15"/></clipPath>
  <style>
    text{{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;user-select:none}}
    .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}}
  </style>
</defs>
<rect x="5" y="5" width="890" height="260" rx="16" fill="url(#bg)" stroke="url(#brd)" stroke-width="1.5"/>
<rect x="6" y="6" width="888" height="258" rx="15" fill="url(#grid)"/>
<path d="M 6 6 L 894 6 L 894 36 L 6 36 Z" fill="#0B1324" opacity="0.9"/>
<circle cx="24" cy="21" r="5" fill="#FF5F56"/><circle cx="40" cy="21" r="5" fill="#FFBD2E"/><circle cx="56" cy="21" r="5" fill="#27C93F"/>'''


def conveyor():
    s = [f'<g>']
    # frame, legs, rollers, belt
    s.append(f'<rect x="{BELT_X0}" y="{BELT_Y}" width="{BELT_X1 - BELT_X0}" height="13" rx="2" fill="url(#steel)" stroke="{LINE}" stroke-width="0.9"/>')
    for lx in range(BELT_X0 + 40, BELT_X1, 150):
        s.append(f'<rect x="{lx}" y="{BELT_Y + 13}" width="5" height="11" fill="{PANEL}"/>'
                 f'<rect x="{lx - 5}" y="{BELT_Y + 23}" width="15" height="3" rx="1.5" fill="{LINE}"/>')
    s.append(f'<rect x="{BELT_X0}" y="{BELT_Y - 2}" width="{BELT_X1 - BELT_X0}" height="4" rx="2" fill="{DARK}"/>')
    s.append(f'<line x1="{BELT_X0}" y1="{BELT_Y}" x2="{BELT_X1}" y2="{BELT_Y}" stroke="{STEEL}" stroke-width="2.6" '
             f'stroke-dasharray="10,8" opacity="0.85">'
             f'<animate attributeName="stroke-dashoffset" values="18;0" dur="0.55s" repeatCount="indefinite"/></line>')
    for rx in range(BELT_X0 + 12, BELT_X1, 44):
        s.append(f'<g transform="translate({rx},{BELT_Y + 6.5})">'
                 f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="0.9s" '
                 f'repeatCount="indefinite" additive="sum"/>'
                 f'<circle r="4.6" fill="{DARK}" stroke="{STEEL}" stroke-width="0.9"/>'
                 f'<path d="M-3.2,0 H3.2 M0,-3.2 V3.2" stroke="{STEEL}" stroke-width="0.8" opacity="0.8"/></g>')
    # infeed marker where the drone drops crates
    s.append(f'<path d="M{BELT_X0 + 8},{BELT_Y - 22} v-9 M{BELT_X0 + 3},{BELT_Y - 28} l5,6 l5,-6" fill="none" '
             f'stroke="{G}" stroke-width="1.3" opacity="0.55"><animate attributeName="opacity" '
             f'values="0.2;0.85;0.2" dur="{C}s" repeatCount="indefinite"/></path>')
    # crates riding the belt
    ncr, travel = N_CRATES, N_CRATES * C
    cy = BELT_Y - CRATE_H / 2 - 1
    for i in range(ncr):
        beg = PICK_P * C - i * C
        s.append(f'<g><animateTransform attributeName="transform" type="translate" '
                 f'values="{BELT_X0 + 10},{cy};{BELT_X1 - 10},{cy}" dur="{travel}s" begin="{beg:.3f}s" '
                 f'calcMode="linear" repeatCount="indefinite"/>{crate()}</g>')
    # scanner gate near the pick point
    s.append(f'<g><rect x="{BELT_X1 - 74}" y="{BELT_Y - 54}" width="4" height="52" rx="2" fill="{PANEL}"/>'
             f'<rect x="{BELT_X1 - 74}" y="{BELT_Y - 58}" width="46" height="7" rx="3" fill="{PANEL}" stroke="{LINE}" stroke-width="0.7"/>'
             f'<rect x="{BELT_X1 - 74}" y="{BELT_Y - 50}" width="44" height="46" fill="{A}" opacity="0">'
             f'<animate attributeName="opacity" values="0;0.16;0" keyTimes="0;0.06;0.18" dur="{C}s" repeatCount="indefinite"/></rect>'
             f'<circle cx="{BELT_X1 - 34}" cy="{BELT_Y - 54}" r="2" fill="{A}">'
             f'<animate attributeName="opacity" values="1;0.2;1" dur="1.1s" repeatCount="indefinite"/></circle></g>')
    s.append('</g>')
    return "".join(s)


def lift():
    s = ['<g>']
    for rx in (LIFT_X - 30, LIFT_X + 26):
        s.append(f'<rect x="{rx}" y="{LIFT_TOP - 6}" width="6" height="{LIFT_BOT - LIFT_TOP + 26}" rx="3" '
                 f'fill="url(#steel)" stroke="{LINE}" stroke-width="0.8"/>')
    for ry in range(LIFT_TOP + 4, LIFT_BOT + 16, 16):
        s.append(f'<line x1="{LIFT_X - 24}" y1="{ry}" x2="{LIFT_X + 26}" y2="{ry}" stroke="{LINE}" stroke-width="0.7" opacity="0.45"/>')
    # drive belt
    s.append(f'<line x1="{LIFT_X - 33}" y1="{LIFT_TOP - 4}" x2="{LIFT_X - 33}" y2="{LIFT_BOT + 18}" stroke="{A}" '
             f'stroke-width="1.6" stroke-dasharray="5,7" opacity="0.6">'
             f'<animate attributeName="stroke-dashoffset" values="0;-24" dur="1.1s" repeatCount="indefinite"/></line>')
    # top out-feed platform
    s.append(f'<rect x="{LIFT_X - 34}" y="{LIFT_TOP - 12}" width="68" height="8" rx="3" fill="url(#steel)" stroke="{LINE}" stroke-width="0.9"/>'
             f'<text x="{LIFT_X - 42}" y="{LIFT_TOP - 5}" class="mono" font-size="7" fill="{A}" text-anchor="end" letter-spacing="1">OUTFEED</text>')
    # rising shelves, each carrying a crate between hand-off and the top
    span = LIFT_BOT - LIFT_TOP
    dur = 3 * C
    t_place = (LIFT_BOT - SHELF_PLACE_Y) / span
    t_top = (LIFT_BOT - SHELF_GRAB_Y) / span
    for j in range(3):
        beg = -j * C
        s.append(f'<g><animateTransform attributeName="transform" type="translate" '
                 f'values="0,{LIFT_BOT};0,{LIFT_TOP}" dur="{dur}s" begin="{beg:.3f}s" calcMode="linear" repeatCount="indefinite"/>'
                 f'<rect x="{LIFT_X - 26}" y="-3" width="52" height="6" rx="2" fill="url(#steel)" stroke="{STEEL}" stroke-width="0.8"/>'
                 f'<path d="M{LIFT_X - 26},3 l-4,5 M{LIFT_X + 26},3 l4,5" stroke="{STEEL}" stroke-width="1.2" opacity="0.6"/>'
                 f'<g transform="translate({LIFT_X},{-3 - CRATE_H / 2})" opacity="0">'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
                 f'keyTimes="0;{t_place:.4f};{t_place + 0.004:.4f};{t_top:.4f};{t_top + 0.004:.4f};1" '
                 f'dur="{dur}s" begin="{beg:.3f}s" repeatCount="indefinite"/>{crate()}</g></g>')
    s.append('</g>')
    return "".join(s)


def arm():
    sh, el, wr, grip, kt = arm_tracks()
    bx, by = BASE
    return f'''<g transform="translate({bx},{by})">
<path d="M-30,6 h60 l-9,-16 h-42 Z" fill="url(#steel)" stroke="{LINE}" stroke-width="1"/>
<rect x="-34" y="6" width="68" height="6" rx="3" fill="{PANEL}" stroke="{LINE}" stroke-width="0.8"/>
{''.join(f'<circle cx="{cx}" cy="9" r="1.6" fill="{STEEL}"/>' for cx in (-26, -13, 13, 26))}
<rect x="-15" y="-16" width="30" height="18" rx="4" fill="url(#armg)" stroke="{STEEL}" stroke-width="1"/>
<circle cx="10" cy="-10" r="2" fill="{G}"><animate attributeName="opacity" values="1;0.2;1" dur="1.3s" repeatCount="indefinite"/></circle>
<g>
  <animateTransform attributeName="transform" type="rotate" values="{sh}" keyTimes="{kt}" dur="{C}s" repeatCount="indefinite"/>
  <rect x="-7.5" y="{-L1 - 4}" width="15" height="{L1 + 10}" rx="7" fill="url(#armg)" stroke="{STEEL}" stroke-width="1.2"/>
  <rect x="-3" y="{-L1 + 6}" width="6" height="{L1 - 18}" rx="3" fill="{G}" opacity="0.18"/>
  <circle r="8.5" fill="{DARK}" stroke="{G}" stroke-width="1.5"/><circle r="3" fill="{G}" opacity="0.75"/>
  <g transform="translate(0,{-L1})">
    <g>
      <animateTransform attributeName="transform" type="rotate" values="{el}" keyTimes="{kt}" dur="{C}s" repeatCount="indefinite"/>
      <rect x="-6" y="{-L2 - 3}" width="12" height="{L2 + 8}" rx="6" fill="url(#armg)" stroke="{STEEL}" stroke-width="1.1"/>
      <rect x="-2.4" y="{-L2 + 5}" width="4.8" height="{L2 - 15}" rx="2.4" fill="{G}" opacity="0.16"/>
      <circle r="7" fill="{DARK}" stroke="{G}" stroke-width="1.4"/><circle r="2.4" fill="{G}" opacity="0.75"/>
      <g transform="translate(0,{-L2})">
        <g>
          <animateTransform attributeName="transform" type="rotate" values="{wr}" keyTimes="{kt}" dur="{C}s" repeatCount="indefinite"/>
          <circle r="5.5" fill="{DARK}" stroke="{G}" stroke-width="1.3"/>
          <rect x="-7" y="2" width="14" height="6" rx="2.5" fill="url(#armg)" stroke="{STEEL}" stroke-width="1"/>
          <g><animateTransform attributeName="transform" type="translate" values="{';'.join(f'{-3.5 * float(v):.2f},0' for v in grip.split(';'))}" keyTimes="{kt}" dur="{C}s" repeatCount="indefinite"/>
            <path d="M-4,8 v7 h2.6" fill="none" stroke="{G}" stroke-width="2.2" stroke-linecap="round"/></g>
          <g><animateTransform attributeName="transform" type="translate" values="{';'.join(f'{3.5 * float(v):.2f},0' for v in grip.split(';'))}" keyTimes="{kt}" dur="{C}s" repeatCount="indefinite"/>
            <path d="M4,8 v7 h-2.6" fill="none" stroke="{G}" stroke-width="2.2" stroke-linecap="round"/></g>
          <g transform="translate(0,{CRATE_H / 2 + 8})" opacity="0">
            <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{PICK_P:.4g};{PICK_P + 0.006:.4g};{PLACE_P:.4g};{PLACE_P + 0.006:.4g};1" dur="{C}s" repeatCount="indefinite"/>
            {crate()}</g>
        </g>
      </g>
    </g>
  </g>
</g></g>'''


def drone_circuit():
    """A closed, non-self-intersecting circuit: lift top -> across -> down ->
    left to the infeed -> out to the margin -> up -> back along the top.
    Because every drone runs the same loop in the same direction they simply
    stay spaced along it and can never meet head-on."""
    pts = [(LIFT_X, DRONE_HOVER_Y), (505, DRONE_HOVER_Y), (505, 178), (34, 178),
           (34, 207), (20, 207), (20, 46), (LIFT_X, 46), (LIFT_X, DRONE_HOVER_Y)]
    segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    drop = sum(segs[:4]) / sum(segs)          # crate is released at pts[4]
    d = f"M{pts[0][0]},{pts[0][1]}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d += f" H{x1}" if y0 == y1 else f" V{y1}"
    return d, drop


def drones():
    path, drop = drone_circuit()
    dur = N_DRONES * C
    carry = 1.45 / N_DRONES                   # each crate is carried for 1.45 cycles
    t0, t1, t2 = 0.010, 0.010 + carry, 0.027 + carry
    props = "".join(
        f'<g transform="translate({px},{py})"><animateTransform attributeName="transform" type="rotate" '
        f'from="0" to="360" dur="0.19s" repeatCount="indefinite" additive="sum"/>'
        f'<ellipse rx="8" ry="1.9" fill="{B}" opacity="0.8"/>'
        f'<ellipse rx="8" ry="1.9" fill="{B}" opacity="0.25" transform="rotate(60)"/></g>'
        for px, py in [(-12, -7), (12, -7), (-12, 7), (12, 7)])
    body = (f'<line x1="-12" y1="-7" x2="12" y2="7" stroke="{PANEL}" stroke-width="3.4"/>'
            f'<line x1="-12" y1="7" x2="12" y2="-7" stroke="{PANEL}" stroke-width="3.4"/>'
            + props +
            f'<rect x="-9" y="-6" width="18" height="12" rx="4" fill="url(#armg)" stroke="{B}" stroke-width="1.3"/>'
            f'<rect x="-4" y="5" width="8" height="4" rx="1.6" fill="{DARK}" stroke="{B}" stroke-width="0.9"/>'
            f'<circle cy="7" r="1.5" fill="{B}" opacity="0.9"/>'
            f'<path d="M-13,9 h5 M8,9 h5" stroke="{STEEL}" stroke-width="1.4" stroke-linecap="round"/>')
    out = []
    for k in range(N_DRONES):
        beg = GRAB_P * C - dur + k * C
        out.append(
            f'<g><animateMotion path="{path}" dur="{dur}s" begin="{beg:.3f}s" calcMode="linear" '
            f'keyPoints="0;0;{drop:.4f};{drop:.4f};1" keyTimes="0;{t0:.4f};{t1:.4f};{t2:.4f};1" '
            f'repeatCount="indefinite"/>' + body +
            f'<circle cx="-12" cy="-7" r="1.6" fill="{G}"><animate attributeName="opacity" values="1;0.15;1" '
            f'dur="0.9s" begin="{-k * 0.3:.1f}s" repeatCount="indefinite"/></circle>'
            f'<circle cx="12" cy="-7" r="1.6" fill="#FF5F56"><animate attributeName="opacity" values="0.15;1;0.15" '
            f'dur="0.9s" begin="{-k * 0.3:.1f}s" repeatCount="indefinite"/></circle>'
            f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" '
            f'keyTimes="0;{t0 - 0.005:.4f};{t0:.4f};{t1:.4f};{t1 + 0.005:.4f};1" dur="{dur}s" '
            f'begin="{beg:.3f}s" repeatCount="indefinite"/>'
            f'<line x1="0" y1="9" x2="0" y2="{DRONE_LIFT_OFF - CRATE_H / 2}" stroke="{STEEL}" stroke-width="1.1"/>'
            f'<g transform="translate(0,{DRONE_LIFT_OFF})">{crate()}</g></g></g>')
    return "".join(out)


def hud():
    # one compact panel parked in clear space — the old corner labels sat on top
    # of the conveyor and the arm base
    return (f'<g transform="translate(545,134)">'
            f'<rect width="146" height="36" rx="7" fill="#111823" stroke="{LINE}" stroke-width="1" opacity="0.92"/>'
            f'<circle cx="14" cy="14" r="3.2" fill="{G}">'
            f'<animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/></circle>'
            f'<text x="25" y="17" class="mono" font-size="7.5" font-weight="700" fill="{TEXT}">CELL 01 · LOOP ACTIVE</text>'
            f'<text x="14" y="29" class="mono" font-size="6.5" fill="{MUTED}">AUTONOMOUS MATERIAL HANDLING</text></g>')


def title_block():
    items = [(G, "🤖 Perception · Navigation · AI for embodied robots", "0;1;1;0;0", "0;0.02;0.22;0.25;1"),
             (B, "🎓 M.Sc. Robotic Systems Engineering @ RWTH Aachen", "0;0;1;1;0;0", "0;0.25;0.27;0.47;0.5;1"),
             (P_, "⚡ C++ · SIMD / SIMT · CUDA · ROS 2 · Nav2", "0;0;1;1;0;0", "0;0.5;0.52;0.72;0.75;1"),
             (A, "🦿 Humanoids · Quadrupeds · AMRs · Drones", "0;0;1;1;1", "0;0.75;0.77;0.97;1")]
    s = ['<g transform="translate(35, 90)">'
         '<text x="0" y="0" font-size="38" font-weight="900" letter-spacing="2" fill="url(#tg)" filter="url(#glow)">ADYANSH GUPTA</text>'
         f'<text x="0" y="24" class="mono" font-size="12" font-weight="600" fill="#94A3B8" letter-spacing="2">ROBOTICS ENGINEER · PERCEPTION · NAVIGATION · AI</text></g>',
         '<g transform="translate(35, 150)">']
    for col, txt, vals, kts in items:
        s.append(f'<text y="0" font-size="15" font-weight="700" fill="{col}" opacity="0">{txt}'
                 f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="16s" repeatCount="indefinite"/></text>')
    dots = [(G, "1;1;0.25;0.25", "0;0.25;0.26;1"), (B, "0.25;0.25;1;1;0.25;0.25", "0;0.25;0.26;0.5;0.51;1"),
            (P_, "0.25;0.25;1;1;0.25;0.25", "0;0.5;0.51;0.75;0.76;1"), (A, "0.25;0.25;1;1", "0;0.75;0.76;1")]
    s.append('<g transform="translate(2, 16)">')
    for i, (col, vals, kts) in enumerate(dots):
        s.append(f'<circle cx="{i * 14}" cy="0" r="3" fill="{col}" opacity="0.25">'
                 f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="16s" repeatCount="indefinite"/></circle>')
    s.append('</g></g>')
    return "".join(s)


def main():
    svg = (defs()
           + '<g clip-path="url(#frame)">'
           + f'<line x1="16" y1="262" x2="884" y2="262" stroke="{LINE}" stroke-width="1.2" opacity="0.6"/>'
           + conveyor() + lift() + arm() + drones() + hud()
           + '</g>' + title_block() + '</svg>')
    with open("assets/header-banner.svg", "w") as f:
        f.write(svg)
    print(f"wrote assets/header-banner.svg ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
