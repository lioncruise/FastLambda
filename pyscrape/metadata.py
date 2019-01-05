import os, requests, time, pymongo, signal, datetime

client = pymongo.MongoClient()
table = client.java.metadata

def search(page, date, size):
    global total_count
    global prev_time
    global req_count

    if req_count >= 30:
        while time.time()-prev_time < 60.1:
            time.sleep(0.1)

        prev_time = time.time()
        req_count = 0

    q = 'language:java created:%s size:%s' % (date, size)
    payload = {'q': q, 'per_page': 100, 'page': page}

    r = requests.get('https://api.github.com/search/repositories', auth=(os.environ['GITHUB_USER'], os.environ['GITHUB_PW']), params=payload)
    req_count += 1

    if r.status_code != 200:
        raise Exception(r.text)

    if r.json()['total_count'] > 1000:
	print('missed: %s' % date_range)
        total_count = 1000
    else:
        total_count = r.json()['total_count']

    return r.json()['items']
    
def daterange(start, end):
    for n in range(int ((end - start).days)):
	yield start + datetime.timedelta(n)

def main():
    global total_count
    global req_count
    global prev_time
    total_count = 1000
    req_count = 0
    prev_time = time.time()

    size_ranges = ['<5', '>=5']
    start_date = datetime.date(2010, 01, 01)
    end_date = datetime.date(2016, 12, 01)

    for single_date in daterange(start_date, end_date):
        date = single_date.strftime('%Y-%m-%d')

        for size in size_ranges:
            t = time.time()
            for page in range(1, 11):
                try:
                    results = search(page, date, size)
                except Exception as e:
                    print('search threw exception: %s' % e)
                    break

                if len(results) > 0:
                    table.insert_many(results)

                if total_count < (page)*100:
                    break

            print('finished %s, %s in %fs' % (date, size, time.time()-t))

if __name__ == '__main__':
    main()
