import os, requests, json, subprocess, time, pymongo, signal, sys
from multiprocessing import Process, Queue, Lock, Value, current_process

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_dir, '..'))

from ..parse import parse_files

clone_dir = '/home/data/repos'
fromdb = client.metadata.copy
todb = client.full.repos
djangodb = client.full.django

parsers = 12

def parser(lock):
    client = pymongo.MongoClient()

    while True:
        with lock:
            repo = fromdb.find_one()
            if not repo:
                return
            fromdb.delete_one({'id': repo['id']})

        path = os.path.join(clone_dir, str(repo['id'])[0], str(repo['id'])[1], str(repo['id']))
        if not os.path.isdir(path):
            client.metadata.cloned.delete_one({'id': repo['id']})
            continue

        start = time.time()
        parse_results = scrape(path)
        t = time.time() - start
        print('parsing took %fs' % t)

        pylines = 0
        for f in parse_results[0]:
            pylines += f['lines']

        repo['pyfiles'] = parse_results[0]
        repo['filetypes'] = parse_results[1]
        repo['pylines'] = pylines

        todb.insert_one(repo)

        for f in repo['pyfiles']:
            if 'django' in f['mods']:
                djangodb.insert_one(repo)
                break
                
def scrape(path):
    pyfiles = []
    dirs = [path]
    ftypes = {}

    while len(dirs) != 0:
        d = dirs.pop(-1)
        for rel in os.listdir(d):
            f = os.path.join(d, rel)
	    if os.path.islink(f):
	        continue
            elif os.path.isdir(f):
		dirs.append(f)
            elif os.path.isfile(f):
                if f.endswith('.py'):
                    pyfiles.append(f)

                ftype = os.path.splitext(f)[1]
                if ftype == '':
                    ftype = 'none'
                else:
                    ftype = ftype.strip('.').lower()

                if not ftype in ftypes:
                    ftypes[ftype] = []

                ftypes[ftype].append(os.path.getsize(f))

    return [parse_files(pyfiles), ftypes]

def main():
    aggstart = time.time()

    lock = Lock()
    procs = []
    for k in range(parsers):
        p = Process(target=parser, args=(lock,))
        p.start()
        procs.append(p)


    for proc in procs:
        proc.join()
        proc.terminate()
    
    return time.time() - aggstart

if __name__ == '__main__':
    t = main()
    print('finished parsing in %fs' % t)
