import os
import sys
import urllib2
import logging
import datetime
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath("../"))
from ReviewRecord import *


def fetch(args):
    hotel_name = args[0]
    hotel_id = args[1]
    api_url = hotel_id
    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20141201 Firefox/3.5.6'}
    req = urllib2.Request(url=api_url, headers=headers)
    f = urllib2.urlopen(req)
    if f.getcode() != 200:
        logging.error("http %d --> Get %s " % (f.getcode(), api_url))
        return None

    doc = f.read()
    soup = BeautifulSoup(doc)
    recos = soup.find_all('li', attrs = {"class": "comment-item"})

    r1 = []
    for reco in recos:
        r = ReviewRecord()
        r.hotel_name = hotel_name
        r.hotel_url = api_url
        r.source_site = "dianping"
        r.nick_name = reco.find('a', class_='name').string

        comment_date = reco.find('span', class_= 'time').string
        if str(comment_date).split("-")[0] != '14':
            r.comment_date = '15-' + comment_date
        else:
            r.comment_date = comment_date
        r.check_in_date = r.comment_date
        comment = reco.find('p', class_ = 'desc J-desc')
        if comment == None:
            r.comment = reco.find('p', class_ = 'desc').string
        else:
            r.comment = comment.string
        r.consume_detail = ""
        rate = reco.find('p', class_ = 'shop-info').find('span')
        r.rate = int(str(rate).split("str")[1].split("0")[0])
        r.timestamp = datetime.datetime.now()
        r1.append(r)
    return r1
