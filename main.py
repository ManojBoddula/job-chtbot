import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone, timedelta
# CONFIG
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CACHE_FILE = "seen_jobs.json"

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise Exception("TELEGRAM_TOKEN or CHAT_ID is missing. Set secrets in GitHub Actions.")

KEYWORDS = [
    "python", "developer", "software engineer", "ai", "ml",
    "machine learning", "data scientist", "data analyst",
    "nlp", "deep learning", "genai", "llm", "rag",
    "data engineer", "mle", "analytics", "multimedia", "chatbots"
]

CITIES = ["hyderabad", "bangalore", "pune", "chennai", "mumbai",
          "gurgaon", "delhi", "noida", "kolkata", "ahmedabad"]

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}
# CACHE FUNCTIONS
def load_seen_jobs():
    if not os.path.exists(CACHE_FILE):
        return set()
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_seen_jobs(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(data), f, indent=2)

seen_jobs = load_seen_jobs()
# TELEGRAM FUNCTION
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        print(f"[Telegram] Sent message: {text[:50]}... Status: {resp.status_code}")
    except Exception as e:
        print(f"[Telegram] Failed to send message: {e}")
# HELPER FUNCTIONS
def is_india_job(loc):
    if not loc:
        return False
    loc = loc.lower()
    return "india" in loc or any(city in loc for city in CITIES)

def matches_keywords(title):
    title = title.lower()
    return any(k in title for k in KEYWORDS)

def format_job(job):
    return f"*{job['title']}*\n🏢 {job['company']}\n📍 {job['location']}\n🔗 {job['url']}"
# SCRAPER FUNCTIONS
def scrape_indeed():
    jobs = []
    try:
        url = "https://in.indeed.com/jobs?q=python+developer&fromage=1&limit=50"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")
        cards = soup.select("div.job_seen_beacon")
        for c in cards:
            try:
                title = c.select_one("h2").get_text(strip=True)
                company = (c.select_one(".companyName") or "").get_text(strip=True)
                loc = (c.select_one(".companyLocation") or "").get_text(strip=True)
                link = c.select_one("a").get("href", "")
                if link.startswith("/"):
                    link = "https://in.indeed.com" + link
                if is_india_job(loc) and matches_keywords(title):
                    jobs.append({"title": title, "company": company, "location": loc, "url": link})
            except:
                continue
    except Exception as e:
        print(f"[Indeed] Failed: {e}")
    return jobs

def scrape_naukri():
    jobs = []
    try:
        url = "https://www.naukri.com/python-jobs-in-india"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")
        cards = soup.select(".jobTuple")
        for c in cards:
            try:
                title = (c.select_one("a.title") or "").get_text(strip=True)
                company = (c.select_one(".companyName a") or "").get_text(strip=True)
                loc = (c.select_one(".location span") or "").get_text(strip=True)
                link = (c.select_one("a.title") or "").get("href", "")
                if is_india_job(loc) and matches_keywords(title):
                    jobs.append({"title": title, "company": company, "location": loc, "url": link})
            except:
                continue
    except Exception as e:
        print(f"[Naukri] Failed: {e}")
    return jobs

def run_all_scrapers():
    all_jobs = []
    all_jobs += scrape_indeed()
    all_jobs += scrape_naukri()
    return all_jobs

def filter_and_dedupe(jobs):
    final = []
    seen_urls = set()
    for j in jobs:
        if j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            final.append(j)
    return final

# MAIN FUNCTION
def send_jobs():
    global seen_jobs
    now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)  # IST

    all_jobs = filter_and_dedupe(run_all_scrapers())
    print(f"[Info] Total jobs fetched: {len(all_jobs)}")

    # Send jobs hourly
    if all_jobs:
        send_telegram_message("🚨 *Latest Jobs*")
        for job in all_jobs:
            if job["url"] not in seen_jobs:
                send_telegram_message(format_job(job))
                seen_jobs.add(job["url"])
    else:
        send_telegram_message("⚠️ No jobs found this hour.")

    save_seen_jobs(seen_jobs)
    print("[Info] Job sending completed.")

if __name__ == "__main__":
    send_jobs()
