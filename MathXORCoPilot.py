import krpc
import math
import time

import PID
from consoleprint import print
from vectorMath import *

class MathXORCoPilot:
    def __init__(self, math_os):
        print("Initializing MathXORCoPilot")
        self.setUp(math_os)

    def setUp(self, math_os):
        self.conn = math_os.get_conn()
        self.streams = math_os.get_streams()
        self.maneuver_pilot = math_os.get_maneuver_pilot()

        self.vessel = self.conn.space_center.active_vessel
        self.ut = self.streams.get_stream('ut')
        self.altitude = self.streams.get_stream('mean_altitude')
        print("Initialized MathXORCoPilot")

    def basicLaunch(self, targetAltitude, turnEnd):
        print("Starting launch. Target Alt: " + str(targetAltitude))
        available_thrust = self.vessel.available_thrust
        mass_initial = self.vessel.mass
        turn_exponent = max(1 / (2.25 * (available_thrust / mass_initial) - 1.35), 0.25)
        pitch_angle = 90 * (1 - (self.altitude() / turnEnd) ** turn_exponent)
        self.vessel.auto_pilot.reference_frame=self.vessel.surface_reference_frame
        self.vessel.auto_pilot.target_pitch_and_heading(90,90)
        self.vessel.auto_pilot.engage()
        self.vessel.control.throttle=1.0
        while self.altitude() < 100:
            time.sleep(0.01)
            pass
        print("Passed 100m")
        print("Pitch angle: " + str(pitch_angle))
        print(self.vessel.orbit.apoapsis_altitude < targetAltitude)
        while self.vessel.orbit.apoapsis_altitude < targetAltitude:
            time.sleep(0.01)
            self.vessel.auto_pilot.target_pitch_and_heading((90 * (1 - (self.altitude() / turnEnd) ** turn_exponent)),90)
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
        circularization_node = self.maneuver_pilot.plan_circularization(True)
        self.maneuver_pilot.execute_node(circularization_node)
        
    def hover(self,setpoint,kill_horizontal = False):
        print("Hovering")
        vertical_speed_pid = PID.PID(0.25,0.025,0.006)
        vertical_speed_pid.setpoint(setpoint)
        vertical_speed_pid.ClampI = 30.0
        if kill_horizontal:
            print("Killing horizontal speed")
            horizontal_speed_pid = PID.PID(0.15,0.05,0.006)
            horizontal_speed_pid.setpoint(0.0)
            horizontal_speed_pid.ClampI = 1.0
            horizontal_velocity_ref_frame = self.getHorizontalVelocityReferenceFrame()
            autopilot = self.vessel.auto_pilot
            autopilot.reference_frame = horizontal_velocity_ref_frame #self.vessel.surface_reference_frame self.vessel.orbit.body.reference_frame
            # autopilot.stopping_time = (0.25,0.25,0.25)
            autopilot.attenuation_angle = (2.9,2.9,2.9)
            # autopilot.time_to_peak = (5,5,5)
            # autopilot.overshoot = (0.01,0.01,0.01)
            autopilot.target_direction = (1,0,0)
            autopilot.target_roll = math.nan
            autopilot.engage()
            up_vector = self.getUpVectorInReferenceFrame(horizontal_velocity_ref_frame) #self.vessel.orbit.body.reference_frame)
        vertical_speed = self.streams.get_stream('vertical_speed') #self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'vertical_speed')
        horizontal_speed = self.streams.get_stream('horizontal_speed') #self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'horizontal_speed')
        self.vessel.control.throttle = 1.0
        executing = True
        while executing:
            _throttle = max(0,min(1,vertical_speed_pid.update(vertical_speed())))
            # print("Vertical Speed: " + str(vertical_speed())[:5] + " | deltaThrottle: " + str(_throttle)[:5])
            self.vessel.control.throttle = _throttle
            if kill_horizontal:
                horizontal_speed_pid_output = horizontal_speed_pid.update(horizontal_speed())
                # _optimal_target = vector_subtract(up_vector, vector_scale(self.getOppositeHorizontalVelocityVector(horizontal_velocity_ref_frame,up_vector),abs(max(-1,min(1,horizontal_speed_pid_output)))))
                _optimal_target = self.getOppositeHorizontalVelocityVector(horizontal_velocity_ref_frame, up_vector, horizontal_speed_pid_output)
                autopilot.target_direction = _optimal_target
                # print("Autopilot Target Direction: " + str(autopilot.target_direction) + " || " + str(autopilot.target_pitch) + " - " + str(autopilot.target_heading) + " - " + str(autopilot.target_roll))
            if self.vessel.situation.landed == self.vessel.situation:
                print("Landed. Ending hover")
                executing = False
                autopilot.target_direction = up_vector
                self.vessel.control.throttle = 0.0
                time.sleep(5)
            if self.vessel.situation.splashed == self.vessel.situation:
                print("Landed. Ending hover")
                executing = False
                autopilot.target_direction = up_vector
                self.vessel.control.throttle = 0.0
                time.sleep(5)
            time.sleep(0.01)
        
    def hoverSlam(self, targetHeight = None):
        _radarAlt = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'surface_altitude')
        vertical_speed = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'vertical_speed')
        if not targetHeight:
            targetHeight = 10
        print("Hoverslamming at " + str(targetHeight))
        _g = (6.674080043*10**-11) * self.vessel.orbit.body.mass / self.vessel.orbit.body.equatorial_radius**2  # Constant G = 6.674080043*10**-11 m³/s²
        while vertical_speed() > -1:
            time.sleep(0.5)
        self.vessel.auto_pilot.disengage()
        self.vessel.auto_pilot.sas = True
        time.sleep(.1)
        self.vessel.auto_pilot.sas_mode = self.vessel.auto_pilot.sas_mode.retrograde
        # self.vessel.auto_pilot.wait()
        if _radarAlt() < targetHeight:
            print("Already lower than target, burning immediately")
            targetHeight = max(0, _radarAlt() - 50)
        executing = True
        _burning = False
        while executing:
            _trueRadar = _radarAlt() - targetHeight
            _maxDeceleration = (self.vessel.available_thrust / self.vessel.mass) - _g
            _stopDistance = vertical_speed()**2 / (2 * _maxDeceleration)
            if _burning:
                _idealThrottle = _stopDistance / _trueRadar
                #_impactTime = _trueRadar / abs(vertical_speed())
                self.vessel.control.throttle = _idealThrottle
                if _idealThrottle <= 0:
                    if vertical_speed() < 3:
                        executing = False
                        self.vessel.control.throttle = 0.0
            if _trueRadar < _stopDistance:
                _burning = True
            time.sleep(0.01)

    def kill_horizontalVelocity(self):
        print("Killing Horizontal Velocity")
        self.vessel.control.throttle = 0.0
        horizontal_speed = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'horizontal_speed')
        print("Horizontal Speed: " + str(horizontal_speed()))
        _ref_frame = self.getHorizontalVelocityReferenceFrame()#self.vessel.surface_velocity_reference_frame
        _oppositeHorizontalVelocityVector = self.getOppositeHorizontalVelocity() #self.getOppositeHorizontalVelocityVector(_ref_frame)
        autopilot = self.vessel.auto_pilot
        autopilot.reference_frame = _ref_frame
        autopilot.target_direction = _oppositeHorizontalVelocityVector # self.conn.space_center.transform_direction(velocity, ref_frame, self.vessel.surface_reference_frame)
        # autopilot.stopping_time = (0.25,0.25,0.25)
        autopilot.attenuation_angle = (2.9,2.9,2.9)
        # autopilot.time_to_peak = (5,5,5)
        # autopilot.overshoot = (0.01,0.01,0.01)
        autopilot.engage()
        print("Autopilot Target Direction: " + str(autopilot.target_direction) + " || " + str(autopilot.target_pitch) + " - " + str(autopilot.target_heading) + " - " + str(autopilot.target_roll))
        # autopilot.wait()
        while autopilot.error > 1:
            time.sleep(0.01)
        print("Vessel oriented. Starting burn")
        _burning = True
        self.vessel.control.throttle = 1.0
        while _burning:
            autopilot.target_direction = self.getOppositeHorizontalVelocity()
            if horizontal_speed() < 50:
                self.vessel.control.throttle = 0.1
            if horizontal_speed() < 0.3:
                _burning = False
            sleep(0.01)
        self.vessel.control.throttle = 0.0
        print("Horizontal velocity killed")
        autopilot.disengage

    def getHorizontalVelocityReferenceFrame(self):
        return self.conn.space_center.ReferenceFrame.create_hybrid(
            position=self.vessel.orbit.body.reference_frame, 
            rotation=self.vessel.surface_reference_frame)
    
    def getOppositeHorizontalVelocityVector(self, horizontal_velocity_ref_frame, up_vector = None, _factor = 1.0):
        if not up_vector:
            up_vector = self.getUpVectorInReferenceFrame(horizontal_velocity_ref_frame)
        _horizontalVelocityVector = self.vessel.flight(horizontal_velocity_ref_frame).velocity
        _oppositeHorizontalVelocityVector = vector_get_opposite(_horizontalVelocityVector)
        _oppositeHorizontalVelocityVectorScaled = vector_scale(_oppositeHorizontalVelocityVector,90)
        _oppositeHorizontalVelocityVectorScaledIsolated = vector_project_onto_plane(up_vector, _oppositeHorizontalVelocityVector)
        _result = vector_subtract(up_vector, vector_scale(_oppositeHorizontalVelocityVectorScaledIsolated, abs(max(-1,min(1,_factor)))))
        # return self.conn.space_center.transform_direction(_result, horizontal_velocity_ref_frame, self.vessel.surface_reference_frame)
        return _result

    def getUpVectorInReferenceFrame(self, _ref_frame):
        return self.conn.space_center.transform_direction((1,0,0), self.vessel.surface_reference_frame, _ref_frame)

    def getOnlyHorizontalVelocity(self):
        velocityVector = self.vessel.flight(self.getHorizontalVelocityReferenceFrame()).velocity
        return (0,velocityVector[1],velocityVector[2])
    
    def getOppositeHorizontalVelocity(self):
        return vector_get_opposite(self.getOnlyHorizontalVelocity())
    
    def hoverAtAlt(self, targetAltitude, kill_horizontalVelocity = False):
        self.hoverSlam(targetAltitude)
        self.hover(0, True)

    def land(self):
        _radarAlt = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'surface_altitude')
        vertical_speed = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'vertical_speed')
        print(_radarAlt() / abs(vertical_speed()))
        while _radarAlt() / abs(vertical_speed()) > 30:
            print(_radarAlt() / abs(vertical_speed()))
            time.sleep(0.01)
        # self.kill_horizontalVelocity()
        self.hoverSlam()