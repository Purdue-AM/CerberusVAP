# Imported Libraries:
#import os.path
import os
import math
from gcode_parsing_functions import extrude, diameter_input, setup, inputs, pattern_diameter, get_layer_height, final_commands, static_commands, pattern_commands, parse_line
#from gcode_parsing_functions import *
import sys
import numpy as np
from itertools import islice
from scipy.spatial import Delaunay
from scipy.spatial import ConvexHull

def toolchange(file, UV_time, light_diameter, overlap, x_light_offset, y_light_offset, brightness):
    
    # Indexes
    j = 0
    # Initialization Variables
    x_vec = []
    y_vec = []
    finalcure = False
    toolchange = False
    toolcount = 0
    X = 0
    Y = 1
    Z = 2
    
    # Have a new name for the output
    output_a = file.split('.')
    output = output_a[0] + '_parsed.gcode' # change to .gcode later
    
    
    # Get all x & y points for the last x layers
    with open(file,'r') as file:
    
        # Extract all lines of the file
        lines = file.readlines()
        file.seek(0)
            
        with open(output, 'w') as parse_file:
            
            # !!!!!!!!!!!!!!!!!!!!!
            while lines[j].startswith(';'):
                j = j + 1
            
            while j < len(lines) - 1: # EOF
                
                while toolchange == False and j < len(lines) - 1:
                    lines_it = lines[j] # Get the line being read from g-code
                    
                    # To prevent tool change before curing commands are written
                    if lines_it.startswith('T') == False or (lines_it.startswith('T') and toolcount == 0): # other lines not starting with T get written
                        parse_file.write(lines_it)
                    
                    # Need toolcount > 1 for toolchange 
                    if lines_it.startswith('T'):
                        toolcount = toolcount + 1
                    
                    # Get x and y distances for curing pattern
                    elif ('G1' in lines_it and 'X' in lines_it and 'Y' in lines_it):
                        parse = parse_line(lines_it)
                        x_vec.append(parse[X])
                        y_vec.append(parse[Y])
                    
                    # Calculate current delta H and check if greater than desired delta H
                    elif (' Z' in lines_it and 'G1' in lines_it and 'nozzle' not in lines_it):
                        parse = parse_line(lines_it)
                        print(parse[Z])
                        height = parse[Z]
                            
                    # Get tool associated with line (stores tool number until next tool command appears)
                    if lines_it.startswith('T0') and toolcount > 1:
                        toolchange = True
                        pin = '~1'
        
                    elif lines_it.startswith('T1') and toolcount > 1:
                        toolchange = True
                        pin = '~2'
                    
                    j = j + 1
                
                # Raise nozzle before curing
                parse_file.write('G1 Z' + str(height + 10))
                
                # Make Toolhead Wait before proceeding to curing to make sure 
                # nothing extrudes while it's moving to the curing location
                parse_file.write('G4 P2000')
                
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
                        y = y_light_offset + y_min + b * (light_diameter - overlap)
                        x = x_light_offset + x_min + a * (light_diameter - overlap)
                        
                        # Input curing commands
                        pattern_commands(parse_file, x, y, height, UV_time, finalcure, brightness, pin)
        
                # Turn UV light off after curing the layers
                parse_file.write('\nM42 P~ S0 ;turns UV off\n') 
                
                # Write the tool change line when the curing commands are written (not before due to the tool offset programmed in Simplify3D)
                if lines_it.startswith('T') == True: 
                    parse_file.write(lines_it)
                    
                # Reset tool change
                toolchange = False
                
        print('\nCommands for the UV curing pattern have been written in the G-code')
        
    return(parse_file);
    
    
## Initialization variables
#diameter = 0
#part_diameter = 0
#algorithm = True
#x_vec = []
#y_vec = []
#finalcure = False
#toolchange = False
#toolcount = 0
#
## !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#brightness = 255
#UV_time = 1 # how long to turn on UV, in seconds
#light_diameter = 10
#overlap = 0
#x_light_offset = 0
#y_light_offset = 0
#
#
## Indexes
#i = 0
#j = 0
#k = 0
#
#X = 0
#Y = 1
#Z = 2
#E = 3
#
## Open new file
#file = input('Enter a filename: ')
#
## Have a new name for the output
#output_a = file.split('.')
#output = output_a[0] + '_parsed.gcode' # change to .gcode later
#
#
## Get all x & y points for the last x layers
#with open(file,'r') as file:
#
#    # Extract all lines of the file
#    lines = file.readlines()
#    file.seek(0)
#        
#    with open(output, 'w') as parse_file:
#        
#        # !!!!!!!!!!!!!!!!!!!!!
#        while lines[j].startswith(';'):
#            j = j + 1
#        
#        while j < len(lines) - 1: # EOF
#            
#            while toolchange == False and j < len(lines) - 1:
#                lines_it = lines[j] # Get the line being read from g-code
#                
#                # To prevent tool change before curing commands are written
#                if lines_it.startswith('T') == False or (lines_it.startswith('T') and toolcount == 0): # other lines not starting with T get written
#                    parse_file.write(lines_it)
#                
#                # Need toolcount > 1 for toolchange 
#                if lines_it.startswith('T'):
#                    toolcount = toolcount + 1
#                
#                # Get x and y distances for curing pattern
#                elif ('G1' in lines_it and 'X' in lines_it and 'Y' in lines_it):
#                    parse = parse_line(lines_it)
#                    x_vec.append(parse[X])
#                    y_vec.append(parse[Y])
#                
#                # Calculate current delta H and check if greater than desired delta H
#                elif (' Z' in lines_it and 'G1' in lines_it and 'nozzle' not in lines_it):
#                    parse = parse_line(lines_it)
#                    print(parse[Z])
#                    height = parse[Z]
#                        
#                # Get tool associated with line (stores tool number until next tool command appears)
#                if lines_it.startswith('T0') and toolcount > 1:
#                    toolchange = True
#                    pin = '~1'
#    
#                elif lines_it.startswith('T1') and toolcount > 1:
#                    toolchange = True
#                    pin = '~2'
#                
#                j = j + 1
#            
#            # Raise nozzle before curing
#            parse_file.write('G1 Z' + str(height + 10))
#            
#            # Make Toolhead Wait before proceeding to curing to make sure 
#            # nothing extrudes while it's moving to the curing location
#            parse_file.write('G4 P2000')
#            
#            # Get max and min x & y distances to form the rectangular pattern
#            x_max = np.amax(x_vec)
#            x_min = np.amin(x_vec)
#            y_max = np.amax(y_vec)
#            y_min = np.amin(y_vec)
#            
#            m = int(np.ceil((x_max - x_min) / light_diameter))
#            n = int(np.ceil((y_max - y_min) / light_diameter))
#            
#            # Start curing pattern
#            for b in range(0, n):
#                for a in range(0, m): 
#                    y = y_light_offset + y_min + b * (light_diameter - overlap)
#                    x = x_light_offset + x_min + a * (light_diameter - overlap)
#                    
#                    # Input curing commands
#                    pattern_commands(parse_file, x, y, height, UV_time, finalcure, brightness, pin)
#    
#            # Turn UV light off after curing the layers
#            parse_file.write('\nM42 P~ S0 ;turns UV off\n') 
#            
#            # Write the tool change line when the curing commands are written (not before due to the tool offset programmed in Simplify3D)
#            if lines_it.startswith('T') == True: 
#                parse_file.write(lines_it)
#                
#            # Reset tool change
#            toolchange = False
#            
#    print('\nCommands for the UV curing pattern have been written in the G-code')