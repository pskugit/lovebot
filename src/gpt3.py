import os
import openai
openai.api_key = os.environ("OPENAI_API_KEY")

NAME_ME = "Chris"

class Gpt3():
    def __init__(self):
        pass
        
    def request(self, prompt,stop_sequences, temperature=0.7, dryrun=False):
        if dryrun:
            return "This is a test reply in order to save API Tokens"
        response = openai.Completion.create(
          engine="text-davinci-002",#"text-curie-001",
          prompt=prompt,
          temperature=temperature,
          max_tokens=64,
          frequency_penalty=0,
          top_p=1,
          presence_penalty=0,
          stop=stop_sequences
        )
        reply = response["choices"][0]["text"].strip()
        return reply
    
    def _conversation_to_body(self, conversation, name_them, name_me=NAME_ME, last_n=5):
        text = ""
        for myturn, hearted, message in conversation[-last_n:]:
            text += name_them if myturn else name_me
            text += ": "
            text += message
            text += "\n"
        return text
    
    def build_prompt(self, conversation, name_them, name_me=NAME_ME, initial=True):
        """if initial == True, it expects the "conversation" to be a bio, else the body shall be a conversation with the custom "conversation structure"""
        primer1 = f"This is a Tinder chat between {name_me} from Berlin and {name_them}.\n"

        if initial:
            assert isinstance(conversation, str)
            primer2 = f"{name_them}s profile says:\n"
            primer3 = f"\n\n{name_me} asks a witty question relating to her profile:"
            prompt = primer1+primer2+conversation+primer3
        else: 
            body = self._conversation_to_body(conversation, name_them, name_me=NAME_ME, last_n=5)
            primer4 = f"{name_me} tends to ask witty entertaining questions.\n"
            prompt = f"{primer1} {primer4}\n{body}{name_me}:"
        return prompt





