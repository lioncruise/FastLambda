import sys, json, os

params = {'size':'size', 'forks_count':'forks', 'stargazers_count':'stars', 'watchers_count':'watchers'}

def format(param, fname):
    with open(fname, 'w') as fd:
        fd.write('# year mean median\n')

        for year in sorted(data):
            if param == 'size':
                data[year][param]['mean'] /= 1000
                data[year][param]['median'] /= 1000
            fd.write('%s %s %s\n' % (year, data[year][param]['mean'], data[year][param]['median']))

def main():
    for param in params:
        outfile = '%s.data' % params[param]
        path = os.path.join(os.path.dirname(__file__), 'bin', outfile)
        format(param, path)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: format_metadata.py <infile.json>')
        sys.exit(1)

    with open(sys.argv[1], 'r') as fd:
        data = json.load(fd)

    main()
