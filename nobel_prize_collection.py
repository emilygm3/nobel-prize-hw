
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

def top_countries(limit=10):
    pipeline = [
        {"$match": {"bornCountry": {"$exists": True}}},
        {"$group": {
            "_id": "$bornCountry",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]

    results = db.collection.aggregate(pipeline)

    for doc in results:
        print(doc["_id"], doc["count"])

# top_countries()


def top_categories():
    pipeline = [
        {"$unwind": "$prizes"},  # Break out each prize into its own document
        {"$group": {
            "_id": "$prizes.category",  # Group by category
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}  # Sort descending
    ]

    results = db.collection.aggregate(pipeline)

    for doc in results:
        print(doc["_id"], doc["count"])

# top_categories()

# def laureate_ages():
#     for laureate in db.collection.find({"born": {"$exists": True}, "prizes": {"$exists": True}}):
#         born_year = int(laureate["born"][:4])  # Take first 4 chars of 'YYYY-MM-DD'
#
#         for prize in laureate["prizes"]:
#             prize_year = int(prize["year"])
#             age = prize_year - born_year
#             print(f"{laureate['firstname']} {laureate['surname']} won {prize['category']} at age {age}")

# laureate_ages()

def ages_of_laureates():
    pipeline = [
    {"$match": {"born": {"$exists": True}, "prizes": {"$exists": True}}},
    {"$unwind": "$prizes"},
    {"$project": {
        "_id": 0,
        "age": {
            "$subtract": [
                {"$toInt": "$prizes.year"},
                {"$toInt": {"$substr": ["$born", 0, 4]}}
            ]
        }
    }}
    ]

    results = db.collection.aggregate(pipeline)
    ages = [doc["age"] for doc in results]

    return ages

def top_category_per_country(limit=10):
    pipeline = [
        # Break out each prize
        {"$unwind": "$prizes"},

        # Ignore missing country
        {"$match": {"bornCountry": {"$exists": True}}},

        # Count how many times each (country, category) appears
        {"$group": {
            "_id": {
                "country": "$bornCountry",
                "category": "$prizes.category"
            },
            "count": {"$sum": 1}
        }},

        # Sort by country, then highest count first
        {"$sort": {
            "_id.country": 1,
            "count": -1
        }},

        # For each country, keep the first (highest) category
        {"$group": {
            "_id": "$_id.country",
            "topCategory": {"$first": "$_id.category"},
            "count": {"$first": "$count"}
        }},

        # Optional: sort final output by count descending
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]

    results = db.collection.aggregate(pipeline)

    for doc in results:
        print(doc["_id"], ":", doc["topCategory"], "(", doc["count"], ")")

top_category_per_country()

