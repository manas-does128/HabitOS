"""
coding_fetcher.py
Real API integrations for: LeetCode, Codeforces, GitHub, CodeChef, HackerRank, GeeksForGeeks
All functions return a normalised dict or None on failure.
"""
import requests, json
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "HabitOS/2.0 (productivity tracker; github.com/habitos)"}
TIMEOUT = 8


# ─────────────────────────────────────────────
# LeetCode  (public GraphQL – no auth needed)
# ─────────────────────────────────────────────
def fetch_leetcode(username: str) -> dict | None:
    url = "https://leetcode.com/graphql"
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        username
        profile { ranking realName }
        submitStats {
          acSubmissionNum { difficulty count submissions }
        }
        userCalendar { activeYears streak totalActiveDays submissionCalendar }
        contestBadge { name }
      }
      userContestRanking(username: $username) {
        attendedContestsCount
        rating
        globalRanking
        badge { name }
      }
    }
    """
    try:
        r = requests.post(
            url,
            json={"query": query, "variables": {"username": username}},
            headers={**HEADERS, "Content-Type": "application/json",
                     "Referer": "https://leetcode.com"},
            timeout=TIMEOUT
        )
        if r.status_code != 200:
            return None
        data = r.json().get("data", {})
        user = data.get("matchedUser")
        if not user:
            return None

        ac = user.get("submitStats", {}).get("acSubmissionNum", [])
        counts = {d["difficulty"]: d["count"] for d in ac}

        calendar_raw = user.get("userCalendar", {}).get("submissionCalendar", "{}")
        try:
            calendar = json.loads(calendar_raw) if isinstance(calendar_raw, str) else {}
        except Exception:
            calendar = {}

        contest = data.get("userContestRanking") or {}

        return {
            "platform": "LeetCode",
            "username": username,
            "total_solved": counts.get("All", 0),
            "easy_solved":  counts.get("Easy", 0),
            "medium_solved":counts.get("Medium", 0),
            "hard_solved":  counts.get("Hard", 0),
            "ranking":      user.get("profile", {}).get("ranking", 0),
            "contests":     contest.get("attendedContestsCount", 0),
            "contest_rating": round(contest.get("rating") or 0),
            "submission_calendar": calendar,   # {unix_ts_str: count}
            "streak": user.get("userCalendar", {}).get("streak", 0),
            "total_active_days": user.get("userCalendar", {}).get("totalActiveDays", 0),
        }
    except Exception:
        return None


# ─────────────────────────────────────────────
# Codeforces  (official public REST API)
# ─────────────────────────────────────────────
def fetch_codeforces(username: str) -> dict | None:
    try:
        # user info
        info_r = requests.get(
            f"https://codeforces.com/api/user.info?handles={username}",
            headers=HEADERS, timeout=TIMEOUT
        )
        if info_r.status_code != 200 or info_r.json().get("status") != "OK":
            return None
        u = info_r.json()["result"][0]

        # rated contests
        rating_r = requests.get(
            f"https://codeforces.com/api/user.rating?handle={username}",
            headers=HEADERS, timeout=TIMEOUT
        )
        contests = 0
        max_rating = u.get("maxRating", 0)
        if rating_r.status_code == 200 and rating_r.json().get("status") == "OK":
            contests = len(rating_r.json()["result"])

        # solved problems (status)
        status_r = requests.get(
            f"https://codeforces.com/api/user.status?handle={username}&from=1&count=1000",
            headers=HEADERS, timeout=TIMEOUT
        )
        solved, easy, medium, hard = set(), 0, 0, 0
        monthly_activity = {}   # "YYYY-MM": count
        if status_r.status_code == 200 and status_r.json().get("status") == "OK":
            for sub in status_r.json()["result"]:
                if sub.get("verdict") != "OK":
                    continue
                p = sub.get("problem", {})
                pid = f"{p.get('contestId','')}{p.get('index','')}"
                if pid in solved:
                    continue
                solved.add(pid)
                rating = p.get("rating", 0) or 0
                if rating <= 1200:   easy += 1
                elif rating <= 2000: medium += 1
                else:                hard += 1
                ts = sub.get("creationTimeSeconds", 0)
                if ts:
                    month = datetime.utcfromtimestamp(ts).strftime("%Y-%m")
                    monthly_activity[month] = monthly_activity.get(month, 0) + 1

        return {
            "platform": "Codeforces",
            "username": username,
            "rating": u.get("rating", 0),
            "max_rating": max_rating,
            "rank": u.get("rank", "unrated"),
            "max_rank": u.get("maxRank", "unrated"),
            "contests": contests,
            "total_solved": len(solved),
            "easy_solved": easy,
            "medium_solved": medium,
            "hard_solved": hard,
            "monthly_activity": monthly_activity,
            "avatar_url": u.get("titlePhoto", ""),
            "contribution": u.get("contribution", 0),
        }
    except Exception:
        return None


# ─────────────────────────────────────────────
# GitHub  (public REST API – no auth needed)
# ─────────────────────────────────────────────
def fetch_github(username: str) -> dict | None:
    try:
        r = requests.get(
            f"https://api.github.com/users/{username}",
            headers={**HEADERS, "Accept": "application/vnd.github.v3+json"},
            timeout=TIMEOUT
        )
        if r.status_code != 200:
            return None
        u = r.json()

        # repos for star count
        repos_r = requests.get(
            f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
            headers={**HEADERS, "Accept": "application/vnd.github.v3+json"},
            timeout=TIMEOUT
        )
        total_stars, languages = 0, {}
        repos = []
        if repos_r.status_code == 200:
            repos = repos_r.json()
            for repo in repos:
                total_stars += repo.get("stargazers_count", 0)
                lang = repo.get("language")
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1

        # contribution events (last 90 days approximation via events API)
        events_r = requests.get(
            f"https://api.github.com/users/{username}/events/public?per_page=100",
            headers={**HEADERS, "Accept": "application/vnd.github.v3+json"},
            timeout=TIMEOUT
        )
        monthly_activity = {}
        contribution_dates = []
        if events_r.status_code == 200:
            for event in events_r.json():
                created = event.get("created_at", "")
                if created:
                    try:
                        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        month = dt.strftime("%Y-%m")
                        monthly_activity[month] = monthly_activity.get(month, 0) + 1
                        contribution_dates.append(dt.strftime("%Y-%m-%d"))
                    except Exception:
                        pass

        return {
            "platform": "GitHub",
            "username": username,
            "name": u.get("name") or username,
            "bio": u.get("bio") or "",
            "public_repos": u.get("public_repos", 0),
            "followers": u.get("followers", 0),
            "following": u.get("following", 0),
            "total_stars": total_stars,
            "avatar_url": u.get("avatar_url", ""),
            "monthly_activity": monthly_activity,
            "contribution_dates": contribution_dates,
            "top_languages": dict(sorted(languages.items(), key=lambda x: -x[1])[:5]),
            "total_repos": len(repos),
        }
    except Exception:
        return None


# ─────────────────────────────────────────────
# HackerRank  (public profile API)
# ─────────────────────────────────────────────
def fetch_hackerrank(username: str) -> dict | None:
    try:
        r = requests.get(
            f"https://www.hackerrank.com/rest/hackers/{username}/scores_elo",
            headers=HEADERS, timeout=TIMEOUT
        )
        profile_r = requests.get(
            f"https://www.hackerrank.com/rest/contests/master/hackers/{username}/profile",
            headers=HEADERS, timeout=TIMEOUT
        )
        solved, badges, stars = 0, 0, 0
        if profile_r.status_code == 200:
            data = profile_r.json().get("model", {})
            solved = data.get("solved_challenges", 0)
            badges = data.get("badges_count", 0)
            stars  = data.get("level", 0)
        return {
            "platform": "HackerRank",
            "username": username,
            "total_solved": solved,
            "badges": badges,
            "stars": stars,
        }
    except Exception:
        return None


# ─────────────────────────────────────────────
# GeeksForGeeks  (public stats API)
# ─────────────────────────────────────────────
def fetch_gfg(username: str) -> dict | None:
    try:
        r = requests.get(
            f"https://geeks-for-geeks-stats-api.vercel.app/?raw=Y&userName={username}",
            headers=HEADERS, timeout=TIMEOUT
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("status") == "error" or "error" in str(data.get("info","")):
            return None
        info = data.get("info", {})
        return {
            "platform": "GeeksForGeeks",
            "username": username,
            "total_solved": data.get("totalProblemsSolved", 0),
            "easy_solved": data.get("Easy", {}).get("count", 0),
            "medium_solved": data.get("Medium", {}).get("count", 0),
            "hard_solved": data.get("Hard", {}).get("count", 0),
            "institution": info.get("instituteRank", ""),
            "score": info.get("codingScore", 0),
            "monthly_streak": info.get("monthlyScore", 0),
        }
    except Exception:
        return None


# ─────────────────────────────────────────────
# CodeChef  (public profile scrape – JSON endpoint)
# ─────────────────────────────────────────────
def fetch_codechef(username: str) -> dict | None:
    try:
        r = requests.get(
            f"https://www.codechef.com/users/{username}",
            headers={**HEADERS, "Accept": "text/html"},
            timeout=TIMEOUT
        )
        if r.status_code != 200:
            return None
        import re
        html = r.text
        # Extract rating from page
        rating_match = re.search(r'"currentRating":(\d+)', html)
        max_rating_match = re.search(r'"highestRating":(\d+)', html)
        stars_match = re.search(r'"stars":"(\d+\*)"', html)
        solved_match = re.search(r'(\d+)\s*(?:Problems|problems)\s*Solved', html)

        rating     = int(rating_match.group(1))     if rating_match     else 0
        max_rating = int(max_rating_match.group(1)) if max_rating_match else 0
        stars      = stars_match.group(1)           if stars_match      else "–"
        solved     = int(solved_match.group(1))     if solved_match     else 0

        return {
            "platform": "CodeChef",
            "username": username,
            "rating": rating,
            "max_rating": max_rating,
            "stars": stars,
            "total_solved": solved,
        }
    except Exception:
        return None


# ─────────────────────────────────────────────
# Aggregate across all fetched platforms
# ─────────────────────────────────────────────
def aggregate_stats(platform_results: dict) -> dict:
    """
    platform_results: {"LeetCode": {...}, "GitHub": {...}, ...}
    Returns a summary dict used by the dashboard.
    """
    total_solved = 0
    total_easy = total_medium = total_hard = 0
    total_contests = 0
    best_rating = 0
    github_repos = 0
    github_stars = 0
    monthly_activity = {}   # "YYYY-MM" → count (merged across platforms)
    contribution_dates = []  # list of "YYYY-MM-DD" strings

    for plat, data in platform_results.items():
        if not data:
            continue
        total_solved  += data.get("total_solved", 0)
        total_easy    += data.get("easy_solved", 0)
        total_medium  += data.get("medium_solved", 0)
        total_hard    += data.get("hard_solved", 0)
        total_contests += data.get("contests", 0)

        rating = data.get("rating", 0) or data.get("contest_rating", 0)
        if rating and rating > best_rating:
            best_rating = rating

        if plat == "GitHub":
            github_repos = data.get("public_repos", 0)
            github_stars = data.get("total_stars", 0)
            contribution_dates += data.get("contribution_dates", [])

        # merge monthly activity
        for month, cnt in data.get("monthly_activity", {}).items():
            monthly_activity[month] = monthly_activity.get(month, 0) + cnt

        # LeetCode calendar → contribution_dates
        if plat == "LeetCode":
            for ts_str, cnt in data.get("submission_calendar", {}).items():
                try:
                    dt = datetime.utcfromtimestamp(int(ts_str))
                    for _ in range(cnt):
                        contribution_dates.append(dt.strftime("%Y-%m-%d"))
                except Exception:
                    pass

    # Build last-12-months activity array
    today = datetime.utcnow()
    month_labels, month_data = [], []
    for i in range(11, -1, -1):
        dt = datetime(today.year, today.month, 1) - timedelta(days=i*30)
        label = dt.strftime("%b %Y")
        key   = dt.strftime("%Y-%m")
        month_labels.append(dt.strftime("%b"))
        month_data.append(monthly_activity.get(key, 0))

    # Build heatmap: date → count (last 365 days)
    heatmap = {}
    date_counts = {}
    for d in contribution_dates:
        date_counts[d] = date_counts.get(d, 0) + 1

    base = datetime.utcnow().date()
    for i in range(364, -1, -1):
        d = (base - timedelta(days=i)).isoformat()
        heatmap[d] = date_counts.get(d, 0)

    return {
        "total_solved":   total_solved,
        "easy_solved":    total_easy,
        "medium_solved":  total_medium,
        "hard_solved":    total_hard,
        "total_contests": total_contests,
        "best_rating":    best_rating,
        "github_repos":   github_repos,
        "github_stars":   github_stars,
        "month_labels":   month_labels,
        "month_data":     month_data,
        "heatmap":        heatmap,          # {"YYYY-MM-DD": count}
        "platforms":      platform_results, # raw per-platform
    }
