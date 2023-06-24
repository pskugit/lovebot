
class Conversation():
    """Conversation based on a list of following format: [(1,0,"message one"),(0,0,"message two"),(1,0,"message three")]
    where the tuple contaions (theirs-flag, hearted-flag, text)
    """
    def __init__(self, message_list):   
        self.message_list = message_list
        self.myturn = True if not message_list else (message_list[-1][0] or message_list[-1][1])
        self.is_doubled_down =  False if (len(message_list) < 3) else message_list[-1][0] * message_list[-2][0]

    def find_in_conversation(self, searchstring, only_mine=False):
        """returns the text of the first message of the conversation that contains the searchstring"""
        for theirs, hearted, message_text in self.message_list:
            if not (only_mine and theirs):
                if searchstring in message_text:
                    return message_text
        return ""
    
    def _get_sample_message_list(self):
        return [(False,0,"message one"),(True,0,"message two"),(False,0,"message three"), (True,0,"message four")]

    def get_latest_message_text(self):
        return self.message_list[-1][2] if self.message_list else "intital"
    
    def __len__(self):
        return len(self.message_list)