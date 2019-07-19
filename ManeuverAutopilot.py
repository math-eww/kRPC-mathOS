import krpc
import math
import time

from consoleprint import print

class ManeuverAutopilot:
    def __init__(self, math_os):
        print("Initializing ManeuverAutopilot")
        self.set_up(math_os)

    def set_up(self, math_os):
        self.conn = math_os.get_conn()
        self.streams = math_os.get_streams()

        self.ut = self.streams.get_stream('ut') #conn.add_stream(getattr, conn.space_center, 'ut')
        self.vessel = self.conn.space_center.active_vessel
        print("Initialized ManeuverAutopilot")

    def execute_node(self, node):
        print("Executing node in " + str(node.time_to) + " with dV " + str(node.delta_v))
        # Engaging autopilot steering
        self.vessel.control.sas = False
        self.vessel.control.rcs = False
        # self.vessel.auto_pilot.engage()
        # self.vessel.auto_pilot.reference_frame = node.reference_frame
        # self.vessel.auto_pilot.target_direction = (0, 1, 0)
        # self.vessel.auto_pilot.wait()
        self.vessel.auto_pilot.disengage()
        self.vessel.auto_pilot.sas = True
        time.sleep(.1)
        self.vessel.auto_pilot.sas_mode = self.vessel.auto_pilot.sas_mode.maneuver
        self.vessel.auto_pilot.wait()
        # Get burn duration, start time, and warp to start - 5s lead
        realBurnDuration = self.calculate_burn_duration(node.delta_v)
        burnStartTime = node.ut - (realBurnDuration/2.)
        self.conn.space_center.warp_to(burnStartTime - 30)
        self.vessel.auto_pilot.wait()
        # Execute burn
        while self.ut() < burnStartTime:
            #print("Waiting to burn " + str(self.ut()) + " | " + str(burnStartTime))
            time.sleep(0.1)
        print("Executing burn")
        self.vessel.control.throttle = 1.0
        time.sleep(realBurnDuration - 0.1)
        #TODO: This could use some work
        print("Fine tuning")
        self.vessel.control.throttle = 0.05
        remainingBurn = self.conn.add_stream(node.remaining_burn_vector, node.reference_frame)
        while remainingBurn()[1] > 0.3:
            time.sleep(0.01)
        self.vessel.control.throttle = 0.0
        node.remove()

    def calculate_burn_duration(self, deltaV):
        # Calculate real burn duration using rocket equation
        availableThrust = self.vessel.available_thrust
        effectiveISP = self.vessel.specific_impulse * 9.82
        massInitial = self.vessel.mass
        massFinal = massInitial / math.exp(deltaV/effectiveISP)
        flow_rate = availableThrust / effectiveISP
        return (massInitial - massFinal) / flow_rate

    def plan_circularization(self, atApoapsis):
        # Creates a circularization node using vis-via equation 
        # atApoapsis: boolean, circularizes at periapsis if false
        print("Planning circularization, creating node")
        if (atApoapsis):
            r = self.vessel.orbit.apoapsis
            timeTo = self.vessel.orbit.time_to_apoapsis
        else:
            r = self.vessel.orbit.periapsis
            timeTo = self.vessel.orbit.time_to_periapsis
        mu = self.vessel.orbit.body.gravitational_parameter
        a1 = self.vessel.orbit.semi_major_axis
        a2 = r
        print(a2)
        print(r)
        v1 = math.sqrt(mu*((2./r)-(1./a1)))
        v2 = math.sqrt(mu*((2./r)-(1./a2)))
        deltaV = v2 - v1
        return self.vessel.control.add_node(self.ut() + timeTo, prograde=deltaV)