import math
import time
import krpc

from mathosProgramThread import MathOSProgramThread as Thread

import ManeuverAutopilot
import MathXORCoPilot
import InGameScreen
import InGameConsole
import consoleprint
import streams

print = print

class MathOS:
    def __init__(self):
        self.conn = krpc.connect(name='mathos:main')
        self.vessel = self.conn.space_center.active_vessel
        self.data_streams = streams.Streams(self.conn)
        self.processes = {}
        self.running_process = ''
        self.ui = {}
        consoleprint.setUpConsole(self.conn)
        global print
        print = consoleprint.print
        self.start_streams()
        self.setup_ui()
        self.maneuver_pilot = ManeuverAutopilot.ManeuverAutopilot(self)
        self.math_pilot = MathXORCoPilot.MathXORCoPilot(self)
        print("mathOS: loaded")
        print("kRPC version: " + str(self.conn.krpc.get_status().version))

    def update(self):
        #buttons
        #perfor user's chosen function
        i = 0
        for button_clicked in self.ui['buttons'][1]:
            if button_clicked():
                if 'main' in self.processes:
                    if self.processes['main'].isAlive():
                        self.processes['main'].terminate()
                    self.processes['main'].join
                    del self.processes['main']
                    print("Terminated")
                self.ui['buttons'][0][i].clicked = False
                button_text = self.ui['buttons'][0][i].text.content
                if self.running_process == button_text:
                    self.running_process = ''
                else:
                    _funcToExec = self.ui['buttons'][3][self.ui['buttons'][2].index(button_text)]
                    # _funcToExec()
                    self.processes['main'] = Thread(target=_funcToExec,daemon=True)
                    self.processes['main'].start()
                    self.running_process = button_text
                break
            i += 1
        i = 0
        #reset buttons to false to prevent clicks while a function is running from being executed next
        for button_clicked in self.ui['buttons'][1]:
            if button_clicked():
                self.ui['buttons'][0][i].clicked = False
            i += 1
        #get user input
        if self.ui['input_field'].changed:
            self.ui['input_field'].changed = False
            print(self.ui['input_field'].value)
        #update telemetry
        _all_streams = self.data_streams.get_all_streams()
        self.ui['telemetry_screen'].update({ list(_all_streams.keys())[i] : _all_streams[list(_all_streams.keys())[i]]() for i in range(len(_all_streams))})
        #debugging
        self.data_streams.print_streams()

    def setup_ui(self):
        #Setup telemetry screen
        self.ui['telemetry_screen'] = self.ui_add_telemetry_screen()
        #Setup user input field for console
        user_input_screen = InGameScreen.InGameScreen(self.conn,40,800,[''],False,'bottom',800,5,-125,0,True) #conn, height, width, data, shouldAutosize, position, limit, margin=5, xoffset=0, yoffset=0, isInput = False, isButtons = False
        self.ui['input_field'] = user_input_screen.get_input_field()
        #Setup buttons
        self.ui['buttons'] = self.ui_add_control_buttons()

    def ui_add_telemetry_screen(self):
        _all_streams = self.data_streams.get_all_streams()
        _data = { list(_all_streams.keys())[i] : _all_streams[list(_all_streams.keys())[i]]() for i in range(len(_all_streams))}
        return InGameScreen.InGameScreen(self.conn, 200, 275, _data, True, 'right', 12, 5, 0, -250)

    def ui_add_control_buttons(self):
        #Buttons
        buttons_text= ['Hover', 'Land', 'Launch', 'Circularize', 'Execute Node', 'Test']
        functions_for_buttons = [self._hover, self._hoverSlam, self._launch, self._circularize, self._executeNextNode, self._test]
        buttons_screen = InGameScreen.InGameScreen(self.conn,400,80,buttons_text,True,'right',800,5,0,-50,False,True)
        buttons = buttons_screen.get_buttons()
        buttons_clicked = []
        for button in buttons:
            buttons_clicked.append(self.conn.add_stream(getattr, button, 'clicked'))
        return [buttons, buttons_clicked, buttons_text, functions_for_buttons]
    
    #Button functions
    def _return_user_control(self):
        print("Returning control to user")
        self.vessel.control.throttle = 0.0
        self.vessel.auto_pilot.disengage()
        self.vessel.auto_pilot.sas = True
    def _launch(self,targetAlt = 85000):
        try:
            self.math_pilot.basicLaunch(85000,45000)
        finally:
            print("Aborting launch program")
            self._return_user_control()
    def _circularize(self,atApoapsis = False):
        try:
            nextNode = self.maneuver_pilot.plan_circularization(atApoapsis)
            self.maneuver_pilot.execute_node(nextNode)
        finally:
            print("Aborting circularization program")
            self._return_user_control()
    def _executeNextNode(self):
        try:
            nextNode = self.vessel.control.nodes[0]
            self.maneuver_pilot.execute_node(nextNode)
        finally:
            print("Aborting node execution program")
            self._return_user_control()
    def _hover(self):
        try:
            self.math_pilot.hover(0, True)
        finally:
            print("Aborting hover program")
            self._return_user_control()
    def _hoverSlam(self,targetHeight = 20):
        try:
            self.math_pilot.hoverSlam(targetHeight)
            self.math_pilot.hover(-1, True)
        finally:
            print("Aborting hover slam program")
            self._return_user_control()
    def _hoverAtAlt(self,targetAltitude = 1000):
        try:
            self.math_pilot.hoverAtAlt(targetAltitude)
        finally:
            print("Aborting hover at alt program")
            self._return_user_control()
    def _test(self):
        try:
            self.math_pilot.killHorizontalVelocity()
        finally:
            print("Aborting test program")
            self._return_user_control()

    def start_streams(self):
        self.data_streams.create_stream('apoapsis_altitude')
        self.data_streams.create_stream('periapsis_altitude')
        self.data_streams.create_stream('mean_altitude')
        self.data_streams.create_stream('surface_altitude')
        self.data_streams.create_stream('orb_speed')
        self.data_streams.create_stream('srf_speed')
        self.data_streams.create_stream('vertical_speed')
        self.data_streams.create_stream('horizontal_speed')
        self.data_streams.create_stream('dynamic_pressure')
    
    def get_math_pilot(self):
        return self.math_pilot
    
    def get_maneuver_pilot(self):
        return self.maneuver_pilot

    def get_streams(self):
        return self.data_streams
    
    def get_conn(self):
        return self.conn


if __name__ == '__main__':
    _mathOS = MathOS()
    time.sleep(5)
    _mathOS.data_streams.create_stream('ut')
    #conn.add_stream(getattr, conn.space_center, 'ut')
    while True:
        _mathOS.update()
        time.sleep(0.5)