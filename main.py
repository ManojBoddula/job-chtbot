import os
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["ai", "machine learning", "ml", "data scientist"]
MAX_JOBS = 20

TEST_MODE = os.getenv("TEST_MODE", "False") == "True"

# ------------------ STATIC SCRAPER FUNCTION ------------------ #
def fetch_static_site(url, source, selector_title, selector_link, link_prefix=""):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select(selector_title)[:10]:
            title_tag = job
            link_tag = job.select_one(selector_link)
            if title_tag:
                link = link_prefix + link_tag["href"] if link_tag else ""
                jobs.append({"source": source, "title": title_tag.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print(f"ERROR: fetch_{source} failed:", e)
        return []

# ------------------ WEBSITES ------------------ #
def fetch_fresherworld():
    return fetch_static_site(
        "https://www.fresherworld.com/jobs/ai-machine-learning",
        "FresherWorld",
        ".jobTitle",
        "a",
        "https://www.fresherworld.com"
    )

def fetch_internshala():
    return fetch_static_site(
        "https://internshala.com/internships/ai-internship",
        "Internshala",
        ".internship_meta a",
        "a",
        "https://internshala.com"
    )

def fetch_workindia():
    return fetch_static_site(
        "https://www.workindia.in/job-search/ai%20engineer",
        "WorkIndia",
        ".job-title",
        "a",
        "https://www.workindia.in"
    )

def fetch_placement_india():
    return fetch_static_site(
        "https://www.placementindia.com/jobs/search-jobs-in-india.html?keyword=ai",
        "PlacementIndia",
        ".jobListRow a",
        "a",
        ""
    )

def fetch_monster_india():
    return fetch_static_site(
        "https://www.monsterindia.com/search/ai-engineer-jobs",
        "MonsterIndia",
        ".job-tittle h3",
        "a",
        ""
    )

def fetch_remoteok():
    try:
        url = "https://remoteok.com/remote-ai-jobs"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for row in soup.select("tr.job")[:10]:
            title_tag = row.select_one("h2")
            link_tag = row.select_one("a.preventLink")
            if title_tag:
                link = "https://remoteok.com" + link_tag["href"] if link_tag else ""
                jobs.append({"source": "RemoteOK", "title": title_tag.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_remoteok failed:", e)
        return []

def fetch_weworkremotely():
    try:
        url = "https://weworkremotely.com/remote-jobs/search?term=ai"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select("section.jobs article li")[:10]:
            title_tag = job.select_one("span.title")
            link_tag = job.select_one("a")
            if title_tag and link_tag:
                link = "https://weworkremotely.com" + link_tag["href"]
                jobs.append({"source": "WeWorkRemotely", "title": title_tag.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_weworkremotely failed:", e)
        return []

def fetch_indeed():
    try:
        url = "https://www.indeed.com/jobs?q=ai+engineer&l=India"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        jobs = []
        for job in soup.select(".job_seen_beacon")[:10]:
            title_tag = job.select_one("h2 span")
            link_tag = job.select_one("h2 a")
            if title_tag:
                link = "https://www.indeed.com" + link_tag["href"] if link_tag else ""
                jobs.append({"source": "Indeed", "title": title_tag.text.strip(), "link": link})
        return jobs
    except Exception as e:
        print("ERROR: fetch_indeed failed:", e)
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

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text}
        )
        print("DEBUG: Telegram API response:", response.status_code, response.text)
    except Exception as e:
        print("ERROR: Failed to send Telegram message:", e)

# ------------------ MAIN ------------------ #
def main():
    print("DEBUG: Starting GitHub Actions run...")

    jobs = []

    if TEST_MODE:
        # Send test job when testing
        jobs.append({
            "source": "TestSite",
            "title": "AI Engineer (Test Job)",
            "link": "https://example.com/job"
        })
    else:
        # Real scraping from all websites
        jobs.extend(fetch_fresherworld())
        jobs.extend(fetch_internshala())
        jobs.extend(fetch_workindia())
        jobs.extend(fetch_placement_india())
        jobs.extend(fetch_monster_india())
        jobs.extend(fetch_remoteok())
        jobs.extend(fetch_weworkremotely())
        jobs.extend(fetch_indeed())

    jobs = filter_jobs(jobs)
    jobs = deduplicate_jobs(jobs)

    print("DEBUG: Total jobs found:", len(jobs))
    for job in jobs[:10]:
        print(f"{job['title']} [{job['source']}] - {job['link']}")

    send_telegram(jobs)
    print("DEBUG: Finished GitHub Actions run.")

if __name__ == "__main__":
    main()
