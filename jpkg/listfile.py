class ListFile:
    def __init__(self, filename):
        self.filename = filename
        self.database = set()
        try:
            with open(self.filename, 'r') as fid:
                for line in fid:
                    self.database.add(line.strip())
        except FileNotFoundError:
            pass


    def add(self, item):
        self.database.add(item)


    def remove(self, item):
        self.database.remove(item)


    def write(self):
        l = list(self.database)
        l.sort()
        with open(self.filename, 'w') as fid:
            for item in l:
                fid.write(item + '\n')
