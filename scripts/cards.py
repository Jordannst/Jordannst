"""Generate the README images in assets/readme, light and dark.

Run daily by .github/workflows/cards.yml. Locally:
    GH_TOKEN=$(gh auth token) python scripts/cards.py
"""
import base64
import json
import os
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "Jordannst")
OUT = Path(__file__).resolve().parent.parent / "assets" / "readme"

# Portfolio palette (jordannst.dev); "name" matches GitHub's heading color.
THEMES = {
    "light": dict(fg="#0a0a0a", muted="#737373", grid="#969696", surface="#fafafa", border="#e5e5e5", name="#1f2328"),
    "dark": dict(fg="#fafafa", muted="#a1a1a1", grid="#ffffff80", surface="#141414", border="#ffffff1a", name="#f0f6fc"),
}
BLUE, GREEN = "#8da7ff", "#a6c9a9"
SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif'
FOLD_TOP = "M39.4 4 19.6 15.5Q16.4 17.3 16.4 20.2V33L39.4 19.9Z"
FOLD_BOTTOM = "m28.9 28.3 17.3 7.6q1.4.6 1.4 1.6v10.4q0 2.6-2.4 4.2L32.3 60V43.3L16.5 35.7Z"

QUERY = """{
  user(login: "%s") {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
  }
}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY % USER}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}"},
    )
    with urllib.request.urlopen(req) as res:
        body = json.load(res)
    if "errors" in body:
        raise SystemExit(body["errors"])  # keep the previous images instead of drawing made-up numbers
    return body["data"]["user"]


def b64(name):
    return base64.b64encode((OUT / name).read_bytes()).decode()


def dots(t, y, x2):
    return f'<line x1="0" y1="{y}" x2="{x2}" y2="{y}" stroke="{t["grid"]}" stroke-width="2" stroke-dasharray="2 5"/>'


def header(t):
    # No viewBox: the rail spans any width while its dots stay 2px.
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="48" role="img" aria-label="Jordan Sutarto">
<svg x="0" y="6" width="24" height="24" viewBox="0 0 64 64"><path fill="{t["fg"]}" d="{FOLD_TOP}"/><path fill="{BLUE}" d="{FOLD_BOTTOM}"/></svg>
<text x="32" y="27" fill="{t["name"]}" style='font: 600 24px {SANS}'>Jordan Sutarto</text>
{dots(t, 44, "100%")}
</svg>
"""


def footer(t, pogo):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="72" role="img" aria-label="Pogo">
{dots(t, 64, "100%")}
<svg x="100%" overflow="visible"><image x="-104" y="0" width="80" height="64" style="image-rendering: pixelated" href="data:image/png;base64,{pogo}"/></svg>
</svg>
"""


def card(t, serif, label, title, body, note=""):
    joints = "".join(f'<circle cx="{x}" cy="54" r="2" fill="{t["muted"]}" opacity=".5"/>' for x in (1, 389))
    note = f'<text x="370" y="37" text-anchor="end">{note}</text>' if note else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="390" height="228" viewBox="0 0 390 228" role="img" aria-label="{escape(label)}">
<style>
@font-face {{ font-family: "Instrument Serif"; src: url(data:font/woff2;base64,{serif}) format("woff2"); }}
text {{ font: 13px {SANS}; fill: {t["muted"]}; }}
.serif {{ font-family: "Instrument Serif", Georgia, serif; fill: {t["fg"]}; }}
.title {{ font-size: 22px; }}
.num {{ font-size: 30px; letter-spacing: -.5px; }}
.fg {{ fill: {t["fg"]}; }}
</style>
<rect x=".5" y=".5" width="389" height="219" rx="7" fill="{t["surface"]}" stroke="{t["border"]}"/>
<text x="20" y="38" class="serif title">{title}</text>{note}
{dots(t, 54, 390)}{joints}
{body}
</svg>
"""


def activity(t, serif, s):
    def stat(x, y, value, caption, gap=18):
        return (f'<text x="{x}" y="{y}" class="serif num">{value}</text>'
                f'<text x="{x}" y="{y + gap}">{caption}</text>')

    top, base = 178, 200
    pitch = 350 / len(s["weeks"])
    peak = max(s["weeks"]) or 1
    bars = ""
    for i, n in enumerate(s["weeks"]):
        h = max(1, round(n / peak * (base - top), 1))
        bars += f'<rect x="{20 + i * pitch + 1:.1f}" y="{base - h}" width="{pitch - 2:.2f}" height="{h}" rx="1" fill="{BLUE if n else t["grid"]}"/>'
    total = f'{s["contributions"]:,}'
    underline = 13.5 * len(total)  # ponytail: digit-width estimate for the serif; measure glyphs if it drifts
    body = (stat(20, 90, total, "contributions", gap=26)  # extra room for the underline
            + f'<svg x="17" y="94" width="{underline:.0f}" height="7" viewBox="0 0 200 14" preserveAspectRatio="none">'
              f'<path d="M3 9C42 8 65 4 100 5S159 7 197 3" fill="none" stroke="{GREEN}" stroke-width="2.6" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>'
            + stat(205, 90, f'{s["commits"]:,}', "commits", gap=26)
            + stat(20, 148, f'{s["prs"]:,}', "pull requests")
            + stat(205, 148, f'{s["streak"]} days', "longest streak")
            + bars)
    label = (f'Last 12 months: {total} contributions, {s["commits"]:,} commits, '
             f'{s["prs"]:,} pull requests, {s["streak"]}-day longest streak')
    return card(t, serif, label, "Last 12 months", body)


def languages(t, serif, s):
    segs = s["langs"] + [("Other", s["other"], t["grid"])]
    avail = 350 - 2 * (len(segs) - 1)
    x, bar = 20, ""
    for _, pct, color in segs:
        w = avail * pct / 100
        bar += f'<rect x="{x:.1f}" y="72" width="{w:.1f}" height="8" rx="2" fill="{color}"/>'
        x += w + 2
    legend = ""
    for i, (name, pct, color) in enumerate(s["langs"]):
        bx, y = 20 + (i % 2) * 185, 114 + (i // 2) * 26
        legend += (f'<circle cx="{bx + 4}" cy="{y - 4}" r="4" fill="{color}"/>'
                   f'<text x="{bx + 16}" y="{y}" class="fg">{escape(name)}</text>'
                   f'<text x="{bx + 165}" y="{y}" text-anchor="end">{pct:.1f}%</text>')
    label = "Languages by code size: " + ", ".join(f"{n} {p:.1f}%" for n, p, _ in s["langs"])
    return card(t, serif, label, "Languages", bar + legend, "by code size")


def stats(u):
    c = u["contributionsCollection"]
    weeks = c["contributionCalendar"]["weeks"]
    streak = run = 0
    for w in weeks:
        for d in w["contributionDays"]:
            run = run + 1 if d["contributionCount"] else 0
            streak = max(streak, run)
    sizes, colors = Counter(), {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            sizes[e["node"]["name"]] += e["size"]
            colors[e["node"]["name"]] = e["node"]["color"] or "#8b949e"
    total = sum(sizes.values()) or 1
    langs = [(n, size * 100 / total, colors[n]) for n, size in sizes.most_common(8)]
    return dict(
        contributions=c["contributionCalendar"]["totalContributions"],
        commits=c["totalCommitContributions"],
        prs=c["totalPullRequestContributions"],
        streak=streak,
        weeks=[sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks],
        langs=langs,
        other=max(0, 100 - sum(p for _, p, _ in langs)),
    )


def main():
    s = stats(fetch())
    serif, pogo = b64("instrument-serif.woff2"), b64("pogo.png")
    for name, t in THEMES.items():
        (OUT / f"header-{name}.svg").write_text(header(t), encoding="utf-8")
        (OUT / f"footer-{name}.svg").write_text(footer(t, pogo), encoding="utf-8")
        (OUT / f"activity-{name}.svg").write_text(activity(t, serif, s), encoding="utf-8")
        (OUT / f"languages-{name}.svg").write_text(languages(t, serif, s), encoding="utf-8")
    print(f'{s["contributions"]} contributions, {s["commits"]} commits, {s["prs"]} PRs, '
          f'{s["streak"]}-day streak, {len(s["langs"])} languages')


if __name__ == "__main__":
    main()
