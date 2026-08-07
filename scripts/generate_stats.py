#!/usr/bin/env python3
"""Build assets/github-stats.svg — a self-generated GitHub stats card.

Everything is pulled straight from the GitHub API and rendered here, so the
card depends on no third-party image service that can rate-limit, break or
shut down. A daily GitHub Action regenerates and commits it.

  python3 scripts/generate_stats.py --user Adyansh04            # live
  python3 scripts/generate_stats.py --user X --contrib c.json   # offline test

Auth: set GITHUB_TOKEN for the contribution calendar (GraphQL) and higher
REST limits. Without a token it falls back to a public contributions endpoint.
"""
import argparse
import datetime as dt
import json
import os
import urllib.error
import urllib.request

W, H = 900, 300
G, B, P_, A = "#3FB950", "#58A6FF", "#A371F7", "#D29922"
TEXT, MUTED, LINE, PANEL, BG = "#E6EDF3", "#8B949E", "#30363D", "#111823", "#0d1117"

# Byte counts for these wildly overstate reality (notebooks embed image data,
# HTML is usually generated docs), so they are excluded from the language mix.
IGNORE = {"jupyter notebook", "html", "css", "mdx", "tex", "scss", "makefile"}

# Repos excluded from the LANGUAGE MIX only — this profile repo and the
# portfolio site are web projects that would drown out the robotics work.
# Their commits, stars and every other statistic still count normally.
LANG_EXCLUDE = {"adyansh04", "my-portfolio", "my-portfolio-v2"}

LANG_COLOR = {
    "Python": "#3572A5", "C++": "#f34b7d", "C": "#555555", "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a", "CMake": "#DA3434", "Shell": "#89e051", "Dockerfile": "#384d54",
    "Cuda": "#3A4E3A", "Java": "#b07219", "Go": "#00ADD8", "Rust": "#dea584",
}


def api(url, token=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": "adyansh-stats", "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def graphql(query, variables, token):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "User-Agent": "adyansh-stats", "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


CAL_Q = """
query($login:String!){ user(login:$login){
  contributionsCollection{
    totalCommitContributions totalPullRequestContributions
    totalIssueContributions totalPullRequestReviewContributions
    contributionCalendar{ totalContributions
      weeks{ contributionDays{ date contributionCount weekday } } } } } }
"""


def fetch(user, token, contrib_file, cache=None):
    if cache:                                   # offline rendering check
        c = json.load(open(cache))
        days = [{"date": x["date"], "count": x["count"]}
                for x in json.load(open(contrib_file))["contributions"]]
        own = [r for r in c["repos"] if not r["fork"]]
        return dict(profile=c["user"], own=own, langs=c.get("langs_filtered", c["langs"]),
                    days=days, extra={}, skipped=c.get("skipped", []),
                    stars=sum(r["stargazers_count"] for r in own),
                    forks=sum(r["forks_count"] for r in own))
    prof = api(f"https://api.github.com/users/{user}", token)
    repos, page = [], 1
    while True:
        chunk = api(f"https://api.github.com/users/{user}/repos"
                    f"?per_page=100&type=owner&page={page}", token)
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]

    langs, skipped = {}, []
    for r in own:
        if r["name"].lower() in LANG_EXCLUDE:
            skipped.append(r["name"])
            continue
        try:
            for k, v in api(r["languages_url"], token).items():
                langs[k] = langs.get(k, 0) + v
        except urllib.error.HTTPError:
            break

    extra = {}
    days = None
    if token:
        try:
            d = graphql(CAL_Q, {"login": user}, token)["data"]["user"]["contributionsCollection"]
            extra = {"commits": d["totalCommitContributions"], "prs": d["totalPullRequestContributions"],
                     "issues": d["totalIssueContributions"], "reviews": d["totalPullRequestReviewContributions"]}
            days = [{"date": x["date"], "count": x["contributionCount"]}
                    for wk in d["contributionCalendar"]["weeks"] for x in wk["contributionDays"]]
        except Exception:
            days = None
    if days is None:
        if contrib_file:
            days = json.load(open(contrib_file))["contributions"]
        else:
            days = api(f"https://github-contributions-api.jogruber.de/v4/{user}?y=last")["contributions"]
        days = [{"date": x["date"], "count": x["count"]} for x in days]

    return dict(profile=prof, own=own, langs=langs, days=days, extra=extra,
                skipped=skipped,
                stars=sum(r["stargazers_count"] for r in own),
                forks=sum(r["forks_count"] for r in own))


def streaks(days):
    """(current, longest) run of consecutive days with at least one contribution."""
    today = dt.date.today()
    best = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        best = max(best, run)
    cur = 0
    for d in reversed(days):
        date = dt.date.fromisoformat(d["date"])
        if date > today:
            continue
        if d["count"] > 0:
            cur += 1
        elif date != today:      # today not yet logged shouldn't break the streak
            break
    return cur, best


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;")


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 10000 else f"{n:,}"


def render(d):
    prof, days = d["profile"], d["days"]
    total = sum(x["count"] for x in days)
    active = sum(1 for x in days if x["count"] > 0)
    cur, best = streaks(days)
    langs = {k: v for k, v in d["langs"].items() if k.lower() not in IGNORE}
    ltot = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda t: -t[1])[:6]
    stamp = dt.date.today().isoformat()

    # extra angles worth showing
    weeks = [sum(x["count"] for x in days[i:i + 7]) for i in range(0, len(days) - 6, 7)]
    peak_week = max(weeks) if weeks else 0
    per_day = total / active if active else 0
    wd = [0] * 7
    for x in days:
        wd[(dt.date.fromisoformat(x["date"]).weekday() + 1) % 7] += x["count"]
    busiest = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][wd.index(max(wd))]
    since = dt.date.fromisoformat(prof["created_at"][:10]) if prof.get("created_at") else None
    years = f"{(dt.date.today() - since).days / 365.25:.1f}" if since else "—"
    star_repo = max(d["own"], key=lambda r: r["stargazers_count"], default=None)

    H_ = 320
    s = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H_}" width="100%" height="100%">
<defs>
  <linearGradient id="sbg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#080C14"/><stop offset="50%" stop-color="#0F172A"/><stop offset="100%" stop-color="#05080F"/>
  </linearGradient>
  <linearGradient id="sbrd" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="{G}" stop-opacity="0.9"/><stop offset="50%" stop-color="{B}" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="{P_}" stop-opacity="0.9"/>
  </linearGradient>
  <pattern id="sgrid" width="30" height="30" patternUnits="userSpaceOnUse">
    <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#1E293B" stroke-width="0.8" opacity="0.45"/>
  </pattern>
  <style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}}
  .h{{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}}</style>
</defs>
<rect x="5" y="5" width="{W - 10}" height="{H_ - 10}" rx="16" fill="url(#sbg)" stroke="url(#sbrd)" stroke-width="1.5"/>
<rect x="6" y="6" width="{W - 12}" height="{H_ - 12}" rx="15" fill="url(#sgrid)"/>
<text x="24" y="30" class="h" font-size="13" font-weight="800" fill="{TEXT}" letter-spacing="1.4">GITHUB STATS</text>
<circle cx="{W - 218}" cy="25" r="3" fill="{G}"><animate attributeName="opacity" values="1;0.25;1" dur="2s" repeatCount="indefinite"/></circle>
<text x="{W - 24}" y="29" font-size="8.5" fill="{MUTED}" text-anchor="end">self-generated · updated {stamp}</text>
<line x1="24" y1="40" x2="{W - 24}" y2="40" stroke="{LINE}" stroke-width="1" opacity="0.7"/>''']

    # ── hero figures ──────────────────────────────────────────────────────
    e = d["extra"]
    hero = [(fmt(total), "CONTRIBUTIONS · 12 MONTHS", G),
            (str(len(d["own"])), "PUBLIC REPOSITORIES", B),
            (fmt(e["commits"]) if e else str(best), "COMMITS · 12 MONTHS" if e else "LONGEST STREAK · DAYS", A)]
    for i, (val, lab, c) in enumerate(hero):
        x = 152 + i * 300
        s.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" begin="{0.1 * i:.2f}s" fill="freeze"/>'
                 f'<text x="{x}" y="112" font-size="50" font-weight="800" fill="{c}" text-anchor="middle">{val}</text>'
                 f'<text x="{x}" y="130" font-size="8" fill="{MUTED}" text-anchor="middle" letter-spacing="1.2">{lab}</text></g>')
        if i < 2:
            s.append(f'<line x1="{x + 150}" y1="62" x2="{x + 150}" y2="136" stroke="{LINE}" opacity="0.6"/>')

    # ── supporting pills, two rows of four ────────────────────────────────
    pills = [("ACTIVE DAYS", f"{active}/{len(days)}"), ("CURRENT STREAK", f"{cur}d"),
             ("PEAK WEEK", str(peak_week)), ("PER ACTIVE DAY", f"{per_day:.1f}"),
             ("BUSIEST DAY", busiest), ("STARS · FORKS", f"{d['stars']} · {d['forks']}"),
             ("ON GITHUB", f"{years} yrs"),
             # the third hero already shows commits when a token is available;
             # otherwise it shows the longest streak, so swap in a different pill
             ("LONGEST STREAK", f"{best}d") if e else ("LANGUAGES", str(len(langs)))]
    for i, (lab, val) in enumerate(pills):
        x = 30 + (i % 4) * 212
        y = 152 + (i // 4) * 34
        s.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.35s" begin="{0.3 + 0.04 * i:.2f}s" fill="freeze"/>'
                 f'<rect x="{x}" y="{y}" width="202" height="26" rx="13" fill="{PANEL}" stroke="{LINE}"/>'
                 f'<text x="{x + 14}" y="{y + 17}" font-size="7" fill="{MUTED}" letter-spacing="0.7">{lab}</text>'
                 f'<text x="{x + 188}" y="{y + 17}" font-size="10.5" font-weight="700" fill="{TEXT}" text-anchor="end">{val}</text></g>')

    # ── language mix ──────────────────────────────────────────────────────
    ly = 246
    s.append(f'<text x="30" y="{ly - 6}" font-size="8" fill="{MUTED}" letter-spacing="1.2">LANGUAGES · BY CODE VOLUME</text>')
    if d.get("skipped"):
        s.append(f'<text x="{W - 30}" y="{ly - 6}" font-size="7.5" fill="{MUTED}" text-anchor="end">'
                 f'excludes {", ".join(esc(x) for x in d["skipped"])}</text>')
    off = 0.0
    for i, (name, size) in enumerate(top):
        seg = (W - 60) * size / ltot
        c = LANG_COLOR.get(name, [G, B, P_, A][i % 4])
        r = 'rx="6"' if i in (0, len(top) - 1) else ''
        s.append(f'<rect x="{30 + off:.1f}" y="{ly}" width="0" height="15" {r} fill="{c}">'
                 f'<animate attributeName="width" values="0;{seg:.1f}" dur="0.7s" begin="{0.55 + 0.07 * i:.2f}s" fill="freeze"/></rect>')
        off += seg
    s.append(f'<rect x="30" y="{ly}" width="{W - 60}" height="15" rx="6" fill="none" stroke="{LINE}" stroke-width="0.8"/>')
    for i, (name, size) in enumerate(top):
        x = 30 + i * 142
        c = LANG_COLOR.get(name, [G, B, P_, A][i % 4])
        s.append(f'<circle cx="{x + 4}" cy="{ly + 33}" r="3.8" fill="{c}"/>'
                 f'<text x="{x + 14}" y="{ly + 36}" font-size="8.5" fill="{TEXT}">{esc(name)} '
                 f'<tspan fill="{MUTED}">{size / ltot * 100:.1f}%</tspan></text>')

    tail = f' · top repo {esc(star_repo["name"])} ★{star_repo["stargazers_count"]}' if star_repo and star_repo["stargazers_count"] else ""
    foot = (f'{e["prs"]} PRs · {e["issues"]} issues · {e["reviews"]} reviews · 12 mo{tail}'
            if e else f'{ltot / 1e6:.1f} MB of tracked robotics code{tail}')
    s.append(f'<text x="24" y="{H_ - 14}" font-size="8" fill="{MUTED}">{foot}</text>')
    s.append(f'<text x="{W - 24}" y="{H_ - 14}" font-size="8" fill="{MUTED}" text-anchor="end">'
             f'built from the GitHub API · no third-party services</text>')
    s.append('</svg>')
    return "\n".join(s)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user", required=True)
    p.add_argument("--out", default="assets/github-stats.svg")
    p.add_argument("--contrib", help="local contributions JSON (offline testing)")
    p.add_argument("--cache", help="local {user,repos,langs} JSON (offline testing)")
    args = p.parse_args()
    data = fetch(args.user, os.environ.get("GITHUB_TOKEN"), args.contrib, args.cache)
    svg = render(data)
    with open(args.out, "w") as f:
        f.write(svg)
    print(f"wrote {args.out} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
