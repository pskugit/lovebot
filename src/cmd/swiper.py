import os
import time
import shutil
import logging
import importlib

from src.mymodels_onnx import TRAINED_MODELS
from src.tinderweb import TinderAutomator, Controller, SLEEP_MULTIPLIER
from src.utils import load_config

def main():
    path_prefix, config = load_config()

    SLEEP_MULTIPLIER = int(config["DEFAULT"]["SleepTime"])
    scraping_folder_path = config['SCRAPING']["ScrapingFolder"]
    os.makedirs(scraping_folder_path, exist_ok=True)

    # setup logger
    logger = logging.getLogger('TA')
    logger.setLevel(logging.INFO)
    timestr = time.strftime("%Y%m%d-%H%M")
    os.makedirs(path_prefix+"logs", exist_ok=True)
    logging_file_name = f'logs/swiper_run_{timestr}.log'
    fh = logging.FileHandler(path_prefix+logging_file_name, 'w', 'utf-8')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    # initialize automator
    ta = TinderAutomator(chromedata_path=config['DEFAULT']['ChromeDataPath'])

    # initialize models
    bikini_model = TRAINED_MODELS["bikini"](model_path=config["MODELS"]["Bikini"])
    os.makedirs(scraping_folder_path+"/bikini", exist_ok=True)
    like_model = TRAINED_MODELS["like"](model_path=config["MODELS"]["Like"])

    # setup controller and start the process
    with Controller(ta) as controller:
        start_time = str(time.ctime())
        counter = 0
        reset_counter = 0
        target_count = int(config["SCRAPING"]["Count"])
        while (counter < target_count) and (reset_counter < int(config["SCRAPING"]["RetryCount"])):
            print(f"\n{counter+1}/{target_count}, errors {reset_counter}")
            try:
                # scrape images
                controller.scrape(scraping_folder_path)
                # apply bikini model
                preds, logitss = bikini_model.inference_pathlist(ta.current_profile.image_paths, apply_softmax=True)
                ta.current_profile.has_bikini = "bikini" in preds
                # save image seperately if bikini
                bikini_index_list = [i for i, pred in enumerate(preds) if pred == 'bikini']
                bikini_paths = [ta.current_profile.image_paths[i] for i in bikini_index_list]
                for bikini_path in bikini_paths:
                    shutil.copy2(bikini_path, scraping_folder_path+"/bikini/"+bikini_path.split("/")[-1])
                # apply like model if neccesary
                if not ta.current_profile.has_bikini:
                    preds, logitss = like_model.inference_pathlist(ta.current_profile.image_paths, apply_softmax=True)
                    ta.current_profile.likescore = preds.count(like_model.classes[1]) / len(preds)
                
                print(ta.current_profile)
                #ta.current_profile.show_images()
                controller.choice()
                counter += 1
                reset_counter = 0
            except Exception as e:
                print(e)
                reset_counter +=1
                print("error... resetting",reset_counter)
                ta.reset()
    
    run_report = "Run from "+start_time+f"\nI swiped on {counter} matches for you.\nGood luck!"
    logger.info(run_report)
    return run_report

if __name__ == "__main__":
    main()

