import os, requests, json, subprocess

def search():
    payload = {'q':'language:python'}
    r = requests.get('https://api.github.com/search/repositories', auth=(os.environ['GITHUB_USER'], os.environ['GITHUB_PW']), params=payload)

    if r.status_code != 200:
        print("invalid username or password")
    
    return r.json()['items']

# clone_url, size, stargazers_count, forks_count,
def scrape(path):
    fstats = []
    for rel in os.listdir(path):
        f = os.path.join(path, rel)

        if os.path.isdir(f):
            fstats.extend(scrape(f))
        elif f.endswith('.py'):
            fstats.append(parse(f))

    return fstats

def parse(path):
    stats = {'lines': 0}
    modules = {}
    functions = []

    with open(path, 'r') as fd:
        for line in fd:
            line = line.split()
            if len(line) == 0:
                continue

            stats['lines'] += 1

            if line[0] == 'import':
                for k in range(1, len(line)):
                    line[k] = line[k].strip(',')
                    if not line[k] in modules:
                        modules[line[k]] = {'functions':[]}

                continue

            elif line[0] == 'from':
                for k in range(3, len(line)):
                    line[k] = line[k].strip(',')
                    if not line[k] in functions:
                        functions.append(line[k])

                continue

    stats['modules'] = modules
    stats['functions'] = functions
    return stats

def main():
    data = {}
    results = search()

    # TODO: threads, multiple pages of results
    for result in results:
        path = '/tmp/pyscrape/%s' % result['id']
        subprocess.check_output(['git', 'clone', result['clone_url'], path], stderr=subprocess.STDOUT)
        subprocess.check_output(['rm', '-rf', os.path.join(path, '.git')])

        data[result['id']] = scrape(path)
        
        subprocess.check_output(['rm', '-rf', path])
        break

    print(data)
    #print(json.dumps(results[0], indent=4, sort_keys=True))

if __name__ == '__main__':
    main()
