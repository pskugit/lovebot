import os
import openai
import pandas as pd
DEFAULT_NAME_ME = "Kim"
LOCATION_ME = "Berlin"

class Allowance():
    def __init__(self, path="gpt_allowance.csv"):
        self.data = pd.DataFrame()
        self.path = path
        if not os.path.exists(path):
            with open(self.path,'a') as fd:
                fd.write("Date,Tokens\n")
                fd.write(str(pd.Timestamp.today().date())+",50")
                self.tokens = 50
        self.read()

    def read(self):
        self.data = pd.read_csv(self.path, header=0)
        if str(pd.Timestamp.today().date()) == self.data.Date.iloc[-1]:
            self.tokens = self.data.Tokens.iloc[-1]
        else:
            with open(self.path,'a') as fd:
                fd.write(str("\n"+str(pd.Timestamp.today().date()))+",50")
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

class Gpt():
    def __init__(self, openai_api_key: str, allowance: Allowance, model):
        self.allowance = allowance
        self.model = model
        openai.api_key = openai_api_key
        pass

class ChatGpt(Gpt):
    def __init__(self, openai_api_key, allowance, model="gpt-3.5-turbo"):
        super().__init__(openai_api_key, allowance, model)

    def request(self, prompt, temperature=0.7, dryrun=False, return_completion_object=False):
        if dryrun:
            return "This is a test reply in order to save API Tokens"
        completion = openai.ChatCompletion.create(
          model=self.model,
          temperature=temperature,
          messages=prompt
        )
        if return_completion_object:
            return completion
        reply = completion.choices[0].message.content.strip("\"")
        if self.allowance is not None:
            self.allowance.decrement()  
        return reply

    def _conversation_to_messages(self, conversation, name_them, name_me=DEFAULT_NAME_ME, last_n=0):
            gpt_messages = []
            for theirs, hearted, message in conversation.message_list[-last_n:]:
                role = "user" if theirs else "assistant"
                gpt_messages.append({"role": role, "content": message})
            return gpt_messages
    
    def build_prompt(self, conversation, bio, name_them, name_me=DEFAULT_NAME_ME, initial=True, double_down=False, last_n=0):
        gpt_messages = []

        """if initial == True, it expects the "conversation" to be a bio, else the body shall be a conversation with the custom "conversation structure"""
        setting_primer = f"Setting: Dating App. {LOCATION_ME}.\nYou act as {name_me}: A chill and educated person who always finds the right words to be attractive to others \
            You are chatting with {name_them}, who matched with you on Tinder. {name_me} has a friendly but straightforward attitude.\n\
            {name_me} tends to ask witty entertaining questions relating to {name_them}'s profile and the ongoing conversation and aims to shedule a date with {name_them}.\n\
            Only provide the next chat message of any given conversation."
        gpt_messages.append({"role": "system", "content": setting_primer})
        assert isinstance(bio, str)
        if not bio:
            bio_primer = f"{name_them}\'s profile is empty so for now, only the name is known to us and that {name_them} is looking to find someone interesting.\n"
        else:  
            bio_primer = f"{name_them}\'s profile says:\n{bio}"
        gpt_messages.append({"role": "system", "content": bio_primer})

        if initial:
            initial_primer = f"{name_me} starts the chat wittily (without introducing formally)"
            gpt_messages.append({"role": "system", "content": initial_primer})

        else: 
            chat_messages = self._conversation_to_messages(conversation, name_them, name_me=name_me, last_n=last_n)
            gpt_messages.extend(chat_messages)

            if double_down:
                double_down_primer = f"Since {name_them} has not yet replied to {name_me}'s message, {name_me} continues with a more straightforward approach.\n"
                gpt_messages.append({"role": "system", "content": double_down_primer})

        return gpt_messages


class Gpt3(Gpt):
    def __init__(self, openai_api_key, allowance, model="text-davinci-003"):
        super().__init__(openai_api_key, allowance, model)
        
    def request(self, prompt, stop_sequences="infer", stop_sequences_names=("name_me", "name_them"), temperature=0.7, max_tokens=128, dryrun=False):
        if stop_sequences=="infer":
            stop_sequences=[stop_sequences_names[0]+":",stop_sequences_names[0]+":",stop_sequences_names[1]+" responds", stop_sequences_names[1]+"'s response"]
        if dryrun:
            return "This is a test reply in order to save API Tokens"
        response = openai.Completion.create(
          model=self.model,
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
    
    def build_prompt(self, conversation, bio: str, name_them: str, name_me :str=DEFAULT_NAME_ME , initial=True, double_down=False, last_n=0):
        """if initial == True, it expects the "conversation" to be a bio, else the body shall be a conversation with the custom "conversation structure"""
        primer1 = f"Setting: Dating App. {LOCATION_ME}.\n{name_me} is a chill and educated person who always finds the right words to be attractive to others. \
            This is a chat between {name_me} and {name_them}. {name_me} has a friendly but straightforward attitude.\n"
        assert isinstance(bio, str)
        if not bio:
            primer2 = f"{name_them}s profile is empty so for now, only the name is known to us and that {name_them} is looking to find someone interesting.\n"
        else:  
            primer2 = f"{name_them}s profile says:\n"

        if initial:
            primer3 = f"{name_me} starts the chat (while not introducing formally) by wittily saying:"
            prompt = f"{primer1}{primer2}{bio}\n{primer3}"
        else: 
            body = self._conversation_to_body(conversation, name_them, name_me=name_me, last_n=last_n)
            primer4 = f"{name_me} tends to ask witty entertaining questions relating to {name_them}'s profile and the ongoing conversation and aims to shedule a date with {name_them}.\n"
            if double_down:
                primer5 = f"Since {name_them} has not yet replied to {name_me}'s message, {name_me} continues with a more straightforward approach.\n"
                prompt = f"{primer1}{primer2}{bio}\n{primer4}\n{body}\n{primer5}{name_me}:"
            else:
                prompt = f"{primer1}{primer2}{bio}\n{primer4}\n{body}{name_me}:"
        return prompt





