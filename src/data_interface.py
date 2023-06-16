import pandas as pd
import numpy as np
import time

STATUS_CODE = {0: "NEW",
              1: "RUNNING",
              2: "ERRONOUS",
              10: "DONE",
              11: "EXPIRED",
              12: "FAILED",
              13: "MANUAL"
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

    def set_LastMessageTimestamp(self, id_, timestamp=0):
        if not timestamp:
            timestamp = time.time()
        self.data.loc[id_,"LastMessageTimestamp"] = timestamp

    def get_LastMessageTimestamp(self, id_):
        return self.data.loc[id_,"LastMessageTimestamp"]
       
    def set_MsgCount(self, id_, msg_count):
        self.data.loc[id_,"msg_count"] = msg_count
    
    def get_MsgCount(self, id_):
        return self.data.loc[id_,"msg_count"]

    def set_Status(self, id_, status):
        self.data.loc[id_,"Status"] = status

    def get_Status(self, id_):
        return self.data.loc[id_,"Status"]

    def set_ErrorCount(self, id_, count):
        self.data.loc[id_,"ErrorCount"] = count  

    def get_ErrorCount(self, id_):
        return self.data.loc[id_,"ErrorCount"]
    
    def set_Rank(self, id_, rank):
        self.data.loc[id_,"ErrorCount"] = rank  

    def get_Rank(self, id_):
        return self.data.loc[id_,"ErrorCount"]
    
    def save(self):
        print("saved backlog")
        self.data.to_csv(self.path)