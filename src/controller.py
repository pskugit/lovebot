import time
from statemachine import StateMachine, State

SLEEP_MULTIPLIER = 2

class Controller(StateMachine):
    swiping = State('swiping', initial=True)
    texting = State('texting')
    scraping = State('scraping')
    chat = swiping.to(texting)
    scrape = swiping.to(scraping)
    choice = scraping.to(swiping)
    swipe = texting.to(swiping)
    
    def wait(self, sec):
        time.sleep(sec*SLEEP_MULTIPLIER)

    def on_enter_swiping(self):
        print('Swiping!')

    def on_choice(self):
        self.model.current_profile.evaluate()
        left_btn, right_btn, superlike_btn = self.model.find_swipe_buttons()
        choice_dict = {"left": left_btn,
                        "right": right_btn,
                        "superlike": superlike_btn}
        choice = self.model.current_profile.choice
        choice_dict[choice].click()
        self.wait(1)
        super_like_dialog = self.model.find_by_xpath('//*[@id="q1595321969"]/main/div/button[1]/div[2]/div[2]', silent=True)
        if super_like_dialog is not None:
            self.model.remove_overlay()
            choice_dict[choice].click()
        print(f'Swiping {choice}. Closing card!')
        self.model.remove_overlay()
        self.model.current_profile = None
        self.wait(0.5)

    def on_scrape(self, folder_name):
        print("on_scrape folder_name:",folder_name)
        open_card_infos = self.model.open_card()
        print('Opened card! Retrieved open_card_infos.')
        print(open_card_infos)
        downloads = self.model.scrape_images(folder_name=folder_name)
        #print('Saved images...')
        #print(downloads)
    
    def __enter__(self):
        self.model.start_browser()
        return self

    def __exit__(self, *args): 
        self.model.end_session()
