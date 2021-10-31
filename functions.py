import cv2
import math
import numpy as np


def removeHair(image):
    img = image.copy()

    # We will work on a grayscale image
    imgray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # We need to create a kernel for mophologyEx. This is a 4x4 matrix filled with 1s
    # The bigger the kernel, the better we can remove the hair. We don't want to use a bigger
    # kernel though because we may modify the lesion too much
    kernel = np.ones((4,4),np.uint8)
    # We now apply a morphologyEx with the parameter MORPH_BLACKHAT
    morphEx = cv2.morphologyEx(imgray, cv2.MORPH_BLACKHAT, kernel)

    # Apply a threshold on the morph image
    _,threshold = cv2.threshold(morphEx,10,255,cv2.THRESH_BINARY)

    # Use the inpaint function
    img = cv2.inpaint(img,threshold,1,cv2.INPAINT_TELEA)

    return img

def calculateDistance(x1,y1,x2,y2):
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    return dist
        
def getImageWithContour(image):
    img = image.copy()
    # We need to convert it into gray img
    imgray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)

    # We create a threshold
    ret, thresh = cv2.threshold(imgray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    
    kernel = np.ones((3,3),np.uint8)
    opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 2)

    # smoothen 
    smooth = cv2.dilate(opening,kernel,iterations=3)

    contours, hierarchy = cv2.findContours(smooth, 
        cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # We need to calculate the middle of the contour and see which one is closest to the middle
    middle_Contour = None
    min_dist = 1000
    for c in contours:
        M = cv2.moments(c)
        # Get the middle of the contour
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])

        # Calculate the distance from the middle of the contour to the middle of the image
        dist = calculateDistance(cX,cY,512/2,512/2)

        if dist<min_dist:
            min_dist = dist
            middle_Contour = c



    # We draw the contour which was closest to the middle.    
    cv2.drawContours(img, middle_Contour, -1, (0, 255, 0), 3)
    
    return img