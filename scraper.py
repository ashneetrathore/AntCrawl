import re
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import Counter

# Initialize a list of valid domains
domainList = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]
# Initialize a dictionary to store url patterns and associated occurrences
patternLog = dict()
# Initialize a set to store hashes of page content for duplicate detection
seen_hashes = set()
# Initialize a set to store unique URLs, defined by just the URL, discarding the fragment
uniqueURLs = set()
# Initialize a list that stores the url of the longest page in index 0 and the # of words in index 1
longest_page = ["", 0]
# Initialize a Counter object that will store words and associated frequencies
word_freq = Counter()
# Initialize a dictionary to store ics subdomains and an associated count of the unique pages under that subdomain
ics_subdomains = dict()
# Initialize a set of stopwords to ignore when counting words/frequencies
stopwords = {
    'a', 'also', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and',
    'any', 'are', "aren", 'as', 'at', 'be', 'because', 'been', 'before', 'being',
    'below', 'between', 'both', 'but', 'by', "can", 'cannot', 'could', "couldn",
    'did', "didn", 'do', 'does', "doesn", 'doing', "don", 'down', 'during',
    'each', 'few', 'for', 'from', 'further', 'had', "hadn", 'has', "hasn",
    'have', 'having', 'he', 'her', 'here',
    'hers', 'herself', 'him', 'himself', 'his', 'how', 'i',
    'if', 'in', 'into', 'is', "isn", 'it',
    'its', 'itself', "let", 'me', 'may', 'more', 'most', "mustn", 'my', 'myself',
    'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought',
    'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan", 'she',
    'should', "shouldn", 'so', 'some', 'such',
    'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves',
    'then', 'there', 'these', 'they',
    'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
    'very', 'was', "wasn", 'we', 'were',
    "weren", 'what', 'when', 'where', 'which',
    'while', 'who', 'whom', 'why', 'will', 'with', 'would',
    "wouldn", 'you', 'your', 'yours',
    'yourself', 'yourselves', 'll', 're', 've'
}

def scraper(url, resp):
    # Get a list of links that are scraped from the resp
    links = extract_next_links(url, resp)
    # Write to files for report analytics
    write_num_unique_urls()
    write_longest_page()
    write_top_50()
    write_subdomains()
    return links

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # If response status is 200 --> OK
    if resp.status == 200:
        # If page has no content, return []
        if not resp.raw_response or not resp.raw_response.content:
            return []

        # If HTML page cannot be decoded into utf-8 string, return []
        try:
            decoded = resp.raw_response.content.decode('utf-8')
        except UnicodeError:
            return []

        # Extract text content from HTML page
        soup = BeautifulSoup(decoded, 'html.parser')
        text_content = soup.get_text(separator=" ", strip=True)

        # If page has low information, is too large, or is a duplicate, return []
        if (has_low_info(text_content) or
            is_large_file(resp.raw_response) or
            is_duplicate(text_content)
        ):
            return []

        # Update the longest_page and word_freq variables
        update_longest_page(url, text_content)
        update_top_50(text_content)

        # Initialize a list to store links scraped from page
        valid_links = []
        # Iterate over the <a> tags in the HTML (getting links on the page)
        for link in soup.find_all('a'):
            new_link = link.get("href")
            # Form an absolute URL
            absolute_url = urljoin(url, new_link)
            # Get rid of fragment part in URL
            absurl = urlparse(absolute_url)._replace(fragment="").geturl()

            # Check if url has a valid domain, is unique, and is valid overall, and if so, add to the list of scraped links
            if is_valid_domain_and_unique(absurl) and is_valid(absurl):
                valid_links.append(absurl)

        return valid_links
    # If response status is 300 --> Redirect
    elif resp.status == 300:
        return extract_next_links(resp.raw_response.url, resp)
    # If response status is any other code --> Error -> Return []
    else:
        return []

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        # If url doesn't have http or https scheme, url is not valid
        if parsed.scheme not in set(["http", "https"]):
            return False
        # If url has any of the below file extensions, url is not valid
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|img|apk|sql|war|ppsx)$", parsed.path.lower()):
            return False

        # If url needs to be filtered out or is a trap, url is not valid
        if (
                filter_out(parsed) or
                is_trap(parsed)
        ):
            return False
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def has_low_info(content):
    # Gets a list of all the words from a content string
    # If the length of the list is below 100 --> page has low information --> Returns True
    words = re.findall(r"\w+", content)

    if len(words) < 100:
        return True
    else:
        return False

def is_large_file(raw_response):
    # Gets the size of a file
    # If the file is 1MB or above --> file is too large --> Returns True
    content_size = raw_response.headers.get("Content-Length")
    if content_size and int(content_size) >= 10 ** 6:
        return True
    else:
        return False

def is_duplicate(content):
    # Assigns a hash to a content string
    # If hash has been seen before --> duplicate detected --> Returns True
    hashed_page = hashlib.md5(content.encode('utf-8')).hexdigest()
    if hashed_page in seen_hashes:
        return True
    else:
        seen_hashes.add(hashed_page)
        return False

def is_valid_domain_and_unique(url):
    parsed = urlparse(url)
    valid_domain = False
    unique_url = False

    # Iterate through the domain list to find a matching valid domain
    for domain in domainList:
        if parsed.netloc.endswith(domain):
            # Matching domain has been found --> valid_domain is set to True
            valid_domain = True
            if url not in uniqueURLs:
                # url is a unique URL --> unique_url is set to True
                uniqueURLs.add(url)
                unique_url = True
                if parsed.netloc.endswith(".ics.uci.edu"):
                    # Domain is a subdomain of .ics.uci.edu AND page is unique --> update the ics_subdomains variable
                    update_subdomain(parsed)
            break
    # If url has a valid domain AND is a unique url, the url is valid
    return valid_domain and unique_url

def filter_out(parsed_url):
    # Filter out calendar pages
    if (re.search(r"^/events.*\d{4}-\d{2}.*$", parsed_url.path) or
        re.search(r"^/events/week.*$", parsed_url.path) or
        re.search(r"^/events/list.*$", parsed_url.path)):
            return True
    # Filter out gitlab, ML archives, and cert
    if (
            parsed_url.netloc.startswith("gitlab.ics.uci.edu")
            or parsed_url.netloc.startswith("archive.ics.uci.edu")
            or parsed_url.netloc.startswith("www.cert.ics.uci.edu")
    ):
        return True
    # Filter out doku.php
    if parsed_url.path.startswith("/doku.php"):
        return True
    return False

def is_trap(parsed_url):
    # Assemble a url pattern using the scheme + netloc + path part of the url
    pattern = (parsed_url.scheme +
               "://" +
               parsed_url.netloc +
               parsed_url.path
               )
    # If pattern has been seen before, increment its count. Otherwise, initialize pattern to 1
    if pattern in patternLog:
        patternLog[pattern] += 1
    else:
        patternLog[pattern] = 1

    # If pattern occurrence hits 15 or above, trap is detected --> Returns True
    if patternLog[pattern] >= 15:
        return True
    else:
        return False

def update_subdomain(parsed):
    # Remove any spaces from subdomain and convert to lowercase
    subdomain = parsed.netloc.strip().lower()
    # If subdomain of page has been seen before, increment its count. Otherwise, initialize the subdomain to 1
    if subdomain in ics_subdomains:
        ics_subdomains[subdomain] += 1
    else:
        ics_subdomains[subdomain] = 1

def update_longest_page(url, content):
    # Get a list of all the words from a content string (words = alphabet sequences)
    # If the length of the list is larger than the current longest page length, update the longest_page variable
    len_content = len(re.findall(r"[a-zA-Z]+", content))
    if len_content > longest_page[1]:
        longest_page[0] = url
        longest_page[1] = len_content

def update_top_50(content):
    # Update the overall word_freq variable with the tokens gathered from one page
    # .update() from Counter class will add values for the same keys together
    word_freq.update(extract_token_dict(content))

def extract_token_dict(content_string):
    # Get a list of all tokens from a content string (token = alphabet sequences of length 2 or greater)
    tokens = re.findall(r'[a-zA-Z]{2,}', content_string.strip())
    # Filter out stopwords from list and convert each token in the list to lowercase
    filtered_tokens = [token.lower() for token in tokens if token.lower() not in stopwords]
    # Call compute_word_frequencies to get dictionary of <token, frequency> pairs
    return compute_word_frequencies(filtered_tokens)

def compute_word_frequencies(tokens: list) -> dict:
    # Returns a dictionary that maps the tokens in the list to the number of their occurrences
    word_count = Counter()
    for t in tokens:
        if word_count.get(t) is None:
            word_count[t] = 1
        else:
            word_count[t] += 1
    return word_count

def write_num_unique_urls():
    # Write number of unique URLs to file
    unique_url_count = len(uniqueURLs)
    with open("unique_url.txt", "w") as file:
        file.write(f"{unique_url_count}\n")

def write_longest_page():
    # Write the longest page and the # of words on that page to file
    with open("longest_page.txt", "w") as file:
        file.write(f"{longest_page[0]}:{longest_page[1]}\n")

def write_top_50():
    # Write the top 50 words across all pages to file
    # .most_common(x) from Counter class gets the top x words, in order of decreasing frequency
    with open("top50.txt", "w") as file:
        for word, freq in word_freq.most_common(50):
            file.write(f"{word}:{freq}\n")

def write_subdomains():
    # Write the ics.uci.edu subdomains (in alphabetical order) and their associated unique pages to file
    with open("subdomain.txt", "w") as file:
        for subdomain, count in sorted(ics_subdomains.items()):
            file.write(f"{subdomain}:{count}\n")
