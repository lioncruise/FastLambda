import sys, json, pymongo, os
import numpy as np
from stdlib_list import stdlib_list

client = pymongo.MongoClient()
repos = client.sample.sample_data
metadata = client.metadata.sample
freqs = client.sample.freqs
#ftypes = client.sample.ftypes
ftypes = client.sample.pip_ftypes

def standard_mods():
    libs2 = stdlib_list('2.7')
    libs3 = stdlib_list('3.5')
    ret = []

    for mod in libs2:
        if not '.' in mod:
            ret.append(mod)

    for mod in libs3:
        if not '.' in mod and mod not in ret:
            ret.append(mod)

    return ret

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

def frequencies():
    banned = standard_mods()
    total = repos.count()
    curr = 0
    cursor = repos.find(no_cursor_timeout=True)
    for repo in cursor:
        print('processed %s out of %s' % (curr, total))
        
        year = get_year(repo)
        keys = ['total', year]
        for s in repo['pyfiles']:
            for mod, submods in s['mods'].items():
                if mod in banned:
                    continue
                entry = freqs.find_one({'mod':mod})
                if not entry:
                    entry = {
                        'mod': mod,
                        'total': {'count':0, 'submods':{}},
                        '2016': {'count':0, 'submods':{}},
                        '2015': {'count':0, 'submods':{}},
                        '2014': {'count':0, 'submods':{}},
                        '2013': {'count':0, 'submods':{}},
                        '2012': {'count':0, 'submods':{}},
                        '2011': {'count':0, 'submods':{}},
                        '2010': {'count':0, 'submods':{}},
                    }

                entry['total']['count'] += 1
                entry[year]['count'] += 1

                for submod in submods:
                    if not submod:
                        continue

                    submod = submod.replace('.', '%')

                    for key in keys:
                        if not submod in entry[key]['submods']:
                            entry[key]['submods'][submod] = 1
                        else:
                            entry[key]['submods'][submod] += 1

                freqs.replace_one({'mod': mod}, entry, upsert=True)

        for ftype, data in repo['filetypes'].items():
                entry = ftypes.find_one({'filetype':ftype})
                if not entry:
                    entry = {
                        'filetype': ftype,
                        'total': {'count':0, 'size': 0},
                        '2016': {'count':0, 'size': 0},
                        '2015': {'count':0, 'size':0},
                        '2014': {'count':0, 'size':0},
                        '2013': {'count':0, 'size':0},
                        '2012': {'count':0, 'size':0},
                        '2011': {'count':0, 'size':0},
                        '2010': {'count':0, 'size':0},
                    }

                entry['total']['count'] += data['count']
                entry[year]['count'] += data['count']

                entry['total']['size'] += data['agg_size']
                entry[year]['size'] += data['agg_size']


                ftypes.replace_one({'filetype': ftype}, entry, upsert=True)

        curr += 1

    cursor.close()

def metastats(query):
    params = {'size':[], 'forks_count':[], 'stargazers_count':[], 'watchers_count':[]}
        
    for repo in metadata.find(query):
        for param in params:
            params[param].append(repo[param])

    stats = {}
    for param, array in params.items():
        stats[param] = {
            'sum': np.sum(array),
            'mean': np.mean(array),
s            'median': np.median(array),
            'std': np.std(array),
            'max': np.max(array),
            'min': np.min(array)
        }

    return stats

def write_counts(out):
    counts = {
        '2010': metadata.find({'created_at': {'$gt':'2010', '$lt':'2011'}}).count(),
        '2011':  metadata.find({'created_at': {'$gt':'2011', '$lt':'2012'}}).count(),
        '2012':  metadata.find({'created_at': {'$gt':'2012', '$lt':'2013'}}).count(),
        '2013':  metadata.find({'created_at': {'$gt':'2013', '$lt':'2014'}}).count(),
        '2014':  metadata.find({'created_at': {'$gt':'2014', '$lt':'2015'}}).count(),
        '2015':  metadata.find({'created_at': {'$gt':'2015', '$lt':'2016'}}).count(),
        '2016':  metadata.find({'created_at': {'$gt':'2016'}}).count()
    }

    with open(out, 'w') as fd:
        fd.write('# year count\n')
        for year in sorted(counts):
            fd.write('%s %s\n' % (year, float(counts[year])/1000.0))

def write_meta(out):
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

    with open(out, 'w') as fd:
        json.dump(stats, fd, indent=4, sort_keys=True)


def main():
    bin_dir = os.path.join(os.path.dirname(__file__), 'plots', 'bin')
    frequencies()
    #write_meta(os.path.join(bin_dir, 'sample_meta.json'))
    #write_counts(os.path.join(bin_dir, 'sample_counts.data'))

if __name__ == '__main__':
    if len(sys.argv) != 1:
        print('Usage: analyze.py')
        sys.exit(1)

    main()
