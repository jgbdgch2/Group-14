import cv2
import numpy as np
import math
import opencv_text_detection_image as text_detect

def measure_line(points):
    x1, y1, x2, y2 = points
    return ((x1-x2)**2 + (y1-y2)**2)**(1/2)
    
def compare_lines(points1, points2):
    if measure_line(points1) > measure_line(points2):
        return points1
    return points2

#finds angle of given line
#important as comparing slopes will often lead to undefined values
#0 is horizontal, with values ranging [90, -90)
def find_line_angle(line):
    x1, y1, x2, y2= line[0]
    
    rise = y2 - y1
    run = x2 - x1
    
    return math.degrees(math.atan(rise/run))

def find_measurement_marker(file_name):
    lines_list = []
     
    # Read image
    image = cv2.imread(file_name)
     
    # Convert image to grayscale
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
     
    # Use canny edge detection
    edges = cv2.Canny(gray,50,150,apertureSize=3)
     
    # Apply HoughLinesP method to
    # to directly obtain line end points
    lines = cv2.HoughLinesP(
                edges, # Input edge image
                1, # Distance resolution in pixels
                np.pi/180, # Angle resolution in radians
                threshold=100, # Min number of votes for valid line
                minLineLength=5, # Min allowed length of line
                maxLineGap=50 # Max allowed gap between line for joining them
                )

    detected_text, rW, rH = text_detect.find_text(image)
    #print(detected_text, rW, rH)
    
    max_line = (0, 0, 0, 0)
    
    # Find line of maximum length
    for points in lines:
        max_line = compare_lines(points[0], max_line)
     
    # Draw detected elements to image
    for points in lines:
          # Extracted points nested in the list
        x1,y1,x2,y2=points[0]
        # Draw the lines joing the points
        # On the original image
        cv2.line(image,(x1,y1),(x2,y2),(0,255,0),2)
        # Maintain a simples lookup list for points
        lines_list.append([(x1,y1),(x2,y2)])

    for (startX, startY, endX, endY) in detected_text:
        # scale the bounding box coordinates based on the respective
        # ratios
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        # draw the bounding box on the image
        cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
         
    # Save the result image
    #cv2.imwrite('detectedLines.png',image)

    return max_line

def find_wall(file_name):
    lines_list = []
     
    # Read image
    image = cv2.imread(file_name)
    
    	
    
     
    # Convert image to grayscale
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
     
     
    (thresh, blackAndWhiteImage) = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
     
    # Use canny edge detection
    edges = cv2.Canny(gray,50,150,apertureSize=3)
     
    # Apply HoughLinesP method to
    # to directly obtain line end points
    lines = cv2.HoughLinesP(
                edges, # Input edge image
                1, # Distance resolution in pixels
                np.pi/180, # Angle resolution in radians
                threshold=100, # Min number of votes for valid line
                minLineLength=10, # Min allowed length of line
                maxLineGap=250 # Needs to get adjusted on the fly, based on the inch pixel ratio
                )
    #print(lines)
                
    for points in lines:
          # Extracted points nested in the list
        x1,y1,x2,y2=points[0]
        # Draw the lines joing the points
        # On the original image
        cv2.line(image,(x1,y1),(x2,y2),(0,255,0),2)
        # Maintain a simples lookup list for points
        lines_list.append([(x1,y1),(x2,y2)])
        
    for points in lines_list:
        print(points)
    
    cv2.imwrite('detectedLinesblack.png',blackAndWhiteImage)
    cv2.imwrite('detectedLinesgray.png',gray)
    cv2.imwrite('detectedLinesedges.png',edges)
    cv2.imwrite('detectedLines.png',image)

def machine_learning_feature_data_extractor(im, pixelToInches):
    elements = []
    bounding_boxes = stephanie_function(im)
    for box in bounding_boxes:
        if box.label == "wall":
            elements.append(will_black_box(im, box.bounding, pixelToInches))
    return elements

def feature_data_extractor(im, bounding_box, pixelToInches, element_type):
    if element_type == "Wall":
        data = find_wall(im, bounding_box, pixelToInches)
        return create_wall(data)
    
def create_wall(center, length, typ):
    return building_data.Wall()
    
    
find_wall("wall-with-door.png")

