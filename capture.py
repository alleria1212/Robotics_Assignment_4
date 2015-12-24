import os, sys, math
from PIL import Image, ImageDraw
import block_detection
import os
import cv2

def capture2():
	camera = cv2.VideoCapture(-1)
	retval, im = camera.read()
	cv2.imwrite('images/capture.jpg', im)
	return im

if __name__ == '__main__':
	capture2()
