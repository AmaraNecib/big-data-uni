# TP01 – Python Web Scraping Case-study

**University of Eloued** — Faculty of Exact Sciences — Department of Computer Science
Second-year Master: IA & Data Science — Module: **Big Data Analytics**
Academic season: 2026/2027

A simple web-scraping project that fetches a full book from the **Shamela**
library (an educational website), extracts its text with **BeautifulSoup**,
and saves the result to a **CSV** file with **pandas** (more than 1,000 rows).

---

## Website chosen

| | |
|---|---|
| Site | [shamela.ws](https://shamela.ws) – the Arabic "Shamela" library |
| Book | [نسب معد واليمن الكبير – ابن الكلبي](https://shamela.ws/book/28172) |
| Pages | 720 pages |

The assignment asks for **"an educational website"** (no specific site), and
Shamela is an educational text library, so it was chosen as the target.

---

## How the assignment is answered

| # | Question | Where in the code |
|---|----------|-------------------|
| 1 | Fetch the content of all pages and display the HTML source | `fetch_html()` downloads the 720 pages, `main()` prints the source of page 1 |
| 2 | Extract the data with **BeautifulSoup** | `parse_page()` extracts page, chapter and paragraphs |
| 3 | Save the results to **CSV** with **pandas** | `main()` → `df.to_csv("data/shamela_book.csv")` |
| 4 | The file must have **≥ 1,000 rows** | One row per paragraph → **6,642 rows** (`assert len(df) >= 1000`) |

---

## Requirements

* Python 3.x
* `requests`, `beautifulsoup4`, `pandas` (see `requirements.txt`)

## Setup

The virtual environment is named **`tp-01`**:

```bash
# create and activate the environment
python -m venv tp-01

# Windows
tp-01\Scripts\activate
# Linux / macOS
source tp-01/bin/activate

# install the dependencies
pip install -r requirements.txt
```

## Run

```bash
python shamela_scraper.py
```

Output: `data/shamela_book.csv`

### CSV columns

| column | meaning |
|--------|---------|
| `page_id` | sequential page id on the website |
| `print_page` | page number in the printed book (ص) |
| `juz` | volume / part (ج) |
| `chapter` | chapter (chapter of the book) |
| `paragraph_no` | paragraph order inside the page |
| `text` | the paragraph text |

---

## Result

```
Saved 6642 rows from 720 book pages to data/shamela_book.csv
OK: the file has at least 1,000 rows.
```
