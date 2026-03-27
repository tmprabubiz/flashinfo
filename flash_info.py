import json, os, csv, logging, feedparser, random, time, requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import trafilatura

load_dotenv()
CSV_OUTPUT = "data/flash_info_output.csv"
CONFIG_FILE = "flash_info_sources.json"

# Item 10 & 11: Multi-Key & Model Handling
API_KEYS = os.getenv("GEMINI_API_KEY", "").split(",")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") 

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("synthesis_engine")

def get_seen_urls():
    if not os.path.exists(CSV_OUTPUT): return set()
    with open(CSV_OUTPUT, "r", encoding="utf-8-sig") as f:
        return {row['url'] for row in csv.DictReader(f) if 'url' in row}

def get_spark(title, text, domain):
    # Item 7: The Dice Approach (Lateral Lenses)
    lenses = ["Maritime History", "Architectural Philosophy", "Ancient Linguistics", "Botanical Evolution", "Tactical Warfare"]
    selected_lens = random.choice(lenses)
    
    prompt = f"Role: Abstract Reader. Lens: {selected_lens}. Subject: {title}. Context: {text[:1200]}. Task: 3 bullets on Pivot Era, Evolution, and Human Ritual lost. Use remote associations."

    for key in API_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={key.strip()}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            elif res.status_code == 401:
                log.warning(f"Key {key[:5]}... failed. Trying next.")
        except: continue
    return None

def main():
    seen_urls = get_seen_urls()
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
    
    for s in sources[:40]: # Batch processing
        if s["url"] in seen_urls: continue
        try:
            is_feed = any(x in s["url"].lower() for x in [".xml", ".rss", "feed", "atom"])
            if is_feed:
                feed = feedparser.parse(s["url"])
                if not feed.entries: continue
                entry = feed.entries[0]
                title, content, link = entry.title, entry.get('summary', ''), entry.link
            else:
                downloaded = trafilatura.fetch_url(s["url"])
                content = trafilatura.extract(downloaded)
                title = s["url"].split('/')[-1].replace('-', ' ').title()
                link = s["url"]

            if not content: continue
            spark = get_spark(title, content, s['domain'])
            if spark:
                all_results.append({
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "domain": s["domain"], "title": title, "url": link,
                    "summary_snippet": spark,
                    "source_group": "SPARK" if int(s.get('tier', 3)) <= 2 else "CONTEXT"
                })
                time.sleep(2)
        except: continue

    if all_results:
        os.makedirs("data", exist_ok=True)
        with open(CSV_OUTPUT, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "domain", "title", "url", "summary_snippet", "source_group"])
            if os.stat(CSV_OUTPUT).st_size == 0: writer.writeheader()
            writer.writerows(all_results)
    log.info(f"DONE. {len(all_results)} connections forged.")

if __name__ == "__main__": main()
