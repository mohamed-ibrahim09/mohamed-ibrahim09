#!/usr/bin/env python3
"""Draw assets/live.svg from real GitHub data (refreshed daily by the workflow).

Uses the GraphQL contribution calendar when a token allows it, and falls back
to public events over REST. Standard library only.
"""
import datetime as dt
import json
import os
import pathlib
import random
import sys
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
cfg = yaml.safe_load((ROOT / "profile.yml").read_text(encoding="utf-8"))
USER = cfg["github"]
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
WEEKS = 30
MODE = "placeholder" if "--placeholder" in sys.argv else "demo" if "--demo" in sys.argv else "live"


def call(url, body=None):
    if os.environ.get("USE_GH_CLI") and not body:  # local testing behind a proxy
        import subprocess
        return json.loads(subprocess.run(["gh", "api", url.replace("https://api.github.com/", "")],
                                         check=True, capture_output=True, text=True).stdout)
    req = urllib.request.Request(url, data=body, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-build"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    if body:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


today = dt.datetime.now(dt.timezone.utc).date()
start = today - dt.timedelta(days=WEEKS * 7 - 1 + (today.weekday() + 1) % 7)  # a Sunday
if MODE == "live":
    user = call(f"https://api.github.com/users/{USER}")
    repos = call(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
    counts, source = {}, "public activity"
else:
    user, repos, counts, source = {}, [], {}, "contributions"
    if MODE == "demo":  # synthetic data, only for previewing the layout
        rnd = random.Random(7)
        for i in range((today - start).days + 1):
            counts[str(start + dt.timedelta(days=i))] = rnd.choice([0, 0, 1, 2, 3, 5, 8])

if MODE == "live" and TOKEN:
    q = {"query": "query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){"
         "contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}",
         "variables": {"u": USER, "f": f"{start}T00:00:00Z", "t": f"{today}T23:59:59Z"}}
    try:
        res = call("https://api.github.com/graphql", json.dumps(q).encode())
        weeks = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for w in weeks:
            for d in w["contributionDays"]:
                counts[d["date"]] = d["contributionCount"]
        source = "contributions"
    except Exception as e:  # fall back to events
        print("graphql failed, using events:", e)
        counts = {}

if MODE == "live" and not counts:
    for page in (1, 2, 3):
        try:
            ev = call(f"https://api.github.com/users/{USER}/events/public?per_page=100&page={page}")
        except Exception:
            break
        for e in ev:
            day = e["created_at"][:10]
            n = e["payload"].get("size", 1) if e["type"] == "PushEvent" else 1
            counts[day] = counts.get(day, 0) + n

total = sum(v for k, v in counts.items() if k >= str(start))
streak, d = 0, today
if counts.get(str(d), 0) == 0:
    d -= dt.timedelta(days=1)
while counts.get(str(d), 0) > 0:
    streak += 1
    d -= dt.timedelta(days=1)
pushed = max((r["pushed_at"] for r in repos if not r["fork"]), default=None)
ago = ""
if pushed:
    days = (today - dt.date.fromisoformat(pushed[:10])).days
    ago = "today" if days == 0 else f"{days}d ago"
stars = sum(r["stargazers_count"] for r in repos if not r["fork"])
n_repos = sum(1 for r in repos if not r["fork"])
mx = max(counts.values(), default=0) or 1


def level(n):
    if n <= 0:
        return 0
    r = n / mx
    return 1 if r <= .25 else 2 if r <= .5 else 3 if r <= .75 else 4


W, H, C, G = 800, 178, 11, 3
css = [
    "svg{--bg:#ffffff;--bdr:#d0d7de;--txt:#1f2328;--mut:#59636e;--key:#0550ae;"
    "--l0:#ebedf0;--l1:#aceebb;--l2:#4ac26b;--l3:#2da44e;--l4:#116329}",
    "@media (prefers-color-scheme:dark){svg{--bg:#0d1117;--bdr:#30363d;--txt:#e6edf3;--mut:#8b949e;--key:#79c0ff;"
    "--l0:#161b22;--l1:#0e4429;--l2:#006d32;--l3:#26a641;--l4:#39d353}}",
    "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace;font-size:12px;fill:var(--txt)}",
    ".card{fill:var(--bg);stroke:var(--bdr)}.mut{fill:var(--mut)}.big{font-size:26px;font-weight:700}",
    ".l0{fill:var(--l0)}.l1{fill:var(--l1)}.l2{fill:var(--l2)}.l3{fill:var(--l3)}.l4{fill:var(--l4)}",
    ".c{opacity:0;animation:pop .5s ease-out forwards}@keyframes pop{from{opacity:0}to{opacity:1}}",
    ".now{animation:pulse 2s ease-in-out infinite}@keyframes pulse{50%{opacity:.45}}",
    "@media (prefers-reduced-motion:reduce){.c{animation:none;opacity:1}.now{animation:none}}",
]
p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">',
     f'<title id="t">GitHub activity for {USER}: {total} {source} in {WEEKS} weeks, {streak} day streak, last push {ago}</title>',
     "<style>" + "".join(css) + "</style>",
     f'<rect class="card" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10"/>',
     f'<text class="mut" x="24" y="30">last {WEEKS} weeks</text>']
for w in range(WEEKS):
    for dow in range(7):
        day = start + dt.timedelta(days=w * 7 + dow)
        if day > today:
            continue
        n = counts.get(str(day), 0)
        cls = f"c l{level(n)}" + (" now" if day == today else "")
        p.append(f'<rect class="{cls}" style="animation-delay:{w * 0.04:.2f}s" x="{24 + w * (C + G)}" y="{44 + dow * (C + G)}" '
                 f'width="{C}" height="{C}" rx="2"><title>{day}: {n}</title></rect>')
x0 = 520
stats = [(str(total), source), (f"{streak}d", "current streak"), (ago or "-", "last push"), (str(n_repos), "public repos")]
if MODE == "placeholder":
    stats = [("-", source), ("-", "current streak"), ("-", "last push"), ("-", "public repos")]
for i, (num, label) in enumerate(stats):
    cx, cy = x0 + (i % 2) * 140, 62 + (i // 2) * 62
    p.append(f'<text class="big" x="{cx}" y="{cy}">{num}</text><text class="mut" x="{cx}" y="{cy + 18}">{label}</text>')
p.append(f'<text class="mut" x="{W - 24}" y="{H - 14}" text-anchor="end" font-size="11">{"waiting for the first scheduled update" if MODE == "placeholder" else f"updated {today} by GitHub Actions"}</text>')
p.append("</svg>")
(ROOT / "assets").mkdir(exist_ok=True)
(ROOT / "assets" / os.environ.get("OUT", "live.svg")).write_text("\n".join(p) + "\n", encoding="utf-8")
print(f"built assets/live.svg ({source}, total={total}, streak={streak}, last push {ago}, repos={n_repos})")
