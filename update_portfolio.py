#!/usr/bin/env python3
"""
Portfolio Auto-Updater
Fetches latest GitHub repos and updates the projects section in index.html.
Run: python3 update_portfolio.py
"""

import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

GITHUB_USER = "maruftak"
HTML_FILE = "index.html"

# Projects to always keep (live sites, FYP — hardcoded with rich descriptions)
PINNED = {
    "HoneyPot-FYP": {
        "type": "security",
        "icon": "shield",
        "desc": "Advanced IoT camera honeypot with real-time attack dashboard and threat intelligence. Deploys decoy devices to attract, capture, and analyze live malicious traffic from global threat actors. Final year project.",
        "tags": ["Python", "IoT Security", "Threat Intel", "Real-time Dashboard"],
        "live": None,
    },
    "IoTLogAnalyzer": {
        "type": "security",
        "icon": "file",
        "desc": "Specialized platform to process and visualize IoT honeypot log files. Transforms raw packet captures into structured threat intelligence — classifies botnet families, maps CVE exploits, and generates automated geographic attacker reports.",
        "tags": ["Python", "Log Analysis", "CVE Mapping", "Botnet Classification"],
        "live": None,
    },
    "TurkStay": {
        "type": "web",
        "icon": "globe",
        "desc": "Licensed Turkish tour operator platform. Users build fully custom travel packages — selecting destinations, accommodation, tours, and experiences across Istanbul, Cappadocia, Pamukkale, and more. Stripe payments integrated.",
        "tags": ["Next.js", "React", "Tailwind CSS", "Stripe", "Vercel"],
        "live": "https://turk-stay.vercel.app/",
    },
    "MenuBangla": {
        "type": "web",
        "icon": "send",
        "desc": "Restaurant management and digital menu platform tailored for the Bangladeshi market. Enables restaurants to manage menus, showcase dishes, and reach customers online. Currently active and growing.",
        "tags": ["Full-Stack", "Web App", "Restaurant Tech"],
        "live": "https://www.menubangla.com",
    },
    "TerraformAWS": {
        "type": "cloud",
        "icon": "cloud",
        "desc": "Practical Terraform configurations for AWS infrastructure. Covers VPC, EC2, S3, IAM, and networking — with explanations and production-ready patterns for cloud resource provisioning using Infrastructure as Code.",
        "tags": ["Terraform", "AWS", "HCL", "IaC"],
        "live": None,
    },
}

ICONS = {
    "shield": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "file": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    "globe": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "send": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 11l19-9-9 19-2-8-8-2z"/></svg>',
    "cloud": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>',
    "code": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
}

GITHUB_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>'
EXTERNAL_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'


def fetch_repos():
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=50&sort=updated"
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-updater"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[warn] Could not fetch repos: {e}")
        return []


def guess_type(repo):
    name = repo.get("name", "").lower()
    desc = (repo.get("description") or "").lower()
    lang = (repo.get("language") or "").lower()
    combined = name + " " + desc

    if any(k in combined for k in ["honeypot", "iot", "security", "threat", "exploit", "cve", "botnet", "pentest", "hack", "ctf"]):
        return "security"
    if any(k in combined for k in ["terraform", "aws", "cloud", "infra", "k8s", "docker", "devops"]):
        return "cloud"
    return "web"


def guess_icon(repo_type):
    return {"security": "shield", "cloud": "cloud", "web": "code"}.get(repo_type, "code")


def build_card(name, data, github_url):
    ptype = data.get("type", "web")
    icon_key = data.get("icon", "code")
    desc = data.get("desc") or "No description provided."
    tags = data.get("tags", [])
    live = data.get("live")

    tag_html = "".join(f'<span class="project-tag">{t}</span>' for t in tags)

    live_badge = ""
    if live:
        live_badge = f'<span class="badge-live">LIVE</span>'

    live_link = ""
    if live:
        live_link = f'<a href="{live}" class="project-link" target="_blank" rel="noopener noreferrer" aria-label="Open {name} live site" onclick="event.stopPropagation()">{EXTERNAL_ICON}</a>'

    gh_link = f'<a href="{github_url}" class="project-link" target="_blank" rel="noopener noreferrer" aria-label="View {name} on GitHub" onclick="event.stopPropagation()">{GITHUB_ICON}</a>'

    onclick = f"window.open('{live or github_url}','_blank')"

    return f"""
        <div class="project-card {ptype} fade-in" onclick="{onclick}" role="article" tabindex="0" aria-label="{name} project">
          <div class="project-top">
            <div class="project-icon" aria-hidden="true">{ICONS.get(icon_key, ICONS['code'])}</div>
            <div class="project-links">{live_badge}{live_link}{gh_link}</div>
          </div>
          <div class="project-name">{name}</div>
          <p class="project-desc">{desc}</p>
          <div class="project-tags">{tag_html}</div>
        </div>"""


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching repos for @{GITHUB_USER}...")
    repos = fetch_repos()
    print(f"  Found {len(repos)} repos")

    # Build project map: pinned first, then new repos not in pinned
    project_cards = []

    # Add pinned projects in order
    for name, data in PINNED.items():
        gh_url = f"https://github.com/{GITHUB_USER}/{name}"
        project_cards.append(build_card(name, data, gh_url))

    # Add new repos not already pinned
    pinned_names_lower = {k.lower() for k in PINNED}
    for repo in repos:
        rname = repo.get("name", "")
        if rname.lower() in pinned_names_lower:
            continue
        if repo.get("fork"):
            continue
        desc = repo.get("description") or f"Repository: {rname}"
        lang = repo.get("language") or ""
        rtype = guess_type(repo)
        icon = guess_icon(rtype)
        homepage = repo.get("homepage") or ""
        tags = [lang] if lang else []
        data = {
            "type": rtype,
            "icon": icon,
            "desc": desc,
            "tags": tags,
            "live": homepage if homepage.startswith("http") else None,
        }
        project_cards.append(build_card(rname, data, repo["html_url"]))
        print(f"  + Added new repo: {rname}")

    # Read HTML
    try:
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print(f"[error] {HTML_FILE} not found. Run from portfolio directory.")
        sys.exit(1)

    # Replace projects grid content
    grid_content = "\n".join(project_cards) + "\n\n      "
    new_html = re.sub(
        r'(<div[^>]+id="projects-grid"[^>]*>)(.*?)(</div>\s*</div>\s*</section>)',
        lambda m: m.group(1) + grid_content + m.group(3),
        html,
        flags=re.DOTALL
    )

    if new_html == html:
        print("[warn] Pattern not matched — HTML structure may have changed. No update made.")
        sys.exit(1)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"[ok] {HTML_FILE} updated with {len(project_cards)} projects")
    print(f"[ok] Done at {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
