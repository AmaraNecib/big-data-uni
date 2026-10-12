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
├── TP1_web_scraping/        # the main TP1 solution  (book 28172)
│   ├── shamela_scraper.py
│   ├── data/book_28172.csv
│   └── README.md
├── TP1_extra/               # the extra part, same work  (book 2122)
│   ├── shamela_scraper.py
│   ├── data/book_2122.csv
│   └── README.md
├── requirements.txt
└── tp-01/                   # python virtual environment
```

* **TP1_web_scraping** – the TP1 case-study, on the book
  [نسب معد واليمن الكبير](https://shamela.ws/book/28172) (720 pages → 6,642 rows).
* **TP1_extra** – the extra part (for more marks), same work on another book
  [شرح الآجرومية](https://shamela.ws/book/2122) (302 pages → 1,568 rows).

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
python shamela_scraper.py

cd ../TP1_extra
python shamela_scraper.py
```

Each script writes its CSV file inside its own `data/` folder.
