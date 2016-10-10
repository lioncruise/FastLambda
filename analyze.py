import sys, json, pymongo

client = pymongo.MongoClient()
pkgs = client.pyscrape.packages

def subfrequencies(query):
    subfreq = {}
    for repo in pkgs.find(query):
        for s in scripts:
            for mod, submod in s['mods'].items():
                if mod not in subfreq:
                    subfreq[mod] = {}

                if submod not in subfreq[mod]:
                    subfreq[mod] = 1
                else:
                    subfreq[mod] += 1

    return subfreq

def frequencies(query):
    freq = {}
    for repo in pkgs.find(query):
        for s in scripts:
            for mod in s['mods']:
                if mod not in freq:
                    freq[mod] = 1
                else:
                    freq[mod] += 1

    return freq


def main(f):
    freq = frequencies()

    return freq['total']

if __name__ == '__main__':
    main()
