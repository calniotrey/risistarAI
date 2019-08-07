import time

class Request:
    def __init__(self, url, payload):
        self.url = url
        self.payload = payload
        self.response = None
        self.date = time.time()
        self.content = None

    def connect(self, session):
        self.response = session.post(self.url, data=self.payload)
        self.date = time.time()
        self.content = self.response.content.decode().replace("\n", "").replace("\t", "")
        return self.response

    def saveToFile(self, filePath):
        if (self.response != None):
            with open(filePath, 'wb') as file:
                file.write(self.response.content)
