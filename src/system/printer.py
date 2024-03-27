import numpy as np
from sympy import symbols, diff
import os
import sys
import yaml

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
stage_config_path = os.path.join(root_path, '..\config\stages.yaml')
controller_config_path = os.path.join(root_path, '..\config\controller.yaml')
pressure_config_path = os.path.join(root_path, '..\config\pressure.yaml')
system_config_path = os.path.join(root_path, '..\config\printer.yaml')
output_path = os.path.join(root_path, '\data')

sys.path.insert(0, root_path)

from stages.stage_control import Staging, Aerotech
from control.controller import Controller

print(root_path)
#print(stage_config_path)
#print(controller_config_path)
#print(system_config_path)

with open(stage_config_path, 'r') as file:
    stage_cfg = yaml.safe_load(file)

with open(controller_config_path, 'r') as file:
    ctrl_cfg = yaml.safe_load(file)

with open(pressure_config_path, 'r') as file:
    pressure_cfg = yaml.safe_load(file)

with open(system_config_path, 'r') as file:
    system_cfg = yaml.safe_load(file)


class Printer:
    def __init__(self):
        # Axis specifier
        self.xaxis = system_cfg['axes']['x_axis']['id']
        self.yaxis = system_cfg['axes']['y_axis']['id']
        self.zaxis = system_cfg['axes']['z_axis']['id']

        # Initial speed in each axis
        self.xspeed = system_cfg['axes']['x_axis']['speed']
        self.xspeed_fast = system_cfg['axes']['x_axis']['speed_fast']
        self.yspeed = system_cfg['axes']['y_axis']['speed']
        self.zspeed = system_cfg['axes']['z_axis']['speed']
        self.zspeed_slow = system_cfg['axes']['z_axis']['speed_slow']

        self.current_x = 0
        self.current_y = 0

        self.pressure = 0

        self.recipe = system_cfg['recipe']

        # Update this later
        self.starting_locations = []

        self.controller = Controller(ctrl_cfg['params']['ref_line_width'])
        self.base_speed = self.controller.base_process(ctrl_cfg['params']['ref_line_width'])

        self.current_pressure = 0
        self.current_location = [0, 0, 0]

        self.base_camera_offset = system_cfg['camera_offset']
        self.camera_offset = self.base_camera_offset.copy()

        self.print_location = [0, 0, 0]
        self.moving_height = system_cfg['moving_height']

        self.ref_width = ctrl_cfg['params']['ref_line_width']
        self.estimated_line_width = 0

        # Initialize stages using Aerotech class
        self.staging = Aerotech(stage_cfg['substrate']['GLASS'], stage_cfg['mode']['incremental'])
        self.staging.send_message('~INITQUEUE\n') # Initialize the queue


    def update_process_speed(self, line_width, prev_speed):
        return self.controller.process_model(line_width, prev_speed)

    def save_controller_properties(self, data, filename):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        csv_path = os.path.join(output_path, filename)

        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data) 
        

    def set_pressure(self, pressure):
        voltage = pressure_cfg['params']['gain'] * pressure + pressure_cfg['params']['bias']

        if voltage < 0.1:
            voltage = 0
            self.vdisp("Voltage too low, setting to 0")
            self.staging.setPressure(voltage)
            self.current_pressure = 0
        elif voltage > 5:
            voltage = 5
            self.vdisp("Voltage too high, setting it to 5")
            self.staging.setPressure(voltage)
            self.current_pressure = (voltage - pressure_cfg['params']['bias']) / pressure_cfg['params']['gain']
        else:
            self.staging.set_pressure(voltage)
            self.curretn_pressure = pressure

    def linear_print(self, axis, distance, speed):
        self.set_pressure_regulator(1)
        self.set_pressure(self.pressure)
        self.set_pressure_solenoid(1)
        if (axis == 0):
            self.staging.goto(x=distance, f=speed)
        elif (axis == 1):
            self.staging.goto(y=distance, f=speed)
        elif (axis == 2):
            self.staging.goto(z=distance, f=speed)
        else:
            raise Exception("Trying to move via a nonexistent axis")
        self.set_pressure(0)
        self.set_pressure_regulator(0)
        self.set_pressure_solenoid(0)
        self.current_location = [self.staging.x, self.staging.y, self.staging.z]


    def linear_b(self, distance, speed):
        self.staging.goto_b(b=distance, f=speed)


    def linear(self, axis, distance, speed):
        if (axis == 0):
            self.staging.goto(x=distance, f=speed)
        elif (axis == 1):
            self.staging.goto(y=distance, f=speed)
        elif (axis == 2):
            self.staging.goto(z=distance, f=speed)
        else:
            raise Exception("Trying to move via a nonexistent axis")
        self.current_location = [self.staging.x, self.staging.y, self.staging.z]

    def grab_image(self):
        camera_controller = CameraController("measurement_camera")
        camera_controller.configure_for_software_trigger()

        image_grabber = ImageGrabber(camera_controller)
        image = image_grabber.grab_image()

        camera_controller.stop_grabbing()
        camera_controller.close()

        return image
 
    def estimate_line_width(self, image, cnt):
        estimator = LineWidthEstimator(image)
        binary, contour = estimator.contour_detection()
        angle = estimator.get_orientation(contour)
        rot_image = estimator.rotate_image(contour, -angle)
        points, _, line_image = estimator.line_extraction(rot_image)
        line_width = estimator.line_width(points, self.ref_width)

        t_str = time.strftime("%Y%m%d-%H%M%S")
        img_str = "itr" + str(cnt) + "-" + t_str + "original" + ".png"
        cv2.imwrite(img_str, image)

        t_str = time.strftime("%Y%m%d-%H%M%S")
        img_str = "itr" + str(cnt) + "-" + t_str + "binary" + ".png"
        cv2.imwrite(img_str, binary)

        t_str = time.strftime("%Y%m%d-%H%M%S")
        img_str = "itr" + str(cnt) + "-" + t_str + "contour" + ".png"
        cv2.imwrite(img_str, contour)

        t_str = time.strftime("%Y%m%d-%H%M%S")
        img_str = "itr" + str(cnt) + "-" + t_str + "rot" + ".png"
        cv2.imwrite(img_str, rot_image)

        t_str = time.strftime("%Y%m%d-%H%M%S")
        img_str = "itr" + str(cnt) + "-" + t_str + "line" + ".png"

        cv2.imwrite(img_str, line_image)


        return line_width

    def linear_estimator(self, axis, distance, speed):

        intervals = [(distance/2.5), (distance/15), (distance/15)]
        line_widths = []

        cnt = 1
        for it in range(0, 3):

            if (axis == 0):
                self.staging.goto(x=intervals[it], f=speed)
            elif (axis == 1):
                self.staging.goto(y=intervals[it], f=speed)
            elif (axis == 2):
                self.staging.goto(z=intervals[it], f=speed)
            else:
                raise Exception("Trying to move via a nonexistent axis")

            captured_img = self.grab_image()

            line_widths.append(self.estimate_line_width(captured_img, cnt))
            cnt+=1

        if len(line_widths) != 0:
            self.estimated_line_width = sum(line_widths) / len(line_widths)

        self.current_location = [self.staging.x, self.staging.y, self.staging.z]

        return self.estimated_line_width

    def move_to_location(self, location):
        current_z = self.current_location[2]
        self.linear(self.zaxis, self.moving_height - current_z, self.zspeed)

        current_x = self.current_location[0]
        self.linear(self.xaxis, location[0] - current_x, self.xspeed)

        current_y = self.current_location[1]
        self.linear(self.yaxis, location[1] - current_y, self.yspeed)

        current_z = self.current_location[2]

        self.linear(self.zaxis, location[2] - current_z, self.zspeed)
        #self.linear(self.zaxis, (location[2] - current_z) / 3, self.zspeed_slow)

    def move_to_camera(self):
        current_z = self.current_location[2]
        self.linear(self.zaxis, self.moving_height - current_z, self.zspeed)

        current_x = self.current_location[0]
        self.linear(self.xaxis,  self.camera_offset[0] - current_x , self.xspeed_fast)
        #self.linear(self.xaxis, (self.camera_offset[0] - current_x) / 10, self.xspeed)

        current_y = self.current_location[1]
        self.linear(self.yaxis, self.camera_offset[1] - current_y, self.yspeed)

        current_z = self.current_location[2]
        #self.linear(self.zaxis, 2 * (self.camera_offset[2] - current_z) / 3, self.zspeed)
        self.linear(self.zaxis, self.camera_offset[2] - current_z, self.zspeed)

    def move_to_nozzle(self):
        current_z = self.current_location[2]
        self.linear(self.zaxis, self.moving_height - current_z, self.zspeed)

        current_x = self.current_location[0]
        self.linear(self.xaxis, self.print_location[0] - current_x , self.xspeed_fast)
        #self.linear(self.xaxis, (self.print_location[0] - current_x) / 10, self.xspeed)

        current_y = self.current_location[1]
        self.linear(self.yaxis, self.print_location[1] - current_y, self.yspeed)

        current_z = self.current_location[2]
        self.linear(self.zaxis, 6 * (self.print_location[2] - current_z) / 7, self.zspeed)
        self.linear(self.zaxis, (self.print_location[2] - current_z ) / 7, self.zspeed_slow)

        for idx, (prt, curr) in enumerate(zip(self.print_location, self.current_location)):
            if abs(prt - curr) > 1:
                raise ValueError("Error between print location and current location greater than 1mm!")



