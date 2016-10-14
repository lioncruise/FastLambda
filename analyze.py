import sys, json, pymongo
import numpy as np

client = pymongo.MongoClient()
repos = client.pyscrape.repos
metadata = client.metadata.metadata
freqs = client.pyscrape.freqs

def get_year(repo):
    if repo['created_at'] > '2016':
        return '2016'
    elif repo['created_at'] > '2015':
        return '2015'
    elif repo['created_at'] > '2014':
        return '2014'
    elif repo['created_at'] > '2013':
        return '2013'
    elif repo['created_at'] > '2012':
        return '2012'
    elif repo['created_at'] > '2011':
        return '2011'

    return '2010'

def frequencies(query):
    freq = {}
    for repo, scripts in repos.find(query).items():
        year = get_year(repo)
        for s in scripts:
            for mod, submods in s['mods'].items():
                entry = freqs.find_one({'mod':mod}).count()
                if not entry:
                    entry = {
                        'mod': mod,
                        'total': 0,
                        '2016': 0,
                        '2015': 0,
                        '2014': 0,
                        '2013': 0,
                        '2012': 0,
                        '2011': 0,
                        '2010': 0,
                        'submods': {}
                    }

                entry['total'] += 1
                entry[year] += 1

                for submod in submods:
                    if not submod in entry['submods']:
                        entry['submods'][submod] = 1
                    else:
                        entry['submods'][submod] += 1

                freqs.replace_one({'mod': mod}, entry, upsert=True)
                        

    return freq

def metastats(query):
    params = ['size', 'forks_count', 'stargazers_count', 'watchers_count']
    stats = {}
    for param in params:
        stats[param] = {
            'sum': 0,
            'mean': 0.0,
            'variance': 0.0,
        }
        
    # Welford's method for online mean & variance
    num = 0.0
    for repo in metadata.find(query):
        num += 1
        for param in params:
            val = repo[param]
            stats[param]['sum'] += val

            delta = val - stats[param]['mean']
            stats[param]['mean'] += delta/num
            stats[param]['variance'] += delta*(val - stats[param]['mean'])

    for param in params:
        stats[param]['variance'] = stats[param]['variance']/(num-1)

    return stats

def main(out):
    #frequencies()
    stats = {
        'total': metastats({}),
        '2010': metastats({'created_at': {'$gt':'2010', '$lt':'2011'}}),
        '2011':  metastats({'created_at': {'$gt':'2011', '$lt':'2012'}}),
        '2012':  metastats({'created_at': {'$gt':'2012', '$lt':'2013'}}),
        '2013':  metastats({'created_at': {'$gt':'2013', '$lt':'2014'}}),
        '2014':  metastats({'created_at': {'$gt':'2014', '$lt':'2015'}}),
        '2015':  metastats({'created_at': {'$gt':'2015', '$lt':'2016'}}),
        '2016':  metastats({'created_at': {'$gt':'2016'}})
    }

    print(stats)
    with open(out, 'w') as fd:
        json.dump(stats, fd, indent=4, sort_keys=True)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: analyze.py <out.txt>')

    main(sys.argv[1])
