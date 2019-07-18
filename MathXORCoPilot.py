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
            _autopilot.reference_frame = _horizontalVelocityRefFrame #self.vessel.surface_reference_frame
            # _autopilot.reference_frame = self.vessel.orbit.body.reference_frame
            # _autopilot.stopping_time = (0.25,0.25,0.25)
            _autopilot.attenuation_angle = (2.9,2.9,2.9)
            # _autopilot.time_to_peak = (5,5,5)
            # _autopilot.overshoot = (0.01,0.01,0.01)
            _autopilot.target_direction = (1,0,0)#self.getHorizontalVelocityCounterVector(_horizontalVelocityRefFrame,1)
            _autopilot.target_roll = math.nan
            _autopilot.engage()
            _upVector = self.conn.space_center.transform_direction((1,0,0), self.vessel.surface_reference_frame, _horizontalVelocityRefFrame)#self.vessel.orbit.body.reference_frame)
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
                _antiHorizontalVelocityVector = self.vessel.flight(_horizontalVelocityRefFrame).velocity
                _horizontalSpeedVector = vector_project_onto_plane(_upVector,_antiHorizontalVelocityVector)
                _horizontalSpeedVectorNormalized = vector_normalize(_horizontalSpeedVector)
                #scale east/north by pid
                _horizontalSpeedVectorNormalizedProduct = (
                    _horizontalSpeedVectorNormalized[0]*_horizontalSpeedPID_output,
                    _horizontalSpeedVectorNormalized[1]*_horizontalSpeedPID_output,
                    _horizontalSpeedVectorNormalized[2]*_horizontalSpeedPID_output
                    ) #vector_scale(_horizontalSpeedVectorNormalized, (10000000 * _horizontalSpeedPID_output))
                _horizontalSpeedVectorNormalizedProductNormalized = vector_normalize(_horizontalSpeedVectorNormalizedProduct)
                _target_direction = vector_subtract(_upVector, _horizontalSpeedVectorNormalizedProduct)
                _target_direction = vector_normalize(_target_direction)
                # _target_direction = vector_subtract(_upVector, vector_scale(self.getHorizontalVelocityCounterVector(_horizontalVelocityRefFrame),_horizontalSpeedPID_output))
                # _autopilot.target_direction = _target_direction #vector_scale(_horizontalSpeedVectorNormalizedProductNormalized,-1)#(_target_direction[0], _target_direction[1], _target_direction[2])
                # _autopilot.target_direction = self.getHorizontalVelocityCounterVector(_horizontalVelocityRefFrame)
                _oppositeAntiHorizontalVelocityVector = vector_get_opposite(_antiHorizontalVelocityVector)
                _oppositeAntiHorizontalVelocityVector = vector_scale(_oppositeAntiHorizontalVelocityVector,90)
                _oppositeAntiHorizontalVelocityVector = vector_project_onto_plane(_upVector, _oppositeAntiHorizontalVelocityVector)
                _optimal_target = vector_subtract(_upVector, vector_scale(_oppositeAntiHorizontalVelocityVector,abs(max(-1,min(1,_horizontalSpeedPID_output)))))
                _autopilot.target_direction = _optimal_target
                print("Autopilot Target Direction: " + str(_autopilot.target_direction))
                # print(
                #     "H. Spd: " + str(_horizontalSpeed())[:5] + "| PID: " + str(_horizontalSpeedPID_output) + "\n" + 
                #     "Vec0: " + str(_antiHorizontalVelocityVector) + "\n" +
                #     "Vec1: " + str(_oppositeAntiHorizontalVelocityVector) + "\n" +
                #     "Vec2: " + str(_horizontalSpeedVector) + "\n" +
                #     "Vec3: " + str(_horizontalSpeedVectorNormalized) + "\n" +
                #     "Vec4: " + str(_horizontalSpeedVectorNormalizedProduct) + "\n" +
                #     "Vec5: " + str(_horizontalSpeedVectorNormalizedProductNormalized) + "\n" +
                #     "input: " + str(self.vessel.flight(_horizontalVelocityRefFrame).velocity) + "\n" +
                #     "up: " + str(_upVector) + "\n" +
                #     "tVec: " + str(_target_direction) + "\n" +
                #     "AP: " + str(_autopilot.target_direction) + "\n" +
                #     "AP Srf: " + str(_autopilot.target_pitch) + " - " + str(_autopilot.target_heading) + " - " + str(_autopilot.target_roll) + " - " + "\n" +
                #     "V Speed: " + str(_verticalSpeed())[:5] + " | deltaThrottle: " + str(_throttle)[:5] + "\n" +
                #     "getHorzCounter: " + str(self.getHorizontalVelocityCounterVector(_horizontalVelocityRefFrame))
                #     )
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
    
        # DECLARE LOCAL LOCK hsVec TO VXCL(UP:VECTOR,SRFRETROGRADE:VECTOR):NORMALIZED.
        # LOCK STEERING TO UP:VECTOR - (hsVec * HORZPID:UPDATE(TIME:SECONDS, SHIP:GROUNDSPEED)).
        # self.vessel.surface_reference_frame(1,0,0) - (self.vessel.surface_velocity_reference_frame(0,-1,0) * _horizontalSpeedPID.update(_horizontalSpeed())
        
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
        ref_frame = self.getHorizontalVelocityReferenceFrame()#self.vessel.surface_velocity_reference_frame
        # velocity = self.vessel.flight(ref_frame).velocity
        # velocity = self.conn.space_center.transform_direction(velocity, ref_frame, self.vessel.surface_reference_frame)
        while True:
            velocity = self.vessel.flight(ref_frame).velocity
            print('Surface velocity = (%.1f, %.1f, %.1f)' % velocity)
            #print(self.getHorizontalVelocityCounterVector(ref_frame))
            print('Target vector = (%.1f, %.1f, %.1f)' % self.getHorizontalVelocityCounterVector(ref_frame))
            time.sleep(1)
        # self.vessel.auto_pilot.target_direction = (0, -1, 0)
        # # self.vessel.auto_pilot.stopping_time = 2
        # self.vessel.auto_pilot.time_to_peak = (1,1,1)
        # self.vessel.auto_pilot.overshoot = (0.1,0.1,0.1)
        # self.vessel.auto_pilot.wait()
        # print("Vessel oriented, burning")
        # self.vessel.control.throttle = 1.0
        # while _horizontalSpeed() > 0.1:
        #     time.sleep(0.001)
        # self.vessel.control.throttle = 0.0

    def getHorizontalVelocityReferenceFrame(self):
        return self.conn.space_center.ReferenceFrame.create_hybrid(
            position=self.vessel.orbit.body.reference_frame, 
            rotation=self.vessel.surface_reference_frame)
    
    def getHorizontalVelocityCounterVector(self, horizontalVelocityReferenceFrame):
        vessel_velocity_rel_to_body = self.vessel.flight(horizontalVelocityReferenceFrame).velocity
        vessel_position_bdy = self.vessel.position(self.vessel.orbit.body.reference_frame)
        body_to_vessel_norm = vector_normalize(vessel_position_bdy)
        vessel_to_north_vec = self.conn.space_center.transform_direction((0,5,0), self.vessel.surface_reference_frame, self.vessel.orbit.body.reference_frame)
        offset_vessel_to_north_vec = vector_add(vessel_position_bdy, vessel_to_north_vec)
        vessel_to_east_vec = self.conn.space_center.transform_direction((0,0,5), self.vessel.surface_reference_frame, self.vessel.orbit.body.reference_frame)
        offset_vessel_to_east_vec = vector_add(vessel_position_bdy, vessel_to_east_vec)
        hrz_velocity_north = vector_dot_product(vessel_velocity_rel_to_body, vector_normalize(vessel_to_north_vec))
        hrz_velocity_east = vector_dot_product(vessel_velocity_rel_to_body, vector_normalize(vessel_to_east_vec))
        hrz_velocity = vector_project_onto_plane(vessel_velocity_rel_to_body, vessel_position_bdy)
        hrz_velocity_mag = vector_length(hrz_velocity)
        hrz_velocity_norm = vector_normalize(hrz_velocity)
        hrz_counter_velocity_norm = vector_scale(hrz_velocity_norm, -1.0)
        hrz_counter_velocity_mag = hrz_velocity_mag if (hrz_velocity_mag < 5.0) else 5.0
        hrz_counter_velocity = vector_scale(hrz_counter_velocity_norm, hrz_counter_velocity_mag)
        counter_direction_zenith = 90#28.36
        zenith_counter_velocity = vector_scale(body_to_vessel_norm, counter_direction_zenith)
        result = vector_add(zenith_counter_velocity, hrz_counter_velocity)
        result = self.conn.space_center.transform_direction(result, horizontalVelocityReferenceFrame, self.vessel.surface_reference_frame)
        return (result[0],result[1],result[2])
    
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