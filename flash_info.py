import json, os, csv, logging, feedparser, random, time, requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import trafilatura

# --- RECTIFICATION: EXPLICIT KEY LOADING ---
load_dotenv()
def fetch_key(env_name):
    val = os.getenv(env_name)
    if not val and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if env_name in line: return line.split("=")[-1].strip().strip("'\"")
    return val

CSV_OUTPUT = "data/flash_info_output.csv"
CONFIG_FILE = "flash_info_sources.json"
GEMINI_KEYS = (fetch_key("GEMINI_API_KEY") or "").split(",")
GNEWS_KEY = fetch_key("GNEWS_API_KEY")

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("sovereign_engine")

# --- RECTIFICATION: BROWSER ROTATION ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def get_spark(title, text, domain, link):
    lenses = ["Maritime History", "Architectural Philosophy", "Ancient Linguistics", "Botanical Evolution", "Tactical Warfare", "Psychological Archetypes"]
    selected_lens = random.choice(lenses)
    
    # RECTIFICATION: SEED SYNTHESIS (Use Title/Link if text is missing due to 403)
    context_text = text[:1500] if text else f"Subject is {title} located at {link}. Use internal 2026 knowledge."
    prompt = f"Role: Abstract Reader. Lens: {selected_lens}. Subject: {title}. Context: {context_text}. Task: 3 bullets on Pivot Era, Evolution, and Human Ritual lost."

    for key in GEMINI_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key.strip()}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            elif res.status_code == 401: log.warning(f"Key Error 401. Rotating...")
        except: continue
    return None

def main():
    if not os.path.exists(CONFIG_FILE): return
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: config = json.load(f)
    
    # Flatten sources logic
    def find_sources(obj, domain="General"):
        found = []
        if isinstance(obj, dict):
            d = obj.get("domain", domain); tier = obj.get("tier", 3)
            for k, v in obj.items():
                if isinstance(v, str) and v.startswith("http"): found.append({"url": v, "domain": d, "tier": tier})
                else: found.extend(find_sources(v, d))
        elif isinstance(obj, list):
            for item in obj: found.extend(find_sources(item, domain))
        return found

    sources = find_sources(config)
    seen_urls = set()
    if os.path.exists(CSV_OUTPUT):
        with open(CSV_OUTPUT, "r", encoding="utf-8-sig") as f:
            seen_urls = {row['url'] for row in csv.DictReader(f) if 'url' in row}

    all_results = []
    for s in sources:
        if s["url"] in seen_urls: continue
        try:
            log.info(f"🔍 Probing: {s['url'][:50]}...")
            content = None
            title = s["url"].split('/')[-1].replace('-', ' ').title() or "Insight"
            
            # --- RECTIFICATION: AGGRESSIVE FETCH ---
            try:
                resp = requests.get(s["url"], headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=15)
                if resp.status_code == 200:
                    content = trafilatura.extract(resp.text)
                else: log.warning(f"  - Blocked {resp.status_code}. Initiating Seed Synthesis.")
            except: log.warning("  - Connection Refused. Initiating Seed Synthesis.")

            # FORCED SYNTHESIS: Even if content is None, we generate a Spark from the Title
            spark = get_spark(title, content, s['domain'], s['url'])
            
            if spark:
                all_results.append({
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "domain": s["domain"], "title": title, "url": s["url"],
                    "summary_snippet": spark,
                    "source_group": "SPARK" # RECTIFICATION: Synthesis-Based Promotion
                })
                log.info(f" ✅ Spark Forged: {title[:30]}")
                time.sleep(random.uniform(2, 5)) # Jitter logic
        except Exception as e: log.error(f"Error: {e}")

    if all_results:
        os.makedirs("data", exist_ok=True)
        with open(CSV_OUTPUT, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "domain", "title", "url", "summary_snippet", "source_group"])
            if os.stat(CSV_OUTPUT).st_size == 0: writer.writeheader()
            writer.writerows(all_results)
    log.info(f"DONE. {len(all_results)} connections forged.")

if __name__ == "__main__": main()
