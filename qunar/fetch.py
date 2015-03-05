import os
import sys
import json
import urllib2
import logging
import datetime

sys.path.append(os.path.abspath("../"))
from ReviewRecord import *
from hotel_review import *
from hotel_review_content import *


def fetch(args):
    hotel_name = args[0]
    hotel_id = args[1]
    api_url = "http://review.qunar.com/api/h/%s/detail/rank/v1/page/1" % hotel_id
    f = urllib2.urlopen(api_url)
    if f.getcode() != 200:
        logging.error("HTTP %d --> GET %s " % (f.getcode(), api_url))
        return None

    d = f.read()
    review = hotel_review.from_dict(json.loads(d))

    rl = []
    for r in review.data.list:
        record = ReviewRecord()
        record.hotel_name = hotel_name
        record.source_site = "qunar"
        if r.content:
            content = hotel_review_content.from_dict(json.loads(r.content))
            record.comment = content.feedContent
            record.check_in_date = content.checkInDate
            record.rate = content.evaluation
            record.hotel_url = content.hotelUrl
            record.hotel_name = content.hotelName
        record.nick_name = r.nickName
        record.comment_date = datetime.datetime.fromtimestamp(r.feedTime/1000)
        record.timestamp = datetime.datetime.now()
        rl.append(record)
    return rl
