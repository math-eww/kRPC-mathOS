import krpc
import math
import time

import ManeuverAutopilot
import PID
from consoleprint import print
from vectorMath import *

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
        
    def hover(self,setpoint,killHorizontal = False):
        print("Hovering")
        _verticalSpeedPID = PID.PID(0.25,0.025,0.006)
        _verticalSpeedPID.setpoint(setpoint)
        _verticalSpeedPID.ClampI = 30.0
        if killHorizontal:
            print("Killing horizontal speed")
            _horizontalSpeedPID = PID.PID(0.15,0.05,0.006)
            _horizontalSpeedPID.setpoint(0.0)
            _horizontalSpeedPID.ClampI = 1.0
            _horizontalVelocityRefFrame = self.getHorizontalVelocityReferenceFrame()
            _autopilot = self.vessel.auto_pilot
            _autopilot.reference_frame = _horizontalVelocityRefFrame #self.vessel.surface_reference_frame self.vessel.orbit.body.reference_frame
            # _autopilot.stopping_time = (0.25,0.25,0.25)
            _autopilot.attenuation_angle = (2.9,2.9,2.9)
            # _autopilot.time_to_peak = (5,5,5)
            # _autopilot.overshoot = (0.01,0.01,0.01)
            _autopilot.target_direction = (1,0,0)
            _autopilot.target_roll = math.nan
            _autopilot.engage()
            _upVector = self.getUpVectorInReferenceFrame(_horizontalVelocityRefFrame) #self.vessel.orbit.body.reference_frame)
        _verticalSpeed = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'vertical_speed')
        _horizontalSpeed = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'horizontal_speed')
        self.vessel.control.throttle = 1.0
        _executing = True
        while _executing:
            _throttle = max(0,min(1,_verticalSpeedPID.update(_verticalSpeed())))
            # print("Vertical Speed: " + str(_verticalSpeed())[:5] + " | deltaThrottle: " + str(_throttle)[:5])
            self.vessel.control.throttle = _throttle
            if killHorizontal:
                _horizontalSpeedPID_output = _horizontalSpeedPID.update(_horizontalSpeed())
                # _optimal_target = vector_subtract(_upVector, vector_scale(self.getOppositeHorizontalVelocityVector(_horizontalVelocityRefFrame,_upVector),abs(max(-1,min(1,_horizontalSpeedPID_output)))))
                _optimal_target = self.getOppositeHorizontalVelocityVector(_horizontalVelocityRefFrame, _upVector, _horizontalSpeedPID_output)
                _autopilot.target_direction = _optimal_target
                # print("Autopilot Target Direction: " + str(_autopilot.target_direction) + " || " + str(_autopilot.target_pitch) + " - " + str(_autopilot.target_heading) + " - " + str(_autopilot.target_roll))
            if self.vessel.situation.landed == self.vessel.situation:
                print("Landed. Ending hover")
                _executing = False
                _autopilot.target_direction = _upVector
                time.sleep(5)
            if self.vessel.situation.splashed == self.vessel.situation:
                print("Landed. Ending hover")
                _executing = False
                _autopilot.target_direction = _upVector
                time.sleep(5)
            time.sleep(0.01)
        
    def hoverSlam(self, targetHeight = None):
        _radarAlt = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'surface_altitude')
        _verticalSpeed = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'vertical_speed')
        if not targetHeight:
            targetHeight = 10
        print("Hoverslamming at " + str(targetHeight))
        _g = (6.674080043*10**-11) * self.vessel.orbit.body.mass / self.vessel.orbit.body.equatorial_radius**2  # Constant G = 6.674080043*10**-11 m³/s²
        while _verticalSpeed() > -1:
            time.sleep(0.5)
        self.vessel.auto_pilot.disengage()
        self.vessel.auto_pilot.sas = True
        time.sleep(.1)
        self.vessel.auto_pilot.sas_mode = self.vessel.auto_pilot.sas_mode.retrograde
        # self.vessel.auto_pilot.wait()
        if _radarAlt() < targetHeight:
            print("Already lower than target, burning immediately")
            targetHeight = max(0, _radarAlt() - 50)
        _executing = True
        _burning = False
        while _executing:
            _trueRadar = _radarAlt() - targetHeight
            _maxDeceleration = (self.vessel.available_thrust / self.vessel.mass) - _g
            _stopDistance = _verticalSpeed()**2 / (2 * _maxDeceleration)
            if _burning:
                _idealThrottle = _stopDistance / _trueRadar
                #_impactTime = _trueRadar / abs(_verticalSpeed())
                self.vessel.control.throttle = _idealThrottle
                if _idealThrottle <= 0:
                    if _verticalSpeed() < 3:
                        _executing = False
                        self.vessel.control.throttle = 0.0
            if _trueRadar < _stopDistance:
                _burning = True
            time.sleep(0.01)

    def killHorizontalVelocity(self):
        print("Killing Horizontal Velocity")
        self.vessel.control.throttle = 0.0
        _horizontalSpeed = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'horizontal_speed')
        print("Horizontal Speed: " + str(_horizontalSpeed()))
        _ref_frame = self.getHorizontalVelocityReferenceFrame()#self.vessel.surface_velocity_reference_frame
        _oppositeHorizontalVelocityVector = self.getOppositeHorizontalVelocity() #self.getOppositeHorizontalVelocityVector(_ref_frame)
        _autopilot = self.vessel.auto_pilot
        _autopilot.reference_frame = _ref_frame
        _autopilot.target_direction = _oppositeHorizontalVelocityVector # self.conn.space_center.transform_direction(velocity, ref_frame, self.vessel.surface_reference_frame)
        # _autopilot.stopping_time = (0.25,0.25,0.25)
        _autopilot.attenuation_angle = (2.9,2.9,2.9)
        # _autopilot.time_to_peak = (5,5,5)
        # _autopilot.overshoot = (0.01,0.01,0.01)
        _autopilot.engage()
        print("Autopilot Target Direction: " + str(_autopilot.target_direction) + " || " + str(_autopilot.target_pitch) + " - " + str(_autopilot.target_heading) + " - " + str(_autopilot.target_roll))
        # _autopilot.wait()
        while _autopilot.error > 1:
            time.sleep(0.01)
        print("Vessel oriented. Starting burn")
        _burning = True
        self.vessel.control.throttle = 1.0
        while _burning:
            _autopilot.target_direction = self.getOppositeHorizontalVelocity()
            if _horizontalSpeed() < 50:
                self.vessel.control.throttle = 0.1
            if _horizontalSpeed() < 0.3:
                _burning = False
            sleep(0.01)
        self.vessel.control.throttle = 0.0
        print("Horizontal velocity killed")
        _autopilot.disengage

    def getHorizontalVelocityReferenceFrame(self):
        return self.conn.space_center.ReferenceFrame.create_hybrid(
            position=self.vessel.orbit.body.reference_frame, 
            rotation=self.vessel.surface_reference_frame)
    
    def getOppositeHorizontalVelocityVector(self, _horizontalVelocityRefFrame, _upVector = None, _factor = 1.0):
        if not _upVector:
            _upVector = self.getUpVectorInReferenceFrame(_horizontalVelocityRefFrame)
        _horizontalVelocityVector = self.vessel.flight(_horizontalVelocityRefFrame).velocity
        _oppositeHorizontalVelocityVector = vector_get_opposite(_horizontalVelocityVector)
        _oppositeHorizontalVelocityVectorScaled = vector_scale(_oppositeHorizontalVelocityVector,90)
        _oppositeHorizontalVelocityVectorScaledIsolated = vector_project_onto_plane(_upVector, _oppositeHorizontalVelocityVector)
        _result = vector_subtract(_upVector, vector_scale(_oppositeHorizontalVelocityVectorScaledIsolated, abs(max(-1,min(1,_factor)))))
        # return self.conn.space_center.transform_direction(_result, _horizontalVelocityRefFrame, self.vessel.surface_reference_frame)
        return _result

    def getUpVectorInReferenceFrame(self, _ref_frame):
        return self.conn.space_center.transform_direction((1,0,0), self.vessel.surface_reference_frame, _ref_frame)

    def getOnlyHorizontalVelocity(self):
        velocityVector = self.vessel.flight(self.getHorizontalVelocityReferenceFrame()).velocity
        return (0,velocityVector[1],velocityVector[2])
    
    def getOppositeHorizontalVelocity(self):
        return vector_get_opposite(self.getOnlyHorizontalVelocity())
    
    def hoverAtAlt(self, targetAltitude, killHorizontalVelocity = False):
        self.hoverSlam(targetAltitude)
        self.hover(0, True)

    def land(self):
        _radarAlt = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'surface_altitude')
        _verticalSpeed = self.conn.add_stream(getattr, self.vessel.flight(self.vessel.orbit.body.reference_frame), 'vertical_speed')
        print(_radarAlt() / abs(_verticalSpeed()))
        while _radarAlt() / abs(_verticalSpeed()) > 30:
            print(_radarAlt() / abs(_verticalSpeed()))
            time.sleep(0.01)
        # self.killHorizontalVelocity()
        self.hoverSlam()