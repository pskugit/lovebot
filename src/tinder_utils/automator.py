import time
import pickle
import pandas as pd

import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *

from src.tinder_utils.conversation import Conversation
from src.tinder_utils.profile import Profile

import urllib
from PIL import Image
import os
import re
import ssl
import socket
hostname = 'www.python.org'
context = ssl.create_default_context()
with socket.create_connection((hostname, 443)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print(ssock.version())

SLEEP_MULTIPLIER = 2

class TinderAutomator():  
    def __init__(self, initial_state="swiping", startpage="https://tinder.com/app/recs", chromedata_path="chromedata", headless=False):
        self.headless = headless
        self.initial_state = initial_state
        self.startpage = startpage
        self.chromedata_path = chromedata_path
        self.log_path = 'runs.log'
        self.browser = None
  
    def start_browser(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--start-maximized")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches",["enable-automation"])
        #options.add_argument("user-data-dir=chromedata")
        if self.chromedata_path is not None:
            options.add_argument("--user-data-dir="+self.chromedata_path)
            print(f"Starting browser with user data at {self.chromedata_path}")
        if self.headless:
            options.add_argument("--headless")
        browser = webdriver.Chrome(options=options)
        self.browser = browser
        self.reset()

    def wait(self, sec):
        time.sleep(sec*SLEEP_MULTIPLIER)

    def find_by_xpath(self, xpath, silent=False):
        try:
            element = self.browser.find_element(By.XPATH, xpath)
        except NoSuchElementException:
            if not silent:
                print("Element not found:", xpath)
            return None
        return element

    def find_and_click(self, xpath):
        element = self.find_by_xpath(xpath)
        if element is not None:
            element.click()
            self.wait(0.5)

    def find_btn(self, searchstring):
        btns = self.browser.find_elements(By.CLASS_NAME, "focus-button-style")
        for btn in btns:
            if btn.text == searchstring:
                return btn

    def get(self,url):
        self.browser.get(url)
        self.wait(0.5)
            
    def quit(self):
        self.browser.quit()
        print("browser closed.")

    def reset(self):
        self.current_profile = None
        self.state = self.initial_state
        self.new_listings = []
        self.wait(0.5)
        self.get(self.startpage)
        self.wait(3)
                   
    def _get_new(self, newtype, match_or_messageListItems):
        """type can be 'matches' or 'conversations'"""
        class_name_dict = {
            "matches": 'Ell',
            "running_conversations": 'messageListItem__name',
        }
        matches = {}
        for i, mli in enumerate(match_or_messageListItems):
            match_meta = {}
            match_meta["Status"] = 0
            match_meta["msg_count"] = 0
            try:
                match_meta["Name"] = mli.find_element(By.CLASS_NAME, class_name_dict[newtype]).text
            except NoSuchElementException:
                continue
            if match_meta["Name"] is None:
                match_meta["Name"] = "UNKNOWN"
            match_meta["Link"] = mli.get_attribute("href")
            id_ = match_meta["Link"].split("/")[-1]
            match_meta["Rank"] = i
            match_meta["ErrorCount"] = 0
            match_meta["LastMessageTimestamp"] = None
            match_meta["RepliedTo"] = None
            matches[id_] = match_meta
        return matches
               
    def generate_tasklist(self):
        """
        collects all matches, both new ones (_get_new) and old ones (_get_new) 
        """
        self.find_btn("Matches").click()
        matchListItems = self.browser.find_elements(By.CLASS_NAME, 'matchListItem')
        new_matches = self._get_new("matches",matchListItems)
        self.wait(0.5)
        self.find_btn("Nachrichten").click()
        messageListItem = self.browser.find_elements(By.CLASS_NAME, 'messageListItem')
        running_conversations = self._get_new("running_conversations",messageListItem)
        tasks = {**new_matches, **running_conversations}
        return tasks
    
    def get_conversation(self):
        # Todo: make Conversation a class
        message_list = []
        messeges = self.browser.find_elements(By.CLASS_NAME, 'msg')
        for messege in messeges:
            message_text = messege.text        
            theirs = "msg--received" in messege.get_attribute("class")
            try:
                hearted = messege.find_element(By.XPATH, "../..").find_elements(By.CSS_SELECTOR, '[role="checkbox"]')[0].get_attribute("aria-checked")
            except IndexError:
                hearted = None
            message_list.append((theirs, hearted, message_text))
        
        conversation = Conversation(message_list)        
        return conversation
    
    def write_message(self, text, dryrun=True): 
        if not text:
            return   
        JS_ADD_TEXT_TO_INPUT = """
          var elm = arguments[0], txt = arguments[1];
          elm.value = txt;
          elm.dispatchEvent(new Event('change'));
          """
        textfeld = self.browser.find_element(By.TAG_NAME, 'textarea')
        self.browser.execute_script(JS_ADD_TEXT_TO_INPUT, textfeld, text)
        textfeld.send_keys(' ')
        textfeld.send_keys(Keys.BACKSPACE)
        if not dryrun:
            self.find_btn("SENDEN").click()
             
    def read_match_info(self):
        try:
            bio = self.browser.find_elements(By.CLASS_NAME, 'BreakWord')[-1].text
        except (NoSuchElementException, IndexError):
            #print("Bio is empty. Returning default text.") #new bahavior handles empty bio in gpt class directly
            bio = ""#Looking for someone interesting. Do you know something fun to experience?"
        
        # header is the first div in the "chat" element
        header = self.browser.find_element(By.CLASS_NAME, "chat").find_element(By.XPATH, "./div")
        header_text = header.text
        # Find the date of matching
        match_date = re.findall("\d+.\d+.\d+",header_text)[0].split(".")
        match_date = pd.Timestamp(year=int(match_date[2]),month=int(match_date[1]),day=int(match_date[0])) 
        return bio, match_date
    
    def end_session(self):
        #with open("cookies.pkl", "wb") as f:
        #    pickle.dump(self.browser.get_cookies() , f)
        self.browser.quit() 
        
    def save_cookies(self):
        with open("cookies.pkl", "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                self.browser.add_cookie(cookie)
    
     #define left and right button
    def find_swipe_buttons(self):
        found_all = False
        try:
            for btn in self.browser.find_elements(By.TAG_NAME, "button"):
                if btn.text =="NEIN":
                    left_btn = btn
                if btn.text =="GEFÄLLT MIR":
                    right_btn = btn
                if btn.text == "SUPER-LIKE":
                    superlike_btn = btn
            found_all = True
        except NoSuchElementException:
            found_all = False
        if found_all:
            return left_btn, right_btn, superlike_btn
        else:
            return None
        
    def remove_overlay(self):
        #text = self.browser.find_element(By.XPATH, '//*').text
        #match_layer = "IT’S A" in text.split("\n")
        #if match_layer:
        self.wait(1)
        self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        self.browser.find_element(By.TAG_NAME, 'body').click()
        self.wait(3)

    def open_card(self):
        profiles = self.browser.find_element(By.CSS_SELECTOR, '[aria-label="Profile"]')
        # tinder always shows 3 profiles at a time. Only the middle one (hence index 1) is the visible one
        name = profiles.find_elements(By.CSS_SELECTOR, '[ itemprop="name"]')[1].text
        try:
            age = profiles.find_elements(By.CSS_SELECTOR, '[itemprop="age"]')[1].text
        except NoSuchElementException:
            age = "0"

        self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_UP)

        open_card = self.browser.find_element(By.CLASS_NAME, "profileContent")
        checksum = hex(len(open_card.text)).split("x")[-1]

        distance = 0
        textblock_list = open_card.text.rsplit("\n")
        for textblock in textblock_list:        
            if "Kilometer entfernt" in textblock:
                km_block = re.findall(r'\d+ Kilometer entfernt', textblock)[0]
                distance = int(km_block.split(" ")[0])

        self.current_profile = Profile((name, age, distance, checksum))
        return name, age, distance, checksum


    def scrape_images(self, folder_name="images"):
        downloads=[]
        name, age, distance, checksum = self.current_profile.infos
        open_card = self.browser.find_element(By.CLASS_NAME, "profileContent")
        carousel = open_card.find_element(By.CLASS_NAME, "profileCard__slider")
        pictures = carousel.find_elements(By.CLASS_NAME, "keen-slider__slide")

        pic_count = len(pictures)
        self.current_profile.pic_count = pic_count
        print(f"\n{name}, {age}, {distance}km, {checksum}: Scraping {pic_count} picture(s)...")

        for i, picture in enumerate(pictures):
            self.wait(0.1) 
            filename = f"{name}_{age}_{distance}_{checksum}_{i}".replace(" ", "")
            pic = picture.find_element(By.CLASS_NAME, "profileCard__slider__img")
            # get url and extension
            url = pic.value_of_css_property("background-image")[5:-2]
            if ".webp" in url:
                extension = ".webp"
            else:
                extension = ".jpg"

            #download file to location
            download = folder_name+"/"+filename+extension
            try:
                urllib.request.urlretrieve(url, download)
            except ValueError:
                print("failed to download image")
                self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
                continue

            # convert to jpg if neccessary
            if extension == ".webp":
                download_jpg = download[:-4]+"jpg"
                im = Image.open(download).convert("RGB")
                im.save(download_jpg, "jpeg")
                os.remove(download)
                download = download_jpg
            downloads.append(download)

            # space to continue
            self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
        self.current_profile.image_paths = downloads
        return downloads