import re
from card import Card, Price

class GoatbotsParser(object):
    def findall(self, s):
        '''Yields all the positions of
        the pattern p in the string s.'''
        pattern = re.compile("[1-8]x")
        i = pattern.search(s)
        if i == None:
            return
        i = i.start()
        while True:
            yield i
            m = pattern.search(s, i + 1)
            if m == None:
                break
            i = m.start()

    def find_name(self, line, pos):
        name = line[pos + 3:].split('(')[0]
        price = float(line[pos + 3:].split('(')[1].split(')')[0])
        foil = False
        if name[-1] == " ":
            foil = True
            name = name[:-1]

        set = "UNK"
        if name[-1].isupper() or name[-1].isnumeric():
            set = name[name.rfind(" ") + 1 :]
            name = name[:name.rfind(" ")]
        return name, set, foil, price

    def parse(self, line):
        found = []
        cards = []
        positions = self.findall(line)
        for i in positions:
            num = int(line[i])
            name, set, foil, price = self.find_name(line, i)
            if name + set + str(foil) in found:
                continue
            found.append(name + set + str(foil))
            cards.append(Card(name, set, Price("", 0.0, price, "", "GoatBots3", num), foil))
            print(str(num) + " " + name + " " + set + " " + str(foil) + " " + str(price))
        return cards