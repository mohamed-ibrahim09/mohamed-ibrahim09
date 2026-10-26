#!/usr/bin/env python3
"""Build README.md and assets/profile.svg from profile.yml.

The SVG is a GitHub-style diff of a `profile.tf` file. Lines appear one by one,
then the status badge flips from Open to Merged. Colours follow the viewer's
light or dark theme, and reduced-motion viewers get the finished state.
"""
import pathlib
from xml.sax.saxutils import escape

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
cfg = yaml.safe_load((ROOT / "profile.yml").read_text(encoding="utf-8"))

# ---------- code lines ----------------------------------------------------

def q(s):
    return f'"{s}"'


def value_text(v):
    if isinstance(v, list):
        return "[" + ", ".join(q(i) for i in v) + "]"
    return q(v)


def value_svg(v):
    if isinstance(v, list):
        inner = ", ".join(f'<tspan class="str">{escape(q(i))}</tspan>' for i in v)
        return "[" + inner + "]"
    return f'<tspan class="str">{escape(q(v))}</tspan>'


card = cfg["card"]
keys = list(card)
pad = max(len(k) for k in keys)
handle = cfg["handle"]

lines = []  # svg markup per line
lines.append(
    f'<tspan class="kw">resource</tspan> <tspan class="str">"engineer"</tspan> '
    f'<tspan class="str">{escape(q(handle))}</tspan> {{'
)
for k in keys:
    lines.append(f'  <tspan class="key">{k.ljust(pad)}</tspan> = {value_svg(card[k])}')
lines.append("}")

n = len(lines)

# ---------- svg -----------------------------------------------------------

W, HDR, ROW = 800, 48, 26
H = HDR + n * ROW + 44
LOOP = 18  # seconds
FIRST, STEP = 6, 3.5  # percent of the loop
PLAN_AT = FIRST + n * STEP + 1.5
FLIP_AT = PLAN_AT + 8


def keyframes(name, start):
    return (
        f"@keyframes {name}{{0%,{start}%{{opacity:0}}"
        f"{start + 1.5}%,95%{{opacity:1}}100%{{opacity:0}}}}"
    )


css = [
    "svg{--bg:#ffffff;--bdr:#d0d7de;--hdr:#f6f8fa;--add:#dafbe1;--gut:#aceebb;"
    "--txt:#1f2328;--mut:#59636e;--key:#0550ae;--str:#0a3069;--kw:#cf222e;"
    "--grn:#1a7f37;--red:#cf222e;--mrg:#8250df}",
    "@media (prefers-color-scheme:dark){svg{--bg:#0d1117;--bdr:#30363d;--hdr:#161b22;"
    "--add:#12261e;--gut:#1b4721;--txt:#e6edf3;--mut:#8b949e;--key:#79c0ff;"
    "--str:#a5d6ff;--kw:#ff7b72;--grn:#3fb950;--red:#f85149;--mrg:#a371f7}}",
    "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
    "'Liberation Mono',monospace;font-size:14px;white-space:pre;fill:var(--txt)}",
    ".card{fill:var(--bg);stroke:var(--bdr)}",
    ".hdr{fill:var(--hdr)}.rule{stroke:var(--bdr)}",
    ".add{fill:var(--add)}.gut{fill:var(--gut)}",
    ".mut{fill:var(--mut)}.grn{fill:var(--grn)}.red{fill:var(--red)}",
    ".key{fill:var(--key)}.str{fill:var(--str)}.kw{fill:var(--kw)}",
    ".pill-open{fill:var(--grn)}.pill-merged{fill:var(--mrg)}",
    ".pilltxt{fill:#ffffff;font-size:12px;font-weight:700}",
    ".fname{font-weight:600}",
    f".row,.plan,.open,.merged{{animation-duration:{LOOP}s;animation-iteration-count:infinite;"
    "animation-timing-function:linear}",
]
for i in range(n):
    start = round(FIRST + i * STEP, 2)
    css.append(keyframes(f"r{i}", start))
    css.append(f".r{i}{{animation-name:r{i}}}")
css.append(keyframes("plan", round(PLAN_AT - 1.5, 2)))
css.append(".plan{animation-name:plan}")
css.append(
    f"@keyframes open{{0%,{FLIP_AT - 1}%{{opacity:1}}{FLIP_AT}%,95%{{opacity:0}}100%{{opacity:1}}}}"
    ".open{animation-name:open}"
)
css.append(
    f"@keyframes merged{{0%,{FLIP_AT - 1}%{{opacity:0}}{FLIP_AT}%,95%{{opacity:1}}100%{{opacity:0}}}}"
    ".merged{animation-name:merged}"
)
css.append(
    "@media (prefers-reduced-motion:reduce){.row,.plan,.merged{animation:none!important;"
    "opacity:1!important}.open{animation:none!important;opacity:0!important}}"
)

parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
    f'role="img" aria-labelledby="t d">'
)
summary = (
    f'{card["name"]}, {card["role"]}. Certified: {", ".join(card["certified"]) if isinstance(card["certified"], list) else card["certified"]}.'
)
parts.append(f'<title id="t">profile.tf: a pull request adding {escape(card["name"])}</title>')
parts.append(f'<desc id="d">{escape(summary)} Shown as a merged diff of a Terraform file.</desc>')
parts.append("<style>" + "".join(css) + "</style>")
parts.append(f'<clipPath id="clip"><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8"/></clipPath>')
parts.append(f'<rect class="card" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8"/>')
parts.append('<g clip-path="url(#clip)">')
parts.append(f'<rect class="hdr" x="0" y="0" width="{W}" height="{HDR}"/>')
parts.append(f'<line class="rule" x1="0" y1="{HDR}" x2="{W}" y2="{HDR}"/>')

# status pill that flips from Open to Merged
parts.append('<g class="open"><rect class="pill-open" x="16" y="13" width="64" height="22" rx="11"/>'
             '<text class="pilltxt" x="48" y="28" text-anchor="middle">Open</text></g>')
parts.append('<g class="merged"><rect class="pill-merged" x="16" y="13" width="78" height="22" rx="11"/>'
             '<text class="pilltxt" x="55" y="28" text-anchor="middle">Merged</text></g>')
parts.append('<text class="fname" x="108" y="29">profile.tf</text>')

# diff stat: +n -0 and five squares
sq_x = W - 16 - 5 * 13
for j in range(5):
    parts.append(f'<rect class="pill-open" x="{sq_x + j * 13}" y="19" width="10" height="10" rx="2"/>')
parts.append(f'<text class="grn" x="{sq_x - 62}" y="29" font-weight="600">+{n}</text>')
parts.append(f'<text class="red" x="{sq_x - 28}" y="29" font-weight="600">−0</text>')

for i, markup in enumerate(lines):
    top = HDR + i * ROW
    parts.append(f'<g class="row r{i}">')
    parts.append(f'<rect class="add" x="0" y="{top}" width="{W}" height="{ROW}"/>')
    parts.append(f'<rect class="gut" x="0" y="{top}" width="76" height="{ROW}"/>')
    parts.append(f'<text class="mut" x="48" y="{top + 18}" text-anchor="end">{i + 1}</text>')
    parts.append(f'<text class="grn" x="62" y="{top + 18}" font-weight="700">+</text>')
    parts.append(f'<text x="92" y="{top + 18}" xml:space="preserve">{markup}</text>')
    parts.append("</g>")

plan_y = HDR + n * ROW + 28
parts.append(
    f'<text class="mut plan" x="92" y="{plan_y}">Plan: 1 to add, 0 to change, 0 to destroy.</text>'
)
parts.append("</g></svg>")

(ROOT / "assets").mkdir(exist_ok=True)
(ROOT / "assets" / "profile.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


# ---------- projects.svg: animated flows ----------------------------------

FW, ROWH, TOP = 800, 112, 16
flows = cfg["flows"]
FH = TOP + len(flows) * ROWH + 8
STEP_S, FLOOP = 0.8, 8
fc = [
    "svg{--bg:#ffffff;--bdr:#d0d7de;--node:#f6f8fa;--txt:#1f2328;--mut:#59636e;"
    "--grn:#1a7f37;--glow:#dafbe1;--key:#0550ae}",
    "@media (prefers-color-scheme:dark){svg{--bg:#0d1117;--bdr:#30363d;--node:#161b22;"
    "--txt:#e6edf3;--mut:#8b949e;--grn:#3fb950;--glow:#12261e;--key:#79c0ff}}",
    "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
    "'Liberation Mono',monospace;font-size:13px;fill:var(--txt)}",
    ".card{fill:var(--bg);stroke:var(--bdr)}.node{fill:var(--node);stroke:var(--bdr)}",
    ".edge{stroke:var(--bdr);stroke-width:2;fill:none}",
    ".lit-n{fill:var(--glow);stroke:var(--grn)}.lit-e{stroke:var(--grn);stroke-width:2;fill:none}",
    ".repo{fill:var(--key);font-weight:700}.note{fill:var(--mut);font-size:12px}",
    ".chk{fill:var(--grn);font-weight:700}",
    f".lit{{opacity:0;animation:lit {FLOOP}s linear infinite}}",
    "@keyframes lit{0%{opacity:0}4%,88%{opacity:1}96%,100%{opacity:0}}",
    "@media (prefers-reduced-motion:reduce){.lit{animation:none;opacity:1}}",
]
fp = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FW} {FH}" width="{FW}" height="{FH}" '
    'role="img" aria-labelledby="ft fd">',
    '<title id="ft">How each project works</title>',
    '<desc id="fd">' + escape(" ".join(
        f'{f["repo"]}: ' + " to ".join(f["stages"]) + "." for f in flows)) + "</desc>",
    "<style>" + "".join(fc) + "</style>",
    f'<rect class="card" x=".5" y=".5" width="{FW - 1}" height="{FH - 1}" rx="8"/>',
]
for r, f in enumerate(flows):
    y0 = TOP + r * ROWH
    st = f["stages"]
    fp.append(f'<text class="repo" x="24" y="{y0 + 18}">{escape(f["repo"])}</text>')
    widths = [len(s) * 7.9 + 22 for s in st]
    gap = (FW - 48 - sum(widths)) / (len(st) - 1)
    x = 24.0
    ny = y0 + 32
    nh = 32
    for i, (s, w) in enumerate(zip(st, widths)):
        d = round(i * STEP_S, 2)
        if i:
            ex1, ex2 = x - gap, x
            fp.append(f'<line class="edge" x1="{ex1:.1f}" y1="{ny + nh / 2}" x2="{ex2:.1f}" y2="{ny + nh / 2}"/>')
            fp.append(f'<line class="lit lit-e" style="animation-delay:{d - 0.4:.2f}s" x1="{ex1:.1f}" y1="{ny + nh / 2}" x2="{ex2:.1f}" y2="{ny + nh / 2}"/>')
        fp.append(f'<rect class="node" x="{x:.1f}" y="{ny}" width="{w:.1f}" height="{nh}" rx="6"/>')
        fp.append(f'<rect class="lit lit-n" style="animation-delay:{d:.2f}s" x="{x:.1f}" y="{ny}" width="{w:.1f}" height="{nh}" rx="6"/>')
        fp.append(f'<text x="{x + w / 2:.1f}" y="{ny + 21}" text-anchor="middle">{escape(s)}</text>')
        x += w + gap
    fp.append(f'<text class="note" x="24" y="{ny + nh + 24}">{escape(f["note"])}</text>')
fp.append("</svg>")
(ROOT / "assets" / "projects.svg").write_text("\n".join(fp) + "\n", encoding="utf-8")

# ---------- README --------------------------------------------------------

gh = cfg["github"]
links = cfg["links"]
out = []
out.append("<!-- Generated by scripts/build.py from profile.yml. Edit profile.yml, not this file. -->")
out.append(
    f'<img src="assets/profile.svg" width="100%" alt="profile.tf diff: {card["name"]}, {card["role"]}">'
)
out.append("")
out.append(" ".join(cfg["intro"].split()))
out.append("")
out.append("## What I've built")
out.append("")
out.append('<img src="assets/projects.svg" width="100%" alt="Architecture flows of the three projects below">')
out.append("")
for p in cfg["projects"]:
    out.append(f'- [{p["repo"]}](https://github.com/{gh}/{p["repo"]}): ' + " ".join(p["text"].split()))
out.append("")
out.append(" ".join(cfg["also"].split()))
out.append("")
out.append(
    f'Find me on [LinkedIn]({links["linkedin"]}), at [{links["portfolio"].split("//")[-1]}]({links["portfolio"]}), '
    f'or by [email](mailto:{links["email"]}).'
)
(ROOT / "README.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("built README.md, assets/profile.svg, assets/projects.svg")
