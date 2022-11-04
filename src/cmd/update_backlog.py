# -*- coding: utf-8 -*-
import os
import time
from dotenv import load_dotenv

from src.tinderweb import TinderAutomator, Controller, SLEEP_MULTIPLIER
from src.data_interface import Backlog
from src.utils import load_config

import configparser
path_prefix, config = load_config()

def main():
    # initialize automator
    ta = TinderAutomator(chromedata_path=config['DEFAULT']['ChromeDataPath'])

    # initialize backlog
    backlog = Backlog(path=path_prefix+"memory/backlog.csv")

    with Controller(ta) as controller:
        # collect matches
        time.sleep(4*SLEEP_MULTIPLIER)
        tasks = ta.generate_tasklist()
        # update backlog
        backlog.update_with_tasks(tasks)
        print(f"Open tasks: {sum(backlog.data.Status <= 10)}")
        # save backlog
        backlog.save()
    
if __name__ == "__main__":
    main()