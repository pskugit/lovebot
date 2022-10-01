from csv import writer
import pandas as pd
import numpy as np

class Allowance():
    def __init__(self, path ="gpt_allowance.csv"):
        self.data = pd.DataFrame()
        self.path = path
        
    def read(self):
        self.data = pd.read_csv(self.path, header=0)
        if str(pd.Timestamp.today().date()) == self.data.Date.iloc[-1]:
            self.tokens = self.data.Tokens.iloc[-1]
        else:
            with open(self.path,'a') as fd:
                fd.write("\n"+str(pd.Timestamp.today().date())+",50")
                self.tokens = 50
    
    def get_tokens(self):
        self.read()
        return self.tokens
    
    def set_tokens(self, value):
        self.read()
        self.data.iloc[-1,1] = value
        self.data.to_csv(self.path, index=None)
    
    def decrement(self):
        self.data.iloc[-1,1] = self.data.iloc[-1,1] -1
        self.data.to_csv(self.path, index=None)
        
        
class Backlog():
    def __init__(self, path ="D:\\programming\\tinder_automator\\backlog.csv"):
        self.data = pd.DataFrame()
        self.path = path
        self.load()
        
    def load(self):    
        self.data = pd.read_csv(self.path, index_col=0)
    
    def update_with_tasks(self, tasks):
        tasks = pd.DataFrame.from_dict(tasks, orient="index")
        backlog_new = tasks[~tasks.index.isin(self.data.index)]
        print(len(backlog_new),"new matches.")
        self.data = pd.concat((backlog_new,self.data))
        self.data = self.data.drop("Rank", axis=1)
        self.data = self.data.merge(tasks.Rank, how="left", left_index=True, right_index=True)
        self.data.Rank = self.data.Rank.fillna(self.data.Rank.max())
        self.data.Rank = np.where(self.data.Status == 0,-1,self.data.Rank)
        self.data = self.data.sort_values("Rank")

    def save(self):
        self.data.to_csv(self.path)