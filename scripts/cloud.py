#!/usr/bin/env python3
"""Draw assets/cloud.svg: a looping, stylized failover scene.

Users send traffic through a load balancer to two Availability Zones. One zone
fails, traffic reroutes, capacity is replaced, the zone recovers, and a backup
copies to a second region. Motion is CSS only (no JavaScript), colours follow
the viewer's theme, and reduced-motion viewers get a calm finished frame.
"""
import pathlib
from xml.sax.saxutils import escape

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
cfg = yaml.safe_load((ROOT / "profile.yml").read_text(encoding="utf-8"))
caps = cfg["cloud"]["captions"]

W, H, L = 800, 380, 16  # canvas and loop length in seconds
# loop timeline in percent: (start, end) windows for each phase
CAP_WIN = [(0, 23), (25, 38), (40, 58), (60, 70), (72, 95)]
FAIL = [(25, 70)]
NEWSRV = [(42, 96)]
BACKUP = [(72, 94)]
VAULT = [(74, 96)]
BADGE = [(88, 96)]
A_FLOW = [(0, 24), (70, 100)]


def kf(name, wins):
    pts = []
    for s, e in wins:
        if s > 0:
            pts += [(round(s - 0.8, 2), 0), (s, 1)]
        else:
            pts.append((0, 1))
        if e < 100:
            pts += [(e, 1), (round(e + 0.8, 2), 0)]
        else:
            pts.append((100, 1))
    if pts[0][0] != 0:
        pts.insert(0, (0, 0))
    if pts[-1][0] != 100:
        pts.append((100, 0))
    body = "".join(f"{p}%{{opacity:{v}}}" for p, v in pts)
    return f"@keyframes {name}{{{body}}}.{name}{{animation:{name} {L}s linear infinite}}"


def mv(name, dx, dy):
    return (
        f"@keyframes {name}{{0%{{transform:translate(0,0);opacity:0}}12%{{opacity:1}}"
        f"88%{{opacity:1}}100%{{transform:translate({dx}px,{dy}px);opacity:0}}}}"
        f".{name}{{animation:{name} 2s linear infinite}}"
    )


css = [
    "svg{--bg:#ffffff;--bdr:#d0d7de;--node:#f6f8fa;--panel:#fafbfc;--txt:#1f2328;--mut:#59636e;"
    "--grn:#1a7f37;--glow:#dafbe1;--red:#cf222e;--redbg:#ffebe9;--pur:#8250df;--purbg:#fbefff;--amb:#bf8700}",
    "@media (prefers-color-scheme:dark){svg{--bg:#0d1117;--bdr:#30363d;--node:#161b22;--panel:#0f141b;"
    "--txt:#e6edf3;--mut:#8b949e;--grn:#3fb950;--glow:#12261e;--red:#f85149;--redbg:#2d1214;"
    "--pur:#a371f7;--purbg:#1f1633;--amb:#d29922}}",
    "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace;"
    "font-size:12px;fill:var(--txt)}",
    ".card{fill:var(--bg);stroke:var(--bdr)}.panel{fill:var(--panel);stroke:var(--bdr)}",
    ".az{fill:none;stroke:var(--bdr);stroke-dasharray:4 4}",
    ".node{fill:var(--node);stroke:var(--bdr)}.slot{fill:none;stroke:var(--bdr);stroke-dasharray:3 3}",
    ".bar{fill:var(--bdr)}.led{fill:var(--grn)}.mut{fill:var(--mut)}",
    ".edge{stroke:var(--bdr);stroke-width:2}.dash{stroke:var(--bdr);stroke-width:2;stroke-dasharray:5 5}",
    ".pk{fill:var(--grn)}.pk2{fill:var(--pur)}",
    ".lb{fill:var(--glow);stroke:var(--grn);stroke-width:2}",
    ".failpanel{fill:var(--redbg);stroke:var(--red);stroke-width:1.5}.failtxt{fill:var(--red);font-weight:700}",
    ".dim{fill:var(--bg);opacity:.7}.redled{fill:var(--red)}",
    ".vbox{fill:var(--node);stroke:var(--bdr);stroke-width:2}",
    ".vlit{fill:var(--purbg);stroke:var(--pur);stroke-width:2}.vkey{fill:var(--pur)}",
    ".ok{fill:var(--grn)}.oktxt{fill:#ffffff;font-weight:700}",
    ".capbar{fill:var(--node);stroke:var(--bdr)}.captxt{font-size:13px}",
    ".sp{opacity:0}",
]
for i, w in enumerate(CAP_WIN):
    css.append(kf(f"c{i}", [w]))
css.append(kf("fail", FAIL))
css.append(kf("newsrv", NEWSRV))
css.append(kf("bk", BACKUP))
css.append(kf("vault", VAULT))
css.append(kf("badge", BADGE))
css.append(kf("aflow", A_FLOW))
css.append(mv("m1", 106, 0))
css.append(mv("m2", 124, -56))
css.append(mv("m3", 124, 58))
css.append(mv("m4", 96, -8))
css.append(
    "@media (prefers-reduced-motion:reduce){.sp,.c0,.c1,.c2,.c3,.c4,.fail,.newsrv,.bk,.vault,.badge,.aflow{animation:none!important}"
    ".c0,.c1,.c2,.c3,.fail,.bk,.pk,.pk2{opacity:0!important}.c4,.newsrv,.vault,.badge,.aflow{opacity:1!important}}"
)

p = []
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
p.append('<title id="t">A load-balanced cloud app surviving a zone failure</title>')
p.append(
    '<desc id="d">A looping illustration. Users send traffic through a load balancer to two Availability Zones. '
    + escape(" ".join(caps))
    + "</desc>"
)
p.append("<style>" + "".join(css) + "</style>")
p.append(f'<rect class="card" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10"/>')

# users
for y in (140, 170, 200):
    p.append(f'<circle class="node" cx="70" cy="{y}" r="8" stroke-width="2"/>')
p.append('<text class="mut" x="70" y="232" text-anchor="middle">users</text>')
p.append('<line class="edge" x1="88" y1="170" x2="190" y2="170"/>')

# load balancer
p.append('<polygon class="lb" points="250,170 235,196 205,196 190,170 205,144 235,144"/>')
p.append('<text x="220" y="175" text-anchor="middle" font-weight="700">LB</text>')
p.append('<text class="mut" x="220" y="216" text-anchor="middle">load balancer</text>')
p.append('<line class="edge" x1="250" y1="170" x2="374" y2="114"/>')
p.append('<line class="edge" x1="250" y1="170" x2="374" y2="228"/>')

# region 1
p.append('<rect class="panel" x="340" y="30" width="260" height="270" rx="10"/>')
p.append('<text class="mut" x="356" y="50">region 1</text>')
for label, top in (("az-a", 62), ("az-b", 176)):
    p.append(f'<rect class="az" x="356" y="{top}" width="228" height="104" rx="8"/>')
    p.append(f'<text class="mut" x="368" y="{top + 18}">{label}</text>')


def server(x, y):
    return (
        f'<rect class="node" x="{x}" y="{y}" width="56" height="40" rx="6" stroke-width="2"/>'
        f'<rect class="bar" x="{x + 8}" y="{y + 10}" width="30" height="4" rx="2"/>'
        f'<rect class="bar" x="{x + 8}" y="{y + 20}" width="22" height="4" rx="2"/>'
        f'<circle class="led" cx="{x + 46}" cy="{y + 12}" r="3.5"/>'
    )


for x in (376, 444):
    p.append(server(x, 94))
    p.append(server(x, 208))
p.append('<rect class="slot" x="512" y="208" width="56" height="40" rx="6"/>')
p.append('<g class="newsrv sp">' + server(512, 208) + "</g>")
p.append('<text class="mut sp newsrv" x="540" y="266" text-anchor="middle" font-size="11">+1 instance</text>')

# az-a failure overlay
p.append('<g class="fail sp">')
p.append('<rect class="failpanel" x="356" y="62" width="228" height="104" rx="8"/>')
for x in (376, 444):
    p.append(f'<rect class="dim" x="{x}" y="94" width="56" height="40" rx="6"/>')
    p.append(f'<circle class="redled" cx="{x + 46}" cy="106" r="3.5"/>')
p.append('<text class="failtxt" x="514" y="118">az-a down</text>')
p.append("</g>")

# region 2 + vault
p.append('<rect class="panel" x="650" y="150" width="124" height="150" rx="10"/>')
p.append('<text class="mut" x="664" y="170">region 2</text>')
p.append('<rect class="vbox" x="680" y="184" width="64" height="64" rx="10"/>')
p.append('<g class="vault sp"><rect class="vlit" x="680" y="184" width="64" height="64" rx="10"/>'
         '<circle class="vkey" cx="712" cy="212" r="7"/><rect class="vkey" x="709" y="214" width="6" height="14" rx="2"/></g>')
p.append('<text class="mut" x="712" y="266" text-anchor="middle">vault</text>')
p.append('<line class="dash" x1="584" y1="228" x2="680" y2="220"/>')
p.append('<g class="badge sp"><rect class="ok" x="660" y="276" width="104" height="18" rx="9"/>'
         '<text class="oktxt" x="712" y="289" text-anchor="middle" font-size="11">HTTP 200</text></g>')

# traffic
for d in (0, 0.66, 1.33):
    p.append(f'<circle class="pk m1" cx="94" cy="170" r="4" style="animation-delay:{d}s"/>')
    p.append(f'<circle class="pk m3" cx="250" cy="170" r="4" style="animation-delay:{d}s"/>')
p.append('<g class="aflow">')
for d in (0, 0.66, 1.33):
    p.append(f'<circle class="pk m2" cx="250" cy="170" r="4" style="animation-delay:{d}s"/>')
p.append("</g>")
p.append('<g class="bk sp">')
for d in (0, 0.66, 1.33):
    p.append(f'<circle class="pk2 m4" cx="584" cy="228" r="4.5" style="animation-delay:{d}s"/>')
p.append("</g>")

# caption bar
p.append('<rect class="capbar" x="24" y="324" width="752" height="40" rx="8"/>')
for i, c in enumerate(caps):
    p.append(f'<text class="captxt sp c{i}" x="44" y="349">{escape(c)}</text>')
p.append("</svg>")

(ROOT / "assets").mkdir(exist_ok=True)
(ROOT / "assets" / "cloud.svg").write_text("\n".join(p) + "\n", encoding="utf-8")
print("built assets/cloud.svg")
