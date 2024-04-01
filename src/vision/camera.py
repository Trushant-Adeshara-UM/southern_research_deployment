import os
import sys
import yaml
import PySpin
import cv2

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_path)

print(root_path)

class Camera:
    """
    Camera class to capture images.

    """

    def __init__(self):
        """

        """
        
        # Retrieve singleton reference to system object
        self.system = PySpin.System.GetInstance()

        # Get current library version
        self.version = self.system.GetLibraryVersion()
        print('Library version: %d.%d.%d.%d' % (self.version.major, self.version.minor, self.version.type, self.version.build))

        # Retrieve list of camera from the system
        self.cam_list = self.system.GetCameras()

        self.num_cameras = self.cam_list.GetSize()

        print('Number of cameras detected: %d' % self.num_cameras)

        # Finish if there are no cameras
        if self.num_cameras == 0:

            # Clear camera list before releasing system
            self.cam_list.Clear()

            # Release system instance
            self.system.ReleaseInstance()

    def grab_image(self):
        image = None

        # Acquire images
        sNodemap = self.cam.GetTLStreamNodeMap()

        # Change bufferhandling mode to NewestOnly
        node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
        if not PySpin.IsReadable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return False

        # Retrieve entry node from enumeration node
        node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
        if not PySpin.IsReadable(node_newestonly):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return False

        # Retrieve integer value from entry node
        node_newestonly_mode = node_newestonly.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node_bufferhandling_mode.SetIntValue(node_newestonly_mode) 

        print('**** IMAGE ACQUISITION ***\n')
        
        try:
            node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsReadable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                return False

            # Retrieve entry node from enumeration node
            node_acquisition_mode_single = node_acquisition_mode.GetEntryByName('SingleFrame')
            if not PySpin.IsReadable(node_acquisition_mode_single):
                print('Unable to set acquisition mode to single frame (entry retrieval). Aborting...')
                return False

            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_single.GetValue()

            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_single)

            print('Acquisition mode set to single frame...')

            #  Begin acquiring images
            #
            #  *** NOTES ***
            #  What happens when the camera begins acquiring images depends on the
            #  acquisition mode. Single frame captures only a single image, multi
            #  frame catures a set number of images, and continuous captures a
            #  continuous stream of images.
            #
            #  *** LATER ***
            #  Image acquisition must be ended when no more images are needed.
            self.cam.BeginAcquisition()

            print('Acquiring images...')

            #  Retrieve device serial number for filename
            #
            #  *** NOTES ***
            #  The device serial number is retrieved in order to keep cameras from
            #  overwriting one another. Grabbing image IDs could also accomplish
            #  this.
            device_serial_number = ''
            node_device_serial_number = PySpin.CStringPtr(self.nodemap_tldevice.GetNode('DeviceSerialNumber'))
            if PySpin.IsReadable(node_device_serial_number):
                device_serial_number = node_device_serial_number.GetValue()
                print('Device serial number retrieved as %s...' % device_serial_number)

            # Close program
            print('Press enter to close the program..')


            # Retrieve and display images
            try:

                #  Retrieve next received image
                #
                #  *** NOTES ***
                #  Capturing an image houses images on the camera buffer. Trying
                #  to capture an image that does not exist will hang the camera.
                #
                #  *** LATER ***
                #  Once an image from the buffer is saved and/or no longer
                #  needed, the image must be released in order to keep the
                #  buffer from filling up.

                image_result = self.cam.GetNextImage()

                #  Ensure image completion
                if image_result.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())

                else:

                    # Getting the image data as a numpy array
                    image_data = image_result.GetNDArray()
                    image = image_data.copy()

            except:

                # End acquisition
                self.cam.EndAcquisition()

                #Deinitialize camera
                self.cam.DeInit()
                print("Image Grab Failed")

                # Release system resources
                del self.cam
                self.cam_list.Clear()
                self.system.ReleaseInstance()
        
        except:
            print("Acquisition failed")

        return image



    def run_camera(self):

        # Run example on each camera
        for i, cam in enumerate(self.cam_list):
            print('Running example for camera %d...' % i)
	    
            self.nodemap_tldevice = cam.GetTLDeviceNodeMap()

            self.cam = cam

            # Initialize camera
            self.cam.Init()

            # Retrieve GenICam nodemap
            self.nodemap = cam.GetNodeMap()


###########
            

	
if __name__ == '__main__':
    test = Camera()
    test.run_camera()
    data = test.grab_image() 
        
    # Display the image
    cv2.imshow('Example - Show image in window', data)

    # Wait for a key press and then destroy all windows
    cv2.waitKey(0)
    cv2.destroyAllWindows()
	







