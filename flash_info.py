import json, os, csv, logging, feedparser, random, time, requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import trafilatura

load_dotenv()
CSV_OUTPUT = "data/flash_info_output.csv"
CONFIG_FILE = "flash_info_sources.json"
API_KEYS = os.getenv("GEMINI_API_KEY", "").split(",")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("synthesis_engine")

# Item 6: The Stealth Header to bypass 403 blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

def get_seen_urls():
    if not os.path.exists(CSV_OUTPUT): return set()
    with open(CSV_OUTPUT, "r", encoding="utf-8-sig") as f:
        return {row['url'] for row in csv.DictReader(f) if 'url' in row}

def get_spark(title, text, domain):
    lenses = ["Maritime History", "Architectural Philosophy", "Ancient Linguistics", "Botanical Evolution", "Tactical Warfare"]
    selected_lens = random.choice(lenses)
    prompt = f"Role: Abstract Reader. Lens: {selected_lens}. Subject: {title}. Context: {text[:1500]}. Task: 3 bullets on Pivot Era, Evolution, and Human Ritual lost. Evocative tone."
    
    for key in API_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={key.strip()}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: continue
    return None

def main():
    seen_urls = get_seen_urls()
    if not os.path.exists(CONFIG_FILE): return
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: config = json.load(f)
    
    def find_sources(obj, domain="General"):
        found = []
        if isinstance(obj, dict):
            d = obj.get("domain", domain)
            for k, v in obj.items():
                if isinstance(v, str) and v.startswith("http"):
                    found.append({"url": v, "domain": d, "tier": obj.get("tier", 3)})
                else: found.extend(find_sources(v, d))
        elif isinstance(obj, list):
            for item in obj: found.extend(find_sources(item, domain))
        return found

    sources = find_sources(config)
    all_results = []
    
    for s in sources:
        if s["url"] in seen_urls: continue
        try:
            is_feed = any(x in s["url"].lower() for x in [".xml", ".rss", "feed", "atom"])
            if is_feed:
                feed = feedparser.parse(s["url"])
                if not feed.entries: continue
                entry = feed.entries[0]
                title, content, link = entry.title, entry.get('summary', ''), entry.link
            else:
                # STEALTH SCRAPE: Using requests with headers to bypass 403
                log.info(f"🕸️ Stealth Scrape: {s['url']}")
                response = requests.get(s["url"], headers=HEADERS, timeout=15)
                if response.status_code == 200:
                    content = trafilatura.extract(response.text)
                    title = s["url"].split('/')[-1].replace('-', ' ').title() or "Static Analysis"
                    link = s["url"]
                else:
                    log.warning(f"  - Blocked: {response.status_code}")
                    continue

            if not content or len(content) < 100: continue
            spark = get_spark(title, content, s['domain'])
            if spark:
                all_results.append({
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "domain": s["domain"], "title": title, "url": link,
                    "summary_snippet": spark,
                    "source_group": "SPARK" if int(s.get('tier', 3)) <= 2 else "CONTEXT"
                })
                log.info(f" ✅ Success: {title[:30]}")
                time.sleep(4) # Respect the tier
        except Exception as e: log.error(f"Error: {e}")

    if all_results:
        os.makedirs("data", exist_ok=True)
        keys = ["date", "domain", "title", "url", "summary_snippet", "source_group"]
        with open(CSV_OUTPUT, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            if os.stat(CSV_OUTPUT).st_size == 0: writer.writeheader()
            writer.writerows(all_results)
    log.info(f"FINISH: {len(all_results)} connections forged.")

if __name__ == "__main__": main()
