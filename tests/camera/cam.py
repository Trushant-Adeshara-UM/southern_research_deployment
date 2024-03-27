import pyspin
import cv2

def acquire_and_display_image():
    # Initialize the system
    system = pyspin.system.GetInstance()
    
    # Get the camera list
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()
    
    if num_cameras == 0:
        cam_list.Clear()
        system.ReleaseInstance()
        print("No cameras detected.")
        return False
    
    # Select the first camera in the list
    camera = cam_list.GetByIndex(0)
    camera.Init()
    
    # Set the pixel format to Mono8
    if camera.PixelFormat.GetAccessMode() == pyspin.RW:
        camera.PixelFormat.SetValue(pyspin.PixelFormat_Mono8)
    else:
        print("Cannot set Pixel Format to Mono8.")
        return False
    
    # Begin acquisition
    camera.BeginAcquisition()
    
    try:
        # Capture a single image
        image_result = camera.GetNextImage()
        
        if image_result.IsIncomplete():
            print(f"Image incomplete with image status {image_result.GetImageStatus()} ...")
        else:
            # Convert the captured image to a format compatible with OpenCV
            image_data = image_result.GetNDArray()
            
            # Display the image using OpenCV
            cv2.imshow('Captured Image', image_data)
            cv2.waitKey(0)  # Wait for a key press to close the image window
        
        # Release the image
        image_result.Release()
        
    except pyspin.SpinnakerException as ex:
        print(f"Error: {ex}")
    finally:
        # End acquisition
        camera.EndAcquisition()
        camera.DeInit()
        del camera
    
    # Clear camera list before releasing system
    cam_list.Clear()
    
    # Release system instance
    system.ReleaseInstance()

acquire_and_display_image()



