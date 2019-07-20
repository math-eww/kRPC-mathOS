import krpc
import math
import time

import PID
from consoleprint import print
from vectorMath import *
from shipmath import *

class MathXORCoPilot:
    def __init__(self, math_os):
        print("Initializing MathXORCoPilot")
        self.set_up(math_os)

    def set_up(self, math_os):
        self.conn = math_os.get_conn()
        self.streams = math_os.get_streams()
        self.maneuver_pilot = math_os.get_maneuver_pilot()

        self.vessel = self.conn.space_center.active_vessel
        self.ut = self.streams.get_stream('ut')
        self.altitude = self.streams.get_stream('mean_altitude')
        print("Initialized MathXORCoPilot")

    def basic_launch(self, target_altitude, turn_end):
        print("Starting launch. Target Alt: " + str(target_altitude))
        available_thrust = self.vessel.available_thrust
        mass_initial = self.vessel.mass
        turn_exponent = max(1 / (2.25 * (available_thrust / mass_initial) - 1.35), 0.25)
        pitch_angle = 90 * (1 - (self.altitude() / turn_end) ** turn_exponent)
        self.vessel.auto_pilot.reference_frame=self.vessel.surface_reference_frame
        self.vessel.auto_pilot.target_pitch_and_heading(90,90)
        self.vessel.auto_pilot.engage()
        self.vessel.control.throttle=1.0
        while self.altitude() < 100:
            time.sleep(0.01)
            pass
        print("Passed 100m")
        print("Pitch angle: " + str(pitch_angle))
        print(self.vessel.orbit.apoapsis_altitude < target_altitude)
        while self.vessel.orbit.apoapsis_altitude < target_altitude:
            time.sleep(0.01)
            self.vessel.auto_pilot.target_pitch_and_heading((90 * (1 - (self.altitude() / turn_end) ** turn_exponent)),90)
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
            horizontal_velocityref_frame = self.get_horizontal_velocity_reference_frame()
            autopilot = self.vessel.auto_pilot
            autopilot.reference_frame = horizontal_velocityref_frame #self.vessel.surface_reference_frame self.vessel.orbit.body.reference_frame
            # autopilot.stopping_time = (0.25,0.25,0.25)
            autopilot.attenuation_angle = (2.9,2.9,2.9)
            # autopilot.time_to_peak = (5,5,5)
            # autopilot.overshoot = (0.01,0.01,0.01)
            autopilot.target_direction = (1,0,0)
            autopilot.target_roll = math.nan
            autopilot.engage()
            up_vector = self.get_up_vector_in_reference_frame(horizontal_velocityref_frame) #self.vessel.orbit.body.reference_frame)
        vertical_speed = self.streams.get_stream('vertical_speed')
        horizontal_speed = self.streams.get_stream('horizontal_speed')
        self.vessel.control.throttle = 1.0
        executing = True
        while executing:
            _throttle = max(0,min(1,vertical_speed_pid.update(vertical_speed())))
            # print("Vertical Speed: " + str(vertical_speed())[:5] + " | deltaThrottle: " + str(_throttle)[:5])
            self.vessel.control.throttle = _throttle
            if kill_horizontal:
                horizontal_speed_pid_output = horizontal_speed_pid.update(horizontal_speed())
                # _optimal_target = vector_subtract(up_vector, vector_scale(self.get_opposite_horizontal_velocity_vector(horizontal_velocityref_frame,up_vector),abs(max(-1,min(1,horizontal_speed_pid_output)))))
                _optimal_target = self.get_opposite_horizontal_velocity_vector(horizontal_velocityref_frame, up_vector, horizontal_speed_pid_output)
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
        
    def hover_slam(self, target_height = None):
        radar_alt = self.streams.get_stream('surface_altitude')
        vertical_speed = self.streams.get_stream('vertical_speed')
        if not target_height:
            target_height = 10
        print("Hoverslamming at " + str(target_height))
        g = get_g(self.vessel) #(6.674080043*10**-11) * self.vessel.orbit.body.mass / self.vessel.orbit.body.equatorial_radius**2  # Constant G = 6.674080043*10**-11 m³/s²
        while vertical_speed() > -1:
            time.sleep(0.5)
        self.vessel.auto_pilot.disengage()
        self.vessel.auto_pilot.sas = True
        time.sleep(.1)
        self.vessel.auto_pilot.sas_mode = self.vessel.auto_pilot.sas_mode.retrograde
        # self.vessel.auto_pilot.wait()
        if radar_alt() < target_height:
            print("Already lower than target, burning immediately")
            target_height = max(0, radar_alt() - 50)
        executing = True
        burning = False
        while executing:
            true_radar = radar_alt() - target_height
            max_deceleration = get_max_deceleration(self.vessel) #(self.vessel.available_thrust / self.vessel.mass) - g
            stop_distance = vertical_speed()**2 / (2 * max_deceleration)
            if burning:
                ideal_throttle = stop_distance / true_radar
                #impact_time = true_radar / abs(vertical_speed())
                self.vessel.control.throttle = ideal_throttle
                if ideal_throttle <= 0:
                    if vertical_speed() < 3:
                        executing = False
                        self.vessel.control.throttle = 0.0
            if true_radar < stop_distance:
                burning = True
            time.sleep(0.01)

    def kill_horizontal_velocity(self):
        print("Killing Horizontal Velocity")
        self.vessel.control.throttle = 0.0
        horizontal_speed = self.streams.get_stream('horizontal_speed')
        print("Horizontal Speed: " + str(horizontal_speed()))
        ref_frame = self.get_horizontal_velocity_reference_frame()
        opposite_horizontal_velocity_vector = self.get_opposite_horizontal_velocity()
        autopilot = self.vessel.auto_pilot
        autopilot.reference_frame = ref_frame
        autopilot.target_direction = opposite_horizontal_velocity_vector
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
        burning = True
        self.vessel.control.throttle = 1.0
        while burning:
            #TODO: get burn duration for horizontal speed dV and impact time and burn when current time - burn duration = impact time - 30s
            autopilot.target_direction = self.get_opposite_horizontal_velocity()
            self.vessel.control.throttle = horizontal_speed() / 100
            if horizontal_speed() < 10:
                self.vessel.control.throttle = 0.1
            if horizontal_speed() < 0.5:
                self.vessel.control.throttle = 0.0
                burning = False
            time.sleep(0.01)
        self.vessel.control.throttle = 0.0
        print("Horizontal velocity killed")
        autopilot.disengage()

    def get_horizontal_velocity_reference_frame(self):
        return self.conn.space_center.ReferenceFrame.create_hybrid(
            position=self.vessel.orbit.body.reference_frame, 
            rotation=self.vessel.surface_reference_frame)
    
    def get_opposite_horizontal_velocity_vector(self, horizontal_velocityref_frame, up_vector = None, _factor = 1.0):
        if not up_vector:
            up_vector = self.get_up_vector_in_reference_frame(horizontal_velocityref_frame)
        horizontal_velocity_vector = self.vessel.flight(horizontal_velocityref_frame).velocity
        opposite_horizontal_velocity_vector = vector_get_opposite(horizontal_velocity_vector)
        # opposite_horizontal_velocity_vector_scaled = vector_scale(opposite_horizontal_velocity_vector,90)
        opposite_horizontal_velocity_vector_isolated = vector_project_onto_plane(up_vector, opposite_horizontal_velocity_vector)
        return vector_subtract(up_vector, vector_scale(opposite_horizontal_velocity_vector_isolated, abs(max(-1,min(1,_factor)))))
        # return self.conn.space_center.transform_direction(_result, horizontal_velocityref_frame, self.vessel.surface_reference_frame)

    def get_up_vector_in_reference_frame(self, ref_frame):
        return self.conn.space_center.transform_direction((1,0,0), self.vessel.surface_reference_frame, ref_frame)

    def get_only_horizontal_velocity(self):
        velocity_vector = self.vessel.flight(self.get_horizontal_velocity_reference_frame()).velocity
        return (0,velocity_vector[1],velocity_vector[2])
    
    def get_opposite_horizontal_velocity(self):
        return vector_get_opposite(self.get_only_horizontal_velocity())
    
    def hover_at_alt(self, target_altitude, kill_horizontal_velocity = False):
        self.hover_slam(target_altitude)
        self.hover(0, kill_horizontal_velocity)

    def land(self, target_altitude = 20):
        # radar_alt = self.streams.get_stream('surface_altitude')
        # vertical_speed = self.streams.get_stream('vertical_speed')
        # print(radar_alt() / abs(vertical_speed()))
        # while radar_alt() / abs(vertical_speed()) > 30:
        #     print(radar_alt() / abs(vertical_speed()))
        #     time.sleep(0.01)
        self.kill_horizontal_velocity()
        self.hover_slam(target_altitude)
        self.hover(-1, True)