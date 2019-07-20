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

plainprint = print
print = print

class MathOS:
    def __init__(self, conn):
        plainprint("mathOS: post")
        self.conn = conn
        self.vessel = self.conn.space_center.active_vessel
        self.data_streams = streams.Streams(self.conn)
        self.processes = {}
        self.running_process = ''
        self.ui = {}
        self.ui['screens'] = {}
        consoleprint.setUpConsole(self.conn)
        global print
        print = consoleprint.print
        self.ui['screens']['console'] = consoleprint.getConsole()
        self.start_streams()
        self.setup_ui()
        self.maneuver_pilot = ManeuverAutopilot.ManeuverAutopilot(self.conn, self.data_streams)
        self.math_pilot = MathXORCoPilot.MathXORCoPilot(self.conn,self.data_streams,self.maneuver_pilot)
        print("mathOS: loaded")
        print("kRPC version: " + str(self.conn.krpc.get_status().version))

    def __del__(self):
        print("mathOS: shutting down")

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
        # self.data_streams.print_streams()

    def setup_ui(self):
        #Setup telemetry screen
        self.ui['telemetry_screen'] = self.ui_add_telemetry_screen()
        self.ui['screens']['telemetry_screen'] = self.ui['telemetry_screen']
        #Setup user input field for console
        user_input_screen = InGameScreen.InGameScreen(self.conn,40,800,[''],False,'bottom',800,5,-125,0,True) #conn, height, width, data, shouldAutosize, position, limit, margin=5, xoffset=0, yoffset=0, isInput = False, isButtons = False
        self.ui['input_field'] = user_input_screen.get_input_field()
        self.ui['screens']['input_field_screen'] = user_input_screen
        #Setup buttons
        self.ui['buttons'] = self.ui_add_control_buttons()

    def ui_add_telemetry_screen(self):
        _all_streams = self.data_streams.get_all_streams()
        _data = { list(_all_streams.keys())[i] : _all_streams[list(_all_streams.keys())[i]]() for i in range(len(_all_streams))}
        return InGameScreen.InGameScreen(self.conn, 200, 275, _data, True, 'right', 12, 5, 0, -250)

    def ui_add_control_buttons(self):
        #Buttons
        buttons_text= [           'Hover',     'Land',     'Launch',     'Circularize',     'Execute Node',        'Test' ]
        functions_for_buttons = [ self._hover, self._land, self._launch, self._circularize, self._execute_next_node, self._test ]
        buttons_screen = InGameScreen.InGameScreen(self.conn,400,80,buttons_text,True,'right',800,5,0,-50,False,True)
        self.ui['screens']['buttons_screen'] = buttons_screen
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
    def _launch(self,target_alt = 85000):
        try:
            self.math_pilot.basic_launch(85000,45000)
        finally:
            print("Aborting launch program")
            self._return_user_control()
    def _land(self):
        try:
            self.math_pilot.land()
        finally:
            print("Aborting landing program")
            self._return_user_control()
    def _circularize(self,at_apoapsis = False):
        try:
            next_node = self.maneuver_pilot.plan_circularization(at_apoapsis)
            self.maneuver_pilot.execute_node(next_node)
        finally:
            print("Aborting circularization program")
            self._return_user_control()
    def _execute_next_node(self):
        try:
            next_node = self.vessel.control.nodes[0]
            self.maneuver_pilot.execute_node(next_node)
        finally:
            print("Aborting node execution program")
            self._return_user_control()
    def _hover(self):
        try:
            self.math_pilot.hover(0, True)
        finally:
            print("Aborting hover program")
            self._return_user_control()
    # def _hover_slam(self,target_height = 20):
    #     try:
    #         self.math_pilot.hover_slam(target_height)
    #         self.math_pilot.hover(-1, True)
    #     finally:
    #         print("Aborting hover slam program")
    #         self._return_user_control()
    # def _hover_at_alt(self,targetAltitude = 1000):
    #     try:
    #         self.math_pilot.hover_at_alt(targetAltitude)
    #     finally:
    #         print("Aborting hover at alt program")
    #         self._return_user_control()
    def _test(self):
        try:
            self.math_pilot.kill_horizontal_velocity()
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
    
    def remove_all_streams(self):
        # plainprint("Removing all streams")
        self.data_streams.remove_all_streams()
        for button_stream in self.ui['buttons'][1]:
            button_stream.remove()
    
    def delete_ui(self):
        plainprint("Removing UI")
        for key in self.ui['screens']:
            print(key)
            self.ui['screens'][key].remove()
        plainprint("UI removed")
        # for key in self.ui:
        #     print(key)
        #     if key == "buttons":
        #         for button in self.ui[key][0]:
        #             print(button)
        #             button.remove()
        #     elif key == "input_field":
        #         pass
        #     else:
        #         self.ui[key].remove()
        #     print(key + " removed")
    
    def stop_all_processes(self):
        plainprint("Stopping processes")
        for key in self.processes:
            if self.processes[key].isAlive():
                self.processes[key].terminate()
            self.processes[key].join
            del self.processes[key]
    
    def restart_math_os(self):
        print("mathOS: restarting")
        # Stop any active threads
        self.stop_all_processes()
        # Remove streams and reset data_streams
        self.remove_all_streams()
        # Remove UI and UI streams
        self.delete_ui()
        # Reset variables
        plainprint("mathOS: post")
        self.processes = {}
        self.running_process = ''
        self.ui = {}
        self.ui['screens'] = {}
        consoleprint.setUpConsole(self.conn)
        self.ui['screens']['console'] = consoleprint.getConsole()
        self.start_streams()
        self.setup_ui()
        del self.maneuver_pilot
        del self.math_pilot
        self.maneuver_pilot = ManeuverAutopilot.ManeuverAutopilot(self.conn, self.data_streams)
        self.math_pilot = MathXORCoPilot.MathXORCoPilot(self.conn,self.data_streams,self.maneuver_pilot)
        print("mathOS: finished restarting")
        print("kRPC version: " + str(self.conn.krpc.get_status().version))

if __name__ == '__main__':
    import gc
    conn = krpc.connect(name='mathos:main')
    running = True
    _mathOS = None
    restart_button_clicked = None
    while running:
        try:
            plainprint("Restart button: ", end="")
            restart_button_screen = InGameScreen.InGameScreen(conn,30,30,['↻'],True,'right',5,5,-80,-50,False,True)
            restart_button = restart_button_screen.get_buttons()[0]
            restart_button_clicked = conn.add_stream(getattr, restart_button, 'clicked')
            if conn.krpc.current_game_scene == conn.krpc.current_game_scene.flight:
                if _mathOS:
                    _mathOS.restart_math_os()
                else:
                    _mathOS = MathOS(conn)
                while conn.krpc.current_game_scene == conn.krpc.current_game_scene.flight:
                    if restart_button_clicked():
                        plainprint("mathOS: restart button pressed")
                        restart_button.clicked = False
                        # conn.ui.clear()
                        conn.ui.message("Rebooting mathOS")
                        break
                    else:
                        _mathOS.update()
                        time.sleep(0.5)
                if _mathOS:
                    _mathOS.remove_all_streams()
                time.sleep(1)
            else:
                plainprint("Waiting for flight to start")
            # del _mathOS
            restart_button_clicked.remove()
            restart_button_screen.remove()
        except krpc.error.RPCError as e:
            plainprint(e)
            if _mathOS:
                _mathOS.remove_all_streams()
            if restart_button_clicked:
                restart_button_clicked.remove()
            plainprint("Scene Changed")
            time.sleep(1)
        except ConnectionAbortedError:
            if _mathOS:
                _mathOS.remove_all_streams()
            if restart_button_clicked:
                restart_button_clicked.remove()
            plainprint("Remote Disconnected")
            running = False
        time.sleep(1)
    conn.close()