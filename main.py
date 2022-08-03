#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -*- coding: utf-8 -*-
import re
import time
import random
import math
import numpy as np
import pandas as pd
import importlib
from tinderweb import TinderAutomator
from data_interface import Allowance, Backlog
from gpt3 import Gpt3
import logging
from selenium.common.exceptions import *


# In[2]:


path_prefix = "/Users/philippskudlik/local_dev/tndr/automator/"


# In[3]:


STATUS_CODE = {0: "NEW",
              1: "RUNNING",
              2: "DONE",
              3: "EXPIRED",
              4: "ERRONOUS"}


# In[4]:


# create logger with 'spam_application'
logger = logging.getLogger('TA')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler('run.log', 'w', 'utf-8')
fh.setLevel(logging.INFO)
logger.addHandler(fh)


# In[5]:


import chromedriver_autoinstaller
chromedriver_autoinstaller.install()


# In[6]:


# initialize automator
ta = TinderAutomator()


# In[7]:


# initialize allowance
allowance = Allowance(path=path_prefix+"gpt_allowance.csv")
logger.info("Remaining Tokens for today: "+str(allowance.get_tokens()))

# initialize backlog
backlog = Backlog(path=path_prefix+"backlog.csv")


# In[8]:


# collect matches
try:
    tasks = ta.generate_tasklist()
except AttributeError:
    time.sleep(4)
    tasks = ta.generate_tasklist()


# In[9]:


# update backlog
backlog.update_with_tasks(tasks)


# In[10]:


# initialize Gpt3
gpt = Gpt3()
gpt_dryrun=False
msg_dryrun=False


# In[11]:


min_date = pd.Timestamp.today()-pd.Timedelta(days=14)
name_me = "Chris"


# In[12]:


start = 0
limit = 10

run_report_header = ""
new_done = 0
logger.info("Remaining tokens: %d",allowance.get_tokens())
logger.info("Open tasks: %d", sum(backlog.data.Status <= 1))
for count, (id_, task) in enumerate(backlog.data[(backlog.data.Status <= 1)][start:start+limit].iterrows()):
    logger.info("-------------------------------------------------")
    logger.info("------------------Processing Nr. %d------------------", count+1)
    if allowance.get_tokens() <= 0:
        logger.warning("Ran out of tokens...")
        break
    # open task
    ta.get(task.Link)
    name_them = task.Name
    logger.info("------------------%s------------------",name_them)
    time.sleep(6)
    
    # get basic information
    try:
        bio, match_date = ta.read_match_info()
    except Exception as e:
        print(e)
        break
        logger.info(str(e))
        #backlog.data.loc[id_,"Status"] = 4
        logger.info("------------------Status: Erronous.")
        continue

    ### CHECK NACH ABBRUCHBEDINGUNGEN
    if (match_date < min_date):
        backlog.data.loc[id_,"Status"] = 3
        logger.info("------------------Status: Expired.")
        continue
        
    myturn, conversation = ta.get_conversation()
    msg_count = len(conversation)
    backlog.data.loc[id_,"msg_count"] = msg_count
    if not myturn:
        logger.info("------------------Status: Running. Still no reply...")
        break

    if msg_count >= 12:
        backlog.data.loc[id_,"Status"] = 2
        logger.info("------------------Status: Done. Message count reached! Yeay!")
        run_report_header = f"Conversation with {name_them} is ready to be taken over! (Nr. {count+1})\n"
        new_done += 1
        continue

    ### INITIATE OR CONTINUE CONVERSATION
    logger.info("------------------Status: Running. Conversing...")
    # update status
    backlog.data.loc[id_,"Status"] = 1
    # build prompt
    if msg_count==0:
        prompt = gpt.build_prompt(bio, name_them, name_me, initial=True)
    else:
        prompt = gpt.build_prompt(conversation, name_them, name_me, initial=False)
    logger.info("::PROMPT::")
    logger.info(prompt)
    # get gpt response
    reply = gpt.request(prompt, stop_sequences=[name_them+":",name_me+":",name_them+" responds"], temperature=0.9, dryrun=gpt_dryrun)
    #update token allowance
    allowance.decrement()    
    logger.info("::GPT::")
    logger.info(reply)
    ta.write_message(reply, dryrun=msg_dryrun)
    time.sleep(3)

# Create run report
run_report_base = "Run from "+str(time.ctime())+f"\nProcessed {count+1} matches.\n{allowance.get_tokens()} tokes remaining for today.\nOpen conversations: {len(backlog.data[backlog.data.Status <= 1])}"
run_report = run_report_header + ("\n" * (run_report_header != "")) + run_report_base
logger.info(run_report)

#update backlog
backlog.save()


# In[15]:


with open("run.log", "r") as f:
    content = "".join(f.readlines())
run_report = run_report+"\n\n\n"+"".join(content)


# In[13]:


import yagmail
yag = yagmail.SMTP("chrssku@gmail.com", oauth2_file=path_prefix+"client_secret_701724446788-id894tinkh6b1j2q86fkkv00d3t5h8b3.apps.googleusercontent.com.json")
TO = "pskudlik@gmail.com"
yag.send(TO, "Run Report",run_report, attachments=['run.log'])
print(run_report)


# In[14]:


ta.end_session()


# In[54]:





# In[ ]:




