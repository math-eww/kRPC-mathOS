import math
import time
import krpc

from mathosProgramThread import MathOSProgramThread as Thread

import ManeuverAutopilot
import MathXORCoPilot
import InGameScreen
import InGameConsole
import consoleprint

conn = None

def main():
    #Setup
    processes = {}
    global conn
    conn = krpc.connect(name='mathos:main')
    vessel = conn.space_center.active_vessel
    consoleprint.setUpConsole(conn)
    print = consoleprint.print
    print("mathOS loaded")
    print("kRPC version: " + str(conn.krpc.get_status().version))

    #Get telemetry
    altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    srf_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
    apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
    periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
    srf_frame = vessel.orbit.body.reference_frame
    obt_frame = vessel.orbit.body.non_rotating_reference_frame
    srf_speed = conn.add_stream(getattr, vessel.flight(srf_frame), 'speed')
    orb_speed = conn.add_stream(getattr, vessel.flight(obt_frame), 'speed')
    dynamic_pressure = conn.add_stream(getattr, vessel.flight(srf_frame), 'dynamic_pressure')

    def setupTelemetryScreen():
        data = {
            'Altitude': altitude(), 
            'Srf Altitude': srf_altitude(), 
            'Apoapsis': apoapsis(), 
            'Periapsis': periapsis(), 
            'Speed': orb_speed(), 
            'Srf Speed': srf_speed(),
            'Dyn Pressure': dynamic_pressure()
            }
        dataScreen = InGameScreen.InGameScreen(
            conn,
            200,
            275,
            data,
            True,
            'right',
            12,
            5,
            0,
            -250
        )
        return dataScreen
    
    telemetryScreen = setupTelemetryScreen()

    def updateTelemetryScreen(dataScreen):
        data = {
            'Altitude': altitude(), 
            'Srf Altitude': srf_altitude(), 
            'Apoapsis': apoapsis(), 
            'Periapsis': periapsis(), 
            'Speed': orb_speed(), 
            'Srf Speed': srf_speed(),
            'Dyn Pressure': dynamic_pressure()
        }
        dataScreen.update(data)

    #conn, height, width, data, shouldAutosize, position, limit, margin=5, xoffset=0, yoffset=0, isInput = False, isButtons = False
    userInputScreen = InGameScreen.InGameScreen(conn,40,800,[''],False,'bottom',800,5,-125,0,True)
    inputField = userInputScreen.getInputField()

    #Button functions
    def return_user_control():
        print("Returning control to user")
        vessel.control.throttle = 0.0
        vessel.auto_pilot.disengage()
        vessel.auto_pilot.sas = True
    def launch(targetAlt = 85000):
        try:
            # conn = krpc.connect(name='mathos:function')
            mathPilot = MathXORCoPilot.MathXORCoPilot(conn)
            mathPilot.basicLaunch(85000,45000)
        finally:
            print("Aborting launch program")
            return_user_control()

    def circularize(atApoapsis = False):
        try:
            # conn = krpc.connect(name='mathos:function')
            maneuverAutopilot = ManeuverAutopilot.ManeuverAutopilot(conn)
            nextNode = maneuverAutopilot.planCircularization(atApoapsis)
            maneuverAutopilot.executeNode(nextNode)
        finally:
            print("Aborting circularization program")
            return_user_control()

    def executeNextNode():
        try:
            # conn = krpc.connect(name='mathos:function')
            maneuverAutopilot = ManeuverAutopilot.ManeuverAutopilot(conn)
            nextNode = vessel.control.nodes[0]
            maneuverAutopilot.executeNode(nextNode)
        finally:
            print("Aborting node execution program")
            return_user_control()

    def hover():
        try:
            # conn = krpc.connect(name='mathos:function')
            mathPilot = MathXORCoPilot.MathXORCoPilot(conn)
            mathPilot.hover(0, True)
        finally:
            print("Aborting hover program")
            return_user_control()

    def hoverSlam(targetHeight = 20):
        try:
            # conn = krpc.connect(name='mathos:function')
            mathPilot = MathXORCoPilot.MathXORCoPilot(conn)
            mathPilot.hoverSlam(targetHeight)
            mathPilot.hover(-1, True)
        finally:
            print("Aborting hover slam program")
            return_user_control()

    def hoverAtAlt(targetAltitude = 1000):
        try:
            # conn = krpc.connect(name='mathos:function')
            mathPilot = MathXORCoPilot.MathXORCoPilot(conn)
            mathPilot.hoverAtAlt(targetAltitude)
        finally:
            print("Aborting hover at alt program")
            return_user_control()

    def test():
        try:
            mathPilot = MathXORCoPilot.MathXORCoPilot(conn)
            mathPilot.killHorizontalVelocity()
        finally:
            print("Aborting test program")
            return_user_control()
    #Buttons
    buttonsText= ['Hover', 'Land', 'Launch', 'Circularize', 'Execute Node', 'Test']
    functionsForButtons = [hover, hoverSlam, launch, circularize, executeNextNode, test]
    buttonsScreen = InGameScreen.InGameScreen(conn,400,80,buttonsText,True,'right',800,5,0,-50,False,True)
    buttons = buttonsScreen.getButtons()
    buttons_clicked = []
    for button in buttons:
        buttons_clicked.append(conn.add_stream(getattr, button, 'clicked'))

    runningProcess = ''
    while True:
        #buttons
        #perfor user's chosen function
        i = 0
        for button_clicked in buttons_clicked:
            if button_clicked():
                if 'main' in processes:
                    if processes['main'].isAlive():
                        processes['main'].terminate()
                    processes['main'].join
                    del processes['main']
                    print("Terminated")
                buttons[i].clicked = False
                buttonText = buttons[i].text.content
                if runningProcess == buttonText:
                    runningProcess = ''
                else:
                    _funcToExec = functionsForButtons[buttonsText.index(buttonText)]
                    # _funcToExec()
                    processes['main'] = Thread(target=_funcToExec,daemon=True)
                    processes['main'].start()
                    runningProcess = buttonText
                break
            i += 1
        i = 0
        #reset buttons to false to prevent clicks while a function is running from being executed next
        for button_clicked in buttons_clicked:
            if button_clicked():
                buttons[i].clicked = False
            i += 1
        #get user input
        if inputField.changed:
            inputField.changed = False
            print(inputField.value)
        #update telemetry
        updateTelemetryScreen(telemetryScreen)
        time.sleep(1)


if __name__ == '__main__':
    main()