import sys, pymongo

client = pymongo.MongoClient()
scraped = client.pyscrape.packages
toscrape = client.toscrape.metadata
final = client.pyscrape.repos

def main():
    for s in scraped.find():
        ts = toscrape.find({'id':s['_id']})
        if ts.count() > 0:
            toscrape.delete_many({'id': s['_id']})

            s['id'] = s['_id']
            del s['_id']
            final.insert_one(s)

if __name__ == '__main__':
    main()
