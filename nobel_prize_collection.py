
from pymongo import MongoClient
import json
import pprint
import matplotlib.pyplot as plt
from scipy import stats
from sklearn import pipeline

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
    return {doc["_id"]: doc["count"] for doc in results}

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
    {"$unwind": "$prizes"},
    {"$match": {"born": {"$exists": True, "$ne": "0000-00-00"}, "gender": {"$ne": "org"}}},
    {"$addFields": {"age": {"$subtract": [
        {"$toInt": {"$substr": ["$prizes.year", 0, 4]}},
        {"$toInt": {"$substr": ["$born", 0, 4]}}
    ]}}},
    {"$bucket": {
        "groupBy": "$age",
        "boundaries": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100],
        "default": "other",
        "output": {"count": {"$sum": 1}}
    }},
    {"$project": {
        "age_range": {"$concat": [{"$toString": "$_id"}, "-", {"$toString": {"$add": ["$_id", 4]}}]},
        "count": 1,
        "_id": 0
    }}
]

    results = db.collection.aggregate(pipeline)
    return {doc["age_range"]: doc["count"] for doc in results}

def laureate_ages_yearly():
    pipeline = [
        {"$unwind": "$prizes"},
        {"$match": {"born": {"$exists": True, "$ne": "0000-00-00"}, "gender": {"$ne": "org"}}},
        {"$project": {
            "_id": 0,
            "year": {"$toInt": "$prizes.year"},
            "age": {"$subtract": [
                {"$toInt": {"$substr": ["$prizes.year", 0, 4]}},
                {"$toInt": {"$substr": ["$born", 0, 4]}}
            ]}
        }}
    ]

    results = db.collection.aggregate(pipeline)
    return [(doc["year"], doc["age"]) for doc in results]

def top_category_per_country(limit=10):
    pipeline = [
    {"$match": {"bornCountry": {"$exists": True}}},
    {"$unwind": "$prizes"},
    {"$group": {
        "_id": {"country": "$bornCountry", "category": "$prizes.category"},
        "count": {"$sum": 1}
    }},
    {"$sort": {"_id.country": 1, "count": -1}},
    {"$group": {
        "_id": "$_id.country",
        "topCategory": {"$first": "$_id.category"},
        "count": {"$first": "$count"}
    }},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]

    results = db.collection.aggregate(pipeline)
    return {doc["_id"]: {"category": doc["topCategory"], "count": doc["count"]} for doc in results}

# top_category_per_country()

def most_prizes_per_year(limit=10):
    pipeline = [
        {"$unwind": "$prizes"},

        {"$group": {
            "_id": "$prizes.year",
            "count": {"$sum": 1}
        }},

        {"$sort": {"count": -1}},
        {"$limit" : limit}
    ]

    results = db.collection.aggregate(pipeline)

    for doc in results:
        print("Year:", doc["_id"], "Prizes won:", doc["count"])

most_prizes_per_year()

def laureate_gender_breakdown():
    pipeline = [
        {"$group": {
            "_id": "$gender",
            "count": {"$sum": 1}
        }}
    ]
    results = db.collection.aggregate(pipeline)
    return {doc["_id"]: doc["count"] for doc in results}

def minor_winners():
    pipeline = [
    {"$unwind": "$prizes"},
    {"$match": {
        "born": {"$exists": True, "$ne": "0000-00-00"},
        "gender": {"$ne": "org"}
    }},
    {"$addFields": {
        "age": {"$subtract": [
            {"$toInt": {"$substr": ["$prizes.year", 0, 4]}},
            {"$toInt": {"$substr": ["$born", 0, 4]}}
        ]}
    }},
    {"$match": {"age": {"$lt": 18}}}
]

    results = db.collection.aggregate(pipeline)
    return [doc for doc in results]

def category_introduction_year():
    pipeline = [
    {"$unwind": "$prizes"},
    {"$group": {
        "_id": "$prizes.category",
        "firstYear": {"$min": "$prizes.year"}
    }},
    {"$sort": {"firstYear": 1}}
]

    results = db.collection.aggregate(pipeline)
    return {doc["_id"]: doc["firstYear"] for doc in results}

def solo_vs_collaborative_prizes():
    pipeline = [
    {"$unwind": "$prizes"},
    {"$group": {
        "_id": {"year": "$prizes.year", "category": "$prizes.category"},
        "winners": {"$sum": 1}
    }},
    {"$addFields": {
        "type": {"$cond": [{"$eq": ["$winners", 1]}, "solo", "collaborative"]}
    }},
    {"$group": {
        "_id": {
            "decade": {"$subtract": [{"$toInt": "$_id.year"}, {"$mod": [{"$toInt": "$_id.year"}, 10]}]},
            "type": "$type"
        },
        "count": {"$sum": 1}
    }},
    {"$sort": {"_id.decade": 1, "_id.type": 1}}
]

    results = db.collection.aggregate(pipeline)
    return {(doc["_id"]["decade"], doc["_id"]["type"]): doc["count"] for doc in results}

def avg_winners_per_category():
    pipeline = [
    {"$unwind": "$prizes"},
    {"$group": {
        "_id": {"year": "$prizes.year", "category": "$prizes.category"},
        "winnersCount": {"$sum": 1}
    }},
    {"$group": {
        "_id": "$_id.category",
        "one_winner":    {"$sum": {"$cond": [{"$eq": ["$winnersCount", 1]}, 1, 0]}},
        "two_winners":   {"$sum": {"$cond": [{"$eq": ["$winnersCount", 2]}, 1, 0]}},
        "three_winners": {"$sum": {"$cond": [{"$eq": ["$winnersCount", 3]}, 1, 0]}}
    }},
    {"$sort": {"_id": 1}}
]

    results = db.collection.aggregate(pipeline)
    return {doc["_id"]: {"one_winner": doc["one_winner"], "two_winners": doc["two_winners"], "three_winners": doc["three_winners"]} for doc in results}

def categories_split():
    pipeline = [
    {"$unwind": "$prizes"},
    {"$group": {
        "_id": {"year": "$prizes.year", "category": "$prizes.category"},
        "shares": {"$push": "$prizes.share"},
        "category": {"$first": "$prizes.category"}
    }},
    {"$addFields": {
        "isUneven": {"$gt": [{"$size": {"$setUnion": ["$shares", []]}}, 1]}
    }},
    {"$match": {"isUneven": True}},
    {"$group": {
        "_id": "$category",
        "unevenCount": {"$sum": 1}
    }},
    {"$sort": {"unevenCount": -1}}
]

    results = db.collection.aggregate(pipeline)
    return {doc["_id"]: doc["unevenCount"] for doc in results}

def category_winners(category):
    results = db.collection.find(
    {"prizes.motivation": {"$regex": category, "$options": "i"}},
    {"firstname": 1, "surname": 1, "prizes.year": 1, "prizes.category": 1, "prizes.motivation": 1}
    )

    return [doc for doc in results]

def country_decades_winners():
    pipeline = [
    {"$match": {"bornCountry": {"$exists": True}}},
    {"$unwind": "$prizes"},
    {"$group": {
        "_id": {
            "country": "$bornCountry",
            "decade": {
                "$subtract": [{"$toInt": "$prizes.year"}, {"$mod": [{"$toInt": "$prizes.year"}, 10]}]
            }
        },
        "count": {"$sum": 1}
    }},
    {"$sort": {"_id.decade": 1}}
]

    results = list(db.collection.aggregate(pipeline))
    return {(doc["_id"]["country"], doc["_id"]["decade"]): doc["count"] for doc in results}


def age_histogram(data):
    # data is the dictionary from ages_of_laureates()
    labels = list(data.keys())
    counts = list(data.values())

    plt.bar(labels, counts, color="steelblue", edgecolor="black")
    plt.xlabel("Age of Winners")
    plt.ylabel("Number of Winners")
    plt.title("Nobel Prize Laureates by Age")
    plt.show()

# stacked bar chart for each category showing proportions of prizes with one, two, and three winners
def category_winners(data):
    categories = [doc["_id"] for doc in data]
    one =   [doc["one_winner"] for doc in data]
    two =   [doc["two_winners"] for doc in data]
    three = [doc["three_winners"] for doc in data]

    x = range(len(categories))

    plt.figure(figsize=(14, 6))
    plt.bar(x, one,   label="1 Winner", color="steelblue")
    plt.bar(x, two,   label="2 Winners", color="orange",   bottom=one)
    plt.bar(x, three, label="3 Winners", color="green",    bottom=[o + t for o, t in zip(one, two)])
    plt.xticks(x, categories, rotation=45, ha="right")
    plt.xlabel("Category")
    plt.ylabel("Number of Prizes")
    plt.title("Nobel Prize Winners per Prize by Category")
    plt.legend()
    plt.show()

# scatterplot with year on x axis and age on y axis, could plot linreg line of best fit
def age_over_time(data):
    years = [doc["year"] for doc in data]
    ages = [doc["age"] for doc in data]
    slope, intercept, r, p, se = stats.linregress(years, ages)
    line = [slope * y + intercept for y in sorted(years)]

    plt.figure(figsize=(14, 6))
    plt.scatter(years, ages, alpha=0.4, color="steelblue", label="Winners")
    plt.plot(sorted(years), line, color="red", label=f"Best fit (r={r:.2f})")
    plt.xlabel("Year")
    plt.ylabel("Age at Time of Winning")
    plt.title("Nobel Prize Winner Age Over Time")
    plt.legend()
    plt.show()

