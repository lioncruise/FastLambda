import sys, json, pymongo, os
import numpy as np
from stdlib_list import stdlib_list

client = pymongo.MongoClient()
repos = client.sample.sample_data
mods = client.sample.mods
ftype_db = client.sample.ftypes

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
    ftypes = {}
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
                entry = mods.find_one({'mod':mod})
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

                mods.replace_one({'mod': mod}, entry, upsert=True)

        for ftype, data in repo['filetypes'].items():
            if not ftype in ftypes:
                ftypes[ftype] = {
                    'total': {'count':0, 'size': 0},
                    '2016': {'count':0, 'size': 0},
                    '2015': {'count':0, 'size':0},
                    '2014': {'count':0, 'size':0},
                    '2013': {'count':0, 'size':0},
                    '2012': {'count':0, 'size':0},
                    '2011': {'count':0, 'size':0},
                    '2010': {'count':0, 'size':0},
                    'files': []
                }

                ftypes[ftype]['total']['count'] += data['count']
                ftypes[ftype][year]['count'] += data['count']

                ftypes[ftype]['total']['size'] += data['agg_size']
                ftypes[ftype][year]['size'] += data['agg_size']

        curr += 1

    for ftype in ftypes:
        ftype_db.insert_one(ftype)

    cursor.close()

def main():
    bin_dir = os.path.join(os.path.dirname(__file__), 'plots', 'bin')
    frequencies()

if __name__ == '__main__':
    if len(sys.argv) != 1:
        print('Usage: analyze_repos.py')
        sys.exit(1)

    main()
