# -*- coding: utf-8 -*-
import os
import configparser
import time

from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from src.tinderweb import TinderAutomator
from dotenv import load_dotenv
load_dotenv()
config = configparser.ConfigParser()
config.read(os.environ["LOVEBOT_CONFIG"])

path_prefix = config['DEFAULT']["PathPrefix"]

# initialize automator and models
ta = TinderAutomator(chromedata_path=config['DEFAULT']['ChromeDataPath'])
ta.start_browser()

running = True
login_completed = False
while running:
    if not login_completed:
        try:
            element = ta.browser.find_element(By.CSS_SELECTOR, '[title="Mein Profil"]')
            name = element.text
            print("Login successful.")
            print(f"Hi, {name}!")
            print("You may close the window now.")
            login_completed = True
        except:
            pass
    try:
       ta.browser.title
       time.sleep(5)
    except NoSuchWindowException as e:
       print("Window closed.")
       running = False