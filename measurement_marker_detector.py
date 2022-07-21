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
    slope = 0
    
    if run == 0.0:
        return -90.0
    else:
        slope = rise/run
    
    return math.degrees(math.atan(slope))
    
#returns the similarity of 2 angles
#90 is a high degree of similarity, 
def compare_line_angle(angle1, angle2):
    if angle1 < 0.0:
        angle1 = angle1 + 180.0
    if angle2 < 0.0:
        angl2 = angle2 + 180.0
    return abs(angle1 - angle2)

#https://stackoverflow.com/questions/2824478/shortest-distance-between-two-line-segments
def segments_distance(line1, line2):
    """ distance between two segments in the plane:
      one segment is (x11, y11) to (x12, y12)
      the other is   (x21, y21) to (x22, y22)
    """
    x11, y11, x12, y12 = line1
    x21, y21, x22, y22 = line2
    if segments_intersect(x11, y11, x12, y12, x21, y21, x22, y22): return 0
    # try each of the 4 vertices w/the other segment
    distances = []
    distances.append(point_segment_distance(x11, y11, x21, y21, x22, y22))
    distances.append(point_segment_distance(x12, y12, x21, y21, x22, y22))
    distances.append(point_segment_distance(x21, y21, x11, y11, x12, y12))
    distances.append(point_segment_distance(x22, y22, x11, y11, x12, y12))
    return min(distances)

def segments_intersect(x11, y11, x12, y12, x21, y21, x22, y22):
    """ whether two segments in the plane intersect:
      one segment is (x11, y11) to (x12, y12)
      the other is   (x21, y21) to (x22, y22)
    """
    dx1 = x12 - x11
    dy1 = y12 - y11
    dx2 = x22 - x21
    dy2 = y22 - y21
    delta = dx2 * dy1 - dy2 * dx1
    if delta == 0: 
        return False  # parallel segments
    s = (dx1 * (y21 - y11) + dy1 * (x11 - x21)) / delta
    t = (dx2 * (y11 - y21) + dy2 * (x21 - x11)) / (-delta)
    return (0 <= s <= 1) and (0 <= t <= 1)

def point_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == dy == 0:  # the segment's just a point
        return math.hypot(px - x1, py - y1)

    # Calculate the t that minimizes the distance.
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)

    # See if this represents one of the segment's
    # end points or a point in the middle.
    if t < 0:
        dx = px - x1
        dy = py - y1
    elif t > 1:
        dx = px - x2
        dy = py - y2
    else:
        near_x = x1 + t * dx
        near_y = y1 + t * dy
        dx = px - near_x
        dy = py - near_y

    return math.hypot(dx, dy)

def calculate_center(max_line, smaller_line, minx, miny):
    x11, y11, x12, y12 = max_line
    x21, y21, x22, y22 = smaller_line
    
    #start with the center of the larger line
    center = (x11+x12/2, y11+y12/2)
    distance = segments_distance(max_line, smaller_line)
    offset = pol2cart(distance, math.radians(find_line_angle(max_line)+90.0))
    
    #create two points, offset from the center of max_line 
    #by the thickness of the wall perpendicular to its angle
    center_option_1 = (center[0] + offset[0], center[1] + offset[1])
    center_option_2 = (center[0] - offset[0], center[1] - offset[1])
    
    distance_1 = point_segment_distance(center_option_1[0], center_option_1[1], x21, y21, x22, y22)
    distance_2 = point_segment_distance(center_option_2[0], center_option_2[1], x21, y21, x22, y22)
    
    if distance_1 < distance_2:
        return (float(center_option_1[0] + minx), float(center_option_1[1] + miny))
    return (float(center_option_2[0] + minx), float(center_option_2[1] + miny))

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return(x, y)
    
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
    
    #find lines
    lines = cv2.HoughLinesP(
                edges, # Input edge image
                .1, # Value of < 1 seems to work best
                np.pi/180, # Angle resolution in radians
                threshold=50, # Min number of votes for valid line
                minLineLength=10, # Min allowed length of line
                maxLineGap=100 #TODO: update to be the span of the largest window or door, 2m default
                )

    #returns longest line found
    max_line = (0, 0, 0, 0)
    for points in lines:
        max_line = compare_lines(points[0], max_line)
        
    if np.array_equiv(max_line, (0, 0, 0, 0)):
        return None
        
    #locates the longest line parallel to max_line
    smaller_line = (0, 0, 0, 0)
    for points in lines:
        if np.array_equiv(points, max_line):
            continue
        if compare_line_angle(find_line_angle(points[0]), find_line_angle(max_line)) > 2.0:
            continue
        smaller_line = compare_lines(points[0], smaller_line)
    
    if np.array_equiv(smaller_line, (0, 0, 0, 0)):
        return None
    
    #draw lines on image. used for testing
    #for points in lines:
        #x1,y1,x2,y2=points[0]
        #cv2.line(image,(x1,y1),(x2,y2),(0,255,0),2)
    #for testing
    #print(smaller_line)
    #cv2.line(image,(smaller_line[0],smaller_line[1]),(smaller_line[2],smaller_line[3]),(255,0,255),2)
    #cv2.imwrite('detectedLines.png',image)
    
    #delete this
    #print("distacnce is", segments_distance(max_line, smaller_line))
    #print(find_line_angle((0,0,10,0)))
    #print(find_line_angle((0,10,0,0)))
    #print(find_line_angle((0,10,1,0)))
    print(max_line, smaller_line)
    
    return calculate_center(max_line, smaller_line, minx, miny), float(measure_line(max_line)), find_line_angle(max_line), segments_distance(max_line, smaller_line)

def machine_learning_feature_data_extractor(im, pixelToInches):
    elements = []
    bounding_boxes = stephanie_function(im)
    for box in bounding_boxes:
        if box.label == "wall":
            elements.append(feature_data_extractor(im, box.bounding, pixelToInches))
    return elements

def feature_data_extractor(im, bounding_box, pixelToInches, element_type):
    if element_type == "Wall":
        center, length, angle, thickness = find_wall(im, bounding_box, pixelToInches)
        return building_data.Wall((center[0]/pixelToInches, center[1]/pixelToInches), length/pixelToInches, angle, thickness/pixelToInches)
    return None
    
    
image = cv2.imread("wall-with-door.png")
points = ((0,0), (len(image[0]-1),len(image)-1))
wall = feature_data_extractor(image, points, 1.0, "Wall")

print(wall.getPos())

