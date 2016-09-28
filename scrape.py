import os, requests, json, subprocess, time
from parse import parse_files

def search(page):
    payload = {'q':'language:python', 'per_page':100, 'page':page}
    r = requests.get('https://api.github.com/search/repositories', auth=(os.environ['GITHUB_USER'], os.environ['GITHUB_PW']), params=payload)

    if r.status_code != 200:
        print("invalid username or password")
    
    return r.json()['items']

# TODO: exclude setup scripts
def scrape(path):
    fstats = []
    pyfiles = []
    for rel in os.listdir(path):
        f = os.path.join(path, rel)

        if os.path.isdir(f):
            fstats.extend(scrape(f))
        elif f.endswith('.py'):
            pyfiles.append(f)
    fstats.append(parse_files(pyfiles))
    return fstats

def wrjs(data, path):
    with open(path, 'w') as fd:
        json.dump(data, fd, indent=4, sort_keys=True)


# TODO: maybe remove all standard python modules?
def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    aggstart = time.time()
    data = {}

    for k in range(1,11):
        try:
            results = search(k)
            # TODO: threads
            for result in results:
                # want to use tmpfs for this but ran out of memory
                path = '%s/clone/%s' % (script_dir, result['id'])
                print('<----- processing %s ----->' % result['id'])

                print('cloning repository...')
                start = time.time()
                subprocess.check_output(['git', 'clone', result['clone_url'], path], stderr=subprocess.STDOUT)
                t = time.time() - start
                print('cloning took %fs' % t)

                subprocess.check_output(['rm', '-rf', os.path.join(path, '.git')])

                print('parsing files')
                start = time.time()
                data[result['id']] = scrape(path)
                t = time.time() - start
                print('parsing took %fs' % t)
                
                subprocess.check_output(['rm', '-rf', path])
                print('<----- finished %s ----->' % result['id'])
        except Exception as e:
            print('failed to parse repo due to %s' % e)

    out = os.path.join(script_dir, 'scrape.json')
    wrjs(data, out)

    t = time.time() - aggstart
    print('scraped %s repos in %fs' % (len(results), t))

if __name__ == '__main__':
    main()
