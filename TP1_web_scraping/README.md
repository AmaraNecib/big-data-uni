# TP1 – Python Web Scraping (main solution)

Scrape the **full book** *نسب معد واليمن الكبير* from the Shamela library (an
educational website) and save all of its text to a CSV file.

| | |
|---|---|
| Website | [shamela.ws](https://shamela.ws) — the Arabic "Shamela" library |
| Book | [نسب معد واليمن الكبير – ابن الكلبي](https://shamela.ws/book/28172) |
| Pages | 720 |
| Result | **6,642 rows** in `data/book_28172.csv` |

## The assignment questions

| # | Question | Answer in the code |
|---|----------|--------------------|
| 1 | Fetch all pages and show the HTML source | `download_page()` downloads the 720 pages, `main()` prints the source of page 1 |
| 2 | Extract the data with **BeautifulSoup** | `extract_page_data()` |
| 3 | Save to **CSV** with **pandas** | `main()` → `df.to_csv(...)` |
| 4 | At least **1,000 rows** | one row per paragraph → 6,642 rows (`assert len(df) >= 1000`) |

## How the code works

The program is only **3 functions**, one job each:

1. **`download_page(page_number)`** — downloads one page
   (`https://shamela.ws/book/28172/<n>`) with `requests` and returns the HTML.
   The pages are downloaded 8 at a time using a `ThreadPoolExecutor`, which is
   fast but still polite to the server.

2. **`extract_page_data(html)`** — parses one page with BeautifulSoup:
   * the page title gives the volume and the chapter, e.g.
     `ج1 - ص17 - <book> - <chapter> - المكتبة الشاملة`;
   * the printed page number is read from the site's own `data-page-num`
     attribute, which works even for pages without `ص` in the title;
   * the text lives inside `<div class="nass">`, one paragraph per `<p>`,
     so we read every `<p>` and keep its text.

3. **`main()`** — drives everything: downloads the pages, builds **one row per
   paragraph**, saves the rows to CSV with pandas, then checks the 1,000-row rule.

## Run

```bash
python shamela_scraper_28172.py
```

## CSV columns

| column | meaning |
|--------|---------|
| `page_id` | sequential page id on the website |
| `print_page` | page number in the printed book (ص) |
| `juz` | volume / part (ج); `1` for a single-volume book |
| `chapter` | chapter of the book |
| `paragraph_no` | paragraph order inside the page |
| `text` | the paragraph text |
