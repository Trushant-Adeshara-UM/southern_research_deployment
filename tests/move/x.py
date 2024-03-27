import os
import sys
import yaml

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\..\src'))
print(root_path)

sys.path.insert(0, root_path)

from system.printer import Printer



line_length = 10

speed = 5

printer = Printer()

printer.linear(0, line_length, speed)
    



