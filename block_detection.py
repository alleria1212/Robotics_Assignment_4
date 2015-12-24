import numpy as np
import sys
import os
import math
import copy
from PIL import Image, ImageDraw
from collections import Counter

### UTILS 

def save_img(img_binary, filename):
    img3 = Image.fromarray(np.uint8(img_binary))
    img3.save(filename)

def show_img(img_binary):
    img3 = Image.fromarray(np.uint8(img_binary))
    img3.show()

### DRAW FUNCTIONS

def draw_centroid(draw, img_c, size=2):
    draw.ellipse([int(img_c[1]) - size, int(img_c[0]) -size, int(img_c[1]) + size, int(img_c[0]) + size], fill='blue')
    
def draw_principal_angle(draw, img_c, p_a):
    draw.line([(y*math.tan(p_a) + img_c[1] - img_c[0]*math.tan(p_a), y) for y in range(0, 720)], fill='yellow', width=5)

def draw(img_original, objects, action='save'):
    img = img_original.copy()
    img_draw = ImageDraw.Draw(img)

    for object in objects:
        draw_principal_angle(img_draw, object['centroid'], object['principal_angle'])
        draw_centroid(img_draw, object['centroid'])

    if action == 'show':
        img.show()
    else:
        img.save(os.path.join('.', 'capture-draw.jpg'))

    return img

### CENTROID & PRINCIPAL ANGLE
class Object_image(object):
    """docstring for ClassName"""
    def __init__(self, matrix, region_id=255):
        self.matrix = copy.deepcopy(matrix)
        self.region_id = region_id

    def moment(self, k, j, x_c=0, y_c=0):
        moment = 0
        for x, row in enumerate(self.matrix):
            for y, p in enumerate(row):
                if p == self.region_id:
                    moment += math.pow(x - x_c, k) * math.pow(y - y_c, j)
        return moment

    def centroid(self):
        x_c = self.moment(1, 0) / self.moment(0, 0)
        y_c = self.moment(0, 1) / self.moment(0, 0)
        return x_c, y_c

    def central_moment(self, k, j):
        x_c, y_c = self.centroid()
        return self.moment(k, j, x_c, y_c)

    def principal_angle(self):
        return 0.5*math.atan2(2*self.central_moment(1, 1), self.central_moment(2, 0) - self.central_moment(0, 2))


### REGION DETECTION

def region_growing(matrix, k, j, i):
    stack = [(k, j), (0, 0)]
    matrix[k][j] = i
 
    while (k, j) != (0, 0):
        for neighboor in [(k, j + 1), (k - 1, j), (k, j - 1), (k + 1, j)]:
            k, j = neighboor
            if k > 0 and k < len(matrix) and j > 0 and j < len(matrix[0]):
                if matrix[k][j] == 1000000:
                    matrix[k][j] = i
                    stack.append((k, j))
        k, j = stack.pop()
    
def region_label(matrix):
    i = 0
    matrix = [[1000000 if (p == 255) else 0 for p in row] for row in matrix]
    for k, row in enumerate(matrix):
         for j, p in enumerate(row):
            if p == 1000000:
                i += 1
                region_growing(matrix, k, j, i)
    
    return matrix

def color_close(ps, cs):
    return sum([abs(z-c) for (z, c) in zip(ps, cs)])/3


def get_block_color(image, color):
    objects = []

    imgarray = np.asarray(image)
    imggrey = [[255 - color_close(p, color) for p in row] for row in imgarray]
    average = np.average(imggrey)
    imgbinary = [[255 if p > average + 10 else 0 for p in row] for row in imggrey]
    res = region_label(imgbinary)
    arr = list(np.asarray(res).ravel())
    counter = Counter(arr)
    counter.pop(0) # We remove the count of the background
    
    num_objects = 1
    if not num_objects: # We try to guess the number of object
        regions = list(filter(lambda region: region[1] > 500, counter.most_common()))
    else:
        regions = counter.most_common(num_objects)

    matrix = [[p if any([p == region[0] for region in regions]) else 0 for p in row] for row in res]
    for _id, (region_id, region_pixels) in enumerate(regions):
        regions[_id] = (255 - _id, region_pixels)
        matrix = [[255 - _id if p == region_id else p for p in row] for row in matrix]

    for (region_id, region_pixels) in regions:
        object = Object_image(matrix, region_id)
        centroid = object.centroid()
        p_a = object.principal_angle()
        objects.append({
            'matrix': [[255 if p == region_id else 0 for p in row] for row in matrix],
            'region_id': region_id, 
            'centroid': centroid, 
            'principal_angle': p_a
        })
        print(centroid[0], centroid[1], p_a)

    return objects


def get_blocks(image):
    colors = {
        'white': (255,255,255)
    }
    objects = []
    for color in colors:
        objects += get_block_color(image, colors[color])
    return objects


if __name__ == '__main__':
    draw = (sys.argv[-1] == '--draw')
    try:
        main(src=sys.argv[1], draw=draw)
    except Exception as e:
        print(e)
        print(USAGE)
