from flask import Flask
from flask_cors import CORS, cross_origin
from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict
import urllib
import requests
from pytz import timezone
from datetime import datetime
from constants import API_ACCESS_KEY, PRIMARY_LINE, DIRECTION_MAP
import os

app = Flask(__name__)
cors = CORS(app)
app.debug = True
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route("/")
@cross_origin()
def home():
    line_map = {
        'L': {
            'url': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l',
            'station': {
                'code': 'L06',
                'name': 'First Ave Station',
            }
        },
        'G': {
            'url': "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
            'station': {
                'code': 'G35',
                'name': 'Clinton-Washington Ave Station',
            }
        }
    }
    eastern = timezone('US/Eastern')
    headers = {
        'x-api-key': API_ACCESS_KEY,
    }
    northbound, southbound = [], []

    train_line = PRIMARY_LINE

    feed = gtfs_realtime_pb2.FeedMessage()

    request = urllib.request.Request(line_map[train_line]['url'], headers=headers)
    response = urllib.request.urlopen(request)
    feed.ParseFromString(response.read())

    entity_list = [MessageToDict(entity) for entity in feed.entity]

    for entity in entity_list:
        if 'tripUpdate' in entity:
            stop_time_updates = entity['tripUpdate'].get('stopTimeUpdate', [])
            for update in stop_time_updates:
                if line_map[train_line]['station']['code'] in update['stopId']:
                    statement = "{} Train arriving at {} at {}".format(
                        update['stopId'],
                        line_map[train_line]['station']['name'],
                        datetime.fromtimestamp(int(update['arrival']['time']), eastern).strftime("%A, %B %d, %Y %I:%M:%S"),
                    )
                    
                    payload = {}
                    payload['line'] = train_line
                    # payload['arrival_time'] = datetime.fromtimestamp(int(update['arrival']['time']), eastern).strftime("%A, %B %d, %Y %I:%M:%S")
                    payload['arrival_time'] = "{} min".format(round((int(update['arrival']['time']) - datetime.now().timestamp())/60))
                    # payload['arrival_time'] = int(update['arrival']['time'])-datetime.now().timestamp()
                    
                    if "N" in update['stopId']:
                        # northbound.append(statement)
                        payload['direction'] = "N"
                        northbound.append(payload)
                    elif "S" in statement:
                        # southbound.append(statement)
                        payload['direction'] = "S"
                        southbound.append(payload)

    return {
        'northbound': northbound,
        'southbound': southbound,
    }

if __name__ == "__main__":
    app.run()