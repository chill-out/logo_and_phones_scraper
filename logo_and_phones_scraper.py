from multiprocessing import Pool
import json
import sys
from bs4 import BeautifulSoup
import phonenumbers
import requests
import re 
from urllib.parse import urljoin, urlparse

class LogoAndPhonesScraper():
    def __init__(self, urls) -> None:
        self.urls = urls
        self.websites_data = []
        self.headers = self._get_headers()
        self.phone_regex = re.compile('^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$|^\+?\(?[0-9]{1,4}\)?[0-9 -\.]+$')
        # self.phone_regex = re.compile('(?:(^?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$')
        self.logo_regex = re.compile('.*logo.*', flags=re.IGNORECASE)

    def _get_headers(self):
        headers = {
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
        }
        return headers


    def get_logo(self, soup):
        logo = None
        images = soup.find_all('img')
        for image in images:
            if re.match(self.logo_regex, image['src']):
                logo = image
                break
        if not logo:
            logo = soup.find("img",{'class': self.logo_regex})
        if not logo:
            return None
        return logo['src']

    def clean_phones(self, phones):
        clean_phones = set()                            # use a set to ensure no duplicates
        for phone in phones:
            phone = re.sub('[^0-9\(\)\+ ]', '', phone)  # remove unwanted characters
            phone = re.sub(' +', ' ', phone)            # remove duplicate spaces
            phone = re.sub('\( ?\)', '', phone)         # remove empty parentheses
            phone = phone.strip()                       # remove surrounding whitespaces
            if phone != '':
                clean_phones.add(phone)
        return list(clean_phones)

    def get_absolute_logo_url(self, url, logo):
        if url.startswith('//'):
            return url[2:]  
        return urljoin(url, logo)
    
    def get_phones(self, soup):
        # using regex
        # regex = self.phone_regex
        # regex_phones = soup.findAll(text=regex)         # use regex to extract only phone numbers
        # using telephone links
        # link_phones = [a.text for a in soup.select("a[href*=tel\:]")]
        link_phones = [a['href'][4:] for a in soup.select("a[href*=tel\:]")]
        # using phonenumbers library
        pn_matches = phonenumbers.PhoneNumberMatcher(soup.text, "US")
        pn_phones = [phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164) for match in pn_matches]

        all_phones = self.clean_phones(link_phones + pn_phones)
        return all_phones
    
    def download_page(self, url):
        headers = self.headers
        page = requests.get(url, headers=headers)
        status_code = page.status_code
        if status_code == 200:
            page_text = page.text
        else: 
            print('Downloading page content from "{}" failed. Status code {}'.format(url, status_code), file=sys.stderr)
            page_text = None
        return url, page_text

    def handle_page_content(self, url, soup):
        '''
        Takes a single url and a soup object of the webpage.
        Returns the url, logo and phones from the page.
        '''
        logo = self.get_logo(soup)
        if not logo:
            print('Failed to find a logo for "{}"'.format(url), file=sys.stderr)
        elif not logo.startswith(url):
            logo = self.get_absolute_logo_url(url, logo)
        phones = self.get_phones(soup)
        website_data = {
            'website': url,
            'logo': logo,
            'phones': phones
        }
        return website_data

    def collect_website_data(self):
        '''
        Collects url, logo and phone data from "self.urls" and saves the results in "self.website_data".
        '''
        urls = self.urls
        # Using a thread pool to concurently download the contents of the urls
        with Pool(len(urls)) as p:
            websites_data = p.map(self.download_page, urls)
        # The rest of the work is done without multithreading 
        for url, page_text in websites_data:
            if page_text:
                soup = BeautifulSoup(page_text, "html.parser")
                website_data = self.handle_page_content(url, soup)
                self.websites_data.append(website_data)

    def export(self):
        return json.dumps(self.websites_data, indent=4)

def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def validate_urls(urls):
    valid_urls = []
    for u in urls:
        if is_url(u):
            valid_urls.append(u)
        else:
            print('The provided input "{}" is not a valid url. Skipping.'.format(u), file=sys.stderr)
    return valid_urls

if __name__ == "__main__":
    lines = sys.stdin.read()
    # with open('websites.txt', 'r') as fh:
    #     lines = fh.read()
    urls = validate_urls(lines.splitlines())
    if len(urls) == 0:
        print('No urls detected. Please enter provide a list of urls seperated by a newline', file=sys.stderr)
    else:
        gatherer = LogoAndPhonesScraper(urls)
        gatherer.collect_website_data()
        print(gatherer.export())
