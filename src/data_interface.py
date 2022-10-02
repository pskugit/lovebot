import pandas as pd
import numpy as np

STATUS_CODE = {0: "NEW",
              1: "RUNNING",
              2: "ERRONOUS",
              10: "DONE",
              11: "EXPIRED",
              12: "FAILED"
              }

STATUS_CODE_INV = {v: k for k, v in STATUS_CODE.items()}      
        
class Backlog():
    def __init__(self, path="backlog.csv"):
        self.data = pd.DataFrame()
        self.path = path
        self.load()
        
    def load(self): 
        # Todo: if no file exists, create file
        try:
            self.data = pd.read_csv(self.path, index_col=0)
        except FileNotFoundError:
            print("Warning: Backlog not found in {self.path}")
    
    def update_with_tasks(self, tasks):
        tasks = pd.DataFrame.from_dict(tasks, orient="index")
        backlog_new = tasks[~tasks.index.isin(self.data.index)]
        print(len(backlog_new),"new matches.")
        self.data = pd.concat((backlog_new,self.data))
        self.data = self.data.drop("Rank", axis=1)
        self.data = self.data.merge(tasks.Rank, how="left", left_index=True, right_index=True)
        self.data.Rank = self.data.Rank.fillna(self.data.Rank.max())
        # all new matches get rank -1
        self.data.Rank = np.where(self.data.Status == STATUS_CODE_INV["NEW"],-1,self.data.Rank)
        # all erronous matched get rank 0
        self.data.Rank = np.where(self.data.Status == STATUS_CODE_INV["ERRONOUS"],-1,self.data.Rank)
        self.data = self.data.sort_values("Rank")

    def save(self):
        self.data.to_csv(self.path)