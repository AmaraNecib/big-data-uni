# Big Data Analytics – TP01 (Python Web Scraping)

**University of Eloued** — Faculty of Exact Sciences — Department of Computer Science
Second-year Master: IA & Data Science — Module: **Big Data Analytics**
Academic season: 2026/2027

Web-scraping project: fetch a full book from the **Shamela** library
(an educational website), extract the text with **BeautifulSoup** and save it
to **CSV** with **pandas** (more than 1,000 rows).

---

## Repository structure

```
big-data-uni/
├── TP1_web_scraping/                 # the main TP1 solution
│   ├── shamela_scraper_28172.py       # scraper for book 28172
│   ├── data/book_28172.csv
│   └── README.md
├── TP1_extra/                        # the extra part: same work, 2 more books
│   ├── shamela_scraper_2122.py        # scraper for book 2122
│   ├── shamela_scraper_36087.py       # scraper for book 36087
│   ├── data/book_2122.csv
│   ├── data/book_36087.csv
│   └── README.md
├── requirements.txt
└── tp-01/                            # python virtual environment
```

Each scraper is named after the **book id** it downloads, and writes its own
CSV file in the `data/` folder.

| folder | book | pages | rows |
|--------|------|------:|-----:|
| TP1_web_scraping | [نسب معد واليمن الكبير](https://shamela.ws/book/28172) | 720 | 6,642 |
| TP1_extra | [شرح الآجرومية](https://shamela.ws/book/2122) | 302 | 1,568 |
| TP1_extra | [فتح رب البرية في شرح نظم الآجرومية](https://shamela.ws/book/36087) | 649 | 2,000 |

---

## Setup

The virtual environment is named **`tp-01`**.

```bash
python -m venv tp-01

# Windows
tp-01\Scripts\activate
# Linux / macOS
source tp-01/bin/activate

pip install -r requirements.txt
```

## Run

```bash
cd TP1_web_scraping
python shamela_scraper_28172.py

cd ../TP1_extra
python shamela_scraper_2122.py
python shamela_scraper_36087.py
```
