import os, requests, json, subprocess, time, pymongo, signal, sys
from parse import parse_files
from multiprocessing import Process, Queue, Lock, Value, current_process

script_dir = os.path.dirname(os.path.realpath(__file__))

parsers = 12

def parser(lock):
    client = pymongo.MongoClient()
    fromdb = client.toscrape.metadata
    todb = client.pyscrape.repos

    while True:
        with lock:
            repo = fromdb.find_one()
            fromdb.delete_one({'id': repo['id']})

        path = '%s/clone/%s' % (script_dir, repo['_id'])

        start = time.time()
        try:
            out = subprocess.check_output(['git', 'clone', '--depth', '1', repo['clone_url'], path], stderr=subprocess.STDOUT)
        except Exception as e:
            db_result = fromdb.insert_one(repo)
            print('clone %s failed, reinserting' % repo['clone_url'])
            subprocess.check_output(['rm', '-rf', path])
            continue

        t = time.time() - start
        print('cloning took %fs' % t)

        start = time.time()
        parse_result = scrape(path)
        t = time.time() - start
        print('parsing took %fs' % t)

        agg_lines = 0
        for f in parse_result:
            agg_lines += f['lines']

        repo['files'] = parse_result
        repo['agg_lines'] = agg_lines

        db_result = todb.insert_one(repo)

        try:            
            subprocess.check_output(['rm', '-rf', path])
        except:
            print("failed to remove %s" % path)

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

def main():
    lock = Lock()

    procs = []
    for k in range(parsers):
        p = Process(target=parser, args=(lock,))
        p.start()
        procs.append(p)

    for proc in procs:
        proc.join()
        proc.terminate()

if __name__ == '__main__':
    main()
