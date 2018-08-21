import sqlite3
from transitions import Machine, State
from pywinauto.application import Application
import pyautogui
import sys
import os
from enum import Enum
import math
import traceback


states_my = [State(name = 'initial'),
             State(name = 'login', on_enter = ['login']),
             State(name = 'checkbuyprices', on_enter = ['checkbuycard']),
             State(name='checkbuyprices', on_enter=['checkbuycard']),
             State(name='checksellprices', on_enter=['checksellcard']),
             State(name='compute_differences', on_enter=['compute_diff']),
             State(name='buy', on_enter=['buy_card']),
             State(name = 'update_binder_after_buying', on_enter = ['update_binder_after_buy']),
             State(name = 'sell', on_enter = ['sell_card']), State(name = 'update_binder_after_selling', on_enter = ['update_binder_after_sell']), State(name = 'close', on_enter = ['close_mtgo'])]



