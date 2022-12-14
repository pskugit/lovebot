# -*- coding: utf-8 -*-
import os
import time
import random
import pandas as pd
import logging

from src.tinderweb import TinderAutomator, Controller, SLEEP_MULTIPLIER
from src.data_interface import Backlog, STATUS_CODE, STATUS_CODE_INV
from src.gpt3 import Gpt3, Allowance
from src.utils import load_config

path_prefix, config = load_config()

SLEEP_MULTIPLIER = int(config["DEFAULT"]["SleepTime"])
name_me = config['DEFAULT']["Name"]
manual_overtake_symbol = config['TEXTING']["ManualOvertakeSymbol"]
openai_api_key = config['MODELS']["OpenAI"]

logger = logging.getLogger('TA')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
timestr = time.strftime("%Y%m%d-%H%M")
os.makedirs(path_prefix+"logs", exist_ok=True)
logging_file_name = f'logs/texter_run_{timestr}.log'
fh = logging.FileHandler(path_prefix+logging_file_name, 'w', 'utf-8')
fh.setLevel(logging.INFO)
logger.addHandler(fh)
logger.info("Remaining Tokens for today: ")

# initialize automator
ta = TinderAutomator(chromedata_path=config['DEFAULT']['ChromeDataPath'])

# initialize allowance
os.makedirs(path_prefix+"memory", exist_ok=True)
allowance = Allowance(path=path_prefix+"memory/gpt_allowance.csv")

# initialize backlog
backlog = Backlog(path=path_prefix+"memory/backlog.csv")

# initialize Gpt3
gpt = Gpt3(openai_api_key, allowance)
logger.info("Remaining Tokens for today: "+str(gpt.allowance.get_tokens()))
gpt_dryrun=False
msg_dryrun=False

min_date = pd.Timestamp.today()-pd.Timedelta(days=60)

def main():
    start = 0
    limit = 25
    no_reply_limit = 10

    with Controller(ta) as controller:
        start_time = str(time.ctime())
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
        open_tasks = sum(backlog.data.Status <= 10)
        logger.info("Open tasks: %d", open_tasks)
        if not open_tasks:
            logger.info("No new matches or open tasks!")
            return

        try:
            for count, (id_, task) in enumerate(backlog.data[(backlog.data.Status < 10)][start:start+limit].iterrows()):
                # reset temporary variables
                double_down = False
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

                # get conversation 
                conversation = ta.get_conversation()
                msg_count = len(conversation)

                ### CHECK NACH ABBRUCHBEDINGUNGEN
                # is the match still relevant?
                if (match_date < min_date):
                    backlog.data.loc[id_,"Status"] = STATUS_CODE_INV["EXPIRED"]
                    logger.info("------------------Status: Expired.")
                    continue
                
                # is the conversation ready for manual control?
                if msg_count >= 12:
                    backlog.data.loc[id_,"Status"] = STATUS_CODE_INV["DONE"]
                    logger.info("------------------Status: Done. Message count reached! Yeay!")
                    logger.info(gpt._conversation_to_body(conversation,name_them))
                    run_report_header = f"Conversation with {name_them} is ready to be taken over! (Nr. {count+1})\n"
                    new_done += 1
                    continue

                # was manual control triggered? Manuel overtrake code in config
                if conversation.find_in_conversation(manual_overtake_symbol, only_mine=True):
                    backlog.data.loc[id_,"Status"] = STATUS_CODE_INV["MANUAL"]
                    continue

                # is it my turn to send a message?    
                backlog.data.loc[id_,"msg_count"] = msg_count
                if not conversation.myturn:
                    logger.info("------------------Status: Running. Still no reply...")
                    #Todo: check if last message is older than 2days
                    #Todo: if so, set extra_shot to true 
                    # else check no_reply_counter and 'continue'
                    no_reply_counter +=1
                    if no_reply_counter > no_reply_limit:
                        break
                    if (random.random() < 0.05) and not conversation.is_doubled_down and (msg_count >= 5):
                        print("...doubling down...")
                        double_down = True
                    else:
                        continue

                ### INITIATE OR CONTINUE CONVERSATION
                logger.info("------------------Status: Running. Conversing...")
                # build prompt
                if msg_count==0:
                    prompt = gpt.build_prompt(bio, name_them, name_me, initial=True)
                else:
                    prompt = gpt.build_prompt(conversation, name_them, name_me, initial=False, double_down=double_down, last_n=0)
                logger.info("::PROMPT::")
                logger.info(prompt)
                # get gpt response (also updates token allowance)
                reply = gpt.request(prompt, stop_sequences=[name_them+":",name_me+":",name_them+" responds", name_them+"'s response"], temperature=0.9, max_tokens=200, dryrun=gpt_dryrun)
                # post processing
                reply = reply.strip("\"\'")
                # avoid accidental manal overtake
                reply = reply.replace(manual_overtake_symbol,"") 
                logger.info("::GPT::")
                logger.info(reply)
                ta.write_message(reply, dryrun=msg_dryrun)
                time.sleep(3)

            # Create run report
            run_report_base = "Run from "+start_time+f"\nI checked on {count+1} matches.\n{gpt.allowance.get_tokens()} GPT tokes remaining for today.\nOpen conversations: {len(backlog.data[backlog.data.Status <= 1])}"
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
    return run_report
    
if __name__ == "__main__":
    main()