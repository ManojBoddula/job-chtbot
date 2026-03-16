import os
import re
import csv
import time
import random
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_JOBS = 40
DATABASE = "jobs_seen.csv"

# ---------------- JOB FILTER ---------------- #
# AI/ML + Software + Entry-level + Internship
JOB_PATTERN = re.compile(
    r"(ai|machine learning|ml engineer|ai engineer|deep learning|"
    r"data scientist|computer vision|nlp|artificial intelligence|"
    r"software engineer|sde|software developer|backend engineer| Prompt|python|python developer)",
    re.IGNORECASE
)

EXPERIENCE_PATTERN = re.compile(
    r"(entry[- ]level|junior|0-2 years|internship|intern)",
    re.IGNORECASE
)

# ---------------- INDIA PRIORITY ---------------- #
INDIA_KEYWORDS = [
    "india","bangalore","bengaluru","hyderabad",
    "pune","chennai","mumbai","delhi","noida","gurgaon",
    "kolkata","kochi","ahmedabad","jaipur","trivandrum"
]

# ---------------- LOAD SEEN JOBS ---------------- #
def load_seen():
    seen = set()
    if os.path.exists(DATABASE):
        with open(DATABASE, "r") as f:
            for row in csv.reader(f):
                seen.add(tuple(row))
    return seen

# ---------------- SAVE JOBS ---------------- #
def save_seen(jobs):
    with open(DATABASE, "a", newline="") as f:
        writer = csv.writer(f)
        for j in jobs:
            writer.writerow([j["title"], j["link"]])

# ---------------- FETCH JOBS FROM REMOTE APIs ---------------- #
def fetch_remotive():
    jobs = []
    try:
        url = "https://remotive.com/api/remote-jobs"
        res = requests.get(url)
        data = res.json()
        for job in data["jobs"]:
            jobs.append({
                "source": "Remotive",
                "title": job["title"],
                "company": job["company_name"],
                "location": job["candidate_required_location"],
                "description": job["description"][:200],
                "link": job["url"]
            })
    except Exception as e:
        print("Remotive error:", e)
    print("Remotive:", len(jobs))
    return jobs

def fetch_arbeitnow():
    jobs = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        res = requests.get(url)
        data = res.json()
        for job in data["data"]:
            jobs.append({
                "source": "Arbeitnow",
                "title": job["title"],
                "company": job["company_name"],
                "location": job["location"],
                "description": job["description"][:200],
                "link": job["url"]
            })
    except Exception as e:
        print("Arbeitnow error:", e)
    print("Arbeitnow:", len(jobs))
    return jobs

def fetch_muse():
    jobs = []
    try:
        for page in range(1, 6):
            url = f"https://www.themuse.com/api/public/jobs?page={page}"
            res = requests.get(url)
            data = res.json()
            for job in data["results"]:
                loc = job["locations"][0]["name"] if job["locations"] else "Unknown"
                jobs.append({
                    "source": "Muse",
                    "title": job["name"],
                    "company": job["company"]["name"],
                    "location": loc,
                    "description": job["contents"][:200],
                    "link": job["refs"]["landing_page"]
                })
            time.sleep(random.uniform(1, 3))
    except Exception as e:
        print("Muse error:", e)
    print("Muse:", len(jobs))
    return jobs

def fetch_internshala():
    jobs = []
    try:
        url = "https://internshala.com/internships"
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        for j in soup.select(".job-title-href")[:40]:
            jobs.append({
                "source": "Internshala",
                "title": j.text.strip() + " Internship",
                "company": "N/A",
                "location": "India",
                "description": "Internship / Entry-level",
                "link": "https://internshala.com" + j["href"]
            })
    except Exception as e:
        print("Internshala error:", e)
    print("Internshala:", len(jobs))
    return jobs

# ---------------- SEARCH DISCOVERY ---------------- #
def fetch_search():
    queries = [
        # AI/ML entry-level and internship jobs
        "AI engineer India internship site:wellfound.com",
        "machine learning Bangalore entry-level site:wellfound.com",
        "data scientist Hyderabad internship site:wellfound.com",
        "deep learning Pune entry-level site:wellfound.com",
        "nlp Chennai internship site:wellfound.com",
        # Software jobs
        "Software engineer India entry-level site:wellfound.com",
        "SDE Bangalore 0-2 years site:wellfound.com",
        "SDE-1 Hyderabad entry-level site:wellfound.com",
        "Backend engineer Pune 0-2 years site:wellfound.com",
        "Frontend engineer Chennai internship site:wellfound.com",
        # Generic remote boards
        "AI engineer site:boards.greenhouse.io",
        "Software engineer site:boards.greenhouse.io",
        "machine learning site:jobs.lever.co",
        "SDE site:jobs.lever.co",
        "data scientist site:ashbyhq.com",
        "Software developer site:ashbyhq.com"
    ]
    jobs = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                results = ddgs.text(q, max_results=120)
                for r in results:
                    body = r.get("body", "")
                    location = "Unknown"
                    if any(city in body.lower() for city in INDIA_KEYWORDS) or "india" in body.lower():
                        location = "India"
                    jobs.append({
                        "source": "Search",
                        "title": r["title"],
                        "company": "Unknown",
                        "location": location,
                        "description": body[:200],
                        "link": r["href"]
                    })
                time.sleep(random.uniform(2, 4))
    except Exception as e:
        print("Search error:", e)
    print("Search:", len(jobs))
    return jobs

# ---------------- FILTER ---------------- #
def filter_jobs(jobs):
    # Keep only jobs matching roles AND entry-level / internship
    filtered = []
    for j in jobs:
        title_desc = j["title"] + " " + j["description"]
        if JOB_PATTERN.search(title_desc) and EXPERIENCE_PATTERN.search(title_desc):
            filtered.append(j)
    return filtered

# ---------------- DEDUP ---------------- #
def deduplicate(jobs, seen):
    unique = []
    for j in jobs:
        key = (j["title"], j["link"])
        if key not in seen:
            unique.append(j)
            seen.add(key)
    return unique

# ---------------- INDIA PRIORITY ---------------- #
def prioritize(jobs):
    india = []
    others = []
    for j in jobs:
        loc = str(j.get("location", "")).lower()
        desc = str(j.get("description", "")).lower()
        if any(k in loc for k in INDIA_KEYWORDS) or "india" in loc or "india" in desc:
            india.append(j)
        elif "remote" in loc:
            india.append(j)
        else:
            others.append(j)
    return india + others

# ---------------- TELEGRAM ---------------- #
def send_telegram(jobs):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")

    india = []
    others = []

    for j in jobs:
        loc = str(j.get("location","")).lower()
        desc = str(j.get("description","")).lower()
        if any(k in loc for k in INDIA_KEYWORDS) or "india" in loc or "india" in desc or "remote" in loc:
            india.append(j)
        else:
            others.append(j)

    def send_message(text):
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat, "text": text}
        )

    # ---------- INDIAN JOBS ---------- #
    if india:
        send_message("🇮🇳 Indian Entry-level & Internship AI/Software Jobs")

        for j in india[:MAX_JOBS]:
            msg = (
                f"💼 {j['title']}\n"
                f"🏢 {j['company']}\n"
                f"📍 {j['location']}\n"
                f"🔗 {j['link']}"
            )
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": msg})
            time.sleep(random.uniform(1, 2))

    # ---------- INTERNATIONAL JOBS ---------- #
    if others:
        send_message("🌍 International Entry-level & Internship AI/Software Jobs")
        for j in others[:MAX_JOBS]:
            msg = (
                f"💼 {j['title']}\n"
                f"🏢 {j['company']}\n"
                f"📍 {j['location']}\n"
                f"🔗 {j['link']}"
            )
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": msg})
            time.sleep(random.uniform(1, 2))

# ---------------- RUN BOT ---------------- #
def run_bot():
    print("\nStarting job finder...\n")
    seen = load_seen()
    jobs = []

    jobs += fetch_remotive()
    jobs += fetch_arbeitnow()
    jobs += fetch_muse()
    jobs += fetch_internshala()
    jobs += fetch_search()

    print("Collected:", len(jobs))

    jobs = filter_jobs(jobs)
    jobs = deduplicate(jobs, seen)
    jobs = prioritize(jobs)

    print("Filtered:", len(jobs))

    send_telegram(jobs)
    save_seen(jobs)
    print("\nRun complete\n")

# ---------------- LOOP ---------------- #
if __name__ == "__main__":
    while True:
        run_bot()
        print("Sleeping 1 hour...\n")
        time.sleep(3600)