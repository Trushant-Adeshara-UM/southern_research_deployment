#!/usr/bin/env python 

import os
import sys
import yaml
import argparse

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src'))
print(root_path)

sys.path.insert(0, root_path)

from system.printer import Printer
from vision.camera import Camera
from vision.line_width_estimator import LineWidthEstimator
from utilities.csv_writer import CSVWriter

# Create the parser
parser = argparse.ArgumentParser(description="Pressure value parser")

# Add required flag for pressure
parser.add_argument('--displacement', type=float, required=True, help='Direction and length of traversal')
parser.add_argument('--pressure', type=int, required=True, help='Pressure while printing')


###############
## Add Delta ##
###############
delta = 10

# Parse the arguments
args = parser.parse_args()

print(args)

# Print receipe
update_print_location = [ [ 0, 0, 0],
                              [ -1.5, 0, 0],
                              [ -2.5, 0, 0], 
                              [ -3.5, 0, 0],
                              [ -4.5, 0, 0],
                              [ -5.5, 0, 0],
                              [ -6.5, 0, 0],
                              [ -7.5, 0, 0], 
                              [ -8.5, 0, 0] ]

# Take input arguements from user
displacement = args.displacement
printer = Printer()
speed = printer.base_speed


# Activate pressure (regulator + solenoid)
printer.staging.set_pressure_regulator(1)
printer.set_pressure(args.pressure)
printer.staging.set_pressure_solenoid(1)

# Initialize csv writer class with fields
fieldnames = ['srno', 'ref_line_width', 'updated_line_width', 'width_error', 'stage_speed'] 

# Create an instance of the CSVWriter class
csv_writer = CSVWriter('output.csv', fieldnames)

# Open the file for writing
csv_writer.open()

cnt = 0

width_error = 0

for location in update_print_location:

    # Log data
    csv_writer.write_row({'srno': cnt, 'ref_line_width': printer.ref_width, 'updated_line_width': printer.estimated_line_width, 
                          'width_error': width_error, 'stage_speed': speed})

    # Print single line
    printer.linear_b(0.1, 5)
    printer.linear(1, displacement, speed)
    printer.linear_b(-0.1, 5)

    # Update camera offset and move to camera
    printer.camera_offset[1] = displacement + printer.base_camera_offset[1]
    printer.camera_offset[0] = update_print_location[cnt][0] + printer.base_camera_offset[0]
    printer.move_to_camera()

    # Get line width from vision system
    updated_line_width = printer.linear_estimator(1, -displacement, 50)
    
    # Update next print location
    printer.print_location = update_print_location[cnt+1]
    
    # Move to nozzle
    printer.move_to_nozzle()

    # Update speed with process model
    speed, width_error = printer.update_process_model(updated_line_width, speed )
    
    # Increment counter
    cnt += 1

    if abs(width_error) < delta:
        break

# Close the file
csv_writer.close()

# Turn of pressure
printer.set_pressure(0)
printer.staging.set_pressure_regulator(0)
printer.staging.set_pressure_solenoid(0)


    



