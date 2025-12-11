import requests
from bs4 import BeautifulSoup
import json
import time
import re
import csv

BASE_URL = "https://letterboxd.com"

def get_watchlist_movies(username):
    """Scrape all movies from a user's watchlist, return dict keyed by film slug."""
    movies = {}
    page = 1
    while True:
        url = f"{BASE_URL}/{username}/watchlist/page/{page}/"
        print(f"Fetching watchlist page: {url}")
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        griditems = soup.select("li.griditem")
        if not griditems:
            break
        for li in griditems:
            rc = li.select_one('div.react-component[data-item-name]')
            if rc:
                slug = rc.get("data-item-link")
                film_id = rc.get("data-film-id")
                name = rc.get("data-item-name")
                year = ""
                m = re.match(r"^(.*)\s+\((\d{4})\)$", name)
                if m:
                    name, year = m.group(1), m.group(2)
                movies[slug] = {
                    "film_id": film_id,
                    "slug": slug,
                    "name": name,
                    "year": year,
                }
        # Pagination: check for next page
        next_link = soup.select_one('a.next')
        if not next_link:
            break
        page += 1
        print("  Waiting 10 seconds before next page request...(Rate limiting protection)")
        time.sleep(10)
    print(f"Found {len(movies)} movies in watchlist.")
    return movies

def get_movie_details(slug):
    url = BASE_URL + slug
    print(f"Fetching movie: {url}")
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    script_tag = soup.find("script", type="application/ld+json")
    if not script_tag or not script_tag.string or not script_tag.string.strip():
        print(f"  No JSON-LD found or it's empty for {slug}")
        return None
    raw_json = script_tag.string.strip()
    if raw_json.startswith("/* <![CDATA[ */"):
        raw_json = raw_json.replace("/* <![CDATA[ */", "").replace("/* ]]> */", "").strip()
    try:
        data = json.loads(raw_json)
    except Exception as e:
        print(f"  Error parsing JSON-LD: {e}")
        return None

    # Runtime extraction
    runtime = ""
    runtime_tag = soup.find("p", class_="text-link text-footer")
    if runtime_tag:
        m = re.search(r"(\d+)\s*mins", runtime_tag.get_text())
        if m:
            runtime = m.group(1)
    data["runtime_mins"] = runtime

    # Flatten some fields for CSV
    director = ""
    if "director" in data:
        if isinstance(data["director"], list):
            director = ", ".join([d["name"] for d in data["director"]])
        else:
            director = data["director"]["name"]
    genre = ", ".join(data.get("genre", [])) if isinstance(data.get("genre"), list) else data.get("genre", "")
    actors = ", ".join([a["name"] for a in data.get("actors", [])]) if "actors" in data else ""

    return {
        "name": data.get("name", ""),
        "url": data.get("url", url),
        "image": data.get("image", ""),
        "director": director,
        "year": data.get("dateCreated", ""),
        "genre": genre,
        "actors": actors,
        "runtime_mins": runtime,
    }

def test_scrape_first_page(username=""):
    """Scrape only the first page of a user's watchlist for testing."""
    if not username:
        username = input("Enter your Letterboxd username for test: ").strip()
    movies = {}
    url = f"{BASE_URL}/{username}/watchlist/"
    print(f"Fetching first watchlist page: {url}")
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    griditems = soup.select("li.griditem")
    for li in griditems:
        rc = li.select_one('div.react-component[data-item-name]')
        if rc:
            slug = rc.get("data-item-link")
            film_id = rc.get("data-film-id")
            name = rc.get("data-item-name")
            year = ""
            m = re.match(r"^(.*)\s+\((\d{4})\)$", name)
            if m:
                name, year = m.group(1), m.group(2)
            movies[slug] = {
                "film_id": film_id,
                "slug": slug,
                "name": name,
                "year": year,
            }
    print(f"Found {len(movies)} movies on first page.")

    results = []
    for slug, info in movies.items():
        details = get_movie_details(slug)
        if details:
            results.append(details)
        print("Waiting 15 seconds before next request...(Rate limiting protection)")
        time.sleep(15)

    # Write to CSV
    if results:
        fieldnames = ["name", "url", "image", "director", "year", "genre", "actors", "runtime_mins"]
        with open("watchlist.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print("\nSaved test results to watchlist.csv")
    else:
        print("\nNo results to save.")


if __name__ == "__main__":
    mode = input("Enter 'test' for test mode (first page only) or 'full' for full scrape: ").strip().lower()
    if mode == "test":
        test_scrape_first_page()
        exit(0)
    username = input("Enter your Letterboxd username: ").strip()
    movies = get_watchlist_movies(username)
    results = []
    for slug, info in movies.items():
        url = BASE_URL + slug
        details = get_movie_details(slug)
        if details:
            results.append(details)
        print("  Waiting 15 seconds before next request...(Rate limiting protection)")
        time.sleep(15)

    # Write to CSV
    if results:
        fieldnames = ["name", "url", "image", "director", "year", "genre", "actors", "runtime_mins"]
        with open("watchlist.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print("\nSaved results to watchlist.csv")
    else:
        print("\nNo results to save.")
