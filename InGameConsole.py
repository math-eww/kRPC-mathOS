import krpc
import math
import time

import InGameScreen

class InGameConsole:
    def __init__(self, conn, height, width):
        print("Initializing InGameConsole")
        self.setUp(conn, height, width)

    def setUp(self, conn, height, width):
        _numberOfLines = (math.floor(height/20))
        self.data = []
        for i in range(_numberOfLines):
            self.data.append('')
        self.screen = InGameScreen.InGameScreen(conn,height,width,self.data,True,'bottom',width, 5, -125, 40)

    def printToConsole(self,line):
        # _toRemove = list(self.data.keys())[0] #next(iter(self.data),None)
        # if (_toRemove):
        #     self.data.pop(_toRemove)
        self.data.pop(0)
        #self.data.update({line: ''})
        self.data.append(line)
        self.screen.update(self.data)