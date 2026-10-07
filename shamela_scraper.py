import re
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from bs4 import BeautifulSoup

BOOK_ID = 28172
LAST_PAGE = 720  # the highest page number of this book
BASE_URL = f"https://shamela.ws/book/{BOOK_ID}"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_html(number: int) -> tuple[int, str | None]:
    """Q1: download the HTML source code of one page (None if it does not exist)."""
    response = requests.get(f"{BASE_URL}/{number}", headers=HEADERS, timeout=30)
    if response.status_code != 200:
        return number, None
    return number, response.text


def parse_page(html: str) -> dict:
    """Q2: use BeautifulSoup to extract the page number, chapter and paragraphs."""
    soup = BeautifulSoup(html, "html.parser")

    # The page title looks like: "ج1 - ص17 - <book> - <chapter> - المكتبة الشاملة"
    title = soup.title.get_text(strip=True) if soup.title else ""
    juz, print_page, chapter = "", "", ""
    match = re.match(r"^ج(\d+) - ص(\d+) - (.+)$", title)
    if match:
        juz, print_page = match.group(1), match.group(2)
        parts = [p.strip() for p in match.group(3).split(" - ")]
        chapter = parts[-2] if len(parts) >= 2 else ""

    # The text lives inside a <div class="nass">, one paragraph per <p>
    container = soup.select_one("div.nass")
    paragraphs = []
    if container:
        for p in container.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                paragraphs.append(text)

    page_id = (container.get("data-page-id") if container else "") or ""
    return {"page_id": page_id, "print_page": print_page, "juz": juz,
            "chapter": chapter, "paragraphs": paragraphs}


def main() -> None:
    # download the 720 pages (a few at a time to keep it fast but polite)
    with ThreadPoolExecutor(max_workers=8) as pool:
        pages = list(pool.map(fetch_html, range(1, LAST_PAGE + 1)))

    # Q2 + one row per paragraph (so we have more than 1,000 rows)
    rows = []
    for number, html in sorted(pages):
        if html is None:
            print(f"page {number}: not found, skipped")
            continue
        if number == 1:  # Q1: show the HTML source code on the screen
            print("HTML SOURCE CODE OF PAGE 1 (first 1000 characters)")
            print("-" * 60)
            print(html[:1000])
            print("-" * 60)
        data = parse_page(html)
        for position, text in enumerate(data["paragraphs"], start=1):
            rows.append({
                "page_id": data["page_id"],
                "print_page": data["print_page"],
                "juz": data["juz"],
                "chapter": data["chapter"],
                "paragraph_no": position,
                "text": text,
            })

    # Q3: save the results to a CSV file with pandas
    df = pd.DataFrame(rows)
    df.to_csv("data/shamela_book.csv", index=False, encoding="utf-8-sig")

    # Q4: check that we have at least 1,000 rows
    pages_count = df["page_id"].nunique()
    print(f"\nSaved {len(df)} rows from {pages_count} book pages to data/shamela_book.csv")
    assert len(df) >= 1000, "We need at least 1000 rows!"
    print("OK: the file has at least 1,000 rows.")


if __name__ == "__main__":
    main()
