import pymongo
import os
import json
import re
import googlemaps
import haversine
from flask import Flask
from flask import request
from flask_cors import CORS
from raven.contrib.flask import Sentry

app = Flask(__name__)
CORS(app)
dbc = pymongo.MongoClient(os.environ.get("MONGO_HOST", "mongo"), int(os.environ.get("MONGO_PORT", 27017)))
db = dbc.chf
# gmaps = googlemaps.Client(key=os.environ["GOOGLE_API_KEY"])
# sentry = Sentry(app, dsn="https://9525e46e053b49828a6813d0276f1377:671f84a52c2b42569af47bb39d941198@sentry.io/208562")


@app.route("/properties")
def get_properties():
    properties_cur = db.properties.find()
    properties_for_sale = []
    properties_sold = []
    for p in properties_cur:
        del p["_id"]
        if p["sold"]:
            properties_sold.append(p)
        else:
            properties_for_sale.append(p)
    properties = properties_for_sale + properties_sold
    return json.dumps({
        "status": "good",
        "properties": properties
    })


@app.route("/properties/<int:pid>")
def get_property(pid):
    p = db.properties.find_one({"id": pid})
    if p is None:
        return json.dumps({
            "status": "error",
            "error": "id-not-found"
        })
    del p["_id"]
    return json.dumps({
        "status": "good",
        "property": p
    })


@app.route("/properties/search/<loc>")
def search(loc):
    # geocode_result = gmaps.geocode(loc)
    # if len(geocode_result) == 0:
    #     return json.dumps({
    #         "status": "error",
    #         "error": "loc-not-found"
    #     })
    # loc = geocode_result[0]["geometry"]["location"]
    loc = {
        "lat": 51.5947244,
        "lng": -2.8576688
    }
    settings = {
        "distmin": -1,
        "distmax": -1,

        "pricemin": -1,
        "pricemax": -1,

        "sold": 0
    }
    search_radius = db.scraper_config.find_one({"name": "search_radius"})
    if search_radius is not None:
        settings["distmax"] = search_radius["val"]
    if request.args.get("distmin", False):
        settings["distmin"] = int(request.args.get("distmin"))
    if request.args.get("distmax", False):
        settings["distmax"] = int(request.args.get("distmax"))
    if request.args.get("pricemin", False):
        settings["pricemin"] = int(request.args.get("pricemin"))
    if request.args.get("pricemax", False):
        settings["pricemax"] = int(request.args.get("pricemax"))
    if request.args.get("sold", False):
        settings["sold"] = int(request.args.get("sold"))
    properties_cur = db.properties.find()
    properties_for_sale = []
    properties_sold = []
    print(settings)
    for p in properties_cur:
        del p["_id"]
        dist = haversine.haversine((loc["lat"], loc["lng"]), (p["loc"]["lat"], p["loc"]["lng"]), True)
        price = int(re.sub(r'[^\d-]+', '', p["price"]))
        p["distance"] = dist
        if (dist <= settings["distmax"] or settings["distmax"] == -1) and\
                (dist >= settings["distmin"] or settings["distmin"] == -1) and\
                (price <= settings["pricemax"] or settings["pricemax"] == -1) and\
                (price >= settings["pricemin"] or settings["pricemin"] == -1):
            if p["sold"]:
                if settings["sold"] == 0 or settings["sold"] == 2:
                    properties_sold.append(p)
            else:
                if settings["sold"] == 0 or settings["sold"] == 1:
                    properties_for_sale.append(p)
    properties_for_sale.sort(key=lambda k: k["distance"])
    properties_sold.sort(key=lambda k: k["distance"])
    properties = properties_for_sale + properties_sold
    return json.dumps({
        "status": "good",
        "properties": properties
    })

if __name__ == '__main__':
    app.run("0.0.0.0", 80)
