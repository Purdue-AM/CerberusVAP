# -*- coding: utf-8 -*-
"""
Created on Fri Feb 8 05:51:00 2019
@author: Aaron Afriat

Description: Functions for gcode parsing code
"""

"""
Functions:
"""

import math
import numpy as np

def get_layer_height(file):
    # Get layer height
    for line in file:
        if line.startswith(';   layerHeight,'):
            layer_height = float(line[line.rfind(',')+1:])
            print(layer_height)
    return layer_height;




def final_commands(parse_file):
    parse_file.write('\nM104 S0 ; turn off extruder')
    parse_file.write('\nM140 S0 ; turn off bed')
    parse_file.write('\nM84 ; disable motors')
    return; 
       
    
        
# This function forces curing after a tool change occurs (needed if a
# part finishes and a new material prints on top of it
def toolchange(file, UV_time, light_diameter, overlap, x_light_offset, y_light_offset, brightness):
    
    # Indexes
    j = 0
    
    # Global Variables
    #global pin
    
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
    output = output_a[0] + '_final.gcode' # change to .gcode later
    
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
                        pin = '4'
        
                    elif lines_it.startswith('T1') and toolcount > 1:
                        toolchange = True
                        pin = '6'
                    
                    j = j + 1
                
                print('writing code here\n')
                print(lines_it)
                
                # Write the tool change line when the curing commands are written (not before due to the tool offset programmed in Simplify3D)
                if lines_it.startswith('T') == True: 
                    parse_file.write(lines_it)
                    
                # Reset tool change
                toolchange = False
                
        print('\nCommands for the UV curing pattern when changing tools have been written in the G-code')
        
    return(parse_file);    
    
    
    
    
def curing_pattern(pin, method, parse_file, height, x_vec, y_vec, y_light_offset, x_light_offset, light_diameter, overlap, UV_time, finalcure, brightness):

    # Make Toolhead Wait before proceeding to curing to make sure 
    # nothing extrudes while it's moving to the curing location
    parse_file.write('G4 P2000\n')
    print('Running UV Algorithm \n')
    
#        # Raise nozzle before curing
#        parse_file.write('G1 Z' + str(height + 10))
    
    # Get max and min x & y distances to form the rectangular pattern
    x_max = np.amax(x_vec)
    x_min = np.amin(x_vec)
    y_max = np.amax(y_vec)
    y_min = np.amin(y_vec)
    
    m = int(np.ceil((x_max - x_min) / light_diameter))
    print(m)
    n = int(np.ceil((y_max - y_min) / light_diameter))
    m = round(m)
    print(m)
    n = round(n)
    print(n)
    # Start curing pattern
    for b in range(0, n):
        for a in range(0, m):
            # accounts for the UV offset from the print head.
            # on the system, lights are y symmetrical and have the
            # same x offset
            if pin == '4': 
                y = y_light_offset/1 + y_min/1 + b * (light_diameter - overlap)
                print(y)
            elif pin == '6': # if hybrid, do not cure with T1
                y = -y_light_offset + y_min + b * (light_diameter - overlap)
            x = x_light_offset/1 + x_min/1 + a * (light_diameter - overlap)
            print(x)
            
            # Input curing commands
            pattern_commands(parse_file, x, y, height, UV_time, finalcure, brightness, pin, method)
    
    return(parse_file);
   
    
    

def pattern_commands(parse_file, x, y, height, UV_time, finalcure, brightness, pin, method):
    # If print finished, cure twice as long
    if finalcure == True:  
        print('writing final commands at deltaH = ' + str(height))
        parse_file.write('G1 X' + str(x) + ' Y' + str(y) + 'E0')
        parse_file.write('\nM42 P' + str(pin) + ' S' + str(brightness) +' ;turns UV on')
        parse_file.write('\nG4 P' + str(2 * UV_time * 1000) + ' ;UV is on for ' + str(2 * UV_time) +' sec')
        parse_file.write('\nM42 P' + str(pin) + ' S0 ;turns UV off')
    
    # If normal layer, cure desired amount
    elif pin == '4' or pin == '6' and method != 3:
        print('writing commands at deltaH = ' + str(height))
        parse_file.write('G1 X' + str(x) + ' Y' + str(y) + 'E0')
        parse_file.write('\nM42 P' + str(pin) + ' S' + str(brightness) +' ;turns UV on')
        parse_file.write('\nG4 P' + str(UV_time * 1000) + ' ;UV is on for ' + str(UV_time) +' sec')   
        parse_file.write('\nM42 P' + str(pin) + ' S0 ;turns UV off\n')
    return(parse_file);
 
    
    
    
def parse_line(passline):
    # This function outputs the gcode command line in usable python format, 
    # passing command values as floats
    if(' F' in passline):
        # We don't care about feedrate, but we want to get rid of this first:
        passline = passline[:passline.rfind('F')].strip()

    if(' Z' in passline):
        # Take in Z:
        Z_ = float(passline[passline.rfind('Z')+1:])
        passline = passline[:passline.rfind('Z')].strip()
    else:
        Z_ = None

    if(' E' in passline):
        # Take the number for E1 and remove that from the 'line' string:
        E_ = float(passline[passline.rfind('E')+1:])
        passline = passline[:passline.rfind('E')].strip()
    else:
        E_ = None

    if(' Y' in passline):
        # Take the number for Y1 and remove that from the 'line' string:
        Y_ = float(passline[passline.rfind('Y')+1:])
        passline = passline[:passline.rfind('Y')].strip()
    else:
        Y_ = None

        # Whatever is left should be X to the end:
    if(' X' in passline):
        X_ = float(passline[passline.rfind('X')+1:])
    else:
        X_ = None


    return([X_, Y_, Z_, E_]);
    
    
    
    
def diameter_input(file):
    part_diameter_1 = float(input('What is the diameter or the part printed with the LEFT tool?: '))
    part_diameter_2 = float(input('What is the diameter or the part printed with the RIGHT tool?: '))
    return(part_diameter_1, part_diameter_2)
    
    
    
    
def pattern_diameter(file, light_diameter, X, Y):
    i = 0
    x = []
    y = []
    
    lines = file.readlines()
    file.seek(0)
    
    while i < len(lines) - 1:
        lines_it = lines[i]

        # Get x and y points for curing pattern
        if 'G1' in lines_it and 'X' in lines_it and 'Y' in lines_it and 'nozzle' not in lines_it:
            parse = parse_line(lines_it)
            if parse[X] != 0 and parse[Y] != 0:
                x.append(parse[X])
                y.append(parse[Y])
            i = i + 1
            
        else:
            i = i + 1    

    x_max = np.amax(x)
    x_min = np.amin(x)
    y_min = np.amin(y)
    y_max = np.amax(y)
    
    if abs(y_max-y_min) > abs(x_max-x_min):
        part_diameter = round(abs(y_max-y_min),2)
    else:
        part_diameter = round(abs(x_max-x_min),2)
    
    print('The part diameter is ' + str(part_diameter) + ' mm')
#    if x_max-x_min < light_diameter and y_max-y_min < light_diameter:
#        algorithm = False
#    else:
#        algorithm = True
#    print(algorithm) 
#    return algorithm;
    return part_diameter;
     



def setup():
    method = int(input('Which printing method are you using? Input "1" for single VAP, "2" for dual VAP or "3" for Hybrid: '))
    sequence = int(input('Print sequence: input "1" if you are printing multiple objects sequentially or "2" if you are printing continuously: '))
    brightness = int(input('Choose a UV brightness from 0 to 255 (choose 0 if you are not using the UV light): '))
    return(method, sequence, brightness);
    
    
    
    
def inputs():
    print('\nWarning: object must be placed on the bed (Z = 0) for the code to iterate.')
#    part_diameter = float(input('Part diameter in mm: '))
    desired_height = float(input('Height at which to cure in mm: '))
    UV_time = int(input('Curing time in seconds: '))
    light_diameter = int(input('UV light diameter in mm: '))
    overlap = int(input('Overlap during curing in mm: '))
    x_light_offset = int(input('Light offset distance in the x-direction (add a negative sign if needed), in mm: '))
    y_light_offset = int(input('Light offset distance in the y-direction (add a negative sign if needed), in mm: '))
    return(desired_height, UV_time, light_diameter, overlap, x_light_offset, y_light_offset);    
           
    
    

def extrude(file, method):  
    # This function activates the transducer only when the G-code has an extruding command
    
    # Indexes
    i = 0
    # Initialization Variables
    extrude = 0
    
    # Create newly parsed file
    output_a = file.split('.')
    output = output_a[0] + '_parsed.gcode' # change to .gcode later

    with open(file,'r') as file:
        # Extract all lines of the file
        lines = file.readlines()
        file.seek(0)
        
        with open(output,'w') as parse_file:
            
            while i < len(lines) - 1:
                lines_it = lines[i] # Get the line being read
                if lines_it.startswith('T0'):
                    pin = '9' # pin associated with tool 0
                elif lines_it.startswith('T1'):
                    pin = '7' # pin associated with tool 1
                print(lines_it)
                # Forces the M106 command to only appear once during a chain of extrusion commands
                while extrude == 0:
                    if 'G1' in lines_it and 'E-' not in lines_it and 'E' in lines_it and 'G92' not in lines_it and 'G1 E' not in lines_it:
                        i = i + 1;
                        lines_it = lines[i]
                        parse_file.write(lines_it)
                        parse_file.write('M400\n')
                        parse_file.write('M42 P' + str(pin) + ' S255 ;turns extruder on\n') # Turn on transducer when G-code is extruding
                        extrude = 1 # This indicates that the M106 command is in place
                    else:
                        break
                    
                # Another while loop forces the continuous toggling on/off of the trasnducer until the end of the file (the very first while loop)
                while extrude == 1:
                    if 'G1' in lines_it and 'E' not in lines_it or 'G1 E-' in lines_it:
                        if method != 3:
                            i = i + 1;
                            lines_it = lines[i]
                            parse_file.write(lines_it)
                            parse_file.write('M400\n')
                            parse_file.write('M42 P' + str(pin) + ' S0 ;turns extruder off\n')
                        extrude = 0 # M107 command is in place
                    else:
                        break
                
                parse_file.write(lines_it)
                i = i + 1
    return(parse_file);




## UNUSED FUNCTIONS
def static_commands(parse_file, finalcure, UV_time, height):
    # If print finished, cure twice as long
    if finalcure == True:
        parse_file.write('G4 P3000')
        parse_file.write('\nG28 ; home all axes')
        parse_file.write('\nM106 S250 ;turns UV on') 
        parse_file.write('\nG4 P' + str(2 * UV_time * 1000) + ' ;UV is on for ' + str(UV_time) +' sec')            
        parse_file.write('\nM106 S0 ;turns UV off\n')
    
    else:
        print('writing commands at deltaH = ' + str(height))
        parse_file.write('G4 P3000')
        parse_file.write('\nG28 ; home all axes')
        parse_file.write('\nM106 S250 ;turns UV on') 
        parse_file.write('\nG4 P' + str(UV_time * 1000) + ' ;UV is on for ' + str(UV_time) +' sec')            
        parse_file.write('\nM106 S0 ;turns UV off')  
        #parse_file.write('/nG4 P' + str(UV_time * 1000) + ' ;UV is off for ' + str(UV_time) +' sec')
    return;   
    
    
    
    
def cool_down(idle_height, idle_time, restart_height, delE, output_file):
    output_file.write("\n\nG91 ; relative positioning\n") # set relative positioning
    output_file.write("M107\n") # turn the fan off
    output_file.write("G0 Z%f ; idle height, relative\n" %(idle_height)) # move to idle height
    output_file.write("G4 P%f ; idle time, ms\n" %(idle_time))
    output_file.write("M400 ; wait for everything\n")
    output_file.write("G0 Z%f ;move to where you'd like to start printing again\n" %(restart_height - idle_height))
    output_file.write("M400\n") # wait to get to the intermediate point before turning on the fan
    output_file.write("M106 \n") # turn the fan (ultrasonic signal) back on
    output_file.write("G1 Z%f E%f\n" %(-restart_height, delE*restart_height))
    output_file.write("G90 ; global positioning again\n\n") # Go back to global coordinates
    delta_extruded = 0 # reset the extruded length.
    return delta_extruded;


def fan_toggle(output_file, line):
    # This function turns the fan (ultrasonic) off, outputs the rapid or non-
    # extruding motion, then turns the fan back on.
    output_file.write('M107 ; turn fan off\n')
    output_file.write(line)
    output_file.write('M106 ; turn fan on\n')
    return;



def fan_on(output_file): 
    # This function turns the fan on
    output_file.write('M400 ; wait\n')
    output_file.write('M106 ; turn fan on \n')
    return;



def fan_off(output_file): 
    # This function turns the fan off
    output_file.write('M400 ; wait\n')
    output_file.write('M107 ; turn fan off \n')
    return;


def line_divider(dist, split_dist, curr_data, prev_data, output_file, times):
    (num_intervals, remainder) = divmod(dist, split_dist)
    deltaX = curr_data[0] - prev_data[0]
    deltaY = curr_data[1] - prev_data[1]

    for i in range(0, int(num_intervals)):
        x_sub = prev_data[0] + ((i * deltaX) / num_intervals)
        y_sub = prev_data[1] + ((i * deltaY) / num_intervals)

        # dist_sub = pow(pow(x_sub, 2) + pow(y_sub, 2), 0.5)
        if(i is not (num_intervals)):
            # output the move:
            output_file.write("G1 X%f Y%f\n" %(x_sub, y_sub))
            cool_down(times[0], times[1], times[2], times[3], output_file)

        else: # last one, so let's move to the final position and
            output_file.write("G1 X%f Y%f \n" %(curr_data[0], curr_data[1]))

    return([curr_data[0], curr_data[1], remainder]);


def calc_dist(data, prev_data):
    num_data = [0]*len(data)
    prev_num_data = [0]*len(prev_data)
    # First, replace None characters with 0:
    for element in data:
        if(np.isnan(element)):
            num_data[data.index(element)] = 0

        else:
            num_data[data.index(element)] = data[data.index(element)]
    for element in prev_data:
        if(np.isnan(element)):
            prev_num_data[prev_data.index(element)] = 0
        else:
            prev_num_data[prev_data.index(element)] = prev_data[prev_data.index(element)]
    # Find Difference:
    X_ = num_data[0] - prev_num_data[0]
    Y_ = num_data[1] - prev_num_data[1]
    Z_ = num_data[2] - prev_num_data[2]
    # Calc the distance:
    dist = pow(pow(X_, 2) + pow(Y_, 2) + pow(Z_, 2), 0.5)
    return dist;



