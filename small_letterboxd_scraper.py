import requests
from bs4 import BeautifulSoup
import json
import time
import re
import csv

MOVIE_URLS = [
    "https://letterboxd.com/film/eddington/",
    "https://letterboxd.com/film/afternoons-of-solitude/",
    "https://letterboxd.com/film/the-mastermind-2025/",
]

def scrape_movie(url):
    print(f"\nFetching: {url}")
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # JSON-LD extraction
    script_tag = soup.find("script", type="application/ld+json")
    if not script_tag or not script_tag.string or not script_tag.string.strip():
        print("  No JSON-LD found or it's empty.")
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

if __name__ == "__main__":
    results = []
    for url in MOVIE_URLS:
        result = scrape_movie(url)
        if result:
            results.append(result)
        print("  Waiting 5 seconds before next request...")
        time.sleep(5)

    # Write to CSV
    if results:
        fieldnames = ["name", "url", "image", "director", "year", "genre", "actors", "runtime_mins"]
        with open("small.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print("\nSaved results to small.csv")
    else:
        print("\nNo results to save.")
