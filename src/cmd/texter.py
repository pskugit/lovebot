# -*- coding: utf-8 -*-
import re
import os
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
from src.data_interface import Backlog, STATUS_CODE, STATUS_CODE_INV
from src.gpt3 import Gpt3, Allowance

import configparser
config = configparser.ConfigParser()
config.read(os.environ["LOVEBOT_CONFIG"])

SLEEP_MULTIPLIER = int(config["DEFAULT"]["SleepTime"])
path_prefix = config['DEFAULT']["PathPrefix"]
name_me = config['DEFAULT']["Name"]

logger = logging.getLogger('TA')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
timestr = time.strftime("%Y%m%d-%H%M")
logging_file_name = f'logs/texter_run_{timestr}.log'
fh = logging.FileHandler(path_prefix+logging_file_name, 'w', 'utf-8')
fh.setLevel(logging.INFO)
logger.addHandler(fh)
logger.info("Remaining Tokens for today: ")

# initialize automator
ta = TinderAutomator(chromedata_path=config['DEFAULT']['ChromeDataPath'])

# initialize allowance
allowance = Allowance(path=path_prefix+"memory/gpt_allowance.csv")

# initialize backlog
backlog = Backlog(path=path_prefix+"memory/backlog.csv")

# initialize Gpt3
gpt = Gpt3(allowance)
logger.info("Remaining Tokens for today: "+str(gpt.allowance.get_tokens()))
gpt_dryrun=False
msg_dryrun=False

min_date = pd.Timestamp.today()-pd.Timedelta(days=60)

def main():
    start = 0
    limit = 25
    no_reply_limit = 5

    with Controller(ta) as controller:
        # collect matches
        time.sleep(4)
        tasks = ta.generate_tasklist()
        # update backlog
        backlog.update_with_tasks(tasks)
        # start texting
        run_report_header = ""
        new_done = 0
        no_reply_counter = 0
        logger.info("Remaining tokens: %d",allowance.get_tokens())
        logger.info("Open tasks: %d", sum(backlog.data.Status <= 10))
        try:
            for count, (id_, task) in enumerate(backlog.data[(backlog.data.Status < 10)][start:start+limit].iterrows()):
                # todo: same loop for erronous matches plus a coounter to indicate the retry count
                logger.info("-------------------------------------------------")
                logger.info("------------------Processing Nr. %d------------------", count+1)
                if gpt.allowance.get_tokens() <= 0:
                    logger.warning("Ran out of tokens...")
                    break
                # open task
                ta.get(task.Link)
                name_them = task.Name
                logger.info("------------------%s------------------",name_them)
                time.sleep(6)
                
                # GET BASIC INFORMATION
                try:
                    bio, match_date = ta.read_match_info()
                    backlog.data.loc[id_,"ErrorCount"] = 0
                    #update status
                    backlog.data.loc[id_,"Status"] = STATUS_CODE_INV["RUNNING"]
                except Exception as e:
                    #logger.info(str(e))
                    logger.info("Some error while fetching match info...")
                    backlog.data.loc[id_,"ErrorCount"] += 1
                    errorcount= backlog.data.loc[id_,"ErrorCount"]
                    if errorcount > 10:
                        backlog.data.loc[id_,"Status"] = STATUS_CODE_INV["FAILED"]
                    else:
                        backlog.data.loc[id_,"Status"] = STATUS_CODE_INV["ERRONOUS"]
                    logger.info(f"------------------Status: Erronous. ErrorCount:{errorcount}")
                    continue

                ### CHECK NACH ABBRUCHBEDINGUNGEN
                # is the match still relevant?
                if (match_date < min_date):
                    backlog.data.loc[id_,"Status"] = STATUS_CODE_INV["EXPIRED"]
                    logger.info("------------------Status: Expired.")
                    continue
                # is it my turn to send a message?    
                myturn, conversation = ta.get_conversation()
                msg_count = len(conversation)
                backlog.data.loc[id_,"msg_count"] = msg_count
                if not myturn:
                    logger.info("------------------Status: Running. Still no reply...")
                    #Todo: check if last message is older than 2days
                    #Todo: if so, set extra_shot to true 
                    # else check no_reply_counter and 'continue'
                    no_reply_counter +=1
                    if no_reply_counter > no_reply_limit:
                        break
                    continue
                # is the conversation ready for manual control?
                if msg_count >= 15:
                    backlog.data.loc[id_,"Status"] = STATUS_CODE_INV["DONE"]
                    logger.info("------------------Status: Done. Message count reached! Yeay!")
                    logger.info(gpt._conversation_to_body(conversation,name_them))
                    run_report_header = f"Conversation with {name_them} is ready to be taken over! (Nr. {count+1})\n"
                    new_done += 1
                    continue

                ### INITIATE OR CONTINUE CONVERSATION
                logger.info("------------------Status: Running. Conversing...")
                # build prompt
                if msg_count==0:
                    prompt = gpt.build_prompt(bio, name_them, name_me, initial=True)
                else:
                    prompt = gpt.build_prompt(conversation, name_them, name_me, initial=False)
                logger.info("::PROMPT::")
                logger.info(prompt)
                # get gpt response (also updates token allowance)
                reply = gpt.request(prompt, stop_sequences=[name_them+":",name_me+":",name_them+" responds", name_them+"'s response"], temperature=0.9, dryrun=gpt_dryrun)
                # post processing
                reply = reply.strip("\"\'")
                logger.info("::GPT::")
                logger.info(reply)
                ta.write_message(reply, dryrun=msg_dryrun)
                # handled successfully
                time.sleep(3)

            # Create run report
            run_report_base = "Run from "+str(time.ctime())+f"\nProcessed {count+1} matches.\n{gpt.allowance.get_tokens()} tokes remaining for today.\nOpen conversations: {len(backlog.data[backlog.data.Status <= 1])}"
            run_report = run_report_header + ("\n" * (run_report_header != "")) + run_report_base
            logger.info(run_report)
        finally:
            #update backlog
            backlog.save()

    #if new_done:
    #    import yagmail
    #    yag = yagmail.SMTP(config['EMAIL']['sender'], oauth2_file=path_prefix+config['EMAIL']['OauthFilePath'])
    #    TO = config['EMAIL']['receiver']
    #    yag.send(TO, "New Conversation finished",run_report, attachments=['../logs/run.log'])
    #    print(run_report)
    return True
    
if __name__ == "__main__":
    main()