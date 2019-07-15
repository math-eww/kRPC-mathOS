import math
import time
import krpc

from threading import Thread

import ManeuverAutopilot
import MathXORCoPilot
import InGameScreen
import InGameConsole
import consoleprint

#Setup
conn = krpc.connect()
vessel = conn.space_center.active_vessel
consoleprint.setUpConsole(conn)
print = consoleprint.print
print("mathOS loaded")
print("kRPC version: " + str(conn.krpc.get_status().version))
#Streams init
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
srf_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
srf_frame = vessel.orbit.body.reference_frame
obt_frame = vessel.orbit.body.non_rotating_reference_frame
srf_speed = conn.add_stream(getattr, vessel.flight(srf_frame), 'speed')
orb_speed = conn.add_stream(getattr, vessel.flight(obt_frame), 'speed')
dynamic_pressure = conn.add_stream(getattr, vessel.flight(srf_frame), 'dynamic_pressure')
#Build screen with stream data, async
def runAsync():
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
    while True:
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
        time.sleep(0.5)
Thread(target=runAsync,daemon=True).start()

#User functions
def launch(targetAlt):
    mathPilot = MathXORCoPilot.MathXORCoPilot(conn)
    mathPilot.basicLaunch(85000,45000)

def circularize(atApoapsis):
    maneuverAutopilot = ManeuverAutopilot.ManeuverAutopilot(conn)
    nextNode = maneuverAutopilot.planCircularization(atApoapsis)
    maneuverAutopilot.executeNode(nextNode)

def executeNextNode():
    maneuverAutopilot = ManeuverAutopilot.ManeuverAutopilot(conn)
    nextNode = vessel.control.nodes[0]
    maneuverAutopilot.executeNode(nextNode)

while True:
    #get user input
    #perfor user's chosen function
    time.sleep(1)