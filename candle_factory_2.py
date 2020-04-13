import sqlite3
from transitions import Machine, State
from pywinauto.application import Application
from pywinauto import keyboard
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
import copy
from card import Card, Price
from goatbot_parser import GoatbotsParser
from hotlist_processor import HotlistProcessor2
import xml.etree.ElementTree as ET

states_my = [State(name = 'initial'),
             State(name = 'login', on_enter = ['login']),
             State(name='download_and_split', on_enter=['download_and_split']),
             State(name = 'checkbuyprices', on_enter = ['checkbuyprices']),
             State(name=  'compute_differences', on_enter=['compute_diff']),
             State(name=  'buy', on_enter=['buy_cards']),
             State(name = 'update_binder_after_buying', on_enter = ['update_binder_after_buy']),
             State(name = 'sell', on_enter = ['sell_card']),
             State(name = 'update_binder_after_selling', on_enter = ['update_binder_after_sell']),
             State(name = 'close', on_enter = ['close_mtgo'])]

transitions = [
    {'trigger': 'go_to_login', 'source': 'initial', 'dest': 'login'},
    {'trigger': 'go_to_download_and_split', 'source': 'login', 'dest': 'download_and_split'},
    {'trigger': 'go_to_check_buy_prices', 'source': 'download_and_split', 'dest': 'checkbuyprices'},
    {'trigger': 'go_to_compute_differences', 'source': 'checkbuyprices', 'dest': 'compute_differences'},
    {'trigger': 'go_to_buy', 'source': 'compute_differences', 'dest': 'buy'},
    {'trigger': 'go_to_update', 'source': 'buy', 'dest': 'update_binder_after_buying'},
    {'trigger': 'go_to_sell', 'source': 'update_binder_after_buying', 'dest': 'sell'},
    {'trigger': 'go_to_update', 'source': 'sell', 'dest': 'update_binder_after_selling'},
    {'trigger': 'go_to_buy', 'source': 'update_binder_after_selling', 'dest': 'checkbuyprices'},
    {'trigger': 'go_to_restart', 'source': 'checkbuyprices', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'compute_differences', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'update_binder_after_selling', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'sell', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'buy', 'dest': 'close'},
    {'trigger': 'go_to_restart', 'source': 'update_binder_after_buying', 'dest': 'close'},
    {'trigger': 'go_to_login', 'source': 'close', 'dest': 'login'}
]


if platform.system() == "Windows":
    chromedriver_path = r"C:\Users\meles\Desktop\magic_bot_3\chromedriver.exe"
else:
    chromedriver_path = "/home/dmm2017/PycharmProjects/candle_factory/chromedriver"


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



class HotlistProcessor(object):
     def __init__(self):
         self.driver_hotlist = None


     def restart(self):
         self.driver_hotlist.quit()
         self.driver_hotlist = None

     def Download(self):
         url = "http://www.mtgotraders.com/hotlist/#/"
         chrome_options = webdriver.ChromeOptions()
         chrome_options.add_argument("--headless")

         chrome_options.add_experimental_option("prefs", {
             "download.default_directory": r"C:\Users\meles\Downloads",
             "download.prompt_for_download": False,
         })

         self.driver_hotlist = webdriver.Chrome(chromedriver_path, options = chrome_options)
         self.driver_hotlist.get(url)
         time.sleep(30)



     def ParseAndDivideXML(self):
         try:
             os.remove('C:\\Users\\meles\\Downloads\\hotlist.dek')
         except:
             pass

         self.driver_hotlist.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
         params = {'cmd': 'Page.setDownloadBehavior',
                   'params': {'behavior': 'allow', 'downloadPath': r"C:\Users\meles\Downloads"}}
         command_result = self.driver_hotlist.execute("send_command", params)

         self.driver_hotlist.get("http://www.mtgotraders.com/hotlist/data/download.php")


         time.sleep(10)
         tree = ET.parse("C:\\Users\\meles\\Downloads\\hotlist.dek")
         chunk_size = 100

         round = int((len(tree.findall('Cards')) - 1) / chunk_size) + 1
         print(round)

         for i in range(round):
             new_tree = copy.deepcopy(tree)
             deck = new_tree.getroot()
             cards = deck.findall('Cards')
             print(len(cards))
             cards_to_delete = cards[0:100 * i] + cards[100 * (i + 1):]
             print(len(cards_to_delete))
             for card in cards[0:100 * i]:
                 deck.remove(card)
             for card in cards[100 * (i + 1):]:
                 deck.remove(card)
             print(len(deck.findall('Cards')))
             new_tree.write("hotlist" + str(i) + ".dek")
         return round

class MTGO_bot(object):

    def __init__(self):
        self.sell_bot = "HotListBot3"
        try:
            self.app = Application(backend="uia").connect(path='MTGO.exe')
        except:
            subprocess.Popen(['cmd.exe', '/c', r'C:\Users\meles\Desktop\mtgo.appref-ms'])
            time.sleep(5)
            self.app = Application(backend="uia").connect(path='MTGO.exe')
        self.bot_to_buy = "GoatBots3"
        self.bot_to_sell = "HotListBot3"
        self.round = 0
        self.rounds_total = 0
        self.current_cards = []
        self.hotlist_cards = []
        self.cards_to_buy = []

    def close(self):
        os.system("taskkill /f /im  MTGO.exe")

    def close_mtgo(self):
        os.system("taskkill /f /im  MTGO.exe")

    def login(self):
        return
        print("Starting...")
        try:
            click_rectangle(self.app.top_window().child_window(auto_id = "CloseButton").rectangle())
        except:
            pass
        try:
            self.app['Magic: The Gathering Online'].window(auto_id="UsernameTextBox").type_keys("VerzillaBot")
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

    def compare_cards(self, card1, card2):
        if card1.name == card2.name and card1.foil == card2.foil and (card1.set == "UNK" or card1.set == card2.set):
            return True
        return False

    def compute_diff(self):
        for card_goatbots in self.current_cards:
            for card_hotlist in self.hotlist_cards:
                if self.compare_cards(card_goatbots, card_hotlist):
                            if card_hotlist.BestBuyPrice() > card_goatbots.BestSellPrice():
                            self.cards_to_buy.append(card_goatbots)
                            print(card_goatbots)

    def download(self):
        processor = HotlistProcessor()
        try:
            processor.Download()
            self.rounds_total = processor.ParseAndDivideXML()
            return True
        except:
            return False

    def download_and_split(self):
        #self.get_prices("GoatBots4")

        processor = HotlistProcessor2()
        self.hotlist_cards = processor.processHotlist()
        processor.restart()
        try:
            os.remove("~/Downloads/hotlist.deck")
        except:
            pass

        while not self.download():
            continue

    def sell_card(self):
        try:
            click_rectangle(self.app.top_window().child_window(auto_id="CloseButton").rectangle())
        except:
            pass
        try:
            print("Go to sell card...")
            print("Selling cards to " + self.bot_to_sell)
            try:
                click_trade(self.app)
                self.app.top_window().window(auto_id="searchTextBox").type_keys(self.bot_to_sell + "{ENTER}")
            except:
                return

            while not self.click_bot_trade(self.sell_bot, "Full Trade List") or self.is_trade_cancelled() or self.is_trade_stalled():
                self.switch_bot()

            time.sleep(6)

            window_sell_name = "Trade: " + self.bot_to_sell

            try:
                num_of_tix = get_tix_number(self.app, self.bot_to_sell)
            except:
                raise Exception

            try:
                if num_of_tix != 0:
                    click_rectangle(
                        self.app[window_sell_name].window(title="Other Products", found_index=1).rectangle())
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



    def click_bot_trade(self, botname, binder):
        index = 0
        while True:
            try:
                index += 1
                if index == 5:
                    return False
                go_to_rectangle(self.app['Magic: The Gathering Online'].window(title=botname).rectangle())
                click_rectangle(self.app['Magic: The Gathering Online'].window(title="Trade", found_index=1).rectangle())
                time.sleep(1)
                click_rectangle(self.app.top_window().window(auto_id=binder, found_index=0).rectangle())
                click_ok_button(self.app)
                return True
            except:
                pass

    def is_trade_cancelled(self):
        try:
            self.app.top_window().window(title="Trade Canceled", found_index=1).rectangle()
            click_rectangle(self.app.top_window().window(auto_id="OkButton", found_index=0).rectangle())
            return True
        except:
            return False

    def is_trade_stalled(self):
        try:
            click_rectangle(self.app.top_window().window(title="Trade Request", found_index=0).window(title="Cancel", found_index = 0).rectangle())
            return True
        except:
            return False

    def switch_sell_bot(self):
        if self.bot_to_sell == "HotListBot3":
            self.bot_to_sell = "HotListBot4"
        elif self.bot_to_sell == "HotListBot4":
            self.bot_to_sell = "HotListBot"
        elif self.bot_to_sell == "HotListBot":
            self.bot_to_sell = "HotListBot2"
        elif self.bot_to_sell == "HotListBot2":
            self.bot_to_sell = "HotListBot3"
        self.app['Magic: The Gathering Online'].window(auto_id="searchTextBox").type_keys(self.bot_to_sell + "{ENTER}")

    def switch_goatbot(self):
        if self.bot_to_buy == "GoatBots1":
            self.bot_to_buy = "GoatBots2"
        elif self.bot_to_buy == "GoatBots2":
            self.bot_to_buy = "GoatBots3"
        elif self.bot_to_buy == "GoatBots3":
            self.bot_to_buy = "GoatBots4"
        elif self.bot_to_buy == "GoatBots4":
            self.bot_to_buy = "GoatBots1"
        self.app['Magic: The Gathering Online'].window(auto_id="searchTextBox").type_keys(self.bot_to_buy + "{ENTER}")

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


    def is_trade_cancelled(self):
        try:
            self.app.top_window().window(title="Trade Canceled", found_index=1).rectangle()
            click_rectangle(self.app.top_window().window(auto_id="OkButton", found_index=0).rectangle())
            return True
        except:
            return False

    def findall(self, p, s):
        '''Yields all the positions of
        the pattern p in the string s.'''
        i = s.find(p)
        while i != -1:
            yield i
            i = s.find(p, i + 1)


    def buy_cards(self):
        pass

    def get_prices(self, botname):
        try:
            import io
            import sys
            stringio = io.StringIO()
            previous_stdout = sys.stdout
            sys.stdout = stringio
            self.app.top_window().window(auto_id="ChatItemsControl").print_control_identifiers()
            sys.stdout = previous_stdout
            string = stringio.getvalue()
            string2 = string[string.rfind(botname + ":   "):]
            parser = GoatbotsParser()
            self.current_goatbot_cards = parser.parse(string2)
        except:
            return None

    def checkbuyprices(self):
        try:
            print("Go to check GoatBots prices...")
            self.bot_to_buy = "GoatBots3"
            try:
                click_trade(self.app)
                self.app.top_window().window(auto_id="searchTextBox").type_keys(self.bot_to_buy + "{ENTER}")
            except:
                return

            if not self.click_bot_trade(self.bot_to_buy, "ABinder"):
                print("Bot is offline")
                self.is_trade_cancelled()

            while self.is_trade_cancelled() or self.is_trade_stalled():
                self.switch_goatbot()
                self.click_bot_trade(self.bot_to_buy, "ABinder")
                time.sleep(3)

            click_rectangle(self.app.top_window().window(title="Search Tools", found_index=0).rectangle())
            click_rectangle(self.app.top_window().window(title="Import Deck", found_index=0).rectangle())
            time.sleep(3)
            keyboard.SendKeys("hotlist" + str(self.round) + ".dek" + "{ENTER}")
            #self.app.top_window().window(title="File name:", found_index = 1).type_keys("hotlist" + str(self.round) + ".dek" + "{ENTER}")
            try:
                click_rectangle(self.app.top_window().window(auto_id="TitleBarCloseButton", found_index=0).rectangle())
            except:
                pass

            time.sleep(16)
            self.get_prices(self.bot_to_buy)
            click_rectangle(self.app.top_window().window(title="Cancel Trade", found_index=1).rectangle())
            time.sleep(3)
            close_chat(self.app)
        except:
            pass




while True:
    try:
        my_bot = MTGO_bot()
        my_MTGO_bot_Machine = Machine(model=my_bot, states=states_my, transitions=transitions, initial='initial')
        my_bot.go_to_login()
        my_bot.go_to_download_and_split()
        while True:
            try:
                my_bot.go_to_check_buy_prices()
                my_bot.go_to_compute_differences()
                my_bot.go_to_buy()
                my_bot.go_to_sell()
                my_bot.go_to_update()
            except:
                my_bot.go_to_restart()
                my_bot.__init__()
                my_bot.go_to_login()
                my_bot.download_and_split()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        traceback.print_exc(file=sys.stdout)