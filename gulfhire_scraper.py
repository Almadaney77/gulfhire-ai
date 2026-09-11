#!/usr/bin/env python3
"""
GulfHire AI — Live Job Scraper
================================
Fetches hospitality listings from official portals and boards, dedupes them,
and writes jobs.js (consumed by gulfhire-ai-live.html).

SETUP (run once):
    pip install requests beautifulsoup4

RUN:
    python gulfhire_scraper.py

SCHEDULE (Linux cron — daily at 7am):
    0 7 * * * /usr/bin/python3 /path/to/gulfhire_scraper.py

Deploy free on: Render.com cron jobs, PythonAnywhere, or a $5 VPS.
NOTE: Respect each site's robots.txt & terms. Official careers portals
(IHG, Accor, Marriott) are JS-heavy — for those we deep-link the search
pages rather than scraping, which keeps you safe and the links evergreen.
"""
import json, re, datetime, html as htmllib
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "GulfHireBot/1.0 (+contact: biopedia001@gmail.com)"}

# ---------------------------------------------------------------------------
# 1. SOURCES WE PARSE DIRECTLY (server-rendered listing pages)
# ---------------------------------------------------------------------------
PARSE_SOURCES = [
    {"name": "Naukrigulf — Madinah hotels",
     "url": "https://www.naukrigulf.com/hotel-jobs-in-al-madina-al-munawarah",
     "city": "madinah", "role": "any",
     "item_sel": "div.job-box, .jobTuple, article",          # adjust after inspecting page
     "title_sel": ".job-title, a.title, h2, h3",
     "co_sel": ".company-name, .comp-name"},
    {"name": "GulfTalent — Saudi housekeepers",
     "url": "https://www.gulftalent.com/saudi-arabia/jobs/title/housekeeper",
     "city": "any", "role": "housekeeping",
     "item_sel": ".job-row, .job-card, li.job",
     "title_sel": ".job-title, h2, h3 a",
     "co_sel": ".employer, .company"},
]

# ---------------------------------------------------------------------------
# 2. EVERGREEN DEEP-LINKS (JS-heavy official portals — we link, not scrape)
# ---------------------------------------------------------------------------
PORTAL_LINKS = [
    {"title": "Receptionist (Chinese Speaker) — Crowne Plaza Madinah", "hotel": "IHG / Crowne Plaza",
     "city": "madinah", "role": "frontdesk", "source": "IHG Careers",
     "url": "https://careers.ihg.com/en/search-and-apply/?q=madinah"},
    {"title": "Sofitel Shahd Al Madinah — multiple roles", "hotel": "Accor / Sofitel",
     "city": "madinah", "role": "any", "source": "Accor Careers",
     "url": "https://careers.accor.com/global/en/jobs?ln=Madinah"},
    {"title": "Team opportunities — Elaf Taiba Hotel, Madinah", "hotel": "Elaf Group",
     "city": "madinah", "role": "any", "source": "Elaf Taiba careers page",
     "url": "https://www.elafhotels.com/elaf-taiba/careers"},
    {"title": "Turndown Attendant — Four Seasons Resort, The Red Sea", "hotel": "Four Seasons",
     "city": "any", "role": "housekeeping", "source": "Four Seasons Careers",
     "url": "https://careers.fourseasons.com/us/en/search-results?keywords=saudi%20arabia"},
    {"title": "Room Attendant / Receptionist — InterContinental Riyadh", "hotel": "IHG / InterContinental",
     "city": "riyadh", "role": "housekeeping", "source": "IHG Careers",
     "url": "https://careers.ihg.com/en/search-and-apply/?q=riyadh"},
]

def classify_role(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ("housekeep", "room attendant", "cleaner", "laundry", "houseman")): return "housekeeping"
    if any(w in t for w in ("waiter", "waitress", "server", "restaurant", "f&b", "barista")): return "waiter"
    if any(w in t for w in ("reception", "front desk", "front office", "concierge", "guest relation")): return "frontdesk"
    if any(w in t for w in ("chef", "cook", "kitchen", "commis", "steward")): return "chef"
    if any(w in t for w in ("security", "guard", "lifeguard", "safety")): return "security"
    return "any"

def parse_source(src):
    jobs = []
    try:
        r = requests.get(src["url"], headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select(src["item_sel"]):
            t = item.select_one(src["title_sel"])
            if not t: continue
            title = re.sub(r"\s+", " ", t.get_text(" ", strip=True))[:120]
            if len(title) < 6: continue
            c = item.select_one(src["co_sel"])
            company = re.sub(r"\s+", " ", c.get_text(strip=True))[:60] if c else "See listing"
            a = t.find("a") or item.find("a", href=True)
            link = a["href"] if a and a["href"].startswith("http") else src["url"]
            jobs.append({"title": title, "hotel": company, "city": src["city"],
                         "role": classify_role(title), "pay": "See listing",
                         "visa": "Verify employer on Qiwa.sa before applying",
                         "source": src["name"], "url": link})
    except Exception as e:
        print(f"  ! {src['name']}: {e}")
    return jobs

def main():
    today = datetime.date.today().strftime("%Y-%m")
    jobs = []
    for src in PARSE_SOURCES:
        print(f"Parsing {src['name']} ...")
        jobs += parse_source(src)

    seen, uniq = set(), []
    for j in jobs:
        key = re.sub(r"\W+", "", j["title"].lower())[:40]
        if key in seen: continue
        seen.add(key); uniq.append(j)

    for j in PORTAL_LINKS:
        j = dict(j); j["pay"] = "See listing"
        j["visa"] = "Official portal only — never apply via WhatsApp agents"
        j["date"] = today; uniq.append(j)
    for j in uniq: j.setdefault("date", today)

    uniq.sort(key=lambda x: (x["city"] != "madinah", x["role"]))
    payload = json.dumps(uniq, ensure_ascii=False, indent=2)
    with open("jobs.js", "w", encoding="utf-8") as f:
        f.write("// Auto-generated by gulfhire_scraper.py — do not hand-edit.\n"
                f"// Updated: {today}\nwindow.GULFHIRE_JOBS = {payload};\n")
    print(f"OK — {len(uniq)} listings written to jobs.js")

if __name__ == "__main__":
    main()
