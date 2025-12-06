## :ant: ANT CRAWL

### :open_book: OVERVIEW
Date: February 2025\
Developer(s): Ashneet Rathore, Nura Ahmed Nasir Abdalla\
Based on assignment instructions from Prof. Iftekhar Ahmed and Prof. Cristina Lopes

Ant Crawl is a web crawler that fetches pages from a Spacetime cache server containing 35,000+ links. It starts from some seed urls and systematically follows links, hence the name "Ant Crawl", inspired by how ants methodically explore a vast space. A custom scraper is used to extract and filter new urls to visit. The crawler continues until all reachable pages are processed, adhering to common practices used in modern web crawlers to ensure efficient and responsible operation.

### :classical_building: ARCHITECTURE
The program follows a custom **frontier-worker architecture** implemented in **Python**. In this design, the frontier serves as a queue of urls to be visited, while a worker fetches pages from the frontier, performs necessary processing, and stores the results.

Upon launch, the program receives a cache host and port from the Spacetime server and instantiates a crawler. When the crawler starts, a worker takes a link from the frontier, downloads it from the cache server, and passes the response (which contains the page content) to a scraper. The **scraper** extracts links from the page and adds valid new urls to the frontier, and the url that was downloaded is marked as visited. This cycle continues until the frontier has no more urls to download.

The scraper applies two types of filtering: url-based and content-based. Links are first subjected to low cost **url-based filtering**, where invalid urls, such as those with undesirable file extensions, are never added to the frontier. The program includes a **trap detection** scheme that logs recurring url patterns to identify infinite traps. Once a worker retrieves a url from the frontier and downloads the page, **content-based filtering** is applied, checking for page size, duplicates, low information, etc.

The program additionally gathers and stores analytics on the crawled pages, including the count of unique urls, the page with the most words, and the top 50 most frequent words (excluding common words like "the" or "is"). These analytics are written to output files created at runtime.

### :open_file_folder: PROJECT FILE STRUCTURE
```bash
AntCrawl/
│── launch.py         # Connects to the cache server and starts the crawler
│── scraper.py        # Extracts and filters URLs from downloaded pages
│── crawler/          
│   │── __init__.py   # Defines the Crawler class
│   │── frontier.py   # Defines the Frontier class
│   └── worker.py     # Defines the Worker class
│── packages/         # Contains external dependencies
│── utils/            # Contains helper modules for the crawler
│── config.ini        # Stores configuration settings
│── README.md         # Project documentation
└── .gitignore        # Specifies files and folders that shouldn't be included in the repo
```

> [!WARNING]
> The original Spacetime cache server is no longer live. These instructions show how the project was configured and ran, but the crawler **cannot be executed** anymore. The upcoming instructions are for reference only.

### :hammer: CONFIGURATION
**1. Clone the repository**
```bash
git clone https://github.com/ashneetrathore/AntCrawl.git
cd AntCrawl
```

**2. Ensure Python 3.6+ and pip are installed**
```bash
python3 --version
python3 -m pip --version
```

**3. Install dependencies**
```bash
python -m pip install packages/spacetime-2.1.1-py3-none-any.whl
python -m pip install -r packages/requirements.txt
```

**4. Open `config.ini` and assign a value of the format `IR UW25 uci-id1,uci-2` to `USERAGENT`**
```ini
# Example assignment w/h team members' UCI IDs
USERAGENT = IR UW25 12345678,87654321
```

### :rocket: EXECUTION
**Run the crawler**
```bash
python3 launch.py
```
To restart the crawler from the seed url, use the following command
```bash
python3 launch.py --restart
```