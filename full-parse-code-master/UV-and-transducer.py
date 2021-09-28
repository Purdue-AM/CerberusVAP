# -*- coding: utf-8 -*-

"""
Created on: Wed July 31 2019
Author: Aaron Afriat

Purpose:
To be used with VAP printing and Simplify 3D

Description:
This code parses a given .gcode file for the purpose of curing one or
multiple parts every few layers for a certain amount of time depending on
the material, area covered by the light and strength of the light.

"""

# Imported Libraries:
#import os.path
import os
import math
from gcode_parsing_functions import curing_pattern, toolchange, extrude, diameter_input, setup, inputs, pattern_diameter, get_layer_height, final_commands, static_commands, pattern_commands, parse_line
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

# User input
method, sequence, brightness = setup()
if brightness != 0:
    desired_height, UV_time, light_diameter, overlap, x_light_offset, y_light_offset = inputs()
    overlap = float(overlap/2)

# User input (manual)
#desired_height = 0.9 # height at which to cure in mm
#UV_time = 5 # how long to turn on UV, in seconds
#light_diameter = 14
#overlap = 0
#x_light_offset = 56
##x_light_offset = 0
#y_light_offset = 38
##y_light_offset = 0
#method = 1
#sequence = 1
#brightness = 255


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
if method == 1 or method == 3:
    with open(file, 'r') as file1:
        part_diameter = pattern_diameter(file1, light_diameter, X, Y)
elif method == 2:
    with open(file, 'r') as file1:
        part_diameter_1, part_diameter_2 = diameter_input(file1)

# Extrusion algorithm
extrude(file, method)

file_a = file.split('.')
file = file_a[0] + '_parsed.gcode' # Now this new file is the one that will be edited instead of the old one

# Have a new name for the output
output_a = file.split('.')
output = output_a[0] + '_parsed.gcode' # change to .gcode later

# Curing algorithm starts
if brightness != 0:
    
    # Get all x & y points for the last x layers
    with open(file,'r') as file1:
    
    # Extract all lines of the file
        lines = file1.readlines()
        file1.seek(0)
        
        # Get layer height before skipping the comments
        layer_height = get_layer_height(file1)
                
        with open(output, 'w') as parse_file:
            
            # Skip top comments as they can cause code to malfunction
            # (change the index to k if you want comments in your parsed file)
            while lines[j].startswith(';'):
                j = j + 1
            
            # Get to layer that reaches desired height and input UV commands
            while finalcure != True: #len(lines)-1:

                while height < desired_height - layer_height and j < len(lines) - 1:  
                    lines_it = lines[j] # Get the line being read from g-code
                    parse_file.write(lines_it)
        
                    # Knows when to cure for longer
                    if lines_it.startswith('; layer end'):
                        finalcure = True
                        break
                    
                    elif lines_it.startswith('T0'):
                        pin = '4'

                    elif lines_it.startswith('T1'):
                        pin = '6'
                        
                    # Get x and y distances for curing pattern
                    elif ('G1' in lines_it and 'X' in lines_it and 'Y' in lines_it):
                        parse = parse_line(lines_it)
                        x_vec.append(parse[X])
                        y_vec.append(parse[Y])
                        
                    # Calculate current delta H and check if greater than desired delta H
                    elif (' Z' in lines_it and 'G1' in lines_it and 'nozzle' not in lines_it):
                        parse = parse_line(lines_it)
                        if parse[Z] != 0:
                            print('parsing: ' + str(parse[Z]))
                            height = round(parse[Z] - last_height,3) # get height < desired height
                            print('height: ' + str(height))

                    # Increase count to get next line
                    j = j + 1
                                
                if finalcure == True:  
                    final_commands(parse_file)

                # Get last z height to get back to Z = 0 since Z adds up in gcode
                last_height = parse[Z]
                height = 0
                print('height reset')
                
                # Do not proceed to cure if just printed with FDM head
                if pin != '6' and method != 3:
                    curing_pattern(pin, method, parse_file, height, x_vec, y_vec, y_light_offset, x_light_offset, light_diameter, overlap, UV_time, finalcure, brightness)
                
        print('\nCommands for the UV curing pattern have been written in the G-code')
        
else: 
    print('No UV curing pattern for you because you chose no brightness!') 

file_a = file.split('.')
file = file_a[0] + '_parsed.gcode' # Now this new file is the one that will be edited instead of the old one

# Now call the toolchange function
toolchange(file, UV_time, light_diameter, overlap, x_light_offset, y_light_offset, brightness)

# Functions to make
# diameter
# parsing x & y
# parsing T and S

# Todo
# Make 
# make the UV function a function in itself so that there should be just three calls in this file
# make a curing_pattern function that refers to pattern_commands for writing commands
# change pins for UV lights and transducers
# separate curing pattern by tool (for non-sequential,cure after every tool change. For hybrid, no curing on T0)

