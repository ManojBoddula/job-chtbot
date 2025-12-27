import os
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["ai", "machine learning", "ml", "data scientist"]
MAX_JOBS = 20

TEST_MODE = os.getenv("TEST_MODE", "False") == "True"

# ------------------ SCRAPERS ------------------ #
def fetch_indeed():
    url = "https://www.indeed.com/jobs?q=ai+engineer&l=India"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select(".job_seen_beacon")[:10]:
            title = job.select_one("h2 span")
            link_tag = job.select_one("h2 a")
            if title:
                link = "https://www.indeed.com" + link_tag["href"] if link_tag else ""
                jobs.append({"source": "Indeed", "title": title.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_indeed failed:", e)
        return []

def fetch_remoteok():
    url = "https://remoteok.com/remote-ai-jobs"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for row in soup.select("tr.job")[:10]:
            title = row.select_one("h2")
            link_tag = row.select_one("a.preventLink")
            if title:
                link = "https://remoteok.com" + link_tag["href"] if link_tag else ""
                jobs.append({"source": "RemoteOK", "title": title.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_remoteok failed:", e)
        return []

def fetch_weworkremotely():
    url = "https://weworkremotely.com/remote-jobs/search?term=ai"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select("section.jobs article li")[:10]:
            title = job.select_one("span.title")
            link_tag = job.select_one("a")
            if title and link_tag:
                link = "https://weworkremotely.com" + link_tag["href"]
                jobs.append({"source": "WeWorkRemotely", "title": title.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_weworkremotely failed:", e)
        return []

def fetch_placement_india():
    url = "https://www.placementindia.com/jobs/search-jobs-in-india.html?keyword=ai"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for row in soup.select(".jobListRow")[:10]:
            title = row.select_one("a")
            if title:
                link = title["href"]
                jobs.append({"source": "PlacementIndia", "title": title.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_placement_india failed:", e)
        return []

def fetch_workindia():
    url = "https://www.workindia.in/job-search/ai%20engineer"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select(".level-job")[:10]:
            title = job.select_one(".job-title")
            link_tag = job.select_one("a")
            if title:
                link = "https://www.workindia.in" + link_tag["href"] if link_tag else ""
                jobs.append({"source": "WorkIndia", "title": title.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_workindia failed:", e)
        return []

def fetch_monster_india():
    url = "https://www.monsterindia.com/search/ai-engineer-jobs"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select(".job-tittle")[:10]:
            title_tag = job.select_one("h3")
            link_tag = job.select_one("a")
            if title_tag and link_tag:
                link = link_tag["href"]
                jobs.append({"source": "MonsterIndia", "title": title_tag.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_monster_india failed:", e)
        return []

# ------------------ NEW SCRAPERS ------------------ #
def fetch_fresherworld():
    url = "https://www.fresherworld.com/jobs/ai-machine-learning"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select(".jobBox")[:10]:
            title_tag = job.select_one(".jobTitle")
            link_tag = job.select_one("a")
            if title_tag and link_tag:
                link = "https://www.fresherworld.com" + link_tag["href"]
                jobs.append({"source": "FresherWorld", "title": title_tag.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_fresherworld failed:", e)
        return []

def fetch_internshala():
    url = "https://internshala.com/internships/ai-internship"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select(".internship_meta")[:10]:
            title_tag = job.select_one("a")
            if title_tag:
                link = "https://internshala.com" + title_tag["href"]
                jobs.append({"source": "Internshala", "title": title_tag.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_internshala failed:", e)
        return []

# ------------------ FILTER + DEDUP ------------------ #
def filter_jobs(jobs):
    return [job for job in jobs if any(k.lower() in job["title"].lower() for k in KEYWORDS)]

def deduplicate_jobs(jobs):
    seen = set()
    unique = []
    for job in jobs:
        key = (job["title"], job["link"])
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique

# ------------------ TELEGRAM ------------------ #
def send_telegram(jobs):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("ERROR: Telegram credentials missing!")
        return

    if not jobs:
        text = "✅ GitHub Test: No jobs found today"
    else:
        text = "🔥 AI/ML Jobs Found:\n\n"
        for job in jobs[:MAX_JOBS]:
            text += f"• {job['title']} [{job['source']}]\n{job['link']}\n\n"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        response = requests.post(url, data=payload)
        print("DEBUG: Telegram API response:", response.status_code, response.text)
    except Exception as e:
        print("ERROR: Failed to send Telegram message:", e)

# ------------------ MAIN ------------------ #
def main():
    print("DEBUG: Starting GitHub Actions run...")

    jobs = []

    if TEST_MODE:
        # Always send one test job during testing
        jobs.append({
            "source": "TestSite",
            "title": "AI Engineer (Test Job)",
            "link": "https://example.com/job"
        })
    else:
        # Real scraping
        jobs.extend(fetch_indeed())
        jobs.extend(fetch_remoteok())
        jobs.extend(fetch_weworkremotely())
        jobs.extend(fetch_placement_india())
        jobs.extend(fetch_workindia())
        jobs.extend(fetch_monster_india())
        jobs.extend(fetch_fresherworld())
        jobs.extend(fetch_internshala())

    jobs = filter_jobs(jobs)
    jobs = deduplicate_jobs(jobs)

    print("DEBUG: Total jobs found:", len(jobs))
    for job in jobs[:10]:
        print(f"{job['title']} [{job['source']}] - {job['link']}")

    send_telegram(jobs)
    print("DEBUG: Finished GitHub Actions run.")

if __name__ == "__main__":
    main()
