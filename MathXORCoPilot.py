import krpc
import math
import time

import ManeuverAutopilot
from consoleprint import print

class MathXORCoPilot:
    def __init__(self, conn):
        print("Initializing MathXORCoPilot")
        self.setUp(conn)
    def setUp(self, conn):
        self.conn = conn
        self.ut = conn.add_stream(getattr, conn.space_center, 'ut')
        self.vessel = conn.space_center.active_vessel
        self.altitude = conn.add_stream(getattr, self.vessel.flight(), 'mean_altitude')
        print("Initialized MathXORCoPilot")
    def basicLaunch(self, targetAltitude, turnEnd):
        print("Starting launch. Target Alt: " + str(targetAltitude))
        availableThrust = self.vessel.available_thrust
        massInitial = self.vessel.mass
        turnExponent = max(1 / (2.25 * (availableThrust / massInitial) - 1.35), 0.25)
        pitchAngle = 90 * (1 - (self.altitude() / turnEnd) ** turnExponent)
        self.vessel.auto_pilot.reference_frame=self.vessel.surface_reference_frame
        self.vessel.auto_pilot.target_pitch_and_heading(90,90)
        self.vessel.auto_pilot.engage()
        self.vessel.control.throttle=1.0
        while self.altitude() < 100:
            time.sleep(0.01)
            pass
        print("Passed 100m")
        print("Pitch angle: " + str(pitchAngle))
        print(self.vessel.orbit.apoapsis_altitude < targetAltitude)
        while self.vessel.orbit.apoapsis_altitude < targetAltitude:
            time.sleep(0.01)
            self.vessel.auto_pilot.target_pitch_and_heading((90 * (1 - (self.altitude() / turnEnd) ** turnExponent)),90)
            pass
        print("Coasting to apoapsis")
        self.vessel.auto_pilot.disengage()
        self.vessel.control.throttle = 0.0
        self.vessel.auto_pilot.sas = True
        time.sleep(0.1)
        self.vessel.auto_pilot.sas_mode = self.vessel.auto_pilot.sas_mode.prograde
        self.vessel.auto_pilot.wait()
        self.conn.space_center.physics_warp_factor = 4
        while self.altitude() < 70000:
            time.sleep(0.01)
            pass
        self.conn.space_center.physics_warp_factor = 0
        maneuverAutopilot = ManeuverAutopilot.ManeuverAutopilot(self.conn)
        circularizationNode = maneuverAutopilot.planCircularization(True)
        maneuverAutopilot.executeNode(circularizationNode)