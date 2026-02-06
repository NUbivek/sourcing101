import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict, fields
from typing import Dict, Iterable, List, Optional, Tuple

import requests
import yaml
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


USER_AGENT = "startup-watch/0.1"


@dataclass
class StartupSignal:
    company: str
    website: str
    linkedin_url: str
    description: str
    hq: str
    headcount: str
    funding_amount: str
    last_round_date: str
    investors: str
    stage_inferred: str
    category_tags: str
    stealth_tag: str
    source: str
    source_url: str
    signal_text: str
    date_captured: str


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def now_utc_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def normalize_company(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def extract_urls(text: str) -> List[str]:
    return re.findall(r"https?://[^\s)\]]+", text)

def extract_primary_website(urls: List[str]) -> str:
    for u in urls:
        if "linkedin.com" in u:
            continue
        return u.split("?")[0]
    return ""

def clean_company_text(text: str) -> str:
    if not text:
        return ""
    first = text.strip().split("\n")[0].strip()
    return first

def extract_company_from_url(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if not m:
        return ""
    domain = m.group(1).lower()
    if "linkedin.com" in domain:
        return ""
    base = domain.split(".")[0]
    if base in ["www", "app", "blog"]:
        return ""
    return base.replace("-", " ").title()


def extract_company_candidates(text: str) -> List[str]:
    candidates = []
    stop = {"Seed", "Series", "Round", "Hiring", "Startup", "Company"}
    for pattern in [
        r"\bat\s+([A-Z][A-Za-z0-9&.,\-]{2,}(?:\s+[A-Z][A-Za-z0-9&.,\-]{2,}){0,3})",
        r"\bjoin\s+([A-Z][A-Za-z0-9&.,\-]{2,}(?:\s+[A-Z][A-Za-z0-9&.,\-]{2,}){0,3})",
        r"\bfrom\s+([A-Z][A-Za-z0-9&.,\-]{2,}(?:\s+[A-Z][A-Za-z0-9&.,\-]{2,}){0,3})",
        r"\bintroducing\s+([A-Z][A-Za-z0-9&.,\-]{2,}(?:\s+[A-Z][A-Za-z0-9&.,\-]{2,}){0,3})",
        r"\bannouncing\s+([A-Z][A-Za-z0-9&.,\-]{2,}(?:\s+[A-Z][A-Za-z0-9&.,\-]{2,}){0,3})",
    ]:
        for match in re.findall(pattern, text):
            name = match.strip()
            if name.split()[0] in stop:
                continue
            candidates.append(name)
    return list(dict.fromkeys(candidates))


def infer_stage(text: str) -> str:
    t = text.lower()
    if "pre-seed" in t or "preseed" in t:
        return "pre-seed"
    if "series a" in t:
        return "series a"
    if re.search(r"\bseed\b", t):
        return "seed"
    return ""


def extract_funding_amount(text: str) -> str:
    m = re.search(r"\$\s?\d{1,3}(?:\.\d+)?\s?(?:m|million|b|billion)", text, re.I)
    if m:
        return m.group(0)
    return ""


def infer_stage_from_amount(text: str) -> str:
    t = text.lower()
    m = re.search(r"\$\s?(\d{1,3}(?:\.\d+)?)\s?(m|million|b|billion)", t, re.I)
    if not m:
        return ""
    value = float(m.group(1))
    unit = m.group(2)
    if unit in ["b", "billion"]:
        value = value * 1000.0
    # Heuristic ranges for early-stage announcements
    if 1.0 <= value <= 5.0:
        return "seed"
    if 10.0 <= value <= 50.0:
        return "series a"
    return ""


def infer_headcount_band(text: str) -> str:
    t = text.lower()
    if "<5" in t or "less than 5" in t or "tiny startup" in t:
        return "<5"
    m = re.search(r"(\d{1,4})\s*(?:employees|people|team)", t)
    if not m:
        return ""
    n = int(m.group(1))
    if n < 5:
        return "<5"
    if n < 20:
        return "5-19"
    if n < 50:
        return "20-49"
    if n < 200:
        return "50-199"
    return "200+"

def infer_stealth_tag(text: str) -> str:
    t = text.lower()
    if "stealth" in t:
        return "stealth"
    if "just launched" in t or re.search(r"\bnew\b", t):
        return "new"
    return ""


def classify_categories(text: str, categories: List[str]) -> List[str]:
    t = text.lower()
    hits = [c for c in categories if c.lower() in t]
    return list(dict.fromkeys(hits))

def source_category_hints(source_name: str) -> List[str]:
    mapping = {
        "Plug and Play Supply Chain": ["supply chain", "logistics"],
        "SVG Thrive": ["agtech", "farm tech"],
        "SVG THRIVE": ["agtech", "farm tech"],
        "SVG Thrive Canada III": ["agtech", "farm tech"],
        "SVG Thrive VI (2020)": ["agtech", "farm tech"],
        "Alchemist Accelerator": ["industrial software", "manufacturing software", "industrial hardware"],
        "MIT delta v": ["industrial software", "manufacturing software", "supply chain"],
        "MIT Delta V": ["industrial software", "manufacturing software", "supply chain"],
        "MIT Delta V (2025 Cohort)": ["industrial software", "manufacturing software", "supply chain"],
        "MIT Delta V (Investor Days 2025)": ["industrial software", "manufacturing software", "supply chain"],
        "MIT Pozen Fellowship (2025 Host Companies)": ["industrial software", "manufacturing software", "supply chain"],
        "Stanford StartX": ["industrial software", "manufacturing software", "agtech"],
        "UC Berkeley SkyDeck": ["industrial software", "manufacturing software", "agtech", "supply chain"],
        "Village Capital": ["supply chain", "agtech", "industrial software"],
        "S2G Investments": ["agtech", "industrial software", "supply chain"],
        "Y Combinator": ["industrial software", "manufacturing software", "agtech", "supply chain"],
        "SkyDeck Fund": ["industrial software", "manufacturing software", "agtech", "supply chain"],
    }
    return mapping.get(source_name, [])


def fetch_html(url: str, playwright_fallback: bool = False) -> Optional[str]:
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    if not playwright_fallback or sync_playwright is None:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
            return html
    except Exception:
        return None


def enrich_from_website(url: str) -> Tuple[str, str]:
    html = fetch_html(url)
    if not html:
        return "", ""
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.string or "").strip() if soup.title else ""
    desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        desc = meta["content"].strip()
    return title, desc

def extract_linkedin_company_url(urls: List[str]) -> str:
    for u in urls:
        if "linkedin.com/company/" in u:
            return u.split("?")[0]
    return ""


def enrich_from_linkedin_company(url: str, chrome_profile_dir: str, chrome_profile_name: str) -> Tuple[str, str, str]:
    if sync_playwright is None:
        return "", "", ""
    try:
        p = sync_playwright().start()
        browser = p.chromium.launch_persistent_context(
            user_data_dir=chrome_profile_dir or None,
            headless=False,
            args=[f"--profile-directory={chrome_profile_name}"] if chrome_profile_dir else [],
        )
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
        p.stop()
    except Exception:
        return "", "", ""

    soup = BeautifulSoup(html, "lxml")
    name = ""
    desc = ""
    headcount = ""
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(" ", strip=True)
    og = soup.find("meta", property="og:description")
    if og and og.get("content"):
        desc = og["content"].strip()
    m = re.search(r"(\d[\d,]+)\s*employees", soup.get_text(" ", strip=True), re.I)
    if m:
        headcount = m.group(1)
    return name, desc, headcount


def parse_linkedin_manual(html_files: List[str], categories: List[str]) -> List[StartupSignal]:
    results: List[StartupSignal] = []
    for path in html_files:
        with open(path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")
        posts = soup.select("div.feed-shared-update-v2")
        for post in posts:
            text = post.get_text(" ", strip=True)
            urls = extract_urls(text)
            stage = infer_stage(text)
            funding = extract_funding_amount(text)
            cats = classify_categories(text, categories)
            if not stage:
                stage = infer_stage_from_amount(text)
            headcount = infer_headcount_band(text)
            stealth_tag = infer_stealth_tag(text)
            companies = extract_company_candidates(text)
            if not companies:
                for u in urls:
                    c = extract_company_from_url(u)
                    if c:
                        companies.append(c)
            if not companies:
                companies = [""]
            linkedin_url = extract_linkedin_company_url(urls)
            website = extract_primary_website(urls)
            for company in companies:
                results.append(
                    StartupSignal(
                        company=company,
                        website=website,
                        linkedin_url=linkedin_url,
                        description="",
                        hq="",
                        headcount=headcount,
                        funding_amount=funding,
                        last_round_date="",
                        investors="",
                        stage_inferred=stage,
                        category_tags=", ".join(cats),
                        stealth_tag=stealth_tag,
                        source="linkedin_manual",
                        source_url="",
                        signal_text=text[:800],
                        date_captured=now_utc_iso(),
                    )
                )
    return results


def scrape_linkedin(
    search_urls: List[str],
    categories: List[str],
    chrome_profile_dir: str,
    chrome_profile_name: str,
    max_posts: int,
    pause_for_login: bool,
    pause_seconds: int,
    use_system_chrome: bool,
    browser_name: str,
) -> List[StartupSignal]:
    if sync_playwright is None:
        print("Playwright not installed; skipping LinkedIn scraping.", file=sys.stderr)
        return []

    results: List[StartupSignal] = []
    with sync_playwright() as p:
        browser_type = {
            "chromium": p.chromium,
            "firefox": p.firefox,
            "webkit": p.webkit,
        }.get(browser_name, p.chromium)
        launch_args = []
        channel = None
        if browser_name == "chromium":
            launch_args = [f"--profile-directory={chrome_profile_name}"] if chrome_profile_dir else []
            channel = "chrome" if use_system_chrome else None
        browser = browser_type.launch_persistent_context(
            user_data_dir=chrome_profile_dir or None,
            headless=False,
            args=launch_args,
            channel=channel,
        )
        page = browser.new_page()
        if pause_for_login:
            page.goto("https://www.linkedin.com", wait_until="domcontentloaded")
            print("If needed, log into LinkedIn in the opened browser window.")
            time.sleep(pause_seconds)

        for url in search_urls:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            collected = 0
            last_height = 0
            for _ in range(10):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(1500)
                height = page.evaluate("document.body.scrollHeight")
                if height == last_height:
                    break
                last_height = height

            posts = page.locator("div.feed-shared-update-v2")
            count = posts.count()
            for i in range(min(count, max_posts)):
                text = posts.nth(i).inner_text()
                urls = extract_urls(text)
                stage = infer_stage(text)
                funding = extract_funding_amount(text)
                cats = classify_categories(text, categories)
                if not stage:
                    stage = infer_stage_from_amount(text)
                headcount = infer_headcount_band(text)
                stealth_tag = infer_stealth_tag(text)
                companies = extract_company_candidates(text)
                if not companies:
                    for u in urls:
                        c = extract_company_from_url(u)
                        if c:
                            companies.append(c)
                if not companies:
                    companies = [""]
                linkedin_url = extract_linkedin_company_url(urls)
                website = extract_primary_website(urls)
                for company in companies:
                    results.append(
                        StartupSignal(
                            company=company,
                            website=website,
                            linkedin_url=linkedin_url,
                            description="",
                            hq="",
                            headcount=headcount,
                            funding_amount=funding,
                            last_round_date="",
                            investors="",
                            stage_inferred=stage,
                            category_tags=", ".join(cats),
                            stealth_tag=stealth_tag,
                            source="linkedin",
                            source_url=url,
                            signal_text=text[:800],
                            date_captured=now_utc_iso(),
                        )
                    )
                collected += 1
                if collected >= max_posts:
                    break
        browser.close()

    return results


def scrape_yc_directory(batch: str, categories: List[str], playwright_fallback: bool) -> List[StartupSignal]:
    url = f"https://www.ycombinator.com/companies?batch={batch}"
    html = fetch_html(url, playwright_fallback)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    data_script = soup.find("script", id="__NEXT_DATA__")
    if not data_script:
        return []

    data = json.loads(data_script.string)
    companies = data.get("props", {}).get("pageProps", {}).get("companies", [])

    results: List[StartupSignal] = []
    for c in companies:
        yc_cats = [x.get("name", "") for x in c.get("categories", [])]
        if categories and not any(cat in yc_cats for cat in categories):
            continue
        desc = c.get("one_liner", "")
        results.append(
            StartupSignal(
                company=c.get("name", ""),
                website=c.get("website", ""),
                linkedin_url="",
                description=desc,
                hq=c.get("location", ""),
                headcount=c.get("team_size", ""),
                funding_amount="",
                last_round_date="",
                investors="Y Combinator",
                stage_inferred="seed",
                category_tags=", ".join(yc_cats),
                stealth_tag="",
                source="yc_directory",
                source_url=url,
                signal_text=desc[:800],
                date_captured=now_utc_iso(),
            )
        )
    return results


def scrape_startupstream(url: str, max_items: int, categories: List[str], playwright_fallback: bool) -> List[StartupSignal]:
    html = fetch_html(url, playwright_fallback)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("a")
    results: List[StartupSignal] = []
    for a in cards:
        name = a.get_text(" ", strip=True)
        href = a.get("href") or ""
        if not name or len(name) > 80:
            continue
        text = name
        cats = classify_categories(text, categories)
        results.append(
            StartupSignal(
                company=name,
                website="",
                linkedin_url="",
                description="",
                hq="",
                headcount="",
                funding_amount="",
                last_round_date="",
                investors="",
                stage_inferred="",
                category_tags=", ".join(cats),
                stealth_tag=infer_stealth_tag(text),
                source="startupstream",
                source_url=href,
                signal_text=text[:800],
                date_captured=now_utc_iso(),
            )
        )
        if len(results) >= max_items:
            break
    return results


def scrape_vc_portfolio_page(name: str, url: str, playwright_fallback: bool) -> List[StartupSignal]:
    html = fetch_html(url, playwright_fallback)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    links = soup.select("a")
    results: List[StartupSignal] = []
    for a in links:
        text = a.get_text(" ", strip=True)
        href = a.get("href") or ""
        if not text or len(text) > 80:
            continue
        if not href or href.startswith("#"):
            continue
        results.append(
            StartupSignal(
                company=text,
                website="",
                linkedin_url="",
                description="",
                hq="",
                headcount="",
                funding_amount="",
                last_round_date="",
                investors=name,
                stage_inferred="",
                category_tags="",
                stealth_tag="",
                source="vc_portfolio",
                source_url=url,
                signal_text=text[:800],
                date_captured=now_utc_iso(),
            )
        )
    return results


def scrape_list_page(name: str, url: str, playwright_fallback: bool) -> List[StartupSignal]:
    html = fetch_html(url, playwright_fallback)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    links = soup.select("a")
    list_items = [li.get_text(" ", strip=True) for li in soup.select("li")]
    base_match = re.search(r"https?://([^/]+)", url)
    base_domain = base_match.group(1).lower() if base_match else ""
    nav_stop = {
        "home", "about", "blog", "news", "events", "contact", "donate", "team",
        "careers", "jobs", "apply", "apply now", "newsletter", "press",
        "privacy", "terms", "linkedin", "twitter", "instagram", "facebook",
        "youtube", "podcast", "our mission", "guiding principles", "awards",
        "annual report", "membership", "portfolio", "companies", "programs",
        "students", "faculty", "research", "partners", "sponsors", "mentors",
        "login", "sign in", "sign up", "faq", "resources", "support", "events",
        "newsroom", "media", "directory", "knowledge base"
    }
    results: List[StartupSignal] = []
    def add_company(text: str, href: str) -> None:
        if not text or len(text) > 80:
            return
        if text.strip().lower() in nav_stop:
            return
        if len(text) < 3:
            return
        results.append(
            StartupSignal(
                company=clean_company_text(text),
                website="",
                linkedin_url="",
                description="",
                hq="",
                headcount="",
                funding_amount="",
                last_round_date="",
                investors=name,
                stage_inferred="",
                category_tags="",
                stealth_tag="",
                source="list_page",
                source_url=url,
                signal_text=text[:800],
                date_captured=now_utc_iso(),
            )
        )

    # Prefer list items (cohort/company lists)
    for text in list_items:
        add_company(text, "")

    # Fallback to anchor text for pages that link out to company sites
    for a in links:
        text = a.get_text(" ", strip=True)
        href = a.get("href") or ""
        if not href or href.startswith("#"):
            continue
        href_norm = href.split("?")[0]
        href_domain_match = re.search(r"https?://([^/]+)", href_norm)
        href_domain = href_domain_match.group(1).lower() if href_domain_match else ""
        looks_like_company_path = any(x in href_norm.lower() for x in ["/company", "/companies", "/portfolio", "/cohort"])
        if href_domain and base_domain and href_domain == base_domain and not looks_like_company_path:
            continue
        add_company(text, href)
    return results


def scrape_s2g_companies(url: str, playwright_fallback: bool, min_year: int) -> List[StartupSignal]:
    html = fetch_html(url, playwright_fallback)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    results: List[StartupSignal] = []

    # S2G companies list uses heading links
    links = soup.select("h2 a, h3 a")
    company_links = []
    for a in links:
        name = a.get_text(" ", strip=True)
        href = a.get("href") or ""
        if not name or not href:
            continue
        if not href.startswith("http"):
            href = "https://www.s2ginvestments.com" + href
        company_links.append((name, href))

    for name, href in company_links:
        founded = ""
        desc = ""
        detail = fetch_html(href, playwright_fallback)
        if detail:
            detail_text = BeautifulSoup(detail, "lxml").get_text(" ", strip=True)
            m = re.search(r"Founded\\s*(\\d{4})", detail_text, re.I)
            if m:
                founded = m.group(1)
            if not desc:
                meta = BeautifulSoup(detail, "lxml").find("meta", property="og:description")
                if meta and meta.get("content"):
                    desc = meta["content"].strip()
        if founded:
            try:
                if int(founded) < min_year:
                    continue
            except ValueError:
                pass
        results.append(
            StartupSignal(
                company=name,
                website="",
                linkedin_url="",
                description=desc,
                hq="",
                headcount="",
                funding_amount="",
                last_round_date="",
                investors="S2G Investments",
                stage_inferred="",
                category_tags="",
                stealth_tag="",
                source="s2g_companies",
                source_url=href,
                signal_text=desc[:800] if desc else name,
                date_captured=now_utc_iso(),
            )
        )

    return results


def scrape_skydeck_portfolio_js(url: str) -> List[StartupSignal]:
    if sync_playwright is None:
        return []
    results: List[StartupSignal] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        texts = page.evaluate(
            \"\"\"\n() => {\n  const sels = [\n    '[data-company]', '[data-name]', '[data-title]',\n    'a[href*=\"/company\"]', 'a[href*=\"/companies\"]', 'a[href*=\"/portfolio\"]',\n    'div[class*=\"company\"]', 'div[class*=\"portfolio\"]', 'div[class*=\"card\"]',\n    'li'\n  ];\n  const out = new Set();\n  sels.forEach(sel => {\n    document.querySelectorAll(sel).forEach(el => {\n      const t = (el.getAttribute('data-company') || el.getAttribute('data-name') || el.getAttribute('data-title') || el.innerText || '').trim();\n      if (t) out.add(t);\n    });\n  });\n  return Array.from(out);\n}\n\"\"\"
        )
        browser.close()
    nav_stop = {
        "home","about","blog","news","events","contact","donate","team","careers","jobs","apply","portfolio",
        "companies","programs","students","faculty","research","partners","sponsors","mentors","login","sign in",
        "sign up","faq","resources","support","media","directory","press","privacy","terms","linkedin","twitter",
        "instagram","facebook","youtube"
    }
    for t in texts:
        name = clean_company_text(t)
        low = name.lower()
        if not name or len(name) < 3 or len(name) > 80:
            continue
        if low in nav_stop:
            continue
        if "batch" in low or "cohort" in low:
            continue
        results.append(
            StartupSignal(
                company=name,
                website="",
                linkedin_url="",
                description="",
                hq="",
                headcount="",
                funding_amount="",
                last_round_date="",
                investors="UC Berkeley SkyDeck",
                stage_inferred="",
                category_tags="",
                stealth_tag="",
                source="skydeck_portfolio_js",
                source_url=url,
                signal_text=name,
                date_captured=now_utc_iso(),
            )
        )
    return results


def scrape_mit_delta_v(url: str, playwright_fallback: bool) -> List[StartupSignal]:
    html = fetch_html(url, playwright_fallback)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    results: List[StartupSignal] = []
    stop = {
        "our 2025 teams", "our teams", "delta v", "about", "contact", "team", "partners",
        "apply", "program", "mentors", "supporters", "entrepreneurship", "mit", "accelerator"
    }
    for header in soup.find_all(["h1", "h2", "h3", "h4"]):
        name = header.get_text(" ", strip=True)
        if not name or len(name) > 60:
            continue
        if name.lower() in stop:
            continue
        # find a nearby website link
        website = ""
        for a in header.find_all_next("a", limit=3):
            href = (a.get("href") or "").strip()
            if href.startswith("http") and "mit.edu" not in href:
                website = href.split("?")[0]
                break
        results.append(
            StartupSignal(
                company=name,
                website=website,
                linkedin_url="",
                description="",
                hq="",
                headcount="",
                funding_amount="",
                last_round_date="",
                investors="MIT delta v",
                stage_inferred="pre-seed",
                category_tags="",
                stealth_tag="",
                source="mit_delta_v",
                source_url=url,
                signal_text=name,
                date_captured=now_utc_iso(),
            )
        )
    return results


def scrape_svg_thrive_cohort(url: str, playwright_fallback: bool) -> List[StartupSignal]:
    html = fetch_html(url, playwright_fallback)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    results: List[StartupSignal] = []
    for li in soup.find_all("li"):
        text = li.get_text(" ", strip=True)
        if not text or len(text) > 160:
            continue
        # Prefer items that look like "Company – description"
        if " - " in text or " – " in text or " — " in text:
            name = re.split(r"\s[-–—]\s", text, maxsplit=1)[0].strip()
            if 2 <= len(name) <= 60:
                results.append(
                    StartupSignal(
                        company=name,
                        website="",
                        linkedin_url="",
                        description="",
                        hq="",
                        headcount="",
                        funding_amount="",
                        last_round_date="",
                        investors="SVG THRIVE",
                        stage_inferred="seed",
                        category_tags="",
                        stealth_tag="",
                        source="svg_thrive",
                        source_url=url,
                        signal_text=text[:800],
                        date_captured=now_utc_iso(),
                    )
                )
    return results


def scrape_skydeck_fund_portfolio(url: str, playwright_fallback: bool) -> List[StartupSignal]:
    html = fetch_html(url, playwright_fallback)
    if not html:
        return []
    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    results: List[StartupSignal] = []
    pattern = re.compile(r"([A-Z][A-Za-z0-9&'\\-\\. ]{2,})\\s\\|\\s(?:Spring|Summer|Fall|Winter)\\s\\d{4}")
    for match in pattern.findall(text):
        name = match.strip()
        if 2 <= len(name) <= 60:
            results.append(
                StartupSignal(
                    company=name,
                    website="",
                    linkedin_url="",
                    description="",
                    hq="",
                    headcount="",
                    funding_amount="",
                    last_round_date="",
                    investors="SkyDeck Fund",
                    stage_inferred="seed",
                    category_tags="",
                    stealth_tag="",
                    source="skydeck_fund",
                    source_url=url,
                    signal_text=name,
                    date_captured=now_utc_iso(),
                )
            )
    return results


def apply_filters(
    signals: List[StartupSignal],
    categories: List[str],
    require_category: bool,
    require_stage: bool,
    filters_cfg: dict,
) -> List[StartupSignal]:
    filtered = []
    for s in signals:
        text = " ".join([s.company, s.description, s.signal_text, s.category_tags])
        cats = classify_categories(text, categories)
        stage = s.stage_inferred or infer_stage(text)
        if not s.category_tags:
            hints = source_category_hints(s.investors or s.source)
            if hints:
                s.category_tags = ", ".join(hints)
                cats = classify_categories(s.category_tags, categories)
        if not s.category_tags:
            s.category_tags = ", ".join(cats)
        if not s.stage_inferred:
            s.stage_inferred = stage
        if not s.stealth_tag:
            s.stealth_tag = infer_stealth_tag(text)
        exclude_list = filters_cfg.get("exclude_companies", [])
        if exclude_list and s.company:
            lower = s.company.lower()
            if any(x.lower() in lower for x in exclude_list):
                continue
        if require_category and not s.category_tags:
            continue
        allowed_sources = filters_cfg.get("early_stage_source_names", [])
        stage_ok = bool(s.stage_inferred or s.stealth_tag)
        if not stage_ok:
            if s.source == "yc_directory" or s.investors in allowed_sources:
                stage_ok = True
        if require_stage and not stage_ok:
            continue
        require_early = filters_cfg.get("require_early_stage_signal", False)
        if require_early:
            keywords = filters_cfg.get("early_stage_keywords", [])
            early_text = text.lower()
            early_hit = any(k.lower() in early_text for k in keywords)
            if s.source == "yc_directory":
                early_hit = True
            if s.investors in allowed_sources:
                early_hit = True
            if not early_hit:
                continue
        filtered.append(s)
    return filtered


def enrich(
    signals: List[StartupSignal],
    linkedin_enrich: bool,
    chrome_profile_dir: str,
    chrome_profile_name: str,
    linkedin_enrich_max: int,
) -> List[StartupSignal]:
    enriched = []
    linkedin_count = 0
    for s in signals:
        if s.website:
            title, desc = enrich_from_website(s.website)
            if title and not s.description:
                s.description = title
            if desc and not s.description:
                s.description = desc
        if linkedin_enrich and s.linkedin_url and linkedin_count < linkedin_enrich_max:
            name, desc, headcount = enrich_from_linkedin_company(
                s.linkedin_url, chrome_profile_dir, chrome_profile_name
            )
            if name and not s.company:
                s.company = name
            if desc and not s.description:
                s.description = desc
            if headcount and not s.headcount:
                s.headcount = headcount
            linkedin_count += 1
        enriched.append(s)
    return enriched


def dedupe(signals: List[StartupSignal]) -> List[StartupSignal]:
    seen: Dict[str, StartupSignal] = {}
    for s in signals:
        key = normalize_company(s.company) or normalize_company(s.website)
        if not key:
            key = f"{s.source}:{s.source_url}:{s.signal_text[:50]}"
        if key not in seen:
            seen[key] = s
    return list(seen.values())


def write_csv(path: str, signals: List[StartupSignal]) -> None:
    fieldnames = [f.name for f in fields(StartupSignal)]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for s in signals:
            w.writerow(asdict(s))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--linkedin-manual", action="store_true")
    ap.add_argument("--pause-for-login", action="store_true")
    ap.add_argument("--pause-seconds", type=int, default=60)
    args = ap.parse_args()

    cfg = load_config(args.config)

    output_dir = cfg.get("output_dir", "output")
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"{output_dir}/startup_watch_{timestamp}.csv"
    os.makedirs(output_dir, exist_ok=True)

    categories = cfg.get("categories", [])
    playwright_fallback = bool(cfg.get("playwright_fallback", {}).get("enabled", False))

    signals: List[StartupSignal] = []

    linkedin_cfg = cfg.get("linkedin", {})
    if linkedin_cfg.get("enabled") and not args.linkedin_manual:
        signals.extend(
            scrape_linkedin(
                linkedin_cfg.get("search_urls", []),
                categories,
                linkedin_cfg.get("chrome_profile_dir", ""),
                linkedin_cfg.get("chrome_profile_name", "Default"),
                int(linkedin_cfg.get("max_posts_per_search", 50)),
                bool(args.pause_for_login),
                int(args.pause_seconds),
                bool(linkedin_cfg.get("use_system_chrome", False)),
                str(linkedin_cfg.get("browser", "chromium")),
            )
        )

    manual_cfg = cfg.get("linkedin_manual", {})
    if args.linkedin_manual or manual_cfg.get("enabled"):
        signals.extend(
            parse_linkedin_manual(
                manual_cfg.get("html_files", []),
                categories,
            )
        )

    yc_cfg = cfg.get("yc_directory", {})
    if yc_cfg.get("enabled"):
        signals.extend(
            scrape_yc_directory(
                yc_cfg.get("batch", ""),
                yc_cfg.get("categories", []),
                playwright_fallback,
            )
        )

    ss_cfg = cfg.get("startupstream", {})
    if ss_cfg.get("enabled"):
        signals.extend(
            scrape_startupstream(
                ss_cfg.get("url", ""),
                int(ss_cfg.get("max_items", 200)),
                categories,
                playwright_fallback,
            )
        )

    vc_cfg = cfg.get("vc_portfolios", {})
    if vc_cfg.get("enabled"):
        for page in vc_cfg.get("pages", []):
            signals.extend(scrape_vc_portfolio_page(page.get("name", ""), page.get("url", ""), playwright_fallback))

    inc_cfg = cfg.get("incubators_and_accelerators", {})
    if inc_cfg.get("enabled"):
        for page in inc_cfg.get("pages", []):
            signals.extend(scrape_list_page(page.get("name", ""), page.get("url", ""), playwright_fallback))

    mdv_cfg = cfg.get("mit_delta_v", {})
    if mdv_cfg.get("enabled"):
        for url in mdv_cfg.get("cohorts", []):
            signals.extend(scrape_mit_delta_v(url, playwright_fallback))

    sky_cfg = cfg.get("skydeck_fund", {})
    if sky_cfg.get("enabled"):
        signals.extend(scrape_skydeck_fund_portfolio(sky_cfg.get("url", ""), playwright_fallback))

    thrive_cfg = cfg.get("svg_thrive_cohorts", {})
    if thrive_cfg.get("enabled"):
        for url in thrive_cfg.get("cohorts", []):
            signals.extend(scrape_svg_thrive_cohort(url, playwright_fallback))

    impact_cfg = cfg.get("impact_specialized_vcs", {})
    if impact_cfg.get("enabled"):
        for page in impact_cfg.get("pages", []):
            signals.extend(scrape_list_page(page.get("name", ""), page.get("url", ""), playwright_fallback))

    s2g_cfg = cfg.get("s2g_companies", {})
    if s2g_cfg.get("enabled"):
        signals.extend(
            scrape_s2g_companies(
                s2g_cfg.get("url", "https://www.s2ginvestments.com/companies"),
                playwright_fallback,
                int(s2g_cfg.get("min_founded_year", 2018)),
            )
        )

    skydeck_js_cfg = cfg.get("skydeck_portfolio_js", {})
    if skydeck_js_cfg.get("enabled"):
        signals.extend(scrape_skydeck_portfolio_js(skydeck_js_cfg.get("url", "")))

    cb_cfg = cfg.get("crunchbase_free", {})
    if cb_cfg.get("enabled"):
        for page in cb_cfg.get("pages", []):
            signals.extend(scrape_vc_portfolio_page("crunchbase_free", page, playwright_fallback))

    filters_cfg = cfg.get("filters", {})
    signals = apply_filters(
        signals,
        categories,
        bool(filters_cfg.get("require_category_match", True)),
        bool(filters_cfg.get("require_stage_match", False)),
        filters_cfg,
    )
    linkedin_cfg = cfg.get("linkedin", {})
    linkedin_enrich_cfg = cfg.get("linkedin_enrichment", {})
    signals = enrich(
        signals,
        bool(linkedin_enrich_cfg.get("enabled", False)),
        linkedin_cfg.get("chrome_profile_dir", ""),
        linkedin_cfg.get("chrome_profile_name", "Default"),
        int(linkedin_enrich_cfg.get("max_company_pages", 50)),
    )
    signals = dedupe(signals)

    write_csv(output_path, signals)
    print(f"Wrote {len(signals)} rows to {output_path}")


if __name__ == "__main__":
    main()
