
from pymongo import MongoClient
import json
import pprint

client = MongoClient()
db = client.prize

with open('laureate.json') as json_file:
    data = json.load(json_file)

prize_data = data["laureates"]
result = db.collection.insert_many(prize_data)


# chemistry_prizes = db.collection.find({"category": "chemistry"})
#
# for prize in chemistry_prizes:
#     pprint.pprint(prize)
