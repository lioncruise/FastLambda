import sys, json, pymongo, os
import numpy as np
from stdlib_list import stdlib_list

client = pymongo.MongoClient()
repos = client.sample.sample_data
import_counts = client.sample.import_counts
lines = client.sample.mod_lines
sub_mods = client.sample.submods
co_imports = client.sample.coimports

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
    imports = {}
    coimports = {}
    pylines = {}
    smods = {}

    curr = 0
    cursor = repos.find(no_cursor_timeout=True)
    for repo in cursor:
        print('processed %s out of %s' % (curr, total)) 
        for s in repo['pyfiles']:
            for mod, submods in s['mods'].items():
                if mod in banned:
                    continue

                if mod not in imports:
                    imports[mod] = []
                    coimports[mod] = {}
                    pylines[mod] = []
                    smods[mod] = {}

                imports[mod].append(len(s['mods'])-1)
                pylines[mod].append(s['lines'])

                for comod in s['mods']:
                    if comod != mod:
                        if comod in coimports[mod]:
                            coimports[mod][comod] += 1
                        else:
                            coimports[mod][comod] = 1

                for submod in submods:
                    if not submod:
                        continue

                    submod = submod.replace('.', '%')
                    if submod in smods[mod]:
                        smods[mod][submod] += 1
                    else:
                        smods[mod][submod] = 1
        curr += 1

    import_counts.insert_many([{'mod':key,'counts':value} for key,value in imports.items()])
    co_imports.insert_many([{'mod':key,'coimports':value} for key,value in coimports.items()])
    lines.insert_many([{'mod':key,'lines':value} for key,value in pylines.items()])
    sub_mods.insert_many([{'mod':key,'submods':value} for key,value in smods.items()])

if __name__ == '__main__':
    if len(sys.argv) != 1:
        print('Usage: analyze_repos.py')
        sys.exit(1)

    frequencies()
