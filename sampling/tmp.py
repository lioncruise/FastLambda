import os, requests, json, subprocess, time, pymongo, signal, sys
from multiprocessing import Process, Queue, Lock, Value, current_process

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_dir, '..'))

sample_dir = '/home/eoakes/sample'
client = pymongo.MongoClient()
db = client.sample.files

def scrape(path):
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
                ftype = os.path.splitext(f)[1]
                if ftype == '':
                    ftype = 'none'
                else:
                    ftype = ftype.strip('.').lower()

                if ftype == 'txt' and os.path.getsize(f) > 8600000:
                    print(f)

    return

def main():
    scrape(sample_dir)

if __name__ == '__main__':
    main()
