# SOURCING101 — PROJECT CONTEXT

# Load this file at the start of every session and every subagent spawn.

## OWNER & PURPOSE
- Owner: Bivek Adhikari, VC analyst
- Goal: Identify pre-seed/stealth/seed/Series A startups in supply chain, manufacturing, and AgTech BEFORE they appear in standard VC databases
- Runtime: Python 3.10+, macOS Apple Silicon (local) + Ubuntu 22.04 (CI)
- Repo: https://github.com/NUbivek/sourcing101.git

---

## INVESTMENT THESIS (drives all scraping decisions)
Track startups in these verticals, in priority order:
1. Supply Chain Intelligence — TMS, WMS, 3PL, demand/supply planning, SCI
2. Manufacturing Tech — factory software, robotics, cobots, digital twin
3. AgTech — precision agriculture, farm management, food supply chain
4. Industrial AI / IoT — Industry 4.0, IIoT, predictive maintenance
5. Procurement & Sourcing — agentic procurement, RFP management
6. Supply Chain Finance — payments, deduction management, working capital
7. Warehousing & Intralogistics — warehouse robotics, WMS, fulfillment
8. Supply Chain Risk — compliance, traceability, ESG reporting

Stage targets: pre-seed · stealth · seed · series-a · series-b · series-c
Geographic scope: US · Canada · EU (15 countries) · Israel · Australia · NZ

---

## REPO STRUCTURE
```text
sourcing101/
├── startup_watch/
│   ├── startup_watch.py
│   ├── config.yaml
│   ├── config.github.yaml
│   └── adapters/
├── scm_pitchbook/
├── tests/
├── requirements.txt
├── pyproject.toml
└── .github/workflows/startup_watch.yml
```

---

## CORE DATA MODEL
- Normalized startup signal output including:
  - company name
  - website
  - description
  - stage
  - categories
  - source name/url
  - scrape timestamp
  - optional enrichment fields (funding, investors, location, headcount)

CSV output convention: lists are pipe-separated.

---

## SOURCE ARCHITECTURE (7 tiers, 200+ adapters target)
1) University incubators
2) Private accelerators
3) VC portfolios
4) News/RSS
5) Public startup databases
6) Specialized industry sources
7) Social signals

---

## SCRAPING TECHNOLOGY RULES
- Static HTML: requests + BeautifulSoup
- JS-rendered pages: Playwright
- RSS/Atom: feedparser
- JSON endpoints: requests
- LinkedIn: local-only auth session (never CI)

---

## CODING STANDARDS
- Python 3.10+, type hints, PEP8
- Config-driven behavior
- Retry + exponential backoff for flaky network calls
- 2–5s randomized delay for scraping requests
- No secrets or user-specific paths in committed code

---

## CI RULES
- `config.github.yaml`: auth-required sources disabled
- LinkedIn disabled in CI
- New non-auth adapters enabled in CI config
- New auth adapters disabled in CI config

---

## STAGE INFERENCE RULES
Canonical values only:
- pre-seed
- stealth
- seed
- series-a
- series-b
- series-c

Amount heuristic (guideline):
- < $1M: pre-seed
- $1M–$5M: seed
- $5M–$20M: series-a
- $20M–$75M: series-b
- > $75M: series-c

---

## TASK SIZE CONSTRAINTS
- 2–3 tasks per phase
- One adapter OR one module per task
- End each task with tests/lint + atomic commit

---

## VERIFICATION CHECKLIST
```bash
python -m pytest tests/ -x -q
python -m flake8 startup_watch/ --max-line-length=100
git log --oneline -3
```

For adapter tasks:
```bash
python -c "from startup_watch.adapters.<id> import <ClassName>; print(<ClassName>().fetch()[:2])"
```
