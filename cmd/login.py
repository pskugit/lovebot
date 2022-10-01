# -*- coding: utf-8 -*-
import os
import configparser

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