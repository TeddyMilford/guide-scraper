import csv
import random
from collections import defaultdict
from datetime import datetime, timedelta

GENRES = sorted([
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Family",
    "Fantasy", "History", "Horror", "Music", "Mystery", "Romance", "Science Fiction", "Thriller",
    "TV Movie", "War", "Western"
])

BLOCK_WIDTH_PER_HOUR = 80  # px
BLOCK_WIDTH_PER_MINUTE = BLOCK_WIDTH_PER_HOUR / 60  # ≈ 1.33 px

def parse_movies(filename):
    movies_by_genre = defaultdict(list)
    action_movies = []
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['name'].strip()
            year = row['year'][:4] if row['year'] else ""
            genres = [g.strip() for g in row['genre'].split(',') if g.strip() in GENRES]
            try:
                runtime = int(row['runtime_mins'])
            except (ValueError, TypeError):
                runtime = 90
            movie = {"title": title, "year": year, "runtime": runtime}
            for genre in genres:
                movies_by_genre[genre].append(movie)
            if "Action" in genres:
                action_movies.append(movie)
    return movies_by_genre, action_movies

def schedule_week(movies, week_start, week_end):
    schedule = []
    time_cursor = week_start
    idx = 0
    n = len(movies)
    while time_cursor < week_end and n > 0:
        movie = movies[idx % n]
        movie_start = time_cursor
        movie_end = movie_start + timedelta(minutes=movie["runtime"])
        if movie_end > week_end:
            break
        schedule.append({
            "title": movie["title"],
            "year": movie["year"],
            "start": movie_start,
            "end": movie_end,
            "runtime": movie["runtime"]
        })
        time_cursor = movie_end
        idx += 1
    return schedule

def build_html(schedule_by_genre, week_start):
    week_end = week_start + timedelta(days=7)
    total_minutes = int((week_end - week_start).total_seconds() // 60)
    total_width = int(total_minutes * BLOCK_WIDTH_PER_MINUTE)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TV Guide - Movie Genres</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .guide-container { display: flex; height: calc(100vh - 80px); width: 100%; border: 1px solid #e5e7eb; background: #fff; }
        .sidebar { width: 120px; min-width: 120px; background: #f3f4f6; border-right: 2px solid #e5e7eb; overflow-y: auto; overflow-x: hidden; scrollbar-width: none; -ms-overflow-style: none; }
        .sidebar::-webkit-scrollbar { display: none; }
        .guide-scroll { flex: 1; overflow-x: auto; overflow-y: auto; position: relative; }
        .time-axis { display: flex; position: sticky; top: 0; background: #fff; z-index: 30; }
        .time-spacer { height: 32px; min-width: 0; max-width: 0; background: #f9fafb; }
        .time-label { height: 32px; width: 80px; min-width: 80px; max-width: 80px; text-align: center; font-size: 0.75rem; border-right: 1px solid #e5e7eb; background: #f9fafb; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .guide-row { display: flex; align-items: center; gap: 2px; height: 60px; border-bottom: 1px solid #e5e7eb; min-width: min-content; }
        .genre-label { width: 120px; min-width: 120px; max-width: 120px; background: #f3f4f6; font-weight: bold; padding: 0.5rem; text-align: right; display: flex; align-items: center; justify-content: flex-end; height: 60px; border-bottom: 1px solid #e5e7eb; }
        .sidebar-header { width: 120px; min-width: 120px; max-width: 120px; height: 32px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; z-index: 10; }
        .movie-block { background: #eff6ff; border: 1px solid #93c5fd; border-radius: 0.25rem; padding: 0.25rem 0.5rem; box-sizing: border-box; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; font-size: 0.875rem; flex-shrink: 0; }
        .current-time-bar { position: absolute; top: 0; bottom: 0; width: 3px; background: #ef4444; z-index: 50; pointer-events: none; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="flex items-center justify-between py-4 px-8 bg-white border-b-2 border-gray-300">
        <div class="text-4xl font-bold">Letterboxd TV Guide</div>
        <div id="current-datetime" class="text-xl text-gray-700 font-mono"></div>
    </div>
    <div class="guide-container">
        <div class="sidebar">
            <div class="sidebar-header"></div>
"""
    # Sidebar genre labels
    for genre in GENRES:
        html += f'<div class="genre-label">{genre}</div>\n'

    html += """        </div>
        <div class="guide-scroll" id="guide-scroll">
"""
    # Time axis: every hour
    html += '<div class="time-axis">'
    html += '<div class="time-spacer"></div>'
    for hour in range(0, 7*24):
        dt = week_start + timedelta(hours=hour)
        html += f'<div class="time-label">{dt.strftime("%a %I%p")}</div>'
    html += '</div>\n'

    # Guide rows
    for genre in GENRES:
        html += '<div class="guide-row">'
        for movie in schedule_by_genre[genre]:
            start_min = int((movie["start"] - week_start).total_seconds() // 60)
            end_min = int((movie["end"] - week_start).total_seconds() // 60)
            block_width = max(20, int((end_min - start_min) * BLOCK_WIDTH_PER_MINUTE))
            html += (
                f'<div class="movie-block" style="width:{block_width}px;" title="{movie["title"]} ({movie["year"]}) - {movie["start"].strftime("%a %I:%M %p")} to {movie["end"].strftime("%I:%M %p")} ({movie["runtime"]} mins)">'
                f'<div class="font-semibold text-blue-900">{movie["title"]}</div>'
                f'<div class="text-xs text-gray-600">{movie["year"]} • {movie["runtime"]}m</div>'
                f'</div>'
            )
        html += '</div>\n'

    # Overlay bar for current time
    html += f"""
    <div id="current-time-bar" class="current-time-bar" style="display:none;"></div>
        </div>
    </div>
    <script>
    function updateCurrentDateTime() {{
        const now = new Date();
        const options = {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                          hour: '2-digit', minute: '2-digit', second: '2-digit' }};
        document.getElementById('current-datetime').textContent = now.toLocaleString(undefined, options);
    }}
    updateCurrentDateTime();
    setInterval(updateCurrentDateTime, 1000);

    function updateCurrentTimeBar() {{
        const weekStart = new Date(Date.UTC(2000,0,2,0,0,0)); // Sunday midnight
        const now = new Date();
        const offsetDays = now.getDay();
        const offsetMinutes = now.getHours() * 60 + now.getMinutes();
        const totalOffsetMinutes = offsetDays * 24 * 60 + offsetMinutes;
        const pxPerMinute = {BLOCK_WIDTH_PER_MINUTE};
        const left = totalOffsetMinutes * pxPerMinute; // No offset needed with sidebar layout
        const bar = document.getElementById('current-time-bar');
        bar.style.left = left + 'px';
        bar.style.display = 'block';
    }}
    updateCurrentTimeBar();
    const container = document.getElementById('guide-scroll');
    const bar = document.getElementById('current-time-bar');
    const barLeft = parseFloat(bar.style.left);
    container.scrollLeft = barLeft - (window.innerWidth * 0.25);

    // Synchronize vertical scrolling between sidebar and content
    const sidebar = document.querySelector('.sidebar');
    container.addEventListener('scroll', function() {{
        sidebar.scrollTop = container.scrollTop;
    }});

    setInterval(updateCurrentTimeBar, 60 * 1000);
    </script>
</body>
</html>
"""
    return html

if __name__ == "__main__":
    movies_by_genre, action_movies = parse_movies('test_full.csv')
    # movies_by_genre, action_movies = parse_movies('watchlist.csv')
    week_start = datetime(2000, 1, 2, 0, 0, 0)  # Sunday midnight
    week_end = week_start + timedelta(days=7)
    schedule_by_genre = {}
    for genre in GENRES:
        movies = movies_by_genre.get(genre, [])
        if not movies:
            movies = action_movies if action_movies else []
        random.shuffle(movies)
        schedule = schedule_week(movies, week_start, week_end)
        schedule_by_genre[genre] = schedule
    html = build_html(schedule_by_genre, week_start)
    with open('tv_guide.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("TV guide generated as tv_guide.html")
