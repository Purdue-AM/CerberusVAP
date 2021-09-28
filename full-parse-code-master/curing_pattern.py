# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 18:25:46 2019

@author: Aaron Afriat
"""

def curing_pattern(pin, sequence, parse_file, height, x_vec, y_vec, y_light_offset, x_light_offset, light_diameter, overlap, UV_time, finalcure, brightness):

    # Make Toolhead Wait before proceeding to curing to make sure 
    # nothing extrudes while it's moving to the curing location
    parse_file.write('G4 P2000')
    print('Running UV Algorithm \n')
    
    # Raise nozzle before curing
    parse_file.write('G1 Z' + str(height + 10))
    
    # Get max and min x & y distances to form the rectangular pattern
    x_max = np.amax(x_vec)
    x_min = np.amin(x_vec)
    y_max = np.amax(y_vec)
    y_min = np.amin(y_vec)
    
    m = int(np.ceil((x_max - x_min) / light_diameter))
    n = int(np.ceil((y_max - y_min) / light_diameter))
    
    # Start curing pattern
    for b in range(0, n):
        for a in range(0, m):
            # accounts for the UV offset from the print head.
            # on the system, lights are y symmetrical and have the
            # same x offset
            if pin == '~1': 
                y = y_light_offset + y_min + b * (light_diameter - overlap)
            elif pin == '~2': # if hybrid, do not cure with T1
                y = -y_light_offset + y_min + b * (light_diameter - overlap)
            x = x_light_offset + x_min + a * (light_diameter - overlap)
            
            # Input curing commands
            pattern_commands(parse_file, x, y, height, UV_time, finalcure, brightness, pin)
    
    # Turn UV light off after curing the layers
    parse_file.write('\nM42 P~ S0 ;turns UV off\n') 