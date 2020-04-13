from selenium import webdriver
import time
from card import Card, Price


class HotlistProcessor2(object):

    def __init__(self):
        self.start_from = "1"
        self.set = "1"
        self.rows = []
        self.driver_hotlist = None
        self.start = None
        self.i = 0
        self.chromedriver_path = r"C:\Users\meles\Desktop\magic_bot_3\chromedriver.exe"

    def restart(self):
        self.start_from = "1"
        self.set = "1"
        self.rows = []
        self.driver_hotlist.quit()
        self.driver_hotlist = None
        self.start = None
        self.i = 0

    def openHotlist(self):
        url = "http://www.mtgotraders.com/hotlist/#/"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        self.driver_hotlist = webdriver.Chrome(self.chromedriver_path, options = chrome_options)
        self.driver_hotlist.get(url)
        time.sleep(60)
        elems = self.driver_hotlist.find_elements_by_class_name('btn')
        elems[0].click()
        elems_2 = self.driver_hotlist.find_element_by_xpath(
            "//*[@id=\"mainContent\"]/div[2]/div[1]/div[2]/div[4]/div[1]/span[2]/span/ul/li[5]")
        elems_2.click()
        time.sleep(4)
        table = self.driver_hotlist.find_element_by_id('main-table')
        rows = table.find_elements_by_tag_name('tr')
        return rows



    def processHotlist(self):
        self.rows = self.openHotlist()
        self.start = time.time()
        cards = []
        while self.i < 200:#len(self.rows):
                cards.append(self.processRow(self.rows[self.i]))
                self.i += 1
        return cards

    def processRow(self, row):
        columns = row.find_elements_by_tag_name('td')
        if len(columns) < 3:
            return
        setname = columns[0].text
        self.set = setname
        cardname = columns[1].text

        price = float(columns[3].text)
        if setname < self.start_from:
            return
        if price < 0.05:
            return
        foil = cardname.endswith("*")
        if foil:
            cardname = cardname[:-7]

        print(setname + " " + cardname + " " + str(price))
        price_struct = Price("", price, 10000, "Hotlistbot3", "", 0)
        card = Card(cardname, setname, price_struct, foil)

        return card

