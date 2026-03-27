import json, os, csv, logging, feedparser, random, time, requests, re
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import trafilatura

# --- RECTIFICATION: ABSOLUTE PATH HANDSHAKE (Item 1) ---
base_path = Path(__file__).resolve().parent
load_dotenv(base_path / ".env")

CSV_OUTPUT = base_path / "data" / "flash_info_output.csv"
CONFIG_FILE = base_path / "flash_info_sources.json"
GEMINI_KEYS = (os.getenv("GEMINI_API_KEY") or "").split(",")

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("oracle_engine")

def get_spark(title, text, domain, url):
    # --- RECTIFICATION: THE DICE METHOD (Item 7) ---
    lenses = ["Maritime Power", "Architectural Philosophy", "Ancient Linguistics", "Botanical Warfare", "Stone Age Rituals", "Psychological Archetypes"]
    lens = random.choice(lenses)
    
    # FORCED CONTENT: If site blocked us, use internal 2026 knowledge
    context = text[:2000] if (text and len(text) > 100) else f"Forced Synthesis for {title}. URL Path: {url}"
    
    prompt = f"LENS: {lens}. SUBJECT: {title}. CONTEXT: {context}. TASK: 3 bullets. 1: Pivot Era (Manual Mastery). 2: Evolution. 3: Human Ritual Lost. START with 'Through the lens of {lens}...' "

    for key in GEMINI_KEYS:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key.strip()}"
        try:
            res = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: continue
    return None

def main():
    if not CONFIG_FILE.exists(): return
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: config = json.load(f)
    
    def find_sources(obj, domain="General"):
        found = []
        if isinstance(obj, dict):
            d = obj.get("domain", domain)
            for k, v in obj.items():
                if isinstance(v, str) and v.startswith("http"): found.append({"url": v, "domain": d})
                else: found.extend(find_sources(v, d))
        elif isinstance(obj, list):
            for item in obj: found.extend(find_sources(item, domain))
        return found

    # RECTIFICATION: SHUFFLE AND PRIORITIZE STATIC (Item 18)
    sources = find_sources(config)
    random.shuffle(sources)
    
    seen_urls = set()
    if CSV_OUTPUT.exists():
        with open(CSV_OUTPUT, "r", encoding="utf-8-sig") as f:
            seen_urls = {row['url'] for row in csv.DictReader(f) if 'url' in row}

    all_results = []
    count = 0
    for s in sources:
        if count >= 15: break # Process high-quality batch
        if s["url"] in seen_urls: continue
        
        try:
            log.info(f"🔮 Analyzing: {s['url']}")
            content = None
            # Extract Title from URL for "Seed Synthesis"
            title_match = re.search(r'/([^/]+)/?$', s["url"])
            title = title_match.group(1).replace('-', ' ').replace('_', ' ').title() if title_match else "Historical Insight"
            
            # ATTEMPT SCRAPE
            try:
                resp = requests.get(s["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    content = trafilatura.extract(resp.text)
                else: log.warning(f"  ! Blocked ({resp.status_code}). Engaging Oracle Seed.")
            except: log.warning("  ! Timeout. Engaging Oracle Seed.")

            # RECTIFICATION: ALWAYS SYNTHESIZE (The Purpose)
            spark = get_spark(title, content, s['domain'], s['url'])
            if spark:
                all_results.append({
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "domain": s["domain"], "title": title, "url": s["url"],
                    "summary_snippet": spark, "source_group": "SPARK"
                })
                count += 1
                log.info(f" ✅ Forged: {title[:30]}")
                time.sleep(2)
        except Exception as e: log.error(f"Error: {e}")

    if all_results:
        CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(CSV_OUTPUT, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "domain", "title", "url", "summary_snippet", "source_group"])
            if os.stat(CSV_OUTPUT).st_size == 0: writer.writeheader()
            writer.writerows(all_results)
    log.info(f"FINISH: {len(all_results)} new seeds planted.")

if __name__ == "__main__": main()
