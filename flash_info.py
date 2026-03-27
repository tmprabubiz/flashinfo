import json, os, csv, logging, feedparser, random, time, requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
CSV_OUTPUT = "data/flash_info_output.csv"
CONFIG_FILE = "flash_info_sources.json"
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("synthesis_engine")

def find_2026_model():
    """Dynamically finds the best 2026 model available to this key."""
    for v in ["v1beta", "v1"]:
        url = f"https://generativelanguage.googleapis.com/{v}/models?key={API_KEY}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                models = res.json().get("models", [])
                for pref in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]:
                    for m in models:
                        if pref in m["name"].lower():
                            return v, m["name"].split("/")[-1]
        except: continue
    return "v1beta", "gemini-2.5-flash"

def get_spark(title, snippet, v, m, domain):
    url = f"https://generativelanguage.googleapis.com/{v}/models/{m}:generateContent?key={API_KEY}"
    
    # LATERAL LENS DICE
    lens = random.choice(["Architecture", "Maritime", "Agriculture", "Philosophy", "Linguistics", "Warfare"])
    
    # The 'Synthesis Manifesto' Prompt
    prompt = f"""
    ROLE: You are the 'Abstract Reader' synthesis engine from 2026. 
    LOGIC: Indefinite Thinking (Manual vs Digital).
    LENS: {lens}
    DOMAIN: {domain}
    SUBJECT: {title}
    CONTEXT: {snippet[:300]}
    
    INSTRUCTION: Do not summarize. Do not complain about limited info. Use the subject as a 'seed' for a lateral connection.
    
    REQUIRED FORMAT (3 BULLETS):
    1. THE PIVOT ERA: Identify a specific era of 'Manual Mastery' related to this subject (e.g., if the subject is an update, discuss the Era of Scribes).
    2. THE EVOLUTION: Connect this modern 'Noise' to a specific 'Happening' in that Era.
    3. THE HUMAN STORY: What 'Fun Gossip' or lifestyle ritual was lost to modern efficiency?
    
    (Provide punchy, evocative bullets only).
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_SEXUALLY_EXPLICIT"]]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=25)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        return f"Status {res.status_code}"
    except: return "Connection Delay"

def main():
    version, model_id = find_2026_model()
    log.info(f"🚀 Manifesto Active: {version}/{model_id}")

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
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

    # Let's process a larger batch (30) now that we know the path is clear
    for s in sources[3:33]: 
        try:
            feed = feedparser.parse(s["url"])
            if not feed.entries: continue
            entry = feed.entries[0]
            log.info(f"✨ Synthesizing: {entry.title[:40]}")
            
            spark = get_spark(entry.title, entry.get('summary',''), version, model_id, s['domain'])
            log.info(f"   SPARK: {spark[:120]}...")
            
            all_results.append({
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "domain": s["domain"], "title": entry.title, "url": entry.link,
                "summary_snippet": spark,
                "source_group": "SPARK" if int(s.get('tier', 3)) <= 2 else "CONTEXT"
            })
            time.sleep(4) 
        except: continue

    if all_results:
        os.makedirs("data", exist_ok=True)
        keys = ["date", "domain", "title", "url", "summary_snippet", "source_group"]
        with open(CSV_OUTPUT, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            if not Path(CSV_OUTPUT).exists() or os.stat(CSV_OUTPUT).st_size == 0: writer.writeheader()
            writer.writerows(all_results)
    log.info(f"DONE. {len(all_results)} connections forged.")

if __name__ == "__main__": main()
