import os, requests, json, subprocess, time, pymongo
from parse import parse_files
from threading import Thread, Lock
from Queue import Queue

client = pymongo.MongoClient('localhost:50000')
db = client.pyscrape

script_dir = os.path.dirname(os.path.realpath(__file__))

data = {}
queue = Queue(100)
searchers = 5
parsers = 10
page = 1
page_lock = Lock()

class Searcher(Thread):
    def run(self):
        global queue
        global page
        while True:
            with page_lock:
                my_page = page
                page += 1

            try:
                results = search(my_page)
            except:
                return

            for result in results:
                while queue.full():
                    pass

                queue.put(result)

class Parser(Thread):
    def run(self):
        global queue
        global data
        while True:
            pkg = queue.get()
            pkg = format_pkg(pkg)
            if pkg['id'] in data:
                raise Exception('attempted to parse same repo twice')
            # want to use tmpfs for this but ran out of memory
            path = '%s/clone/%s' % (script_dir, pkg['id'])

            start = time.time()
            subprocess.check_output(['git', 'clone', pkg['clone_url'], path], stderr=subprocess.STDOUT)
            t = time.time() - start
            print('cloning took %fs' % t)

            subprocess.check_output(['rm', '-rf', os.path.join(path, '.git')])

            if pkg['id'] in data:
                raise Exception('duplicate id in data')

            start = time.time()
            parse_result = scrape(path)
            t = time.time() - start
            print('parsing took %fs' % t)

            data[pkg['id']] = parse_result

            agg_lines = 0
            for f in parse_result:
                agg_lines += f['lines']

            pkg['files'] = parse_result
            pkg['agg_lines'] = agg_lines
            db_result = db.packages.insert_one(pkg)
            
            subprocess.check_output(['rm', '-rf', path])

def cond_del(d, k):
    if k in d:
        del d[k]

def format_pkg(pkg):
    rm_keys = ['name', 'full_name', 'owner', 'html_url', 'private', 'description', 'fork', 'homepage', 'language', 'master_branch', 'default_branch']
    for k in rm_keys:
        cond_del(pkg, k)

    return pkg

def search(page):
    payload = {'q':'language:python', 'per_page':100, 'page':page}

    r = requests.get('https://api.github.com/search/repositories', auth=(os.environ['GITHUB_USER'], os.environ['GITHUB_PW']), params=payload)

    if r.status_code != 200:
        if page == 1:
            print("invalid username or password")
        raise

    return r.json()['items']
    

def scrape(path):
    fstats = []
    pyfiles = []
    for rel in os.listdir(path):
        f = os.path.join(path, rel)

        if os.path.isdir(f):
            fstats.extend(scrape(f))
        elif f.endswith('.py'):
            pyfiles.append(f)
    fstats.extend(parse_files(pyfiles))
    return fstats

def wrjs(data, path):
    with open(path, 'w') as fd:
        json.dump(data, fd, indent=4, sort_keys=True)


def main():
    aggstart = time.time()
    global queue

    wait = []
    for k in range(searchers):
        s = Searcher()
        s.start()
        wait.append(s)
    
    for k in range(parsers):
        Parser().start()

    for thread in wait:
        thread.join()

    while not queue.empty():
        pass

    out = os.path.join(script_dir, 'scrape.json')
    wrjs(data, out)

    t = time.time() - aggstart
    print('finished in %fs' % t)

if __name__ == '__main__':
    main()
