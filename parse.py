import re, sys, json, os, ast

class Parser(ast.NodeVisitor):
    def __init__(self, local):
        self.mods = {}
        self.asnames = {}
        self.local = local

    def visit_Import(self, node):
        for alias in node.names:
            split = alias.name.split('.', 1)
            mod = split[0]

            if mod not in self.mods and mod not in self.local:
                self.mods[mod] = []

            for submod in split[1:]:
                if submod not in self.mods[mod]:
                    self.mods[mod].append(submod)

    def visit_ImportFrom(self, node):
        split = node.module.split('.', 1)
        mod = split[0]
        if len(split) == 1:
            prefix = ''
        else:
            prefix = '%s.' % split[1]

        if mod in self.local:
            return
        if mod not in self.mods:
            self.mods[mod] = []

        for alias in node.names:
            name = '%s%s' % (prefix, alias.name)
            asname = alias.asname

            if name not in self.mods[mod]:
                self.mods[mod].append(name)
            if asname and asname not in self.asnames:
                self.asnames[asname] = name

    def visit_Call(self, node):
        func = node.func
        name = self.get_name(node.func)
        attr = self.get_attr(node.func)

        if name in self.mods:
            mod = name
        elif name in self.asnames:
            mod = self.asnames[name]
        else:
            return

        if attr not in self.mods[mod]:
            self.mods[mod].append(attr)
    
    def get_name(self, func):
        if hasattr(func, 'id'):
            return func.id

        if hasattr(func, 'value'):
            return self.get_name(func.value)

        return 'unknown'

    def get_attr(self, func):
        if type(func) == ast.Name:
            return None

        if type(func) == ast.Attribute:
            return func.attr

        return 'unknown'

def parse_file(s, local):
    tree = ast.parse(s)
    p = Parser(local)
    p.visit(tree)

    return p.mods

def parse_files(pyfiles):
    fstats = []
    local = []
    for f in pyfiles:
        n = os.path.basename(f)
        local.append(n.split('.py')[0])

    for f in pyfiles:
        with open(f, 'r') as fd:
            s = fd.read()
            try:
                fstats.append(parse_file(s, local))
            except Exception as e:
                print('failed to parse file %s because: %s' % (f, e))

    return fstats

if __name__ == '__main__':
    path = sys.argv[1]
    pyfiles = []
    for rel in os.listdir(path):
        f = os.path.join(path, rel)
        if f.endswith('.py'):
            pyfiles.append(f)

    fstats = parse_files(pyfiles)
    print(json.dumps(fstats, indent=4, sort_keys=True))
