import cv2
import numpy as np
import math
import opencv_text_detection_image as text_detect
import building_data

# returns length of line in pixels
def measure_line(points):
    x1, y1, x2, y2 = points
    return ((x1-x2)**2 + (y1-y2)**2)**(1/2)
    
# returns longer line
def compare_lines(points1, points2):
    if measure_line(points1) > measure_line(points2):
        return points1
    return points2

#finds angle of given line
#0 is horizontal, with values ranging (90, -90]
def find_line_angle(line):
    x1, y1, x2, y2 = line
    rise = y2 - y1
    run = x2 - x1
    return math.degrees(math.atan(rise/run))
    
#returns the similarity of 2 angles
#90 is a high degree of similarity, 
def compare_line_angle(angle1, angle2):
    if angle1 < 0.0:
        angle1 = angle1 + 180.0
    if angle2 < 0.0:
        angl2 = angle2 + 180.0
    return abs(angle1 - angle2)

# not in a condition to be called
def find_measurement_marker(file_name):
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

def find_wall(full_image, bounding_box, pixelToInches):

    #guarantees we know where the bottom left corner of the bounding box is,
    #incase the wrong 2 corners are passed
    boundingx1, boundingy1 = bounding_box[0]
    boundingx2, boundingy2 = bounding_box[1]
    minx = min(boundingx1, boundingx2)
    miny = min(boundingy1, boundingy2)
    maxx = max(boundingx1, boundingx2)
    maxy = max(boundingy1, boundingy2)
    
    #don't ask me why its backwards
    image = full_image[miny:maxy, minx:maxx]
                       
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray,50,150,apertureSize=3)
     
    lines = cv2.HoughLinesP(
                edges, # Input edge image
                .5, # Value of < 1 seems to work best
                np.pi/180, # Angle resolution in radians
                threshold=50, # Min number of votes for valid line
                minLineLength=10, # Min allowed length of line
                maxLineGap=100 #TODO: update to be the span of the largest window or door, 2m default
                )
                
    # draw lines on image
    for points in lines:
        x1,y1,x2,y2=points[0]
        cv2.line(image,(x1,y1),(x2,y2),(0,255,0),2)

    max_line = (0, 0, 0, 0)
    for points in lines:
        max_line = compare_lines(points[0], max_line)
        
    smaller_line = (0, 0, 0, 0)
    for points in lines:
        if points == max_line:
            continue
        if compare_line_angle(find_line_angle(points[0]), find_line_angle(max_line)) > 2.0:
            continue
        smaller_line = compare_lines(points[0], smaller_line)
    
    
    
    #cv2.imwrite('detectedLines.png',image)
    
    return (0.0, 0.0), 10.0, 0.0
    
    #min(boundingx1, boundingx2)
    #min(boundingy1, boundingy2)

def machine_learning_feature_data_extractor(im, pixelToInches):
    elements = []
    bounding_boxes = stephanie_function(im)
    for box in bounding_boxes:
        if box.label == "wall":
            elements.append(will_black_box(im, box.bounding, pixelToInches))
    return elements

def feature_data_extractor(im, bounding_box, pixelToInches, element_type):
    #could be updated to use a generic type defined in blueprint_gui
    wall_type = building_data.WallType(1, \
                                       name='-FEATURE NAME-', \
                                       thickness=1.0)
    if element_type == "Wall":
        center, length, angle = find_wall(im, bounding_box, pixelToInches)
        return building_data.Wall(center, length, angle, wall_type)
    return None
    
    
image = cv2.imread("wall-with-door.png")
points = ((0,0), (len(image[0]-1),len(image)-1))
print(feature_data_extractor(image, points, 1.0, "Wall"))

