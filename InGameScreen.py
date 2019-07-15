import krpc
import math
import time

class InGameScreen:
    def __init__(self, conn, height, width, data, shouldAutosize, position, limit, margin=5, xoffset=0, yoffset=0):
        print("Initializing InGameScreen")
        self.setUp(conn, height, width, data, shouldAutosize, position, limit, margin, xoffset, yoffset)

    def setUp(self, conn, height, width, data, shouldAutosize, position, limit, margin, xoffset, yoffset):
        self.limit = limit
        self.position = position
        self.margin = margin
        if shouldAutosize:
            height = len(data) * 20 + (self.margin * 2) 
            print("Creating screen with autosizing height: " + str(height) + ", width: ", width)
        else:
            print("Creating screen with size " + str(height) + "h, " + str(width) + "w")
        print("Set limit to " + str(limit))
        # Get canvas and size
        self.canvas = conn.ui.stock_canvas
        self.canvasSize = self.canvas.rect_transform.size
        # Add a panel to the canvas, then position and size it
        self.panel = self.canvas.add_panel()
        self.rect = self.panel.rect_transform
        self.rect.size = (width, height)
        if position:
            if position == 'right':
                self.rect.position = ((self.canvasSize[0]/2) - (self.rect.size[0]/2) + xoffset, 0 + yoffset)
            if position == 'left':
                self.rect.position = (-1*((self.canvasSize[0]/2) - (self.rect.size[0]/2)) + xoffset, 0 + yoffset)
            if position == 'top':
                self.rect.position = ((self.rect.size[0]/2) + xoffset,(self.canvasSize[1]/2) - (self.rect.size[1]/2) + yoffset)
            if position == 'bottom':
                self.rect.position = ((self.rect.size[0]/2) + xoffset,-1*((self.canvasSize[1]/2) - (self.rect.size[1]/2)) + yoffset)
        else:
            self.rect.position = (0,0)
        i = 0
        self.textItems = []
        self.valueItems = []
        print("Adding text items")
        if type(data) is dict:
            for key, value in data.items():
                #Left side
                self.setUpLeftItems(key, i, 0.60)
                self.textItems[i].rect_transform.size = (self.rect.size[0]*0.60, self.textItems[i].rect_transform.size[1])
                #Right side
                self.setUpRightItems(value, i, 0.40)
                self.valueItems[i].rect_transform.size = (self.rect.size[0]*0.40, self.valueItems[i].rect_transform.size[1])
                i += 1
        elif type(data) is list:
            for item in data:
                self.setUpLeftItems(item, i, 1.0)
                self.textItems[i].rect_transform.size = (self.rect.size[0], self.textItems[i].rect_transform.size[1])
                i += 1

    def setUpLeftItems(self,text,i,widthPercentage):
        #Left side
        self.textItems.append(self.panel.add_text(""))
        self.textItems[i].color = (1,1,1)
        self.textItems[i].size = 18
        self.textItems[i].rect_transform.size = (self.rect.size[0]*widthPercentage, self.textItems[i].rect_transform.size[1])
        self.textItems[i].rect_transform.position = (-1*(self.rect.size[0]/2) + ((self.rect.size[0]*widthPercentage)/2) + self.margin, ((self.rect.size[1]/2) - (self.textItems[i].rect_transform.size[1]/2)) - i*20 - self.margin)
        self.textItems[i].content = str(text)

    def setUpRightItems(self,text,i,widthPercentage):
        self.valueItems.append(self.panel.add_text(""))
        self.valueItems[i].color = (1,1,1)
        self.valueItems[i].size = 18
        self.valueItems[i].rect_transform.position = (1*(self.rect.size[0]/2) - ((self.rect.size[0]*widthPercentage)/2) - self.margin, ((self.rect.size[1]/2) - (self.textItems[i].rect_transform.size[1]/2)) - i*20 - self.margin)
        self.valueItems[i].content = str(text)[:self.limit]

    def update(self,data):
        i = 0
        if type(data) is dict:
            for key, value in data.items():
                self.textItems[i].content = key
                self.valueItems[i].content = str(value)[:self.limit]
                i += 1
        elif type(data) is list:
            for item in data:
                self.textItems[i].content = str(item)
                i += 1