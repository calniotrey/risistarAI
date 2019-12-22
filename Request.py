import time
from UtilitiesFunctions import log

class Request:
    def __init__(self, url, payload):
        self.url = url
        self.payload = payload
        self.response = None
        self.date = time.time()
        self.content = None

    def __repr__(self):
        return "Request (url %s, payload %s)" % (self.url, str(self.payload))

    def connect(self, session):
        connected = False
        while not connected:
            try:
                self.response = session.post(self.url, data=self.payload)
                if self.response.status_code != 503 and self.response.status_code != 500:
                    connected = True
                else:
                    log(None, "Error %i while accessing %s" % (self.response.status_code, self.url))
                    time.sleep(1)
            except:
                log(None, "Error while sending request, sleeping for 10 seconds")
                time.sleep(10)
        self.date = time.time()
        self.content = self.response.content.decode().replace("\n", "").replace("\t", "")
        return self.response

    def saveToFile(self, filePath):
        if (self.response != None):
            with open(filePath, 'wb') as file:
                file.write(self.response.content)
