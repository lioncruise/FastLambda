import os, requests, json, subprocess, time, pymongo, signal, sys
from multiprocessing import Process, Queue, Lock, Value, current_process

script_dir = os.path.dirname(os.path.realpath(__file__))
clone_dir = '/home/data/repos'

cloners = 12

def cloner(lock):
    client = pymongo.MongoClient()
    fromdb = client.metadata.copy

    while True:
        with lock:
            repo = fromdb.find_one()
            if not repo:
                return

            fromdb.delete_one({'id': repo['id']})

        path = os.path.join(clone_dir, str(repo['id'])[0], str(repo['id'])[1], str(repo['id']))

        start = time.time()
        try:
            subprocess.check_output(['git', 'clone', '--depth', '1', repo['clone_url'], path], stderr=subprocess.STDOUT)
            subprocess.check_output(['rm', '-rf', os.path.join(path, '.git')])
        except Exception as e:
            db_result = fromdb.insert_one(repo)
            print('clone %s failed, reinserting' % repo['clone_url'])

            try:
                subprocess.check_output(['rm', '-rf', path])
            except:
                pass

            continue

        t = time.time() - start
        print('cloning took %fs' % t)

def main():
    lock = Lock()

    procs = []
    for k in range(cloners):
        p = Process(target=cloner, args=(lock,))
        p.start()
        procs.append(p)

    for proc in procs:
        proc.join()
        proc.terminate()

if __name__ == '__main__':
    main()
