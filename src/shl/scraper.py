import asyncio
from typing import List, Dict, Any, Tuple
import re
import time
import os
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright
from .catalog_schema import Assessment, canonical_id, now_iso


CATALOG_URL = "https://www.shl.com/products/product-catalog/"
KENEXA_URL = "https://www.shl.com/c/global/ibm-kenexa-catalog/"
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "catalog.jsonl")


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def normalize_url(u: str) -> str:
    u = u.strip()
    if u.startswith("//"):
        u = "https:" + u
    if u.startswith("/"):
        u = "https://www.shl.com" + u
    u = re.sub(r"[?#].*$", "", u)
    return u


def parse_type(text: str) -> str:
    t = text.strip().upper()
    if "PERSONALITY" in t or t == "P":
        return "P"
    if "KNOWLEDGE" in t or "SKILLS" in t or t in {"K", "S", "C", "A", "B"}:
        return "K"
    return t[:1] if t else ""


def extract_detail_fields(html: str, url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    name = ""
    h1 = soup.find("h1")
    if h1 and h1.text:
        name = h1.text.strip()
    if not name:
        title = soup.find("title")
        if title and title.text:
            name = re.sub(r"\s+\|\s*SHL.*$", "", title.text.strip())
    desc = ""
    for el in soup.find_all(text=re.compile(r"Description", re.I)):
        parent = el.find_parent()
        if parent:
            nxt = parent.find_next_sibling()
            if nxt and nxt.text:
                desc = nxt.text.strip()
                break
    if not desc:
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            desc = meta["content"].strip()
    ttype = ""
    for el in soup.find_all(text=re.compile(r"Test Type", re.I)):
        parent = el.find_parent()
        if parent:
            vals = []
            for v in parent.find_all("div"):
                tx = v.text.strip()
                if tx:
                    vals.append(tx)
            if vals:
                ttype = parse_type(", ".join(vals))
                break
    if not ttype:
        for badge in soup.find_all("span"):
            tx = badge.text.strip().upper()
            if tx in {"K", "P", "S", "C", "A", "B", "E"}:
                ttype = parse_type(tx)
                break
    skills = []
    tags = []
    for ul in soup.find_all("ul"):
        items = [li.text.strip() for li in ul.find_all("li") if li.text.strip()]
        for it in items:
            if len(it.split()) <= 6:
                skills.append(it)
    skills = list(dict.fromkeys(skills))[:20]
    language = "en"
    for el in soup.find_all(text=re.compile(r"Languages", re.I)):
        parent = el.find_parent()
        if parent:
            langs = [d.text.strip() for d in parent.find_all("div") if d.text.strip()]
            if langs:
                language = "en"
                break
    return {
        "name": name,
        "description": desc,
        "type": ttype or "",
        "skills": skills,
        "tags": tags,
        "language": language,
        "url": normalize_url(url),
    }


async def collect_catalog_links() -> List[str]:
    links = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(CATALOG_URL, wait_until="networkidle")
            for _ in range(50):
                await page.keyboard.press("End")
                await asyncio.sleep(0.2)
            html = await page.content()
            await browser.close()
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/products/product-catalog/view/" in href:
                links.append(normalize_url(href))
    except Exception:
        pass
    try:
        r = requests.get(KENEXA_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        soup2 = BeautifulSoup(r.text, "html.parser")
        for a in soup2.find_all("a", href=True):
            href = a["href"]
            if "/c/global/ibm-kenexa-catalog/view/" in href:
                links.append(normalize_url(href))
    except Exception:
        pass
    links = list(dict.fromkeys(links))
    return links


def fetch(url: str) -> Tuple[int, str]:
    hdrs = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=hdrs, timeout=30)
    return r.status_code, r.text


def scrape() -> List[Assessment]:
    ensure_dirs()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    links = loop.run_until_complete(collect_catalog_links())
    loop.close()
    items = []
    for u in links:
        code, body = fetch(u)
        if code != 200:
            continue
        data = extract_detail_fields(body, u)
        aid = canonical_id(data["url"])
        item = Assessment(
            id=aid,
            name=data["name"],
            url=data["url"],
            type=data["type"],
            description=data["description"],
            skills=data["skills"],
            tags=data["tags"],
            language=data["language"],
            scraped_at=now_iso(),
        )
        items.append(item)
    return items


def persist(items: List[Assessment]) -> None:
    ensure_dirs()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for it in items:
            f.write(it.to_json() + "\n")


def run() -> Dict[str, Any]:
    items = scrape()
    persist(items)
    return {"count": len(items), "output": OUTPUT_FILE}
