from time import sleep
import os
import sys
import yaml
import argparse

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\..\src'))
stage_config_path = os.path.join(root_path, '..\config\stages.yaml')
pressure_config_path = os.path.join(root_path, '..\config\pressure.yaml')
sys.path.insert(0, root_path)

with open(stage_config_path, 'r') as file:
    stage_config = yaml.safe_load(file)

with open(pressure_config_path, 'r') as file:
    pressure_config = yaml.safe_load(file)

from stages.stage_control import Staging, Aerotech

print()
print('*' * 100)
print(root_path)
print(stage_config_path)
print(pressure_config_path)
print('*' * 100)
print()

print(stage_config)
print()

# Create the parser
parser = argparse.ArgumentParser(description="Pressure value parser")

# Add required flag for pressure
parser.add_argument('--pressure', type=int, required=True, help='Pressure as integer value (PSI)')

# Parse the arguments
args = parser.parse_args()

aerotech_test = Aerotech(stage_config['substrate']['GLASS'], stage_config['mode']['incremental'])

aerotech_test.set_pressure_solenoid(args.pressure)



