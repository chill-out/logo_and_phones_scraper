# Logo And Phones Scraper

This script is used to gather the website logo and any phone numbers listed on the page.

## Description

The script takes urls passed through the standard input, one in each line, and seaches them for the logo and any phone numbers.
When the script is finished, the results are printed in a JSON format.

## Getting Started

### Dependencies

* Python 3.7
* Docker(optional)
* Git

### Installing

* Clone the repository using ```git clone https://github.com/chill-out/logo_and_phones_scraper/```
* Install prerequesites using ```pip install -r requirements.txt```
* Optionally create a docker image using ```docker build --tag logo_and_phones_scraper:0.1```

### Executing program

* Create a text file with the urls you want to scrape (one per line, seperated by newline)
* Run the python script using ```cat YOURFILE.TXT | python -m logo_and_phones_scraper```
* Or run using the docker image using ```cat YOURFILE.TXT | docker run -i logo_and_phones_scraper:0.1```


## Authors

Denis Adamcho

## Version History

* 0.1
    * Initial Release
