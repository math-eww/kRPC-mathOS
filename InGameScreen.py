import krpc
import math
import time

class InGameScreen:
    def __init__(self, conn, height, width, data, should_autosize, position, limit, margin=5, xoffset=0, yoffset=0, is_input = False, is_buttons = False):
        # print("Initializing InGameScreen")
        # Get canvas and size
        self.canvas = conn.ui.stock_canvas
        self.canvasSize = self.canvas.rect_transform.size
        # Add a panel to the canvas, then position and size it
        self.panel = self.canvas.add_panel()
        self.rect = self.panel.rect_transform
        # Store screen details
        self.height = height
        self.width = width
        self.should_autosize = should_autosize
        self.position = position
        self.limit = limit
        self.margin = margin
        self.xoffset = xoffset
        self.yoffset = yoffset
        self.is_input = is_input
        self.is_buttons = is_buttons
        self.is_set_up = False
        
        self.set_up(data)

    def set_up(self,data):
        if self.is_set_up:
            self._remove_all()
        self._size_screen(data)
        self._set_up_data_items(data)
        self.is_set_up = True
        print("Initialized InGameScreen: w: " + str(self.width) + ", h: " + str(self.height) + ", type: " +
            ("buttons" if self.is_buttons else "input" if self.is_input else "screen (1 col)" if type(data) is list else "screen (2 col)"))
    
    def _remove_all(self):
        try:
            if self.is_input:
                self.input_field.remove()
            elif self.is_buttons:
                for i in range(len(self.button_items)):
                    self.button_items[i].remove()
            else:
                for i in range(len(self.text_items)):
                    self.text_items[i].remove()
                for i in range(len(self.value_items)):
                    self.value_items[i].remove()
        except ValueError as e:
            print("Error removing: " + str(e))
    
    def _size_screen(self, data):
        _lineheight = 20
        if (self.is_buttons):
            _lineheight = 30
        if self.should_autosize:
            self.height = len(data) * _lineheight + (self.margin * 2) 
            # print("Creating screen with autosizing height: " + str(self.height) + ", width: ", self.width)
        else:
            # print("Creating screen with size " + str(self.height) + "h, " + str(self.width) + "w")
            pass
        # print("Set limit to " + str(self.limit))
        self.rect.size = (self.width, self.height)
        if self.position:
            if self.position == 'right':
                self.rect.position = ((self.canvasSize[0]/2) - (self.rect.size[0]/2) + self.xoffset, 0 + self.yoffset)
            if self.position == 'left':
                self.rect.position = (-1*((self.canvasSize[0]/2) - (self.rect.size[0]/2)) + self.xoffset, 0 + self.yoffset)
            if self.position == 'top':
                self.rect.position = ((self.rect.size[0]/2) + self.xoffset,(self.canvasSize[1]/2) - (self.rect.size[1]/2) + self.yoffset)
            if self.position == 'bottom':
                self.rect.position = ((self.rect.size[0]/2) + self.xoffset,-1*((self.canvasSize[1]/2) - (self.rect.size[1]/2)) + self.yoffset)
        else:
            self.rect.position = (0,0)
    
    def _set_up_data_items(self, data):
        i = 0
        self.text_items = []
        self.value_items = []
        if self.is_input:
            # print("Adding user input field")
            self._set_up_input_item()
        elif self.is_buttons:
            # print("Adding buttons")
            self.button_items = []
            for item in data:
                self._set_up_buttons(item, i)
                i += 1
        elif type(data) is dict:
            # print("Adding text items: 2 columns")
            for key, value in data.items():
                #Left side
                self._set_up_left_items(key, i, 0.60)
                #Right side
                self._set_up_right_items(value, i, 0.40)
                i += 1
        elif type(data) is list:
            # print("Adding text items: 1 column")
            for item in data:
                self._set_up_left_items(item, i, 1.0)
                self.text_items[i].rect_transform.size = (self.rect.size[0], self.text_items[i].rect_transform.size[1])
                i += 1

    def _set_up_left_items(self,text,i,widthPercentage):
        #Left side
        self.text_items.append(self.panel.add_text(""))
        self.text_items[i].color = (1,1,1)
        self.text_items[i].size = 18
        self.text_items[i].rect_transform.size = (self.rect.size[0]*widthPercentage, self.text_items[i].rect_transform.size[1])
        self.text_items[i].rect_transform.position = (-1*(self.rect.size[0]/2) + ((self.rect.size[0]*widthPercentage)/2) + self.margin, ((self.rect.size[1]/2) - (self.text_items[i].rect_transform.size[1]/2)) - i*20 - self.margin)
        self.text_items[i].content = str(text)

    def _set_up_right_items(self,text,i,widthPercentage):
        self.value_items.append(self.panel.add_text(""))
        self.value_items[i].color = (1,1,1)
        self.value_items[i].size = 18
        self.value_items[i].rect_transform.size = (self.rect.size[0]*widthPercentage, self.value_items[i].rect_transform.size[1])
        self.value_items[i].rect_transform.position = (1*(self.rect.size[0]/2) - ((self.rect.size[0]*widthPercentage)/2) - self.margin, ((self.rect.size[1]/2) - (self.value_items[i].rect_transform.size[1]/2)) - i*20 - self.margin)
        self.value_items[i].content = str(text)[:self.limit]

    def _set_up_input_item(self):
        self.input_field = self.panel.add_input_field()
        self.input_field.color = (1,1,1)
        self.input_field.size = 18
        self.input_field.rect_transform.size = (self.rect.size[0]-(self.margin*2), self.input_field.rect_transform.size[1])
        self.input_field.rect_transform.position = (-1*(self.rect.size[0]/2) + ((self.rect.size[0])/2), ((self.rect.size[1]/2) - (self.input_field.rect_transform.size[1]/2)) - self.margin)
    
    def get_input_field(self):
        return self.input_field

    def _set_up_buttons(self,text,i):
        widthPercentage = 1
        self.button_items.append(self.panel.add_button(text))
        self.button_items[i].color = (1,1,1)
        self.button_items[i].size = 18
        self.button_items[i].rect_transform.size = (self.rect.size[0]*widthPercentage, self.button_items[i].rect_transform.size[1])
        self.button_items[i].rect_transform.position = (0,((self.rect.size[1]/2) - (self.button_items[i].rect_transform.size[1]/2)) - i*30 - self.margin)#(1*(self.rect.size[0]/2) - ((self.rect.size[0]*widthPercentage)/2) - self.margin, ((self.rect.size[1]/2) - (self.button_items[i].rect_transform.size[1]/2)) - i*40 - self.margin)
    
    def get_buttons(self):
        return self.button_items

    def update(self,data):
        if (len(data) != len(self.text_items)):
            self.set_up(data)
        i = 0
        if type(data) is dict:
            for key, value in data.items():
                self.text_items[i].content = key
                self.value_items[i].content = str(value)[:self.limit]
                i += 1
        elif type(data) is list:
            for item in data:
                self.text_items[i].content = str(item)
                i += 1
    
    def remove(self):
        self._remove_all()
        if self.panel:
            self.panel.remove()