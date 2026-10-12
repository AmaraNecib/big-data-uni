# TP1 (extra) – Python Web Scraping

The **extra part** of TP1: exactly the same work as the main solution, but for
another book, so it earns extra marks.

| | |
|---|---|
| Website | [shamela.ws](https://shamela.ws) — the Arabic "Shamela" library |
| Book | [شرح الآجرومية – حسن حفظي](https://shamela.ws/book/2122) |
| Pages | 302 |
| Result | **1,568 rows** in `data/book_2122.csv` |

## The assignment questions

| # | Question | Answer in the code |
|---|----------|--------------------|
| 1 | Fetch all pages and show the HTML source | `download_page()`, printed in `main()` |
| 2 | Extract the data with **BeautifulSoup** | `extract_page_data()` |
| 3 | Save to **CSV** with **pandas** | `main()` → `df.to_csv(...)` |
| 4 | At least **1,000 rows** | one row per paragraph → 1,568 rows |

## How the code works

Same three functions as the main solution:

1. **`download_page(page_number)`** — downloads one page
   (`https://shamela.ws/book/2122/<n>`) and returns its HTML.
2. **`extract_page_data(html)`** — reads the title for the page number and the
   chapter, then reads every `<p>` inside `<div class="nass">`.
   This book has no volume part in its title (`ص1 - <book> - <chapter> - ...`),
   so the code finds `ص` and `ج` wherever they are instead of assuming a fixed
   order; when there is no `ج`, the book is single-volume and `juz` is set to `1`.
3. **`main()`** — downloads the pages, builds one row per paragraph, saves the
   CSV with pandas and checks the 1,000-row rule.

## Run

```bash
python shamela_scraper.py
```

## CSV columns

`page_id`, `print_page`, `juz`, `chapter`, `paragraph_no`, `text`.
