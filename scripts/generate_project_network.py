#!/usr/bin/env python3
"""Build assets/project-network.svg — the project routing map.

Each repository is a card carrying its own two-line description, routed through
a QC sort hub that classifies it into a category neuron and ships it to GitHub.
Cards link to their repository, which is live when the file is opened directly
or served from GitHub Pages. Pure SMIL/CSS, so it animates inside a README.

Run: python3 scripts/generate_project_network.py
"""
import math
import os
import textwrap

CAT = dict(rob="#3FB950", ai="#A371F7", hack="#58A6FF", dev="#F0883E")
DARK = dict(rob="#0b2213", ai="#180d29", hack="#0a1c33", dev="#241402")
BG, TEXT, MUTED, BORDER = "#0d1117", "#E6EDF3", "#8B949E", "#30363d"
GH = "https://github.com/Adyansh04"

P = [
    dict(key="grove", name="grove-g1", emoji="🔥", cat="rob", tier=3, url=f"{GH}/grove-g1",
         short="Embodied-AI autonomy stack for the Unitree G1 humanoid — SLAM, Nav2, MoveIt.", desc="Embodied-AI autonomy stack for the Unitree G1 humanoid — SLAM Toolbox, Nav2, MoveIt on ros2_control, simulation-first."),
    dict(key="go2", name="Go2 Inspection", emoji="🐕", cat="rob", tier=3, url=f"{GH}/go2-ros2-inspection",
         short="Language-driven inspection on a Unitree Go2 quadruped — RTAB-Map, Nav2, YOLOE.", desc="Natural-language facility inspection on a Unitree Go2 quadruped — RTAB-Map, Nav2, YOLOE, Claude MCP."),
    dict(key="whycode", name="WhyCode", emoji="⚡", cat="rob", tier=3, url=f"{GH}/whycode",
         short="6-DOF fiducial localization in C++ — SIMD-tuned, CPU 180% to 12%.", desc="6-DOF WhyCon/WhyCode fiducial localization in C++ — SIMD-optimized, CPU 180% to 12%."),
    dict(key="olive", name="OLIVE", emoji="📍", cat="rob", tier=3, url=f"{GH}/olive",
         short="LiDAR + IMU + vision + encoder fusion (iSAM2) for drift-free localization.", desc="Graph-based LiDAR + IMU + vision + encoder fusion (iSAM2) for drift-free AMR localization."),
    dict(key="r2", name="R2 Robocon", emoji="🏎️", cat="rob", tier=2, url=f"{GH}/R2-Robocon",
         short="ABU Robocon 2024 mecanum robot — YOLO detection, Nav2 waypoint autonomy.", desc="ABU Robocon 2024 mecanum robot — YOLO target detection, Nav2 waypoint autonomy, Micro-ROS."),
    dict(key="agro", name="AgroBot", emoji="🌾", cat="rob", tier=2, url=f"{GH}/AgroBot",
         short="Cotton-plucking agricultural AMR — Cartographer SLAM, YOLO, manipulator.", desc="Cotton-plucking agricultural AMR — Cartographer SLAM, YOLO crop detection, manipulator kinematics."),
    dict(key="omni", name="OmniBot", emoji="⚙️", cat="rob", tier=1, url=f"{GH}/omnibot",
         short="Three-wheel kiwi-drive robot — Micro-ROS on ESP32, EKF pose estimation.", desc="Three-wheel kiwi-drive robot — Micro-ROS on ESP32, EKF pose estimation."),
    dict(key="van", name="Vanguard", emoji="🎯", cat="rob", tier=1, url=f"{GH}/eyrc23_gg_1306",
         short="eYRC 2023-24 — overhead-camera A* navigation with CNN localization.", desc="eYRC 2023-24 — overhead-camera A* navigation with CNN localization and QGIS mapping."),
    dict(key="drone", name="Drone Systems", emoji="🚁", cat="rob", tier=2, url=f"{GH}/TelloEDU-ROS2",
         short="Indoor drone autonomy on Tello EDU and Crazyflie — Nav2, SLAM Toolbox.", desc="Indoor drone autonomy on Tello EDU and Crazyflie — ROS2, Nav2, SLAM Toolbox."),
    dict(key="r1", name="R1 Demo", emoji="🦾", cat="rob", tier=1, url=f"{GH}/r1-demo-rc",
         short="Unitree R1 humanoid teleoperation, joint control and simulation.", desc="Unitree R1 humanoid teleoperation, joint control and simulation interface."),
    dict(key="sepsis", name="Sepsis Atlas", emoji="🩺", cat="ai", tier=2, url=f"{GH}/sepsis-atlas",
         short="Local-first clinical RAG — trial PDFs into grounded evidence tables.", desc="Local-first clinical RAG engine — trial PDFs into source-grounded evidence tables (ChromaDB, Claude)."),
    dict(key="hex", name="Hex AI", emoji="🥇", cat="hack", tier=2, url=f"{GH}/hex-game-hackathon",
         short="1st place — autonomous Hex agent driven by Monte-Carlo Tree Search.", desc="1st place — autonomous Hex pathfinding agent with Monte-Carlo Tree Search."),
    dict(key="snake", name="Itestra Snake", emoji="🥈", cat="hack", tier=1, url=f"{GH}/itestra-hackathon",
         short="2nd place — real-time bot for a competitive multiplayer Snake arena.", desc="2nd place — real-time autonomous bot for competitive multiplayer Snake."),
    dict(key="tpl", name="ros2-template", emoji="📦", cat="dev", tier=1, url=f"{GH}/ros2-project-template",
         short="Production-ready ROS 2 C++/Python template — CMake, GTest, CI/CD.", desc="Production-ready ROS2 C++/Python workspace template — CMake, GTest, CI/CD."),
    dict(key="dock", name="ros-docker-dev", emoji="🐳", cat="dev", tier=1, url=f"{GH}/ros-docker-dev",
         short="GPU-accelerated Docker development environments for ROS 1 and ROS 2.", desc="GPU-accelerated Docker development environments for ROS 1 / ROS 2."),
]


# Custom per-project vector icons — detailed geometry + per-project motion.
# `s` static strokes, `f` filled shapes, `a` animated markup ({C} = accent colour).
ICONS = {
    "grove": dict(  # G1 humanoid: visored head, torso, swinging arms, legs
        f='M-2.8,-7.6 h5.6 a1.3,1.3 0 0 1 1.3,1.3 v2.8 a1.3,1.3 0 0 1 -1.3,1.3 h-5.6 a1.3,1.3 0 0 1 -1.3,-1.3 v-2.8 a1.3,1.3 0 0 1 1.3,-1.3 Z',
        s='M-2.2,-2.6 h4.4 a1,1 0 0 1 1,1 v3.4 a1,1 0 0 1 -1,1 h-4.4 a1,1 0 0 1 -1,-1 v-3.4 a1,1 0 0 1 1,-1 Z M-1.4,2.8 V6.6 M1.4,2.8 V6.6',
        a='<rect x="-1.9" y="-6.2" width="3.8" height="1.4" rx="0.7" fill="{C}" opacity="0.45">'
          '<animate attributeName="opacity" values="0.25;0.9;0.25" dur="2.2s" repeatCount="indefinite"/></rect>'
          '<g><animateTransform attributeName="transform" type="rotate" values="-10 -3.2 -2; 10 -3.2 -2; -10 -3.2 -2" dur="2.6s" repeatCount="indefinite"/>'
          '<path d="M-3.2,-2 L-4.6,2.2" stroke="{C}" stroke-width="1.5" stroke-linecap="round" fill="none"/></g>'
          '<g><animateTransform attributeName="transform" type="rotate" values="10 3.2 -2; -10 3.2 -2; 10 3.2 -2" dur="2.6s" repeatCount="indefinite"/>'
          '<path d="M3.2,-2 L4.6,2.2" stroke="{C}" stroke-width="1.5" stroke-linecap="round" fill="none"/></g>'),
    "go2": dict(  # quadruped: body, head, trotting legs
        s='M-5,-2.2 h8.2 a1.2,1.2 0 0 1 1.2,1.2 v1.8 a1.2,1.2 0 0 1 -1.2,1.2 h-8.2 a1.2,1.2 0 0 1 -1.2,-1.2 v-1.8 a1.2,1.2 0 0 1 1.2,-1.2 Z M4.4,-2.4 L6.4,-5 h1.2',
        f='M6.9,-5.4 m-0.9,0 a0.9,0.9 0 1,0 1.8,0 a0.9,0.9 0 1,0 -1.8,0',
        a='<g><animateTransform attributeName="transform" type="rotate" values="16 -4 2; -16 -4 2; 16 -4 2" dur="0.66s" repeatCount="indefinite"/>'
          '<path d="M-4,2 V5.8" stroke="{C}" stroke-width="1.4" stroke-linecap="round"/></g>'
          '<g><animateTransform attributeName="transform" type="rotate" values="-16 -1.4 2; 16 -1.4 2; -16 -1.4 2" dur="0.66s" repeatCount="indefinite"/>'
          '<path d="M-1.4,2 V5.8" stroke="{C}" stroke-width="1.4" stroke-linecap="round"/></g>'
          '<g><animateTransform attributeName="transform" type="rotate" values="-16 1.2 2; 16 1.2 2; -16 1.2 2" dur="0.66s" repeatCount="indefinite"/>'
          '<path d="M1.2,2 V5.8" stroke="{C}" stroke-width="1.4" stroke-linecap="round"/></g>'
          '<g><animateTransform attributeName="transform" type="rotate" values="16 3.8 2; -16 3.8 2; 16 3.8 2" dur="0.66s" repeatCount="indefinite"/>'
          '<path d="M3.8,2 V5.8" stroke="{C}" stroke-width="1.4" stroke-linecap="round"/></g>'),
    "whycode": dict(  # fiducial: rings + orientation notch + lock pulse
        s='M0,-6.2 a6.2,6.2 0 1,0 0.1,0 M0,-3.4 a3.4,3.4 0 1,0 0.1,0',
        f='M0,0 m-1.3,0 a1.3,1.3 0 1,0 2.6,0 a1.3,1.3 0 1,0 -2.6,0 M-0.7,-7.2 h1.4 v2 h-1.4 Z',
        a='<circle r="6.2" fill="none" stroke="{C}" stroke-width="1.2">'
          '<animate attributeName="r" values="3.4;7.6" dur="1.8s" repeatCount="indefinite"/>'
          '<animate attributeName="opacity" values="0.8;0" dur="1.8s" repeatCount="indefinite"/></circle>'),
    "olive": dict(  # SLAM pin + expanding scan waves
        s='M0,6.2 C-4.4,0.6 -4.4,-2.2 0,-5.8 C4.4,-2.2 4.4,0.6 0,6.2 Z',
        f='M0,-2.4 m-1.6,0 a1.6,1.6 0 1,0 3.2,0 a1.6,1.6 0 1,0 -3.2,0',
        a='<path d="M-5.4,-4.6 a7.6,7.6 0 0,1 10.8,0" fill="none" stroke="{C}" stroke-width="1.2" opacity="0">'
          '<animate attributeName="opacity" values="0;0.9;0" dur="1.9s" repeatCount="indefinite"/></path>'
          '<path d="M-7.4,-2.6 a10,10 0 0,1 14.8,0" fill="none" stroke="{C}" stroke-width="1" opacity="0">'
          '<animate attributeName="opacity" values="0;0.6;0" dur="1.9s" begin="0.5s" repeatCount="indefinite"/></path>'),
    "r2": dict(  # mecanum wheel: rim + spinning angled rollers
        s='M0,-6 a6,6 0 1,0 0.1,0',
        f='M0,0 m-1.2,0 a1.2,1.2 0 1,0 2.4,0 a1.2,1.2 0 1,0 -2.4,0',
        a='<g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="2.6s" repeatCount="indefinite"/>'
          '<path d="M-3.9,-2.4 L-1.6,-4.4 M-1.9,0.6 L1.3,-2.2 M0.4,3.4 L3.6,0.9 M3.2,-3 L4.6,-1.4" '
          'stroke="{C}" stroke-width="1.3" stroke-linecap="round" fill="none"/></g>'),
    "agro": dict(  # cotton plant, swaying
        s='M0,6.4 V-0.8',
        f='',
        a='<g><animateTransform attributeName="transform" type="rotate" values="-5 0 6.4; 5 0 6.4; -5 0 6.4" dur="3.4s" repeatCount="indefinite"/>'
          '<path d="M0,2 C-3.8,1.4 -4.8,-0.8 -4.6,-2.8 C-2.2,-2.6 -0.8,-1 0,0.8" fill="{C}" opacity="0.35" stroke="{C}" stroke-width="1"/>'
          '<path d="M0,0.6 C3.6,-0.2 4.6,-2.4 4.4,-4.4 C2,-4 0.6,-2.4 0,-0.6" fill="{C}" opacity="0.35" stroke="{C}" stroke-width="1"/>'
          '<circle cy="-4.6" r="2.2" fill="{C}"/><circle cx="-1.8" cy="-3" r="1.3" fill="{C}" opacity="0.7"/>'
          '<circle cx="1.9" cy="-2.6" r="1.2" fill="{C}" opacity="0.7"/></g>'),
    "omni": dict(  # kiwi drive: chassis + 3 rollers, slow spin
        s='',
        f='',
        a='<g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="6s" repeatCount="indefinite"/>'
          '<path d="M0,-5.2 L4.6,2.8 H-4.6 Z" fill="none" stroke="{C}" stroke-width="1.5" stroke-linejoin="round"/>'
          '<rect x="-1.8" y="-7.2" width="3.6" height="2.4" rx="1" fill="{C}"/>'
          '<rect x="3.2" y="1.8" width="3.4" height="2.4" rx="1" fill="{C}" transform="rotate(60 4.9 3)"/>'
          '<rect x="-6.6" y="1.8" width="3.4" height="2.4" rx="1" fill="{C}" transform="rotate(-60 -4.9 3)"/>'
          '<circle r="1.4" fill="{C}" opacity="0.6"/></g>'),
    "van": dict(  # A* grid with an animated solved path
        s='M-6,-6 H6 V6 H-6 Z M-2,-6 V6 M2,-6 V6 M-6,-2 H6 M-6,2 H6',
        f='M-5,-5 h2 v2 h-2 Z',
        a='<path d="M-4,-4 H0 V0 H4 V4" fill="none" stroke="{C}" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round" stroke-dasharray="16" stroke-dashoffset="16">'
          '<animate attributeName="stroke-dashoffset" values="16;0;0;16" keyTimes="0;0.45;0.8;1" dur="2.8s" repeatCount="indefinite"/></path>'
          '<circle cx="4" cy="4" r="1.5" fill="{C}"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.45;0.5;0.8;1" dur="2.8s" repeatCount="indefinite"/></circle>'),
    "drone": dict(  # quadcopter with spinning rotors
        s='M-4.2,-4.2 L4.2,4.2 M-4.2,4.2 L4.2,-4.2',
        f='M0,0 m-2,0 a2,2 0 1,0 4,0 a2,2 0 1,0 -4,0',
        a=''.join('<g transform="translate(%s,%s)"><animateTransform attributeName="transform" type="rotate" '
                  'from="0" to="360" dur="0.22s" repeatCount="indefinite" additive="sum"/>'
                  '<ellipse rx="2.9" ry="0.9" fill="{C}" opacity="0.75"/></g>' % (px, py)
                  for px, py in [(-4.6, -4.6), (4.6, -4.6), (-4.6, 4.6), (4.6, 4.6)])),
    "r1": dict(  # articulated arm with a gripper that opens and closes
        s='M-5.2,6.4 h6 M-2.2,6.4 V2.6 L1.8,-1.4',
        f='M-2.2,2.6 m-1.5,0 a1.5,1.5 0 1,0 3,0 a1.5,1.5 0 1,0 -3,0 M1.8,-1.4 m-1.2,0 a1.2,1.2 0 1,0 2.4,0 a1.2,1.2 0 1,0 -2.4,0',
        a='<g transform="translate(1.8,-1.4) rotate(-45)">'
          '<g><animateTransform attributeName="transform" type="translate" values="0,-0.9;0,-1.9;0,-0.9" dur="1.8s" repeatCount="indefinite"/>'
          '<path d="M0,-2.6 V-5.4" stroke="{C}" stroke-width="1.4" stroke-linecap="round"/></g>'
          '<g><animateTransform attributeName="transform" type="translate" values="0,0.9;0,1.9;0,0.9" dur="1.8s" repeatCount="indefinite"/>'
          '<path d="M0,2.6 V5.4" stroke="{C}" stroke-width="1.4" stroke-linecap="round"/></g>'
          '<path d="M0,-2.6 L-2.4,-4.4 M0,2.6 L-2.4,4.4" stroke="{C}" stroke-width="1.2" stroke-linecap="round" opacity="0.5"/></g>'),
    "sepsis": dict(  # clinical document with a live ECG trace
        s='M-5,-6.4 h7.4 l2.6,2.6 V6.4 h-10 Z M2.4,-6.4 v2.6 h2.6',
        f='',
        a='<path d="M-3.4,0.6 h1.6 l1,-3 l1.4,5.4 l1,-2.4 h1.8" fill="none" stroke="{C}" stroke-width="1.3" '
          'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="14" stroke-dashoffset="14">'
          '<animate attributeName="stroke-dashoffset" values="14;0;0" keyTimes="0;0.6;1" dur="2.4s" repeatCount="indefinite"/></path>'),
    "hex": dict(  # hex board with a pulsing winning cell
        s='M0,-6.4 L5.5,-3.2 V3.2 L0,6.4 L-5.5,3.2 V-3.2 Z M0,-3.2 L2.8,-1.6 V1.6 L0,3.2 L-2.8,1.6 V-1.6 Z',
        f='',
        a='<path d="M0,-3.2 L2.8,-1.6 V1.6 L0,3.2 L-2.8,1.6 V-1.6 Z" fill="{C}" opacity="0.3">'
          '<animate attributeName="opacity" values="0.15;0.75;0.15" dur="2s" repeatCount="indefinite"/></path>'),
    "snake": dict(  # snake body slithering + head
        s='',
        f='',
        a='<path d="M-6.4,3.6 H-2.6 a2.2,2.2 0 0,0 2.2,-2.2 V-1.4 a2.2,2.2 0 0,1 2.2,-2.2 H4.4" fill="none" '
          'stroke="{C}" stroke-width="1.7" stroke-linecap="round" stroke-dasharray="2.6,1.6">'
          '<animate attributeName="stroke-dashoffset" values="8.4;0" dur="1.4s" repeatCount="indefinite"/></path>'
          '<circle cx="5.6" cy="-3.6" r="1.9" fill="{C}"/>'
          '<circle cx="6.4" cy="-4.2" r="0.5" fill="#0d1117"/>'),
    "tpl": dict(  # package with a scan line sweeping over it
        s='M-6,-3.2 L0,-6.4 L6,-3.2 V3.6 L0,6.8 L-6,3.6 Z M-6,-3.2 L0,0 L6,-3.2 M0,0 V6.8',
        f='',
        a='<path d="M-6,-3.2 L0,-6.4 L6,-3.2 V3.6 L0,6.8 L-6,3.6 Z" fill="{C}" opacity="0">'
          '<animate attributeName="opacity" values="0;0.28;0" dur="2.6s" repeatCount="indefinite"/></path>'),
    "dock": dict(  # container stack with a blinking status light
        s='M-6.4,0.6 H-1.2 V5 H-6.4 Z M1,0.6 H6.2 V5 H1 Z M-2.8,-4.8 H2.6 V-0.4 H-2.8 Z',
        f='',
        a='<path d="M-5.6,0.6 V5 M-3.8,0.6 V5 M1.8,0.6 V5 M3.6,0.6 V5 M-1.6,-4.8 V-0.4 M0.2,-4.8 V-0.4" '
          'stroke="{C}" stroke-width="0.7" opacity="0.45"/>'
          '<circle cx="4.6" cy="-3.4" r="1.1" fill="{C}">'
          '<animate attributeName="opacity" values="1;0.15;1" dur="1.6s" repeatCount="indefinite"/></circle>'),
}


def icon(key, color, scale=1.0, sw=1.5):
    d = ICONS[key]
    g = (f'<g transform="scale({scale})" stroke="{color}" stroke-width="{sw}" fill="none" '
         f'stroke-linecap="round" stroke-linejoin="round">')
    if d.get("s"):
        g += f'<path d="{d["s"]}"/>'
    if d.get("f"):
        g += f'<path d="{d["f"]}" fill="{color}" stroke="none"/>'
    if d.get("a"):
        g += d["a"].replace("{C}", color)
    return g + '</g>'


def w(path, svg):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, "w") as f:
        f.write(svg)


def head(wd, ht, extra=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {wd} {ht}" '
            f'width="{wd}" height="{ht}">'
            f'<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;user-select:none}}{extra}</style>')


def fusion_conveyornet():
    """FINAL — large labelled routing map: every project is a card with its own
    2-line description, so nothing depends on hover. Cards flank a QC sort hub
    that classifies each package into a category neuron -> output -> GitHub."""
    W_, H_ = 1000, 700
    CW, CH, PITCH = 330, 52, 62
    hub, HS = (500, 250), 38
    T = 12.0
    s = [head(W_, H_)]
    s.append(f'<rect width="{W_}" height="{H_}" rx="14" fill="{BG}" stroke="{BORDER}"/>')
    s.append('<defs><pattern id="pn-grid" width="25" height="25" patternUnits="userSpaceOnUse">'
             f'<path d="M25 0 L0 0 0 25" fill="none" stroke="#151b24" stroke-width="0.7"/></pattern></defs>'
             f'<rect width="{W_}" height="{H_}" rx="14" fill="url(#pn-grid)" opacity="0.7"/>')

    L, R = P[:8], P[8:]
    lcards = [(14, 70 + i * PITCH) for i in range(len(L))]
    rcards = [(W_ - 14 - CW, 101 + i * PITCH) for i in range(len(R))]
    lports = [(hub[0] - HS, hub[1] - 42 + k * 12) for k in range(len(L))]
    rports = [(hub[0] + HS, hub[1] - 36 + k * 12) for k in range(len(R))]

    neurons = {"rob": (380, 420), "ai": (460, 420), "hack": (540, 420), "dev": (620, 420)}
    nlabel = {"rob": "ROBOTICS", "ai": "AI &amp; DATA", "hack": "HACKATHONS", "dev": "DEV TOOLS"}
    out, ship = (500, 545), (500, 640)

    # ---- orthogonal routes, nested so no two traces cross.
    # Cards above the hub turn closest to it, cards below turn farthest out;
    # within each group the outermost card turns first. Elbows are rounded.
    def zpath(x0, y0, tx, py, x1):
        d1 = 1 if tx > x0 else -1
        d2 = 1 if py > y0 else -1
        d3 = 1 if x1 > tx else -1
        r = min(9, abs(tx - x0), abs(x1 - tx), abs(py - y0) / 2)
        if r < 1.5:
            return f"M{x0},{y0} H{tx} V{py} H{x1}"
        return (f"M{x0},{y0} H{tx - d1 * r} Q{tx},{y0} {tx},{y0 + d2 * r} "
                f"V{py - d2 * r} Q{tx},{py} {tx + d3 * r},{py} H{x1}")

    def lanes(cards, ports, side):
        """Assign each card its turn-x so traces nest instead of crossing."""
        idx = list(range(len(cards)))
        above = [i for i in idx if cards[i][1] + CH / 2 <= hub[1]]
        below = [i for i in idx if i not in above]
        tx = {}
        if side == "L":
            near, far = 452, 412          # above group hugs the hub, below runs wide
            for n, i in enumerate(above):          # topmost turns closest to hub
                tx[i] = near - n * 13
            for n, i in enumerate(below):          # topmost turns innermost of the wide band
                tx[i] = far - (len(below) - 1 - n) * 13
        else:
            near, far = W_ - 452, W_ - 412
            for n, i in enumerate(above):
                tx[i] = near + n * 13
            for n, i in enumerate(below):
                tx[i] = far + (len(below) - 1 - n) * 13
        return tx

    routes = []
    ltx = lanes(lcards, lports, "L")
    for i, ((cx0, cy0), (px, py)) in enumerate(zip(lcards, lports)):
        routes.append(zpath(cx0 + CW, cy0 + CH / 2, ltx[i], py, px))
    rtx = lanes(rcards, rports, "R")
    for j, ((cx0, cy0), (px, py)) in enumerate(zip(rcards, rports)):
        routes.append(zpath(cx0, cy0 + CH / 2, rtx[j], py, px))
    for p, d in zip(P, routes):
        c = CAT[p["cat"]]
        s.append(f'<path d="{d}" fill="none" stroke="#1b222c" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<path d="{d}" fill="none" stroke="{c}" stroke-width="1.3" stroke-dasharray="4,8" opacity="0.45" '
                 f'stroke-linecap="round" stroke-linejoin="round">'
                 f'<animate attributeName="stroke-dashoffset" values="24;0" dur="1.2s" repeatCount="indefinite"/></path>')

    # ---- neural stage: hub -> category neurons -> output -> ship (curved)
    nedges, oedges = {}, {}
    for k, (nx, ny) in neurons.items():
        nedges[k] = f"M{hub[0]},{hub[1] + HS} C{hub[0]},{hub[1] + HS + 70} {nx},{ny - 80} {nx},{ny - 17}"
        s.append(f'<path d="{nedges[k]}" fill="none" stroke="{CAT[k]}" stroke-width="1.3" opacity="0.35"/>')
        oedges[k] = f"M{nx},{ny + 17} C{nx},{ny + 62} {out[0]},{out[1] - 62} {out[0]},{out[1] - 24}"
        s.append(f'<path d="{oedges[k]}" fill="none" stroke="{CAT[k]}" stroke-width="1.3" opacity="0.35"/>')
    s.append(f'<path d="M{out[0]},{out[1] + 24} V{ship[1] - 22}" stroke="#1b222c" stroke-width="5"/>'
             f'<path d="M{out[0]},{out[1] + 24} V{ship[1] - 22}" stroke="#3FB950" stroke-width="1.8" stroke-dasharray="6,8">'
             f'<animate attributeName="stroke-dashoffset" values="28;0" dur="0.8s" repeatCount="indefinite"/></path>')

    # ---- travelling packages (arrivals spaced T/15 -> never overlap at the hub)
    for i, (p, d) in enumerate(zip(P, routes)):
        beg = -(i * T / 15)
        c = CAT[p["cat"]]
        s.append(f'''<g><animateMotion path="{d}" keyPoints="0;0;1;1" keyTimes="0;0.34;0.995;1" calcMode="linear" dur="{T}s" begin="{beg:.2f}s" repeatCount="indefinite"/>
<g><animateTransform attributeName="transform" type="scale" values="0;0;1;1;0" keyTimes="0;0.31;0.35;0.985;1" dur="{T}s" begin="{beg:.2f}s" repeatCount="indefinite"/>
<rect x="-10" y="-10" width="20" height="20" rx="4" fill="{DARK[p["cat"]]}" stroke="{c}" stroke-width="1.2"/>
{icon(p["key"], c, 0.8, 1.5)}</g></g>''')

    # ---- sort + relay pulses, fired on each arrival
    spikes = {k: [] for k in CAT}
    for i, p in enumerate(P):
        beg = -(i * T / 15)
        k = p["cat"]
        spikes[k].append(((0.0 if i == 0 else (T - i * T / 15) / T) + 0.06) % 1.0)
        s.append(f'<circle r="3" fill="{CAT[k]}" opacity="0">'
                 f'<animateMotion path="{nedges[k]}" keyPoints="0;0;1;1" keyTimes="0;0.001;0.05;1" calcMode="linear" dur="{T}s" begin="{beg:.2f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0.95;0.95;0;0" keyTimes="0;0.004;0.045;0.05;1" dur="{T}s" begin="{beg:.2f}s" repeatCount="indefinite"/></circle>')
        s.append(f'<circle r="2.6" fill="{CAT[k]}" opacity="0">'
                 f'<animateMotion path="{oedges[k]}" keyPoints="0;0;1;1" keyTimes="0;0.05;0.1;1" calcMode="linear" dur="{T}s" begin="{beg:.2f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0;0.95;0;0" keyTimes="0;0.05;0.075;0.1;1" dur="{T}s" begin="{beg:.2f}s" repeatCount="indefinite"/></circle>')

    # ---- project cards: icon + name + 2-line description, whole card is a link
    for p, (x, y) in zip(P, lcards + rcards):
        c = CAT[p["cat"]]
        lines = textwrap.wrap(p["short"], 54)[:2]
        body = "".join(f'<text x="48" y="{33 + n * 11}" font-size="8" fill="{MUTED}">{ln}</text>'
                       for n, ln in enumerate(lines))
        s.append(
            f'<a href="{p["url"]}" target="_blank" class="hot">'
            f'<title>{p["name"]} — {p["short"]}</title>'
            f'<g transform="translate({x},{y})">'
            f'<rect width="{CW}" height="{CH}" rx="9" fill="{DARK[p["cat"]]}" stroke="{c}" stroke-width="1.3"/>'
            f'<rect width="4" height="{CH}" rx="2" fill="{c}"/>'
            f'<g transform="translate(27,{CH / 2})">{icon(p["key"], c, 0.95, 1.5)}</g>'
            f'<text x="48" y="19" font-size="11.5" font-weight="800" fill="{TEXT}">{p["name"]}</text>'
            f'{body}</g></a>')

    # ---- QC sort hub
    s.append(f'''<g transform="translate({hub[0]},{hub[1]})">
<rect x="-{HS}" y="-{HS}" width="{HS * 2}" height="{HS * 2}" rx="10" fill="#131922" stroke="#D29922" stroke-width="2"/>
<rect x="-{HS}" y="-{HS}" width="{HS * 2}" height="{HS * 2}" rx="10" fill="#D29922" opacity="0">
<animate attributeName="opacity" values="0;0.3;0" keyTimes="0;0.12;1" dur="{T / 15:.3f}s" repeatCount="indefinite"/></rect>
<path d="M-17,0 h34 M0,-17 v34" stroke="#D29922" stroke-width="1.7"/>
<g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="6s" repeatCount="indefinite"/>
<circle r="27" fill="none" stroke="#D29922" stroke-width="0.9" stroke-dasharray="2,9" opacity="0.6"/></g>
<text y="-{HS + 12}" font-size="9" font-weight="800" fill="#D29922" text-anchor="middle">QC · SORT HUB</text></g>''')

    # ---- category neurons
    for k, (nx, ny) in neurons.items():
        sp = sorted(t for t in spikes[k] if 0.02 < t < 0.97)
        vals, kts = ["1.6"], ["0"]
        for t in sp:
            vals += ["1.6", "3.4", "1.6"]
            kts += [fmt6(t - 0.012), fmt6(t), fmt6(t + 0.015)]
        vals.append("1.6")
        kts.append("1")
        s.append(f'<circle cx="{nx}" cy="{ny}" r="15" fill="{DARK[k]}" stroke="{CAT[k]}" stroke-width="1.6">'
                 f'<animate attributeName="stroke-width" values="{";".join(vals)}" keyTimes="{";".join(kts)}" dur="{T}s" repeatCount="indefinite"/></circle>'
                 f'<circle cx="{nx}" cy="{ny}" r="4.5" fill="{CAT[k]}" opacity="0.85"/>'
                 f'<text x="{nx}" y="{ny + 30}" font-size="7" font-weight="700" fill="{CAT[k]}" text-anchor="middle">{nlabel[k]}</text>')
    s.append(f'<text x="{hub[0]}" y="{neurons["rob"][1] - 44}" font-size="7.5" fill="{MUTED}" text-anchor="middle">neural sort · 4 classes</text>')

    # ---- output neuron + shipping
    s.append(f'''<g transform="translate({out[0]},{out[1]})">
<circle r="30" fill="none" stroke="#3FB950" opacity="0.4"><animate attributeName="r" values="26;42" dur="{T / 15:.3f}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.45;0" dur="{T / 15:.3f}s" repeatCount="indefinite"/></circle>
<circle r="24" fill="#0b2213" stroke="#3FB950" stroke-width="2.2"/>
<text y="-2" font-size="9.5" font-weight="900" fill="{TEXT}" text-anchor="middle">ADYANSH</text>
<text y="10" font-size="6" fill="#3FB950" text-anchor="middle">output layer</text></g>''')
    s.append(f'''<g transform="translate({ship[0]},{ship[1]})">
<rect x="-70" y="-22" width="140" height="44" rx="9" fill="#0b2213" stroke="#3FB950" stroke-width="2"/>
<text y="-2" font-size="10" font-weight="800" fill="{TEXT}" text-anchor="middle">github.com/Adyansh04</text>
<text y="11" font-size="7" fill="#3FB950" text-anchor="middle">15 repositories shipped</text></g>''')

    s.append(f'<text x="24" y="30" font-size="12" font-weight="800" fill="{TEXT}" letter-spacing="1">PROJECT ROUTING NETWORK</text>'
             f'<text x="24" y="46" font-size="8.5" fill="{MUTED}">every project runs the same pipeline: build → QC sort → classify → ship</text>'
             f'<text x="{W_ - 24}" y="{H_ - 16}" font-size="8.5" fill="{MUTED}" text-anchor="end">github.com/Adyansh04 · open the live map to click a card</text>')
    s.append('<style>.hot{cursor:pointer}</style></svg>')
    return "".join(s)


def fmt6(x):
    return f"{max(0.001, min(x, 0.999)):.4f}"

def main():
    w("assets/project-network.svg", fusion_conveyornet())
    print("wrote assets/project-network.svg")


if __name__ == "__main__":
    main()
