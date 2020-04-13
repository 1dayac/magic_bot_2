import xml.etree.ElementTree as ET
import copy

tree = ET.parse("C:\\Users\\meles\\Downloads\\hotlist.dek")
chunk_size = 100

round = int((len(tree.findall('Cards')) - 1)/chunk_size) + 1
print(round)

for i in range(round):
    new_tree = copy.deepcopy(tree)
    deck = new_tree.getroot()
    cards = deck.findall('Cards')
    print(len(cards))
    cards_to_delete = cards[0:100*i] + cards[100*(i+1):]
    print(len(cards_to_delete))
    for card in cards[0:100*i]:
        deck.remove(card)
    for card in cards[100*(i+1):]:
        deck.remove(card)
    print(len(deck.findall('Cards')))

    new_tree.write("hotlist" + str(i) + ".dek")



