
from pymongo import MongoClient
import json
import matplotlib.pyplot as plt
from scipy import stats

client = MongoClient()
db = client.prize

with open('laureate.json') as json_file:
    data = json.load(json_file)

prize_data = data["laureates"]
db.collection.delete_many({})
result = db.collection.insert_many(prize_data)


class NobelAPI:

    def __init__(self, db):
        self.collection = db.collection

    def top_countries(self, limit=10):
        pipeline = [
            {"$match": {"bornCountry": {"$exists": True}}},
            {"$group": {"_id": "$bornCountry", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        results = self.collection.aggregate(pipeline)
        return {doc["_id"]: doc["count"] for doc in results}


    def top_categories(self):
        pipeline = [
            {"$unwind": "$prizes"},
            {"$group": {"_id": "$prizes.category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        results = self.collection.aggregate(pipeline)
        return {doc["_id"]: doc["count"] for doc in results}


    def most_prizes_per_year(self, limit=10):
        pipeline = [
            {"$unwind": "$prizes"},
            {"$group": {"_id": "$prizes.year", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        results = self.collection.aggregate(pipeline)
        return {doc["_id"]: doc["count"] for doc in results}


    def laureate_gender(self):
        pipeline = [
            {"$group": {"_id": "$gender", "count": {"$sum": 1}}}
        ]
        results = self.collection.aggregate(pipeline)
        return {doc["_id"]: doc["count"] for doc in results}


    def laureate_ages_yearly(self):
        pipeline = [
            {"$unwind": "$prizes"},
            {"$match": {"born": {"$exists": True, "$ne": "0000-00-00"},
                        "gender": {"$ne": "org"}}},
            {"$project": {
                "_id": 0,
                "year": {"$toInt": "$prizes.year"},
                "age": {"$subtract": [
                    {"$toInt": {"$substr": ["$prizes.year", 0, 4]}},
                    {"$toInt": {"$substr": ["$born", 0, 4]}}
                ]}
            }}
        ]
        return list(self.collection.aggregate(pipeline))


    def ages_of_laureates(self):
        pipeline = [
            {"$unwind": "$prizes"},
            {"$match": {"born": {"$exists": True, "$ne": "0000-00-00"},
                        "gender": {"$ne": "org"}}},
            {"$addFields": {
                "age": {"$subtract": [
                    {"$toInt": {"$substr": ["$prizes.year", 0, 4]}},
                    {"$toInt": {"$substr": ["$born", 0, 4]}}
                ]}
            }},
            {"$bucket": {
                "groupBy": "$age",
                "boundaries": list(range(0, 105, 5)),
                "default": "other",
                "output": {"count": {"$sum": 1}}
            }}
        ]
        results = self.collection.aggregate(pipeline)
        return {doc["_id"]: doc["count"] for doc in results}


    def minor_winners(self):
        pipeline = [
            {"$unwind": "$prizes"},
            {"$match": {"born": {"$exists": True, "$ne": "0000-00-00"},
                        "gender": {"$ne": "org"}}},
            {"$addFields": {
                "age": {"$subtract": [
                    {"$toInt": {"$substr": ["$prizes.year", 0, 4]}},
                    {"$toInt": {"$substr": ["$born", 0, 4]}}
                ]}
            }},
            {"$match": {"age": {"$lt": 18}}}
        ]
        return list(self.collection.aggregate(pipeline))


    def category_introduction_year(self):
        pipeline = [
            {"$unwind": "$prizes"},
            {"$group": {
                "_id": "$prizes.category",
                "firstYear": {"$min": "$prizes.year"}
            }},
            {"$sort": {"firstYear": 1}}
        ]
        results = self.collection.aggregate(pipeline)
        return {doc["_id"]: doc["firstYear"] for doc in results}


    def top_category_per_country(self, limit=10):
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
            {"$limit": limit}
        ]
        results = self.collection.aggregate(pipeline)
        return {doc["_id"]: {"category": doc["topCategory"], "count": doc["count"]} for doc in results}


    def plot_age_histogram(self):
        data = self.ages_of_laureates()
        labels = list(data.keys())
        counts = list(data.values())

        plt.bar(labels, counts)
        plt.xticks(rotation=45)
        plt.title("Nobel Prize Laureates by Age")
        plt.show()

    def plot_category_winners(self):
        pipeline = [
            {"$unwind": "$prizes"},
            {"$group": {
                "_id": {"year": "$prizes.year", "category": "$prizes.category"},
                "winnersCount": {"$sum": 1}
            }},
            {"$group": {
                "_id": "$_id.category",
                "one_winner": {"$sum": {"$cond": [{"$eq": ["$winnersCount", 1]}, 1, 0]}},
                "two_winners": {"$sum": {"$cond": [{"$eq": ["$winnersCount", 2]}, 1, 0]}},
                "three_winners": {"$sum": {"$cond": [{"$eq": ["$winnersCount", 3]}, 1, 0]}}
            }},
            {"$sort": {"_id": 1}}
        ]

        data = list(self.collection.aggregate(pipeline))

        categories = [doc["_id"] for doc in data]
        one = [doc["one_winner"] for doc in data]
        two = [doc["two_winners"] for doc in data]
        three = [doc["three_winners"] for doc in data]

        x = range(len(categories))

        plt.figure(figsize=(14, 6))
        plt.bar(x, one, label="1 Winner", color="steelblue")
        plt.bar(x, two, label="2 Winners", color="orange", bottom=one)
        plt.bar(x, three, label="3 Winners", color="green",
                bottom=[o + t for o, t in zip(one, two)])

        plt.xticks(x, categories, rotation=45, ha="right")
        plt.xlabel("Category")
        plt.ylabel("Number of Prizes")
        plt.title("Nobel Prize Winners per Prize by Category")
        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_age_over_time(self):
        data = self.laureate_ages_yearly()

        years = [d["year"] for d in data]
        ages = [d["age"] for d in data]

        slope, intercept, r, _, _ = stats.linregress(years, ages)
        line = [slope * y + intercept for y in sorted(years)]
        plt.scatter(years, ages, alpha=0.4, color="steelblue")
        plt.plot(sorted(years), line, color="red", label=f"Best fit (r={r:.2f})")
        plt.xlabel("Year")
        plt.ylabel("Age at Time of Winning")
        plt.title("Nobel Prize Winner Age Over Time")
        plt.legend()
        plt.show()

api = NobelAPI(db)

# print(api.top_categories())
# print(api.top_countries())
# print(api.most_prizes_per_year())

# api.plot_age_histogram()
# api.plot_category_winners()
# api.plot_age_over_time()