import os, requests, json, subprocess, time, pymongo, signal, sys
from parse import parse_files
from threading import Thread, Lock, current_thread
from Queue import Queue
from datetime import timedelta, date

script_dir = os.path.dirname(os.path.realpath(__file__))

client = pymongo.MongoClient()
db = client.pyscrape

queue = Queue(100)
searchers = 2
parsers = 2
page = 1
page_lock = Lock()
done = False
done_lock = Lock()

total_count = 1000
req_count = 0
req_lock = Lock()
prev_time = 0
missed = []

date_range = ''
size_range = ''

class Searcher(Thread):
    def run(self):
        global queue
        global page
	global done
        while True:
	    with done_lock:
		    if done:
			return

            with page_lock:
                my_page = page
                print('%s got page %s' % (current_thread(), my_page))
                page += 1

	    if total_count < (my_page+1)*100:
		with done_lock:
		    done = True
		return

            try:
                results = search(my_page)
            except:
                with done_lock:
		    done = True
                return

	    if len(results) == 0:
		time.sleep(0.2)
            for result in results:
                while queue.full():
                    time.sleep(0.01)

                _id = result['id']
                if db.packages.find({'_id': _id}).count() == 0:
                    print('%s putting %s into queue' % (current_thread(), _id))
                    queue.put(result)

class Parser(Thread):
    def run(self):
        global queue
        global data
        while True:
	    pkg = None
	    while not pkg:
		try:
		    pkg = queue.get(timeout=1)
		except:
		    with done_lock:
			if done:
			    return

            pkg = format_pkg(pkg)
	    if db.packages.find({'_id': pkg['_id']}).count() > 0:
		print('package data already in db') # SHOULDNT EVER HAPPEN
		continue

            print('%s got %s from queue' % (current_thread(), pkg['_id']))
            # want to use tmpfs for this but ran out of memory
            path = '%s/clone/%s' % (script_dir, pkg['_id'])

            start = time.time()
	    try:
                subprocess.check_output(['git', 'clone', pkg['clone_url'], path], stderr=subprocess.STDOUT)
	    except Exception as e:
	        print('clone failed due to: %s' % e.output)
		subprocess.check_output(['rm', '-rf', path])
		continue
            t = time.time() - start
            #print('cloning took %fs' % t)

            start = time.time()
            parse_result = scrape(path)
            t = time.time() - start
            #print('parsing took %fs' % t)

            agg_lines = 0
            for f in parse_result:
		agg_lines += f['lines']

            pkg['files'] = parse_result
            pkg['agg_lines'] = agg_lines

	    db_result = db.packages.insert_one(pkg)

	    try:            
	        subprocess.check_output(['rm', '-rf', path])
            except:
		return

def cond_del(d, k):
    if k in d:
        del d[k]

def format_pkg(pkg):
    rm_keys = ['full_name', 'owner', 'homepage', 'language', 'master_branch', 'default_branch', 'has_issues']

    for k in pkg:
        if k.endswith('url') and k != 'clone_url':
            rm_keys.append(k)

    for k in rm_keys:
        cond_del(pkg, k)

    pkg['_id'] = pkg['id']
    del pkg['id']
    return pkg

def search(page):
    global total_count
    global req_count
    global prev_time
    global missed

    req_lock.acquire()
    if req_count >= 30:
        while time.time()-prev_time < 60.1:
            time.sleep(0.1)

        prev_time = time.time()
        req_count = 0

    q = 'language:python created:%s size:%s' % (date_range, size_range)
    payload = {'q': q, 'per_page': 100, 'page': page}

    r = requests.get('https://api.github.com/search/repositories', auth=(os.environ['GITHUB_USER'], os.environ['GITHUB_PW']), params=payload)
    req_count += 1
    req_lock.release()

    if r.status_code != 200:
        if page == 1:
            raise Exception('invalid username or password')
	else:
	    raise Exception('exceeded pages in results')

    if r.json()['total_count'] > 1000 and date_range not in missed:
	print('missed: %s' % date_range)
	missed.append(date_range)

    total_count = r.json()['total_count']

    return r.json()['items']
    

def scrape(path):
    pyfiles = []
    dirs = [path]

    while len(dirs) != 0:
        d = dirs.pop(-1)
        for rel in os.listdir(d):
            f = os.path.join(d, rel)
	    if os.path.islink(f):
	        continue
            elif os.path.isdir(f):
		dirs.append(f)
            elif os.path.isfile(f) and f.endswith('.py'):
                pyfiles.append(f)

    return parse_files(pyfiles)

def wrjs(data, path):
    with open(path, 'w') as fd:
        json.dump(data, fd, indent=4, sort_keys=True)

def daterange(start, end):
    for n in range(int ((end - start).days)):
	yield start + timedelta(n)

def handle_sigint(signal, frame):
    global done
    with done_lock:
	done = True

    sys.exit(0)

def main():
    global page
    global done
    global total_count
    total_count = 1000
    page = 1
    done = False
    signal.signal(signal.SIGINT, handle_sigint)
    aggstart = time.time()

    wait = []
    for k in range(searchers):
        s = Searcher()
        s.start()
        wait.append(s)
    
    for k in range(parsers):
        p = Parser()
        p.start()
	wait.append(p)

    for thread in wait:
        thread.join()

    t = time.time() - aggstart
    return t
    print('finished %s in %fs' % (date_range, t))

if __name__ == '__main__':
    size_ranges = ['<1', '>=1']
    prev_time = time.time()
    start_date = date(2015, 10, 26)
    end_date = date(2016, 01, 01)

    for single_date in daterange(start_date, end_date):
	curr = single_date.strftime('%Y-%m-%d')
	date_range = curr

	for s in size_ranges:
	    size_range = s
	    t = main()
	    print('finished %s, %s in %fs' % (date_range, size_range, t))
    
    path = os.path.join(script_dir, 'missed.json')
    with open(path, 'w') as fd:
	for miss in missed:
		fd.write('%s\n' % miss)
