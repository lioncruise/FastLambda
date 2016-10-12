import os, requests, json, subprocess, time, pymongo, signal, sys
from parse import parse_files
from multiprocessing import Process, Queue, Lock, Value, current_process
from datetime import timedelta, date

script_dir = os.path.dirname(os.path.realpath(__file__))

searchers = 12

date_range = ''
size_range = ''

def searcher(queue, page, page_lock, req_count, req_lock, prev_time, total_count):
    client = pymongo.MongoClient()
    db = client.pyscrape

    while True:
        with page_lock:
            my_page = page.value
            #print('%s got page %s' % (current_process(), my_page))
            page.value += 1

        if total_count.value < (my_page+1)*100:
            return

        try:
            results = search(my_page, req_count, req_lock, prev_time, total_count)
        except Exception as e:
            print('results threw exception: %s' % e)
            return

        for result in results:
            _id = result['id']
            if db.packages.find({'id': _id, 'size': result['size']}).count() == 0:
                pkg = format_pkg(result)
                db.metadata.insert_one(pkg)

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
    
def daterange(start, end):
    for n in range(int ((end - start).days)):
	yield start + timedelta(n)

def main():
    global req_count
    global total_count
    total_count = 1000

    aggstart = time.time()
    
    procs = []
    queue = Queue()

    page = Value('i', 1)
    page_lock = Lock()
    req_lock = Lock()
    prev_time = Value('d', time.time())
    total_count = Value('i', 1000)

    for k in range(searchers):
        s = Process(target=searcher, args=(queue, page, page_lock, req_count, req_lock, prev_time, total_count))
        s.start()
        procs.append(s)

    for proc in procs:
        proc.join()
        proc.terminate()
    
    return time.time() - aggstart

if __name__ == '__main__':
    req_count = Value('i', 0)
    #size_ranges = ['<=1', '1..40', '>40']
    size_ranges = ['>0']
    start_date = date(2010, 01, 01)
    end_date = date(2015, 01, 01)
    for single_date in daterange(start_date, end_date):
        curr = single_date.strftime('%Y-%m-%d')
        date_range = curr

        for s in size_ranges:
            size_range = s
            t = main()
            print('finished %s, %s in %fs' % (date_range, size_range, t))

