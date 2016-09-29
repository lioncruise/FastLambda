import sys, json

def rdjs(f):
    with open(f, 'r') as fd:
        try:
            data = json.load(fd)
        except Exception as e:
            print('could not read json: %s' % e)
            sys.exit(1)

    return data

def frequencies():
    freq = {'proj': {}, 'total': {}}
    for pid, scripts in data.items():
        if len(scripts) > 0:
            freq['proj'][pid] = {}
        for s in scripts:
            for mod, submods in s['modules'].items():
                if mod not in freq['proj'][pid]:
                    freq['proj'][pid][mod] = 1
                else:
                    freq['proj'][pid][mod] += 1

                if mod not in freq['total']:
                    freq['total'][mod] = 1
                else:
                    freq['total'][mod] += 1

    return freq


def main(f):
    global data
    data = rdjs(f)
    freq = frequencies()

    return freq['total']

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: format.py <data.json>')

    mods = main(sys.argv[1])
    srted = sorted(mods.items(), key=lambda x:x[1])

    k = len(srted)-1
    while k >= 0:
        print(srted[k])
        k -= 1
