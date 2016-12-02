'''
Requests repositories from GitHub API, clones them, parses them, and deletes them. Better to get all metadata first.
'''

import os, requests, json, subprocess, time, pymongo, signal, sys
from parse import parse_files
from multiprocessing import Process, Queue, Lock, Value, current_process
from datetime import timedelta, date

script_dir = os.path.dirname(os.path.realpath(__file__))

searchers = 6
parsers = 6

date_range = ''
size_range = ''

def searcher(queue, page, page_lock, req_count, req_lock, prev_time, done, done_lock, total_count):
    client = pymongo.MongoClient()
    db = client.pyscrape

    while True:
        with done_lock:
            if done.value > 0:
                done.value += 1
                return

        with page_lock:
            my_page = page.value
            #print('%s got page %s' % (current_process(), my_page))
            page.value += 1

        if total_count.value < (my_page+1)*100:
            with done_lock:
                done.value += 1
            return

        try:
            results = search(my_page, req_count, req_lock, prev_time, total_count)
        except Exception as e:
            print('results threw exception: %s' % e)
            with done_lock:
                done.value += 1
            return

        if len(results) == 0:
            time.sleep(0.2)

        for result in results:
            _id = result['id']
            if db.packages.find({'_id': _id}).count() == 0:
                #print('%s putting %s into queue' % (current_process(), _id))
                queue.put(result)

def parser(queue, done, done_lock):
    client = pymongo.MongoClient()
    db = client.pyscrape

    while True:
        pkg = None
        while not pkg:
            try:
                pkg = queue.get(block=True, timeout=1.5)
            except:
                with done_lock:
                    if done.value == searchers:
                        #print('parser exiting')
                        return

        pkg = format_pkg(pkg)
        if db.packages.find({'_id': pkg['_id']}).count() > 0:
            continue

        #print('%s got %s from queue' % (current_process(), pkg['_id']))
        path = '%s/clone/%s' % (script_dir, pkg['_id'])
        if os.path.isdir(path):
            #print('another thread is already trying this one')
            continue

        start = time.time()
        try:
            out = subprocess.check_output(['timeout', '120', 'git', 'clone', '--depth', '1', pkg['clone_url'], path], stderr=subprocess.STDOUT)
        except Exception as e:
            print('clone %s failed' % pkg['clone_url'])
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

def search(my_page, req_count, req_lock, prev_time, total_count):
    req_lock.acquire()
    if req_count.value >= 30:
        while time.time()-prev_time.value < 60.1:
            time.sleep(0.1)

        prev_time.value = time.time()
        req_count.value = 0

    q = 'language:python created:%s size:%s' % (date_range, size_range)
    payload = {'q': q, 'per_page': 100, 'page': my_page}

    r = requests.get('https://api.github.com/search/repositories', auth=(os.environ['GITHUB_USER'], os.environ['GITHUB_PW']), params=payload)
    req_count.value += 1
    req_lock.release()

    if r.status_code != 200:
        if my_page == 1:
            raise Exception('invalid username or password')
	else:
	    raise Exception(r.text)

    if r.json()['total_count'] > 1000:
	print('missed: %s' % date_range)
        total_count.value = 1000
    else:
        total_count.value = r.json()['total_count']

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

def daterange(start, end):
    for n in range(int ((end - start).days)):
	yield start + timedelta(n)

def main():
    global req_count
    global total_count
    total_count = 1000

    aggstart = time.time()

    
    sprocs = []
    queue = Queue()
    done = Value('i', 0)
    done_lock = Lock()

    page = Value('i', 1)
    page_lock = Lock()
    req_lock = Lock()
    prev_time = Value('d', time.time())
    total_count = Value('i', 1000)

    procs = []
    for k in range(searchers):
        s = Process(target=searcher, args=(queue, page, page_lock, req_count, req_lock, prev_time, done, done_lock, total_count))
        s.start()
        procs.append(s)
    
    for k in range(parsers):
        p = Process(target=parser, args=(queue, done, done_lock))
        p.start()
        procs.append(p)


    for proc in procs:
        proc.join()
        proc.terminate()
    
    return time.time() - aggstart

if __name__ == '__main__':
    req_count = Value('i', 0)
    size_ranges = ['<=1', '1..40', '>40']
    start_date = date(2016, 01, 01)
    end_date = date(2016, 10, 12)
    for single_date in daterange(start_date, end_date):
        curr = single_date.strftime('%Y-%m-%d')
        date_range = curr

        for s in size_ranges:
            size_range = s
            t = main()
            print('finished %s, %s in %fs' % (date_range, size_range, t))

