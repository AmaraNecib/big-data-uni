# TP1 (extra) – Python Web Scraping

The **extra part** of TP1: exactly the same work as the main solution, but for
two more books, so it earns extra marks. Each book has its own scraper file,
named after the book id, and its own CSV file.

| script | book | pages | rows |
|--------|------|------:|-----:|
| `shamela_scraper_2122.py` | [شرح الآجرومية – حسن حفظي](https://shamela.ws/book/2122) | 302 | 1,568 |
| `shamela_scraper_36087.py` | [فتح رب البرية في شرح نظم الآجرومية](https://shamela.ws/book/36087) | 649 | 2,000 |

## The assignment questions

| # | Question | Answer in the code |
|---|----------|--------------------|
| 1 | Fetch all pages and show the HTML source | `download_page()`, printed in `main()` |
| 2 | Extract the data with **BeautifulSoup** | `extract_page_data()` |
| 3 | Save to **CSV** with **pandas** | `main()` → `df.to_csv(...)` |
| 4 | At least **1,000 rows** | one row per paragraph |

## How the code works

Both scripts use the same three functions:

1. **`download_page(page_number)`** — downloads one page
   (`https://shamela.ws/book/<id>/<n>`) and returns its HTML.
2. **`extract_page_data(html)`** — reads the title for the volume and the
   chapter, reads the printed page number from the `data-page-num` attribute,
   then reads every `<p>` inside `<div class="nass">`.
   These books have no volume part in their titles
   (`ص1 - <book> - <chapter> - ...`), so the code finds `ج` wherever it is and
   defaults `juz` to `1` when the book is single-volume.
3. **`main()`** — downloads the pages, builds one row per paragraph, saves the
   CSV with pandas and checks the 1,000-row rule.

Only the three constants at the top change from one book to another
(`BOOK_ID`, `LAST_PAGE`, `CSV_FILE`).

## Run

```bash
python shamela_scraper_2122.py
python shamela_scraper_36087.py
```

## CSV columns

`page_id`, `print_page`, `juz`, `chapter`, `paragraph_no`, `text`.
