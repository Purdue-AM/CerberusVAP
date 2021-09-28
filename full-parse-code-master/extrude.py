
# Open new file
file = input('Enter a filename: ')
output_a = file.split('.')
output = output_a[0] + '_parsed.gcode' # change to .gcode later

# This function activates the transducer only when the G-code has an extruding command

# Indexes
i = 0
# Initialization Variables
extrude = 0

with open(file,'r') as file:
    # Extract all lines of the file
    lines = file.readlines()
    file.seek(0)
    
    with open(output,'w') as parse_file:
        
        while i < len(lines) - 1:
            lines_it = lines[i] # Get the line being read
            if lines_it.startswith('T0'):
                pin = '7' # pin associated with tool 0
            elif lines_it.startswith('T1'):
                pin = '9' # pin associated with tool 1
            print(lines_it)
            # Forces the M106 command to only appear once during a chain of extrusion commands
            while extrude == 0:
                if 'G1' in lines_it and 'E-' not in lines_it and 'E' in lines_it and 'G92' not in lines_it and 'G1 E' not in lines_it:
                    parse_file.write('M400\n')
                    parse_file.write('M42 P' + str(pin) + ' S255 ;turns UV on\n') # Turn on transducer when G-code is extruding
                    extrude = 1 # This indicates that the M106 command is in place
                else:
                    break
                
            # Another while loop forces the continuous toggling on/off of the trasnducer until the end of the file (the very first while loop)
            while extrude == 1:
                if 'G1' in lines_it and 'E' not in lines_it or 'G1 E-' in lines_it:
                    parse_file.write('M400\n')
                    parse_file.write('M42 P' + str(pin) + ' S0 ;turns UV off\n')
                    extrude = 0 # M107 command is in place
                else:
                    break
            
            parse_file.write(lines_it)
            i = i + 1
            
            
## Open new file
#file = input('Enter a filename: ')
#output_a = file.split('.')
#output = output_a[0] + '_parsed.gcode' # change to .gcode later
#
## This function activates the transducer only when the G-code has an extruding command
#
## Indexes
#i = 0
## Initialization Variables
#extrude = 0
#
#with open(file,'r') as file:
#    # Extract all lines of the file
#    lines = file.readlines()
#    file.seek(0)
#    
#    with open(output,'w') as parse_file:
#        
#        while i < len(lines) - 1:
#            lines_it = lines[i] # Get the line being read 
#            print(lines_it)
#            # Forces the M106 command to only appear once during a chain of extrusion commands
#            while extrude == 0:
#                if 'G1' in lines_it and 'E-' not in lines_it and 'E' in lines_it and 'G92' not in lines_it and 'G1 E' not in lines_it:
#                    parse_file.write('M106\n') # Turn on transducer when G-code is extruding
#                    extrude = 1 # This indicates that the M106 command is in place
#                else:
#                    break
#                
#            # Another while loop forces the continuous toggling on/off of the trasnducer until the end of the file (the very first while loop)
#            while extrude == 1:
#                if 'G1' in lines_it and 'E' not in lines_it or 'G1 E-' in lines_it:
#                    parse_file.write('M107\n')
#                    extrude = 0 # M107 command is in place
#                else:
#                    break
#            
#            parse_file.write(lines_it)
#            i = i + 1
#            
#            
#            
#def extrude(file):  
#    # This function activates the transducer only when the G-code has an extruding command
#    
#    # Indexes
#    i = 0
#    # Initialization Variables
#    extrude = 0
#    
#    # Create separate file where the output will be
#    output_a = file.split('.')
#    output = output_a[0] + '_parsed.gcode' # change to .gcode later
#    
#    # Extract all lines from file
#    with open(file,'r') as file:
#        lines = file.readlines()
#        file.seek(0)
#        
#        # Create new output file
#        with open(output,'w') as parse_file:
#            
#            while i < len(lines) - 1:
#                lines_it = lines[i] # Get the line being read 
#                print(lines_it)
#                # Forces the M106 command to only appear once during a chain of extrusion commands
#                while extrude == 0:
#                    if 'G1' in lines_it and 'E-' not in lines_it and 'E' in lines_it and 'G92' not in lines_it and 'G1 E' not in lines_it:
#                        parse_file.write('M106\n') # Turn on transducer when G-code is extruding
#                        extrude = 1 # This indicates that the M106 command is in place
#                    else:
#                        break
#                    
#                # Another while loop forces the continuous toggling on/off of the trasnducer until the end of the file (the very first while loop)
#                while extrude == 1:
#                    if 'G1' in lines_it and 'E' not in lines_it or 'G1 E-' in lines_it:
#                        parse_file.write('M107\n')
#                        extrude = 0 # M107 command is in place
#                    else:
#                        break
#                
#                parse_file.write(lines_it)
#                i = i + 1
#    return(parse_file);
#    
#file = 'CUBE.gcode'
#parse_file = extrude(file)