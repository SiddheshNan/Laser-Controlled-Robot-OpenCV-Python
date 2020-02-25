import time
import cv2
import numpy as np
import serial
import os

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

camera_ip = 'http://10.0.0.105:8080/video/mjpeg'

__all__ = []
arduino = serial.Serial('/dev/ttyUSB0', 9600)
time.sleep(1)  # waiting the initialization..
print("initialising")


class ColourTracker:
    def __init__(self):
        cv2.namedWindow("ColourTrackerWindow")
        self.capture = cv2.VideoCapture(camera_ip)
        self.capture.set(3, 640)  # set frame width
        self.capture.set(4, 480)  # set frame height
        #self.capture.set(cv2.CAP_PROP_FPS, 8)  # adjusting fps to 5
        self.scale_down = 4

    def run(self):

        def nothing(x):
            pass

        while True:
            f, orig_img = self.capture.read()
            lower = np.array([168, 51, 159], np.uint8)
            upper = np.array([255, 250, 255], np.uint8)
            img = cv2.cvtColor(orig_img, cv2.COLOR_BGR2HSV)
            img = cv2.resize(img, (int(len(orig_img[0]) / self.scale_down), int(len(orig_img) / self.scale_down)))
            red_binary = cv2.inRange(img, lower, upper)
            dilation = np.ones((15, 15), "uint8")
            red_binary = cv2.dilate(red_binary, dilation)

            contours, hierarchy = cv2.findContours(red_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            max_area = 0

            largest_contour = None
            for idx, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > max_area:
                    max_area = area
                    largest_contour = contour
            if not largest_contour is None:
                moment = cv2.moments(largest_contour)
                if moment["m00"] > 1000 / self.scale_down:

                    rect = cv2.minAreaRect(largest_contour)
                    rect = ((rect[0][0] * self.scale_down, rect[0][1] * self.scale_down),
                            (rect[1][0] * self.scale_down, rect[1][1] * self.scale_down), rect[2])
                    box = cv2.cv2.boxPoints(rect)
                    box = np.int0(box)

                    centroid_x = int(moment['m10'] / moment['m00'])
                    centroid_y = int(moment['m01'] / moment['m00'])
                    
                    if centroid_x > 100:
                        print('Right')
                        arduino.write('R'.encode())
                    elif centroid_x < 60:
                        print ('Left')
                        arduino.write('L'.encode())
                    else:
                        print ('Stop')
                        arduino.write('S'.encode())

                    if centroid_y < 45:
                        arduino.write('B'.encode())
                        print ('up')
                    elif centroid_y > 75:
                        arduino.write('F'.encode())
                        print ('Down')
                    else:
                        arduino.write('S'.encode())
                        print ('Stop')

                    arduino.write('S'.encode())

                    cv2.drawContours(orig_img, [box], 0, (0, 0, 255), 2)

            else:
                arduino.write('S'.encode())

            cv2.imshow("ColourTrackerWindow", orig_img)

            if cv2.waitKey(20) % 256 == 27:
                cv2.destroyWindow("ColourTrackerWindow")
                print ("Esc Pressed.. Exiting..")
                self.capture.release()
                break


if __name__ == "__main__":
    colour_tracker = ColourTracker()
    colour_tracker.run()
