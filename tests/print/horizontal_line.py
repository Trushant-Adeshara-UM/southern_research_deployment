import os
import sys
import yaml

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\..\src'))
print(root_path)

sys.path.insert(0, root_path)

from system.printer import Printer


line_length = 10

speed = 0.3

printer = Printer()

print(printer.base_speed)

printer.linear_print(1, line_length, speed)
    



