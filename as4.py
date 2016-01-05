#!/usr/bin/env python
#-*- coding: utf-8 -*-
#Works for the IRT ARM 2

import os, socket, time, math
from PIL import Image, ImageDraw
import block_detection
import camera


PORT = 4000
RECV_BUFLEN = 512
RECV_TIMEOUT = 5.0 # seconds

#experimental determined parameter
x_pixel_to_arm = -0.61471	
y_pixel_to_arm = 0.667 

#reference frame
xbase_arm = -27.51
ybase_arm = 492.6
xbase_pixel = 326.678
ybase_pixel = 351.179

#Socket-Arm Connection
class socket_connection:
    def __enter__(self):
        listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listenSocket.bind(('localhost', PORT))
        listenSocket.listen(1)
        print('Listening on port:', PORT)
        self.clientSocket, self.address = listenSocket.accept()
        listenSocket.close()
        print('Accepted connection on port:', self.address)
        return self.clientSocket

    def __exit__(self, type, value, traceback):
        self.clientSocket.close()

def send_command(sock, command):
    print('Sending command:', command)
    command_bytes = bytes(command+'\0') #works for python 3.4
    sock.send(command_bytes)
    sock.settimeout(RECV_TIMEOUT)
    result = sock.recv(RECV_BUFLEN).decode('utf-8')
    print('Result:', result)
    return result
 
#Armmovement
def move_home(clientSocket):
	return send_command(clientSocket, 'GOHOME')
#Defaultposition
def move_def(clientSocket):
    return send_command(clientSocket, 'MOVP -27.5 493 0 90 0 180')
def move_position(clientSocket, x, y, z, rx, ry, rz):
    command = 'MOVP {x} {y} {z} {rx} {ry} {rz}'.format(x=x, y=y, z=z, rx=rx, ry=ry, rz=rz)
    return send_command(clientSocket, command)

#Gripper
def close_grip(clientSocket):
    return send_command(clientSocket, 'OUTPUT 48 ON')
def open_grip(clientSocket):
    return send_command(clientSocket, 'OUTPUT 48 OFF')

#Defining Speed of the Arm
def set_linespeed_f(clientSocket):
    return send_command(clientSocket, 'SETLINESPEED 17')
def set_linespeed_s(clientSocket):
    return send_command(clientSocket, 'SETLINESPEED 5')
def set_speedrate_f(clientSocket):
    return send_command(clientSocket, 'SETSPEEDRATE 250.00')
def set_speedrate_s(clientSocket):
    return send_command(clientSocket, 'SETSPEEDRATE 100.00')

def grip_position(centroid, principal_angle):
	#Orientation of the gripper
    rx = 90+principal_angle*180/math.pi  

    #Perspektive Transform 
    centroid_rel_x=(centroid[1]-xbase_pixel)*x_pixel_to_arm;
    centroid_rel_y=(centroid[0]-ybase_pixel)*y_pixel_to_arm;
    x=centroid_rel_x+xbase_arm;
    y=centroid_rel_y+ybase_arm;
    return x, y, rx

#Arm goes to the Block and grap it
def get_block(clientSocket, x, y, rx):
    move_position(clientSocket, x, y, -150, rx, 0, 180)
    move_position(clientSocket, x, y, -218, rx, 0, 180) 
    close_grip(clientSocket)
    move_position(clientSocket, x, y, -100, 90, 0, 180) 
    move_def(clientSocket) 								

#Arm put the block to the position (-295,508). (A position which is not taken by the camera, as the Camera has a small zooming function)
def put_block(clientSocket, x, y, rx,i):
    move_position(clientSocket, -295, 508, 30, 90, 0, 180)
    set_linespeed_s(socketIO)		
    set_speedrate_s(socketIO)
    move_position(clientSocket, -295, 508, -218+(40*i), 90, 0, 180) 
    time.sleep(5)
    open_grip(clientSocket)			
    time.sleep(5)
    move_position(clientSocket, -295, 508, 30, 90, 0, 180) 
    set_linespeed_f(socketIO)
    set_speedrate_f(socketIO)
    move_def(clientSocket) 								

if __name__ == '__main__':
    # 1. Take an image
    img=camera.capture2()

    # 2. Detect Block
    blocks = block_detection.get_blocks(img)
    #block_detection.draw(img, blocks)

    #Grabbing the blocks
    with socket_connection() as socketIO:
         set_linespeed_f(socketIO)
         set_speedrate_f(socketIO)
         open_grip(socketIO)
         move_def(socketIO)
         i=0
         for block in blocks:
            # 4. Get one block.
            x, y, rx = grip_position(block['centroid'], block['principal_angle'])
            get_block(socketIO, x, y, rx)
            # 5. Put it to the predefined position
            put_block(socketIO, x, y, rx,i)
            i=i+1
         move_home(socketIO)


