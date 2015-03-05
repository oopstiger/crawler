import logging
import time
import os
import sys
import importlib

sys.path.append(os.path.abspath("../"))
from DataGatewayClient import DataGatewayClient


def load_hotels(target):
    hotels = []
    with open(target + "/hotels.txt") as f:
        encoding = "utf-8"
        for l in f:
            l = l.strip(" \t\r\n")
            if not l:
                continue
            if l.startswith('#'):
                l = l[1:].lstrip(" \t")
                if l.startswith("encoding") and '=' in l:
                    encoding = l.split('=')[1].strip(" \t").lower()
                continue
            args = [a.strip(" \t") for a in l.decode(encoding).split(',')]
            hotels.append(args)
    return hotels


def fetch_latest(target, history):
    try:
        mod = importlib.import_module('%s.fetch' % target)
        fetch = mod.fetch
    except ImportError:
        logging.error("** Crawler \'%s\' not found!" % target)
        return None
    except Exception, e:
        logging.error("** Something is wrong with crawler \'%s\': %s" % (target, str(e)))
        return None

    hotels = load_hotels(target)
    results = []
    for hotel_arg in hotels:
        try:
            records = fetch(hotel_arg)
            if not records:
                continue
        except Exception, e:
            # ignore errors
            logging.error("** Crawler [%s] exception: %s" % (target, str(e)))
            continue

        hotel_key = target + '-' + '-'.join(hotel_arg)
        if hotel_key in history:
            hl = history[hotel_key]
        else:
            hl = []
        newhl = []
        for r in records:
            h = r.hash
            if h not in hl:
                results.append(r)
            newhl.append(h)
        history[hotel_key] = newhl
    return results


def push_record(client, record):
    retries = 0
    while retries < 2:
        try:
            if not client.is_connected():
                client.reconnect()
            code, reason = client.push("hotel_review", record, "mysql")
            if code != 200:
                logging.warning("DataGatewayClient reports " + reason)
                break
            return True
        except Exception, e:
            client.close()
            retries += 1
            logging.error("DataGatewayClient error, retry[" + str(retries) + "] " + str(e))
    return False


def run_crawler(target, period, gateway):
    history = {}
    try:
        client = DataGatewayClient(gateway)
    except Exception, e:
        logging.error(str(e))
        logging.error("*** Can't connect to gateway server " + str(gateway))
        return -1

    while True:
        try:
            logging.info("crawler [%s] is started..." % target)
            records = fetch_latest(target, history)
            count = 0
            for r in records:
                push_record(client, r)
                count += 1
            logging.info("crawler [%s] got %d new records" % (target, count))
        except Exception, e:
            logging.error("Unhandled exception from \'%s\': %s" % (target, str(e)))
        logging.info("crawler [%s] is slept" % target)
        time.sleep(period)


def getarg(argv, name, default=None):
    capture = False
    for a in argv:
        if capture:
            return a
        if a == name:
            capture = True
    return default


if __name__ == "__main__":
    crawlers = []
    for e in os.listdir("./"):
        if not os.path.isdir(e):
            continue
        if os.path.exists(e+"/fetch.py") and os.path.exists(e+"/hotels.txt") and os.path.exists(e+"/__init__.py"):
            crawlers.append(e)

    if len(sys.argv) < 2:
        print("Usage: crawler.py <CRAWLER-ID> [OPTIONS]")
        print("Currently available crawlers are:")
        print("  " + ' '.join(crawlers))
        print("")
        print("OPTIONS may be:")
        print("  -t <PERIOD>   period of crawling, in seconds. Default is 3600.")
        print("  -g <GATEWAR>  address of data gateway server. Default is localhost:8086")
        print("  -l <LEVEL>    log level, within range [0, 50]. Default is 30(warning).")
        exit(1)

    # set log level
    lvl = int(getarg(sys.argv, '-l', "30"))
    logging.getLogger().setLevel(lvl)

    target = sys.argv[1]
    if target not in crawlers:
        print("Crawler \'%s\' not found!" % target)
    period = int(getarg(sys.argv, "-t", "3600"))
    addr = getarg(sys.argv, "-g", "localhost:8086").split(':')
    gateway = (addr[0], int(addr[1]))
    run_crawler(target, period, gateway)
