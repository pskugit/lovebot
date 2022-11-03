import os
import openai
import pandas as pd
from dotenv import load_dotenv
DEFAULT_NAME_ME = "Kim"

class Gpt3():
    def __init__(self, openai_api_key, allowance):
        self.allowance = allowance
        openai.api_key = openai_api_key
        pass
        
    def request(self, prompt,stop_sequences, temperature=0.7, max_tokens=128, dryrun=False):
        if dryrun:
            return "This is a test reply in order to save API Tokens"
        response = openai.Completion.create(
          engine="text-davinci-002",#"text-curie-001",
          prompt=prompt,
          temperature=temperature,
          max_tokens=max_tokens,
          frequency_penalty=0,
          top_p=1,
          presence_penalty=0,
          stop=stop_sequences
        )
        reply = response["choices"][0]["text"].strip()
        if self.allowance is not None:
            self.allowance.decrement()   
        return reply
    
    def _conversation_to_body(self, conversation, name_them, name_me=DEFAULT_NAME_ME, last_n=0):
        text = ""
        for myturn, hearted, message in conversation.message_list[-last_n:]:
            text += name_them if myturn else name_me
            text += ": "
            text += '"'+message+'"'
            text += "\n"
        return text
    
    def build_prompt(self, conversation, name_them, name_me=DEFAULT_NAME_ME, initial=True, double_down=False, last_n=0):
        """if initial == True, it expects the "conversation" to be a bio, else the body shall be a conversation with the custom "conversation structure"""
        primer1 = f"This is a Tinder chat between {name_me} from Berlin and {name_them}.\n"

        if initial:
            assert isinstance(conversation, str)
            primer2 = f"{name_them}s profile says:\n"
            primer3 = f"\n\n{name_me} asks a witty question relating to her profile:"
            prompt = primer1+primer2+conversation+primer3
        else: 
            body = self._conversation_to_body(conversation, name_them, name_me=DEFAULT_NAME_ME, last_n=last_n)
            primer4 = f"{name_me} tends to ask witty entertaining questions relating to the ongoing conversation and aims to shedule a date with {name_them}.\n"
            if double_down:
                primer5 = f"Since {name_them} has not yet replied to {name_me}'s message, {name_me} continues with a more straightforward approach.\n"
                prompt = f"{primer1}{primer4}\n{body}\n{primer5}{name_me}:"
            else:
                prompt = f"{primer1}{primer4}\n{body}{name_me}:"
        return prompt

class Allowance():
    def __init__(self, path="gpt_allowance.csv"):
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



