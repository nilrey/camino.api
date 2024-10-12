class responseMessage():

    def __init__(self):
        self.message = {'error': True, 'text': ''}

    def composeMessage(self, is_error, text):
        self.message['error'] = is_error
        self.message['text']= text

    def set(self, text):
        self.composeMessage(False, text)
    
    def setError(self, text):
        self.composeMessage(True, text)

    def get(self)->dict:
        return self.message