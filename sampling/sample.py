import sys, json, pymongo

client = pymongo.MongoClient()
repos = client.metadata.metadata

def main(size, out):
    out_table = client.metadata[out]
    curr = 0
    count = 0
    query = {}
    for repo in repos.find(query):
        if curr + repo['size'] > size:
            break

        curr += repo['size']
        out_table.insert_one(repo)
        count += 1

    return count

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: sample.py <size> <outtable>')
        sys.exit(1)

    sample_size = main(float(sys.argv[1]), sys.argv[2])
    print('number of samples added to %s: %s' % (sys.argv[2], sample_size))
