import gc
import bs4
import requests
import extruct
import re
import os
import time
import pymongo
import urllib.parse
from raven import Client

# Read configuration from the ``SENTRY_DSN`` environment variable
client = Client(dsn="https://9525e46e053b49828a6813d0276f1377:671f84a52c2b42569af47bb39d941198@sentry.io/208562")

BASE_URL = "https://www.rightmove.co.uk"
START_URL = "/property-for-sale/find/Crook-Hudson-and-Flynn/Magor.html?locationIdentifier=BRANCH%5E140102&includeSSTC=true&_includeSSTC=on"
dbc = pymongo.MongoClient(os.environ.get("MONGO_HOST", "mongo"), int(os.environ.get("MONGO_PORT", 27017)))
db = dbc.chf


def get_properties(url):
    r = requests.get(BASE_URL + url)
    if r.status_code != 200:
        return False
    bs = bs4.BeautifulSoup(r.text, "lxml")
    properties_bs = bs.find(id="l-searchResults").findAll(class_="propertyCard")
    properties = []
    for property_bs in properties_bs:
        if "is-hidden" not in property_bs.parent["class"]:
            a = property_bs.find(class_="propertyCard-link")
            properties.append(a["href"])
            del a
    del r
    del bs
    del properties_bs
    gc.collect()
    return properties


def get_property_details(url):
    r = requests.get(BASE_URL + url)
    if r.status_code != 200:
        return False
    bs = bs4.BeautifulSoup(r.text, "lxml")
    microdata = extruct.extract(r.text)
    microdata = microdata["microdata"][0]["properties"]
    header_price_bs = bs.find(id="propertyHeaderPrice")
    pid = int(re.search("property-for-sale/property-(?P<id>[0-9]+)\.html", url).group("id"))
    floorplan_tab_bs = bs.find(id="floorplanTabs")
    if floorplan_tab_bs is not None:
        floorplan = floorplan_tab_bs.img["src"]
    else:
        floorplan = None
    loc_link = bs.find("a", class_="js-ga-minimap").img["src"]
    loc_d = urllib.parse.parse_qs(urllib.parse.urlparse(loc_link).query)
    data = {"name": microdata["name"],
            "address": microdata["address"]["properties"]["streetAddress"],
            "photos": [],
            "features": [],
            "price": header_price_bs.strong.text.strip(),
            # change this "desc": microdata["description"], to "desc":[]
            "desc": [],
            "floorplan": floorplan,
            "sold": False,
            "loc": {
                "lat": float(loc_d["latitude"][0]),
                "lng": float(loc_d["longitude"][0])
            },
            "id": pid}
    print(data)
    for photo in microdata["photo"]:
        data["photos"].append(photo["properties"]["contentUrl"].replace('http://', 'https://'))
    features_bs = bs.find(class_="key-features").ul.findAll("li")
    for feature_bs in features_bs:
        data["features"].append(feature_bs.text.strip())
    if header_price_bs.find("small", class_="property-header-qualifier") is not None:
        if "Sold" in header_price_bs.find("small", class_="property-header-qualifier").text:
            data["sold"] = True
    # add following lines to get description of house
    for row in bs.findAll('div', attrs = {"class" : "sect"}):
    	data["desc"].append(row.text)
    #close	
    del r
    del bs
    del microdata
    del header_price_bs
    del pid
    del floorplan_tab_bs
    del loc_link
    del loc_d
    del features_bs
    gc.collect()
    return data


def scrape(db):
    print("*******************")
    print("* Starting scrape *")
    print("*******************", flush=True)
    properties = get_properties(START_URL)
    if not properties:
        return False
    db.properties.delete_many({})
    for p in properties:
        p_data = get_property_details(p)
        if not p_data:
            continue
       	db.properties.insert_one(p_data)
        print("Inserted house id: %s" % str(p_data["id"]), flush=True)
        print(str(p_data))
        del p_data
    del properties
    gc.collect()


def timer():
    while True:
        last_scrape = db.scraper_config.find_one({"name": "last_scrape"})
        scrape_interval = db.scraper_config.find_one({"name": "scrape_interval"})
        if scrape_interval is None:
            scrape_interval = 600
        else:
            scrape_interval = scrape_interval["val"]
        if last_scrape is None:
            scrape(db)
            db.scraper_config.insert_one({"name": "last_scrape", "val": int(time.time())})
        else:
            last_scrape = int(last_scrape["val"])
            if (time.time() - last_scrape) >= scrape_interval:
                scrape(db)
                db.scraper_config.update_one({"name": "last_scrape"}, {"$set": {"val": int(time.time())}})
        del last_scrape
        del scrape_interval
        gc.collect()
        time.sleep(10)


if __name__ == '__main__':
    if os.environ.get("RUN_ONCE") == "1":
        scrape()
    else:
        timer()
