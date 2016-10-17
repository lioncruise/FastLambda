import sys, json, pymongo, os

client = pymongo.MongoClient()
freqs = client.sample.sample_freqs
#repos = client.pyscrape.repos
repos = client.sample.sample_data

query = {
    'total': {},
    '2010': {'created_at': {'$gt':'2010', '$lt':'2011'}},
    '2011': {'created_at': {'$gt':'2011', '$lt':'2012'}},
    '2012': {'created_at': {'$gt':'2012', '$lt':'2013'}},
    '2013': {'created_at': {'$gt':'2013', '$lt':'2014'}},
    '2014': {'created_at': {'$gt':'2014', '$lt':'2015'}},
    '2015': {'created_at': {'$gt':'2015', '$lt':'2016'}},
    '2016': {'created_at': {'$gt':'2016'}}
}

def main(num, year):
    total = repos.count(query[year])
    top_mods = freqs.find().sort([["total.count", -1]]).limit(int(num))

    fname = 'top%s-%s.data' % (num, year)
    path = os.path.join(os.path.dirname(__file__), 'bin', fname)
    with open(path, 'w') as fd:
        fd.write('# mod prop\n')

        for repo in top_mods:
            mod = repo['mod']
            count = repo[year]['count']
            prop = float(num)/float(total)
            fd.write('%s %s\n' % (mod, prop))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python get_topmods.py <num> <year>')
        sys.exit(1)
        
    main(sys.argv[1], sys.argv[2])
