import os, requests, json, subprocess, time, pymongo, signal, sys
from multiprocessing import Process, Queue, Lock, Value, current_process

clone_dir = '/home/data/repos'
parsers = 12

def parser(lock):
    client = pymongo.MongoClient()
    fromdb = client.metadata.copy
    missdb = client.metadata.missed

    while True:
        with lock:
            repo = fromdb.find_one()
            fromdb.delete_one({'id': repo['id']}) 

        path = os.path.join(clone_dir, str(repo['id'])[0], str(repo['id'])[1], str(repo['id']))
        print(path)
        if os.path.exists(path):
            continue

        start = time.time()
        try:
            subprocess.check_output(['timeout', '240', 'git', 'clone', '--depth', '1', repo['clone_url'], path], stderr=subprocess.STDOUT)
        except Exception as e:
            missdb.insert_one(repo)
            print(e)
            try:
                subprocess.check_output(['rm', '-rf', path])
            except:
                pass
            continue

        strip(path)
        t = time.time() - start
        print('cloning and stripping took %fs' % t)

def strip(path):
    empty_check = [path]
    dirs = [path]
    ftypes = {}

    while len(dirs) != 0:
        d = dirs.pop(-1)
        for rel in os.listdir(d):
            f = os.path.join(d, rel)
	    if os.path.islink(f):
                os.unlink(f)
            elif os.path.isdir(f):
		dirs.append(f)
                empty_check.insert(0, f)
            elif os.path.isfile(f) and not f.endswith('.py'):
                os.remove(f)                

    for d in empty_check:
        if os.listdir(d) == []:
            os.rmdir(d)

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
