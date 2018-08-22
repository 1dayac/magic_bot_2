import sqlite3
from transitions import Machine, State
from pywinauto.application import Application
import pyautogui
import sys
import os
from enum import Enum
import math
import traceback
from selenium import webdriver
import win32api, win32con, win32process
import time, subprocess
import platform
from card import Card, Price
import xml.etree.ElementTree as ET

states_my = [State(name = 'initial'),
             State(name = 'login', on_enter = ['login']),
             State(name = 'checkbuyprices', on_enter = ['checkbuycard']),
             State(name='checksellprices', on_enter=['checksellcard']),
             State(name='compute_differences', on_enter=['compute_diff']),
             State(name='buy', on_enter=['buy_card']),
             State(name = 'update_binder_after_buying', on_enter = ['update_binder_after_buy']),
             State(name = 'sell', on_enter = ['sell_card']),
             State(name = 'update_binder_after_selling', on_enter = ['update_binder_after_sell']),
             State(name = 'close', on_enter = ['close_mtgo'])]

transitions = [
    {'trigger': 'go_to_login', 'source': 'initial', 'dest': 'login'},
    {'trigger': 'go_to_check_buy_prices', 'source': 'login', 'dest': 'checkbuyprices'},
    {'trigger': 'go_to_check_sell_prices', 'source': 'checkbuyprices', 'dest': 'checksellprices'},
    {'trigger': 'go_to_compute_differences', 'source': 'checksellprices', 'dest': 'compute_differences'},
    {'trigger': 'go_to_buy', 'source': 'compute_differences', 'dest': 'buy'},
    {'trigger': 'go_to_update', 'source': 'buy', 'dest': 'update_binder_after_buying'},
    {'trigger': 'go_to_sell', 'source': 'update_binder_after_buying', 'dest': 'sell'},
    {'trigger': 'go_to_update', 'source': 'sell', 'dest': 'update_binder_after_selling'},
    {'trigger': 'go_to_buy', 'source': 'update_binder_after_selling', 'dest': 'checkbuyprices'},
    {'trigger': 'go_to_restart', 'source': 'checkbuyrices', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'checksellprices', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'compute_differences', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'update_binder_after_selling', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'sell', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'buy', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'update_binder_after_buying', 'dest': 'close'},
    {'trigger': 'go_to_login', 'source': 'close', 'dest': 'login'}
]


if platform.system() == "Windows":
    chromedriver_path = r"C:\Users\IEUser\Desktop\magic_bot_2\chromedriver.exe"
else:
    chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"

card_pool = []
class HotlistProcessor(object):

    def __init__(self):
        self.start_from = "1"
        self.set = "1"
        self.rows = []
        self.driver_hotlist = None
        self.start = None
        self.i = 0


    def restart(self):
        self.start_from = "1"
        self.set = "1"
        self.rows = []
        self.driver_hotlist.quit()
        self.driver_hotlist = None
        self.start = None
        self.i = 0

    def openHotlist(self):
        card_pool = []
        url = "http://www.mtgotraders.com/hotlist/#/"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        self.driver_hotlist = webdriver.Chrome(chromedriver_path, options = chrome_options)
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

    def ParseAndDivideXML(self, xml):
        import xml.etree.ElementTree as ET
        import copy
        tree = ET.parse(xml)
        root = tree.getroot()
        number_of_cards = 20
        count = 0
        while True:
            print(count)
            if count * number_of_cards > len(list(root)):
                break
            temp_root = copy.deepcopy(root)
            start = 1 + count * number_of_cards
            end = 1 + (count + 1) * number_of_cards
            index = 0
            childs = list(temp_root)
            for i in range(1, start):
                temp_root.remove(childs[i])
            for i in range(end, len(childs)):
                temp_root.remove(childs[i])
            print(len(list(temp_root)))
            tree = ET(temp_root)
            tree.write(open(r'temp_xml\hotlist_' + str(count) + '.xml', 'w'), encoding='unicode')
            count += 1

    def processHotlist(self):
        self.rows = self.openHotlist()
        while self.i < len(self.rows):
            self.processRow(self.rows[self.i])
            self.i += 1

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
        price_struct = Price("", price, 10000, "HotListBot3", "", 0)
        card = Card(cardname, setname, price_struct, foil)
        if is_basic_land(card) or ((card.set == "MS2" or card.set == "MS3") and card.foil):
            return
        card_pool.append(card)
        os.remove('C:\Users\dmm2017\Downloads\hotlist.dek')
        self.driver_hotlist.get("http://www.mtgotraders.com/hotlist/data/download.php")
        self.ParseAndDivideXML(r'C:\Users\dmm2017\Downloads\hotlist.dek')


def is_basic_land(card):
    return card.name == "Swamp" or card.name == "Island" or card.name == "Mountain" or card.name == "Plains" or card.name == "Forest" or card.name.startswith("Urza's")


class NoConfirmTradeException(Exception):
    pass

def go_to_rectangle(rect, sleep = 0):
    pyautogui.moveTo((rect.left + rect.right)/2, (rect.top + rect.bottom)/2)
    time.sleep(sleep)

def double_click_multiple(window, times):
    rect = window.rectangle()
    for i in range(times):
        double_click_rectangle(rect)

def double_click_rectangle(rect, sleep = 0):
    pyautogui.click((rect.left + rect.right)/2, (rect.top + rect.bottom)/2, clicks=2, interval=0.1)
    time.sleep(sleep)

def click_rectangle(rect, sleep = 0):
    pyautogui.click((rect.left + rect.right)/2, (rect.top + rect.bottom)/2)
    time.sleep(sleep)

def right_click_rectangle(rect, sleep = 0):
    pyautogui.rightClick((rect.left + rect.right)/2, (rect.top + rect.bottom)/2)
    time.sleep(sleep)

def click_collection(app):
    click_rectangle(app['Magic: The Gathering Online'].window(auto_id="CollectionButton").rectangle(), 5)

def click_trade(app):
    click_rectangle(app['Magic: The Gathering Online'].window(auto_id="TradeButton", found_index = 0).rectangle(), 5)

def click_ok_button(app):
    click_rectangle(app.top_window().window(auto_id="OkButton").rectangle(), 5)

def close_chat(app):
    index = 0
    while True:
        index += 1
        try:
            if index == 100:
                break
            print("Try to close chat")
            click_rectangle(app['Magic: The Gathering Online'].window(auto_id="CloseButtom", found_index=0).rectangle())
            time.sleep(1)
            break
        except:
            pass

def get_tix_number(app, botname):
    import io
    import sys
    stringio = io.StringIO()
    previous_stdout = sys.stdout
    sys.stdout = stringio
    app.top_window().window(auto_id="ChatItemsControl").print_control_identifiers()
    sys.stdout = previous_stdout
    string = stringio.getvalue()
    num_of_tix = 0
    pos = string.rfind("Take")
    pos1 = string.find(" ", pos + 1) + 1
    pos2 = string.find(" ", pos1)
    num_of_tix = int(string[pos1: pos2])
    print("Taking " + str(num_of_tix) + " tix")
    return num_of_tix

class MTGO_bot(object):
    def __init__(self):
        self.sell_bot = "HotListBot3"
        try:
            self.app = Application(backend="uia").connect(path='MTGO.exe')
        except:
            subprocess.Popen(['cmd.exe', '/c', r'C:\Users\dmm2017\Desktop\mtgo.appref-ms'])
            time.sleep(5)
            self.app = Application(backend="uia").connect(path='MTGO.exe')

    def close(self):
        os.system("taskkill /f /im  MTGO.exe")

    def login(self):
        print("Starting...")
        try:
            click_rectangle(self.app.top_window().child_window(auto_id = "CloseButton").rectangle())
        except:
            pass
        try:
            self.app['Magic: The Gathering Online'].window(auto_id="UsernameTextBox").type_keys("Weill")
            self.app['Magic: The Gathering Online'].window(auto_id="PasswordBox").type_keys("Lastborn220")
            time.sleep(2.5)
            self.app['Magic: The Gathering Online'].window(auto_id="PasswordBox").type_keys("{ENTER}")
            pyautogui.press('enter')

            time.sleep(20)
            try:
                click_rectangle(self.app.top_window().child_window(auto_id="CloseButton").rectangle())
            except:
                pass

            click_collection(self.app)
            time.sleep(10)
            click_trade(self.app)
            time.sleep(10)

        except:
            pass
        try:
            click_rectangle(self.app.top_window().child_window(auto_id = "CloseButton").rectangle())
        except:
            pass

        try:
            click_collection(self.app)
            click_rectangle(self.app['Magic: The Gathering Online'].window(title="ABinder", found_index=0).rectangle())
            click_collection(self.app)
        except:
            pass
        while True:
            try:
                rect = self.app['Magic: The Gathering Online'].child_window(auto_id="DeckPane").child_window(title_re="Item: CardSlot:",
                                                                                           found_index=0).rectangle()
                right_click_rectangle(rect)
                click_rectangle(self.app['Magic: The Gathering Online'].child_window(title_re="Remove All", found_index=0).rectangle())
            except:
                break
        try:

            click_rectangle(self.app['Magic: The Gathering Online'].window(title="Other Products", found_index=1).rectangle())
            self.app['Magic: The Gathering Online'].window(auto_id="searchTextBox").type_keys("event{SPACE}tickets{ENTER}")
            right_click_rectangle(
                self.app['Magic: The Gathering Online'].child_window(title_re="Item: CardSlot: Event", found_index=0).rectangle())
        except:
            self.close_mtgo()

        try:
            click_rectangle(self.app['Magic: The Gathering Online'].child_window(title_re="Add All to", found_index=0).rectangle())
        except:
            try:
                click_rectangle(self.app['Magic: The Gathering Online'].child_window(title_re="Add 1 to", found_index=0).rectangle())
            except:
                pyautogui.moveRel(-10, 0)
                pyautogui.click()
                pass

        def sell_card(self):
            try:
                click_rectangle(self.app.top_window().child_window(auto_id="CloseButton").rectangle())
            except:
                pass
            try:
                print("Go to sell card...")
                print("Selling " + self.db_record[0] + " to " + self.db_record[6])
                try:
                    click_trade(self.app)
                    self.app.top_window().window(auto_id="searchTextBox").type_keys(self.db_record[6] + "{ENTER}")
                except:
                    return

                while not self.click_bot_trade(
                        self.db_record[6]) or self.is_trade_cancelled() or self.is_trade_stalled():
                    self.switch_bot()

                time.sleep(6)
                window_sell_name = "Trade: " + self.db_record[6]

                try:
                    num_of_tix = get_tix_number(self.app, self.db_record[6])
                except:
                    raise Exception
                try:
                    if num_of_tix != 0:
                        click_rectangle(
                            self.app[window_sell_name].window(title="Other Products", found_index=1).rectangle())
                        if self.db_record[6].startswith("Goat"):
                            self.app[window_sell_name].window(auto_id="searchTextBox").type_keys(
                                "event{SPACE}tickets{ENTER}")
                        double_click_multiple(
                            self.app[window_sell_name].child_window(title_re="Item: CardSlot: Event", found_index=0),
                            num_of_tix)
                except:
                    pass

                click_rectangle(self.app[window_sell_name].window(title="Submit", found_index=1).rectangle())
                time.sleep(5)
                try:
                    click_rectangle(self.app[window_sell_name].window(title="Submit", found_index=1).rectangle())
                except:
                    pass
                time.sleep(3)
                index = 0
                while True:
                    try:
                        index += 1
                        click_rectangle(
                            self.app[window_sell_name].window(title="Confirm Trade", found_index=1).rectangle())
                        time.sleep(1)
                        break
                    except:
                        if index == 10:
                            raise NoConfirmTradeException()
                        pass

                close_chat(self.app)
                index = 0
                while True:
                    try:
                        index += 1
                        print("Trying to close window with stuff")
                        click_rectangle(
                            self.app.top_window().window(title="Added to your Collection:", found_index=0).window(
                                auto_id="TitleBarCloseButton").rectangle())
                        time.sleep(1)
                        break
                    except:
                        if index == 20:
                            return
                        try:
                            print("Trying to close window without stuff")
                            click_rectangle(self.app.top_window().window(auto_id="OkButton", found_index=0).rectangle())
                            break
                        except:
                            pass

            except NoConfirmTradeException:
                try:
                    click_rectangle(self.app.top_window().window(title="Cancel Trade", found_index=0).rectangle())
                    close_chat(self.app)
                except:
                    print(sys.exc_info()[0])
                    print(sys.exc_info()[1])
                    traceback.print_exc(file=sys.stdout)
                    pass
            except:
                print("Unexpected error:", sys.exc_info()[0])
                print("Unexpected error:", sys.exc_info()[1])
                traceback.print_exc(file=sys.stdout)

    def switch_bot(self):
        if self.db_record[6] == "HotListBot3":
            self.db_record[6] = "HotListBot4"
        elif self.db_record[6] == "HotListBot4":
            self.db_record[6] = "HotListBot"
        elif self.db_record[6] == "HotListBot":
            self.db_record[6] = "HotListBot2"
        elif self.db_record[6] == "HotListBot2":
            self.db_record[6] = "HotListBot3"
        if self.db_record[6] == "GoatBots1":
            self.db_record[6] = "GoatBots2"
        elif self.db_record[6] == "GoatBots2":
            self.db_record[6] = "GoatBots3"
        elif self.db_record[6] == "GoatBots3":
            self.db_record[6] = "GoatBots1"
        self.app['Magic: The Gathering Online'].window(auto_id="searchTextBox").type_keys(self.db_record[6] + "{ENTER}")

    def checkbuyprices(self):
        processor = HotlistProcessor()
        processor.processHotlist()

while True:
    try:
        my_bot = MTGO_bot()
        my_MTGO_bot_Machine = Machine(model=my_bot, states=states_my, transitions=transitions, initial='initial')
        my_bot.go_to_login()
        while True:
            try:
                my_bot.go_to_check_buy_prices()
                my_bot.go_to_check_sell_prices()
                my_bot.go_to_compute_differences()
                my_bot.go_to_buy()
                my_bot.go_to_update()
                my_bot.go_to_sell()
                my_bot.go_to_update()

            except:
                my_bot.go_to_restart()
                my_bot.__init__()
                my_bot.go_to_login()

    except:
        pass