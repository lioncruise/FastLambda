import os, requests, json, subprocess, time, pymongo, signal, sys
from parse import parse_files
from multiprocessing import Process, Queue, Lock, Value, current_process

clone_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), clone)
my_shard = 'a'

parsers = 2

def parser(lock):
    client = pymongo.MongoClient()
    fromdb = client.split[my_shard]

    while True:
        with lock:
            repo = fromdb.find_one()
            fromdb.delete_one({'id': repo['id']})

        path = os.path.join(clone_dir, repo['id'])

        start = time.time()
        try:
            subprocess.check_output(['git', 'clone', '--depth', '1', repo['clone_url'], path], stderr=subprocess.STDOUT)
            subprocess.check_output(['find', path, '-not', '-name', '"*.py"', '-delete'], stderr=subprocess.STDOUT)
            subprocess.check_output(['find', path, '-type', 'd', '-empty', '-delete'], stderr=subprocess.STDOUT)
            
        except Exception as e:
            db_result = fromdb.insert_one(repo)
            print('clone %s failed, reinserting' % repo['clone_url'])
            subprocess.check_output(['rm', '-rf', path])
            continue

        t = time.time() - start
        print('cloning and stripping took %fs' % t)

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

    tarball = '%s.tar.gz' % my_shard
    subprocess.check_output(['tar', '-cvzf', tarball, clone_dir])
    print('successfully compressed')

if __name__ == '__main__':
    main()
