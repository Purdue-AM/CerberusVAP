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

# Initialization variables
diameter = 0
part_diameter = 0
algorithm = True
x_vec = []
y_vec = []
height = 0
last_height = 0
finalcure = False
toolchange = False
toolcount = 0

# User input
method, sequence, brightness = setup()
if brightness != 0:
    desired_height, UV_time, light_diameter, overlap, x_light_offset, y_light_offset = inputs()
    overlap = float(overlap/2)
#desired_height = 2 # height at which to cure in mm
#UV_time = 1 # how long to turn on UV, in seconds
#light_diameter = 15
#overlap = 5
#x_light_offset = 0
#y_light_offset = 0


# Indexes
i = 0
j = 0
k = 0

X = 0
Y = 1
Z = 2
E = 3

# Open new file
file = input('Enter a filename: ')

# Get part diameter(s)
if sequence == 1:
    with open(file, 'r') as file1:
        part_diameter = pattern_diameter(file1, light_diameter, X, Y)
elif sequence == 2:
    with open(file, 'r') as file1:
        part_diameter_1, part_diameter_2 = diameter_input(file1)

# Extrusion algorithm
extrude(file)
file_a = file.split('.')
file = file_a[0] + '_parsed.gcode' # Now this new file is the one that will be edited instead of the old one

# Have a new name for the output
output_a = file.split('.')
output = output_a[0] + '_parsed_final.gcode' # change to .gcode later

# Curing algorithm starts
if brightness != 0:
    
    # Get all x & y points for the last x layers
    with open(file,'r') as file:
    
    # Extract all lines of the file
        lines = file.readlines()
        file.seek(0)
        
        # Get layer height before skipping the comments
        layer_height = get_layer_height(file)
                
        with open(output, 'w') as parse_file:
            
            # Skip top comments as they can cause code to malfunction
            # (change the index to k if you want comments in your parsed file)
            while lines[j].startswith(';'):
                j = j + 1
            
            # Get to layer that reaches desired height and input UV commands
            while finalcure != True: 

                while height < desired_height - layer_height and j < len(lines) - 1:  
                
                    lines_it = lines[j] # Get the line being read from g-code
                    
                    # To prevent tool change before curing commands are written
                    if lines_it.startswith('T') == False or (lines_it.startswith('T') and toolcount == 0): # other lines not starting with T get written
                        parse_file.write(lines_it)
                    
                    # Need toolcount > 1 for toolchange 
                    if lines_it.startswith('T'):
                        toolcount = toolcount + 1

                    # Knows when to perform the final cure and end the code
                    if lines_it.startswith('; layer end'):
                        finalcure = True
                        break 
                    
                    # Get x and y distances for curing pattern
                    elif ('G1' in lines_it and 'X' in lines_it and 'Y' in lines_it):
                        parse = parse_line(lines_it)
                        x_vec.append(parse[X])
                        y_vec.append(parse[Y])
                        j = j + 1
                        
                    # Calculate current delta H and check if greater than desired delta H
                    elif (' Z' in lines_it and 'G1' in lines_it and 'nozzle' not in lines_it):
                        parse = parse_line(lines_it)
                        if parse[Z] != 0:
                            print('parsing: ' + str(parse[Z]))
                            height = round(parse[Z] - last_height,3) # get height < desired height
                            print('height: ' + str(height))
                        j = j + 1
                    
                    else:
                        j = j + 1
                        
                    # Get tool associated with line (stores tool number until next tool command appears)
                    if lines_it.startswith('T0') and toolcount > 1:
                        pin = '~1'
                        j = j + 1 # ensure we write the next line
                        break # go directly to writing curing commands

                    elif lines_it.startswith('T1') and toolcount > 1:
                        pin = '~2'
                        j = j = 1 # ensure we write the next line
                        break # go directly to writing curing commands
                
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
                
                # If the G-code ended, perform the final cure and end the code
                if finalcure == True:  
                    final_commands(parse_file)

                # Get last z height to get back to Z = 0 since Z adds up in gcode
                last_height = parse[Z]
                height = 0
                
        print('\nCommands for the UV curing pattern have been written in the G-code')
        
else: 
    print('No UV curing pattern for you because you chose no brightness!') 

# Functions to make
# diameter
# parsing x & y
# parsing T and S

# Todo
# WORRY ABOUT HYBRID LATER!!!!
# change pins for UV lights and transducers
# make function for getting coordinates of parts, separated by each tool (immediate)
# separate curing pattern by tool (for non-sequential,cure after every tool change. For hybrid, no curing on T0)
# separate part diameter by tool (for sequential print, get diameter of each part)
# separate transducer patter by method (for hybrid printing, no transducer activation for T0)

# skip skirt lines when outputting to file
    
# Unused code
    
#                    # Get which toolhead is printing and its temperature
#                    if ('M104' in lines_it and 'T' in lines_it):
#                        T_ = int(lines_it[lines_it.rfind('T')+1:])
#                        S_ = int(lines_it[lines_it.rfind('S')+1])
#                        j = j + 1
    
                    
                # Once curing finished, if printing with UV curable material, turn UV light off 
#                if T_ > 0: add statement when UV light not routed to fan anymore
#                parse_file.write('\nM104 S' + str(S_) + 'T' + str(T_ + 30)) # get back to normal extrusion temp
                
                                # If ABS/PLA, reduce temp to prevent extrusion
#                if T_ > 50: add once fan not routed to UV light
#                parse_file.write('\nM104 S' + str(S_) + 'T' + str(T_ - 30))
                