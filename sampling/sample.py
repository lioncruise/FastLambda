import sys, json, pymongo, random

client = pymongo.MongoClient()
repos = client.metadata.metadata

def main(size):
    out_table = client.sample.sample
    total = repos.count()

    curr_size = 0
    count = 0
    query = {}
    while curr_size < size:
        r = random.randint(0, total-1)
        repo = repos.find().limit(-1).skip(r).next()

        if curr_size + repo['size'] > size:
            break

        if out_table.find({'id':repo['id']}).count() == 0:
            out_table.insert_one(repo)
            curr_size += repo['size']
            count += 1

    return count

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: sample.py <size>')
        sys.exit(1)

    sample_size = main(float(sys.argv[1]))
    print('number of samples: %s' % sample_size)
