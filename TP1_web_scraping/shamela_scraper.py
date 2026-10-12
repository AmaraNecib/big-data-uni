"""
TP1 - Python Web Scraping
Scrape the full book "نسب معد واليمن الكبير" from the Shamela library.
Book: https://shamela.ws/book/28172

It answers the 4 questions of the assignment:
  1. download all the pages and show the HTML source of the first page
  2. extract the data with BeautifulSoup
  3. save the data to a CSV file with pandas
  4. the CSV has more than 1,000 rows

Run:  python shamela_scraper.py
"""
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BOOK_ID = 28172
LAST_PAGE = 720  # last page number of this book
BASE_URL = f"https://shamela.ws/book/{BOOK_ID}"
CSV_FILE = Path(__file__).parent / "data" / "book_28172.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (TP1 - educational scraping)"}


def download_page(page_number):
    """Download one page of the book. Return (page_number, html or None)."""
    response = requests.get(f"{BASE_URL}/{page_number}", headers=HEADERS, timeout=30)
    return page_number, (response.text if response.status_code == 200 else None)


def extract_page_data(html):
    """Extract the page info and the paragraphs of one page (BeautifulSoup)."""
    soup = BeautifulSoup(html, "html.parser")

    # The title looks like: "ج1 - ص17 - <book> - <chapter> - المكتبة الشاملة"
    # or without a volume:  "ص1 - <book> - <chapter> - المكتبة الشاملة"
    title = soup.title.get_text(strip=True) if soup.title else ""
    parts = [part.strip() for part in title.split(" - ")]
    # a single-volume book has no "ج" in the title, so we use volume 1
    juz = next((part[1:] for part in parts if re.fullmatch(r"ج\d+", part)), "1")
    print_page = next((part[1:] for part in parts if re.fullmatch(r"ص\d+", part)), "")
    chapter = parts[-2] if len(parts) >= 2 else ""

    # The text lives inside <div class="nass">, one paragraph per <p>
    container = soup.select_one("div.nass")
    paragraphs = []
    if container:
        for tag in container.find_all("p"):
            text = tag.get_text(" ", strip=True)
            if text:
                paragraphs.append(text)

    return {
        "page_id": container.get("data-page-id") if container else "",
        "print_page": print_page,
        "juz": juz,
        "chapter": chapter,
        "paragraphs": paragraphs,
    }


def main():
    # 1. download all the pages (a few at a time: fast and still polite)
    with ThreadPoolExecutor(max_workers=8) as pool:
        pages = list(pool.map(download_page, range(1, LAST_PAGE + 1)))

    # 2. extract the data, one row per paragraph
    rows = []
    for page_number, html in pages:
        if html is None:
            print(f"page {page_number}: not found, skipped")
            continue
        if page_number == 1:  # show the HTML source code on the screen
            print("HTML SOURCE OF PAGE 1 (first 1000 characters)")
            print("-" * 60)
            print(html[:1000])
            print("-" * 60)

        page_data = extract_page_data(html)
        for index, text in enumerate(page_data["paragraphs"], start=1):
            rows.append({
                "page_id": page_data["page_id"],
                "print_page": page_data["print_page"],
                "juz": page_data["juz"],
                "chapter": page_data["chapter"],
                "paragraph_no": index,
                "text": text,
            })

    # 3. save the data to a CSV file with pandas
    CSV_FILE.parent.mkdir(exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

    # 4. the file must have at least 1,000 rows
    print(f"\nSaved {len(df)} rows from {df['page_id'].nunique()} pages -> {CSV_FILE}")
    assert len(df) >= 1000, "We need at least 1,000 rows!"
    print("OK: the file has at least 1,000 rows.")


if __name__ == "__main__":
    main()
