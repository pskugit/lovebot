import random
from PIL import Image
from matplotlib import pyplot as plt

class Profile():
    def __init__(self, open_card_infos):
        # set via open_card()
        self.infos = open_card_infos # (name, age, distance, checksum)
        # set via scrape_images()
        self.pic_count = None 
        self.image_paths = None 
        # set via model results in main script
        self.has_bikini = None 
        self.likescore = None 
        # set via on_choice()
        self.choice = None 
        # score threshold and max distance is set here to be easier to control (Standard = 0.5)
        self.score_threshold = 0.5
        self.max_distance = 1000

    
    def __str__(self):
        return f"{self.infos[0]}_{self.infos[1]}_{self.infos[2]}_{self.infos[3]}\n\npic_count: {self.pic_count}\nbikini pic: {self.has_bikini}\nlikescore: {self.likescore}".replace("-","\n")
        #return f"name: {self.infos[0]}\nage: {self.infos[1]}\ndistance: {self.infos[2]}\n\npic_count: {self.pic_count}\nimage_paths: -{'-'.join(self.image_paths)}\n\nbikini pic: {self.has_bikini}\nlikescore: {self.likescore}\n\nchoice: {self.choice}".replace("-","\n")

    def set_score_threshold(self, value):
        self.score_threshold = value
    
    def set_max_distance(self, value):
        self.max_distance = value
        
    def show_images(self):
        fig = plt.figure(figsize=(16, 7))
        for i, path in enumerate(self.image_paths):
            img = Image.open(path)
            # Adds a subplot at the 1st position
            fig.add_subplot(1, self.pic_count, i+1)
            plt.imshow(img)
            plt.axis('off')
        plt.show()
    
    def evaluate(self):
        self.choice = "left"
        # distance > 1000 km
        if self.infos[2] > self.max_distance:
            self.choice = "left"
            print(f"Evaluated choice to {self.choice} because of distance. Max distance is {self.max_distance}")
        elif self.has_bikini:
            self.choice = "right"
            print(f"Evaluated choice to {self.choice} because of bikini")
        else:
            if self.likescore is None:
                self.choice = "right" if random.random() >= self.score_threshold else "left"
                print(f"Evaluated choice to {self.choice} because of random choice")
                return
            self.choice = "right" if self.likescore >= self.score_threshold else "left"
            print(f"Evaluated choice to {self.choice} because of likescore")
        #self.choice = random.choice(["left", "right"])