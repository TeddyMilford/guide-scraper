# TV Guide Scraper & Generator

This project lets you scrape your [Letterboxd](https://letterboxd.com/) watchlist and generate an interactive, genre-based TV guide as an HTML file.

## Features

- Scrape your Letterboxd watchlist to CSV (`watchlist.csv`)
- Generate a visual, scrollable TV guide by genre for a week

## Python Setup

1. **Install Python 3**
   Download and install Python 3 from [python.org](https://www.python.org/downloads/) if you don't already have it.

2. **(Optional but recommended) Create a virtual environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install required packages:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Run the scraper:**

   ```sh
   python letterboxd_full_scraper.py
   ```
   It will ask you if you want test or full, you can just say full. It will then ask you for your Letterboxd username. This will create a `watchlist.csv` file in the same directory.

5. **Generate the TV guide:**

   ```sh
   python tv_guide_generator.py
    ```
    This will create an `tv_guide.html` file in the same directory.

6. **Open the TV guide:**

    ```sh
    open tv_guide.html
    ```

    Open `tv_guide.html` in your web browser to view your interactive TV guide.
