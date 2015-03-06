import os
import sys
import urllib
import logging
from datetime import datetime
from bs4 import BeautifulSoup


sys.path.append(os.path.abspath("../"))
from ReviewRecord import *


def fetch(args):
    hotel_name = args[0]
    hotel_url = args[1]
    page = urllib.urlopen(hotel_url)
    if page.getcode() != 200:
        logging.error("HTTP %d --> GET %s " % (f.getcode(), api_url))
        return None
    html_doc = page.read()
    TotalScore = 5
    soup = BeautifulSoup(html_doc)
    recos = soup.find_all('li', attrs={"class": "J-ratelist-item rate-list__item"})
    # hotel_name = soup.find('div', class_ = 'hotel-title').find('h5').string
    hotel_url = soup.find('link', rel='canonical')['href']

    rl = []
    for reco in recos:
        r = ReviewRecord()
        r.source_site = 'meituan'
        r.timestamp = datetime.now()
        r.hotel_name = hotel_name
        r.hotel_url = hotel_url
        r.nick_name = reco.find('span', class_='name').string
        r.comment_date = reco.find('span', class_='time').string
        r.check_in_date = r.comment_date
        r.comment = reco.find('p', class_='content').string
        #print r.comment.encode('utf-8')
        r.consume_detail = reco.find('p', class_='deal-title').find('a').string
        r.rate = int(reco.find(style=True)['style'].split(':')[1].split('%')[0]) * TotalScore / 100
        rl.append(r)
    return rl
