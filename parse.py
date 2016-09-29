import re, sys, json, os

def parse_file(fd, local):
    stats = {'lines': 0}
    mods = {}

    for line in fd:
        line = line.split()
        if len(line) == 0:
            continue

        stats['lines'] += 1

        if line[0] == 'import':
            for k in range(1, len(line)):
                line[k] = line[k].strip(',')

                prd = line[k].find('.')
                if prd == -1:
                    mod = line[k]
                    fn = []
                else:
                    mod = line[k][0:prd]
                    fn = [line[k][prd+1:len(line[k])]]

                if mod not in mods and mod not in local:
                    mods[mod] = fn

            continue

        if line[0] == 'from':
            prd = line[1].find('.')
            if prd == -1:
                mod = line[1]
                pfx = ''
            else:
                mod = line[1][0:prd]
                pfx = '%s.' % line[1][prd+1:len(line[1])]

            if mod in local:
                continue
            if not mod in mods :
                mods[mod] = []
            for k in range(3, len(line)):
                line[k] = line[k].strip(',')
                if not line[k] in mods[mod] and not line[k] in local:
                    mods[mod].append('%s%s' % (pfx, line[k]))

            continue

        for stmt in line:
            for mod, refs in mods.items():
                start = stmt.find('%s.' % mod)

                if start != -1:
                    start += len(mod) + 1
                    stmt = stmt[start:len(stmt)]
                    match = re.search('\.|\(|\)|\[|\]', stmt)

                    if match: 
                        end = match.start()
                        ref = stmt[0:end]
                    else:
                        ref = stmt[0:len(stmt)]

                    if ref not in refs:
                        mods[mod].append(ref)


    stats['modules'] = mods
    return stats

# benefit to separating whole modules vs 'from * ' syntax?
# separate functions used vs variables?
def parse_files(pyfiles):
    fstats = []
    local = []
    for f in pyfiles:
        n = os.path.basename(f)
        local.append(n.split('.py')[0])

    for f in pyfiles:
        with open(f, 'r') as fd:
            try:
                fstats.append(parse_file(fd, local))
            except Exception as e:
                print('failed to parse file %s because: %s' % (f, e))

    return fstats
        


if __name__ == '__main__':
    path = sys.argv[1]
    fstats = []
    pyfiles = []
    for rel in os.listdir(path):
        f = os.path.join(path, rel)
        if f.endswith('.py'):
            pyfiles.append(f)

    fstats.extend(parse_files(pyfiles))
    print(json.dumps(fstats, indent=4, sort_keys=True))
