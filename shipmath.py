import math

def get_g(vessel):
    # Constant G = 6.674080043*10**-11 m³/s²
    return (6.674080043*10**-11) * vessel.orbit.body.mass / vessel.orbit.body.equatorial_radius**2
    #TODO: replace with space_center.g?

def get_max_deceleration(vessel):
    return (vessel.available_thrust / vessel.mass) - get_g(vessel)

def get_max_horizontal_deceleration(vessel):
    return vessel.available_thrust / vessel.mass

def calculate_burn_duration(vessel, deltaV):
    # Calculate real burn duration using rocket equation
    available_thrust = vessel.available_thrust
    effective_ISP = vessel.specific_impulse * get_g(vessel) #9.82
    mass_initial = vessel.mass
    mass_final = mass_initial / math.exp(deltaV/effective_ISP)
    flow_rate = available_thrust / effective_ISP
    return (mass_initial - mass_final) / flow_rate