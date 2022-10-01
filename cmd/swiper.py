# %%
# -*- coding: utf-8 -*-
import re
import time
import random
import math
import numpy as np
import pandas as pd
import importlib
import logging
from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
load_dotenv()

from src.tinderweb import TinderAutomator, Controller, SLEEP_MULTIPLIER
from src.data_interface import Allowance, Backlog
from src.gpt3 import Gpt3
from src.mymodels import TRAINED_MODELS

import urllib
from PIL import Image
import os
import re
import shutil
from matplotlib import pyplot as plt
import cv2

import configparser
config = configparser.ConfigParser()
config.read(os.environ["LOVEBOT_CONFIG"])

# %%
SLEEP_MULTIPLIER = int(config["DEFAULT"]["SleepTime"])
path_prefix = config['DEFAULT']["PathPrefix"]
scraping_folder_path = config['SCRAPING']["ScrapingFolder"]

# %%
logger = logging.getLogger('TA')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
timestr = time.strftime("%Y%m%d-%H%M")
logging_file_name = f'logs/swiper_run_{timestr}.log'
fh = logging.FileHandler(path_prefix+logging_file_name, 'w', 'utf-8')
fh.setLevel(logging.INFO)
logger.addHandler(fh)

# %%
# initialize automator and models
ta = TinderAutomator(chromedata_path=config['DEFAULT']['ChromeDataPath'])


# %%
# initialize models
bikini_model = TRAINED_MODELS["bikini"](weights_path=config["MODELS"]["Bikini"])
beauty_model = TRAINED_MODELS["beauty"](weights_path=config["MODELS"]["Beauty"])

# %%
with Controller(ta) as controller:
    counter = 0
    reset_counter = 0
    target_count = int(config["SCRAPING"]["Count"])
    while (counter < target_count) and (reset_counter < int(config["SCRAPING"]["RetryCount"])):
        print(f"\n{counter}/{target_count}, errors {reset_counter}")
        try:
            controller.scrape(scraping_folder_path)
            preds, logitss = bikini_model.inference_pathlist(ta.current_profile.image_paths)
            ta.current_profile.has_bikini = "bikini" in preds
            # save image seperately if bikini
            bikini_index_list = [i for i, pred in enumerate(preds) if pred == 'bikini']
            bikini_paths = [ta.current_profile.image_paths[i] for i in bikini_index_list]
            for bikini_path in bikini_paths:
                shutil.copy2(bikini_path, scraping_folder_path+"/bikini/"+bikini_path.split("/")[-1])

            if not ta.current_profile.has_bikini:
                preds, logitss = beauty_model.inference_pathlist(ta.current_profile.image_paths)
                ta.current_profile.beautyscore = preds.count("hot") / len(preds)
            
            print(ta.current_profile)
            #ta.current_profile.show_images()

            controller.choice()
            counter += 1
            reset_counter = 0
        except:
            reset_counter +=1
            print("error... resetting",reset_counter)
            ta.reset()


