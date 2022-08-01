import cv2
import numpy as np
import math
import opencv_text_detection_image as text_detect
import building_data
import test_frcnn_modified

# returns length of line in pixels
def measure_line(points):
    x1, y1, x2, y2 = points
    val = ((x1-x2)**2 + (y1-y2)**2)**(1/2)
    return val

#return difference between lengths of line
def compare_lines(points1, points2):
    return measure_line(points1)-measure_line(points2)

#returns shortest distance from center of first line segment to the line formed by sceond segment
def compare_line_segments(line1, line2):
    x3, y3, x4, y4 = line1
    x0 = (x3 + x4) / 2
    y0 = (y3 + y4) / 2
    x1, y1, x2, y2 = line2
    distance = abs((x2-x1)*(y1-y0) - (x1-x0)*(y2-y1))/((x2-x1)**2 + (y2-y1)**2)**.5
    return distance

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
        angle2 = angle2 + 180.0
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
    
def point_segment_distance_helper(p, line):
    px, py = p
    x1, y1, x2, y2 = line
    return point_segment_distance(px, py, x1 ,y1, x2, y2)
    
def calculate_center(max_line, smaller_line):
    x11, y11, x12, y12 = max_line
    x21, y21, x22, y22 = smaller_line

    return ((x11+x12+x21+x22)/4, (y11+y12+y21+y22)/4)

def bind_lines(max_line, smaller_line):
    x11, y11, x12, y12 = max_line
    x21, y21, x22, y22 = smaller_line
    x11new, y11new, x12new, y12new = find_a_prime_b_prime((x21, y21), (x22, y22), ((x11+x12)/2, (y11+y12)/2))
    x21new, y21new, x22new, y22new = find_a_prime_b_prime((x11, y11), (x12, y12), ((x21+x22)/2, (y21+y22)/2))

    if measure_line((x11, y11, x11new, y11new)) > measure_line((x11, y11, x12new, y12new)):
        temp = x11new
        x11new = x12new
        x12new = temp
        temp = y11new
        y11new = y12new
        y12new = temp
        
    if measure_line((x21, y21, x21new, y21new)) > measure_line((x21, y21, x22new, y22new)):
        temp = x21new
        x21new = x22new
        x22new = temp
        temp = y21new
        y21new = y22new
        y22new = temp
    
    if measure_line((x11, y11, (x11+x12)/2, (y11+y12)/2)) < measure_line((x11new, y11new, (x11+x12)/2, (y11+y12)/2)):
        x11new = x11
        y11new = y11

    if measure_line((x12, y12, (x11+x12)/2, (y11+y12)/2)) < measure_line((x12new, y12new, (x11+x12)/2, (y11+y12)/2)):
        x12new = x12
        y12new = y12

    if measure_line((x21, y21, (x11+x12)/2, (y11+y12)/2)) < measure_line((x21new, y21new, (x11+x12)/2, (y11+y12)/2)):
        x21new = x21
        y21new = y21

    if measure_line((x22, y22, (x11+x12)/2, (y11+y12)/2)) < measure_line((x22new, y22new, (x11+x12)/2, (y11+y12)/2)):
        x22new = x22
        y22new = y22
        
    max_line_new = (x11new, y11new, x12new, y12new)
    smaller_line_new = (x21new, y21new, x22new, y22new)

    return max_line_new, smaller_line_new
#implementation of an algorithm defined here
#https://math.stackexchange.com/questions/1450858/get-a-line-segment-on-the-line-parallel-to-another-line-segment
def find_a_prime_b_prime(point1, point2, point3):
    xa, ya = point1
    xb, yb = point2
    xc, yc = point3
    #I need the arbitrary precision of standard python ints
    #NumPy gives me overflow errors
    xa = int(xa)
    ya = int(ya)
    xb = int(xb)
    yb = int(yb)
    xc = int(xc)
    yc = int(yc)
    A = int(yb - ya)
    B = int(xa - xb)
    C = int(xb * ya - xa * yb)
    Cprime = int((yc * (xb - xa)) + (xc * (ya - yb)))

    xprimea = int(((B**2)*xa - A*((B * ya) + Cprime)) / (A**2 + B**2))
    yprimea = int(((A**2)*ya - B*((A * xa) + Cprime)) / (A**2 + B**2))
    xprimeb = int(((B**2)*xb - A*((B * yb) + Cprime)) / (A**2 + B**2))
    yprimeb = int(((A**2)*yb - B*((A * xb) + Cprime)) / (A**2 + B**2))
    
    return xprimea, yprimea, xprimeb, yprimeb

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

    max_line = (0, 0, 0, 0)

    # Find line of maximum length
    for points in lines:
        if compare_lines(points, max_line) < 0:
            max_line = points[0]

    # Draw detected elements to image
    for points in lines:
          # Extracted points nested in the list
        x1,y1,x2,y2=points
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

def project_point(point, line):
    x3, y3 = point
    x1, y1, x2, y2 = line
    dx, dy = x2-x1, y2-y1
    det = dx*dx + dy*dy
    a = (dy*(y3-y1)+dx*(x3-x1))/det
    return (x1+a*dx, y1+a*dy)

def find_lines(edges, pixelToInches):
    lines = None
    lines = cv2.HoughLinesP(
                edges, # Input edge image
                .1, # Value of < 1 seems to work best
                np.pi/360, # Angle resolution in radians
                threshold=5, # Min number of votes for valid line
                minLineLength=60/pixelToInches, # Min allowed length of line
                maxLineGap=60/pixelToInches # Max gap allowed in line
                )
    if lines is None:
        return None
        
    return concatinate_lines(lines)
    
def concatinate_lines(lines):
    shape = lines.shape
    lines = lines.reshape(shape[0], 4)
    graph = []
    
    for line in lines:
        derp = [x for x in lines if compare_line_angle(find_line_angle(line), find_line_angle(x)) < 2 and compare_line_segments(line, x) < 1 and x is not line]
        ferp = np.argwhere(np.isin(lines, derp).all(axis=1))
        ferp = ferp.reshape(len(ferp))
        graph.append(lines[ferp])
        
    new_lines = []
    for node in graph:
        new_lines.append(concatinate_lines_helper(node))
    return new_lines
    
def concatinate_lines_helper(node):
    points = []
    for x in node:
        points.append((x[0], x[1]))
        points.append((x[2], x[3]))
    
    point1 = points[0]
    point2 = points[1]
    for herp in points:
        for derp in points:
            distance1 = measure_line((point1[0], point1[1], point2[0], point2[1]))
            distance2 = measure_line((herp[0], herp[1], derp[0], derp[1]))
            if distance1 < distance2:
                point1 = herp
                point2 = derp
    return (point1[0], point1[1], point2[0], point2[1])

def find_wall(full_image, bounding_box, pixelToInches):

    cv2.imwrite('full_image.png',full_image)

    #guarantees we know where the bottom left corner of the bounding box is,
    #incase the wrong 2 corners are passed
    boundingx1, boundingy1 = bounding_box[0]
    boundingx2, boundingy2 = bounding_box[1]
    minx = min(boundingx1, boundingx2)
    miny = min(boundingy1, boundingy2)
    maxx = max(boundingx1, boundingx2)
    maxy = max(boundingy1, boundingy2)
    
    center_of_image = ((minx+maxx)/2, (miny+maxy)/2)
    center_of_image_line = (int((minx+maxx)/2), int((miny+maxy)/2), int((minx+maxx+4)/2), int((miny+maxy)/2))
   

    #don't ask me why its backwards
    image = full_image[miny:maxy, minx:maxx]
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray,50,150,apertureSize=3)

    #find lines 
    lines = find_lines(edges, pixelToInches)

    try:
        if lines is None:
            return None
    except:
        None

    #TODO delete
    #draw lines on image. used for testing
    for points in lines:
        x1,y1,x2,y2=points
        cv2.line(image,(x1,y1),(x2,y2),(0,255,0),2)
    cv2.imwrite('detectedLines.png',image)

    #TODO put this in a loop that breaks when it finds a max line and a suitable paralell line
    #returns longest line found
    max_line = lines[10]
    for points in lines:
        if compare_lines(points, max_line) > 0:
            max_line = points

    if np.array_equiv(max_line, (0, 0, 0, 0)):
        return None

    #locates the longest line parallel to max_line
    smaller_line = center_of_image_line
    for points in lines:
        if np.array_equiv(points, max_line):
            continue
        if compare_line_angle(find_line_angle(points), find_line_angle(max_line)) > 2.0:
            continue
        if segments_distance(points, max_line) < 5 * pixelToInches: #magic number
            continue
        if compare_lines(points, smaller_line) < -20: #magic number
            continue
        if point_segment_distance_helper(center_of_image, points) > point_segment_distance_helper(center_of_image, smaller_line):
            smaller_line = points
        

    if np.array_equiv(smaller_line, (0, 0, 0, 0)):
        return None
    
    new_max_line, new_smaller_line = bind_lines(max_line, smaller_line)
    
    #TODO DELETE
    cv2.line(image,(new_max_line[0],new_max_line[1]),(new_max_line[2],new_max_line[3]),(255,0,255),2)
    cv2.line(image,(new_smaller_line[0],new_smaller_line[1]),(new_smaller_line[2],new_smaller_line[3]),(255,0,255),2)
    cv2.imwrite('detectedLines.png',image)
    
    center = calculate_center(new_max_line, new_smaller_line)
    center = (minx+center[0], len(full_image)-miny-center[1])
    
    windows = findWindows(image, lines, max_line, smaller_line, calculate_center(new_max_line, new_smaller_line), pixelToInches)
    #doors = findDoors()
    return center, float(measure_line(new_max_line)), find_line_angle(max_line), segments_distance(new_max_line, new_smaller_line), windows

def findWindows(image, lines, max_line, smaller_line, center, pixelToInches):
    potential_window_panes = []
    for points in lines:
        if np.array_equiv(points, max_line):
            continue
        if np.array_equiv(points, smaller_line):
            continue
        if compare_line_angle(find_line_angle(points), find_line_angle(max_line)) > 2.0:
            continue
        if measure_line(points) > measure_line(smaller_line):
            continue
        if compare_line_segments(points, max_line) < 5*pixelToInches:
            continue
        if compare_line_segments(points, smaller_line) < 5*pixelToInches:
            continue
        potential_window_panes.append(points)
        
        x1,y1,x2,y2=points
        cv2.line(image,(x1,y1),(x2,y2),(0,255,255),2)
        
    #TODO trim potential_window_panes
    windows = []
    center_line = ((max_line[0]+smaller_line[0])/2, (max_line[1]+smaller_line[1])/2, (max_line[2]+smaller_line[2])/2, (max_line[3]+smaller_line[3])/2)
        
    for lines in potential_window_panes:
        center_of_pane = ((lines[0] + lines[2])/2, (lines[1] + lines[3])/2)
        center_of_window = project_point(center_of_pane, center_line)
        
        window_distance = measure_line((center_of_window[0], center_of_window[1], center[0], center[1]))
        if center_of_window[0] < center[0]:
            window_distance = -window_distance
            
        windows.append((window_distance, measure_line(lines)))
        
        
    cv2.imwrite('detectedLines.png',image)
    windows = [*set(windows)]
    return windows

def machine_learning_feature_data_extractor(im, pixelToInches, buildingSchedule):
    elements = []
    #create story to return
    story = building_data.Story()
    all_dets = test_frcnn_modified.test(im)
    
    for det in all_dets:
        label, box = det
        x1, y1, x2, y2 = box
        
        #TODO REMOVE
        print(det)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.imwrite('bounding_boxes.png',image)
        
        #only consider walls
        if "wall" not in label:
            continue
        
        #find wall
        wall_buffer = feature_data_extractor(im, ((x1, y1), (x2, y2)), pixelToInches, buildingSchedule, "Wall")
        if wall_buffer == None:
            continue
            
        #attach to story
        story.append(wall_buffer[0])
        
        
    return story

def feature_data_extractor(im, bounding_box, pixelToInches, buildingSchedule, element_type):
    #require atleast 1 wall type
    if len(buildingSchedule.listOfWallTypes) < 0:
        return None
    if element_type == "Wall":
        
        results = find_wall(im, bounding_box, pixelToInches)
        if results:
            center, length, angle, thickness, windows = results
            wall = building_data.Wall((float(center[0]/pixelToInches), float(center[1]/pixelToInches)), float(length/pixelToInches), float(angle))
            
            #TODO REMOVE
            
            #'''
            #return windows if there is atleast 1 window type
            if len(buildingSchedule.listOfWindowTypes) > 0:
                for element in windows:
                    wtype = None
                    for entry in buildingSchedule.listOfWindowTypes:
                        if wtype == None:
                            wtype = entry
                        if abs(entry.width-(element[1]/pixelToInches)) < abs(wtype.width-(element[1]/pixelToInches)):
                            wtype = entry
                    window_buffer = building_data.Window(float(element[0]/pixelToInches), windowType=wtype)
                    wall.append(window_buffer)
            #'''
            return (wall, float(thickness/pixelToInches))
    return None

buildingSchedule = building_data.Schedule()
buildingSchedule.append(building_data.WallType(typeNumber=1, name="das conk creet baybee", thickness=8.0))
buildingSchedule.append(building_data.DoorType(typeNumber=2, name="the Pearly Gates", height=84.0, width=36.0))
buildingSchedule.append(building_data.WindowType(typeNumber=3, name="the Pearly window", height=24.0, width=24.0, sillHeight=12.0))

image = cv2.imread("wall-with-door.png")
points = ((0,0), (len(image[0]-1),len(image)-1))
wall = feature_data_extractor(image, points, 6.35, buildingSchedule, "Wall")
print(wall)
print("end of file")
#assert len(wall[0].listOfWindows) > 1
#print(wall.getPos())


#remove this after testing
'''
filepath_image = "save.png"
image = cv2.imread(filepath_image)
machine_learning_feature_data_extractor(image, 40, building_data.Schedule())
'''