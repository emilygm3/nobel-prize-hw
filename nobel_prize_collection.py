
from pymongo import MongoClient
import json
import pprint

client = MongoClient()
db = client.prize

with open('laureate.json') as json_file:
    data = json.load(json_file)

prize_data = data["laureates"]
db.collection.delete_many({})
result = db.collection.insert_many(prize_data)


# chemistry_prizes = db.collection.find({"category": "chemistry"})
#
# for prize in chemistry_prizes:
#     pprint.pprint(prize)

# countries = db.collection.distinct("bornCountry")
# print(countries)


pipeline = [
    {"$match": {"bornCountry": {"$exists": True}}},
    {"$group": {
        "_id": "$bornCountry",
        "count": {"$sum": 1}
    }},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]

results = db.collection.aggregate(pipeline)

for doc in results:
    print(doc["_id"], doc["count"])



