import numpy as np
import ifc_compiler
#TODO add more comments
#TODO lookup hit should return "None" instead of -1

#Note: all members called measurement_system_flag must be "IMPERIAL_UNITS" or "METRIC_UNITS"

class BuildingData:
    #The 3 lists are lists of their respective classes
    #Building schedule is a Schedule object which is create in __init__
    listOfGridlines = []
    listOfElevations = []
    buildingSchedule = 0
    listOfStories = []

    isImperial = True

    def __init__(self):
        self.buildingSchedule = Schedule()
        self.listOfStories = []
        self.listOfGridlines = []
        self.listOfElevations = []
        self.isImperial = True

    #TODO delete, search functions

#    def appendGridline(self, cood0, cood1, measurement_system_flag="IMPERIAL_UNITS"):
#        buffer = Gridline(cood0, cood1, measurement_system_flag)
#        self.listOfGridlines.append(buffer)
    def appendGridline(self, cood0, cood1):
        buffer = Gridline(cood0, cood1)
        self.listOfGridlines.append(buffer)

    #TODO check if elevation already exists, if it does ignore it
#    def appendElevation(self, height, measurement_system_flag="IMPERIAL_UNITS"):
#        buffer = Elevation(height, measurement_system_flag)
#        self.listOfElevations.append(buffer)
    def appendElevation(self, height):
        buffer = Elevation(height)
        self.listOfElevations.append(buffer)

    def appendStory(self, bottomElevation, topElevation):
        buffer = Story(bottomElevation, topElevation)
        self.listOfStories.append(buffer)
        
    def findWallJoinsHelper(self):
        for x in self.listOfStories:
            x.findWallJoins()

class Gridline:
    #The thing that goes inside the bubble
    name=""

    cood0 = (np.inf, np.inf)
    cood1 = (np.inf, np.inf)

    #measurement_system_flag = "IMPERIAL_UNITS"

    #def __init__(self, cood0=(np.inf, np.inf), cood1=(np.inf, np.inf), measurement_system_flag="IMPERIAL_UNITS"):
    def __init__(self, cood0=(np.inf, np.inf), cood1=(np.inf, np.inf)):

        X0, Y0 = cood0
        X1, Y1 = cood1
        #type and bounds checking
        assert type(X0) == type(0.0) and type(Y0) == type(0.0), f"cood0 must be a tuple of floats, got {type(X0)} and {type(Y0)}."
        assert type(X1) == type(0.0) and type(Y1) == type(0.0), f"cood1 must be a tuple of floats, got {type(X1)} and {type(Y1)}."
        #assert measurement_system_flag == "IMPERIAL_UNITS" or \
        #    measurement_system_flag == "METRIC_UNITS", \
        #    f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
        #    got "{measurement_system_flag}" of type {type(measurement_system_flag)}. of type {type(measurement_system_flag)}'
        self.name = "placeholder"
        self.cood0 = cood0
        self.cood1 = cood1
        #self.measurement_system_flag = measurement_system_flag

class Elevation:

    name=""
    height = 0.0
    #measurement_system_flag = "IMPERIAL_UNITS"

    def __init__(self, \
                height=-0.0):
                #measurement_system_flag="IMPERIAL_UNITS"):
        #type checking
        assert type(height) == type(0.0), f"Height must be float, got type {type(height)}"
        #assert measurement_system_flag == "IMPERIAL_UNITS" or \
        #    measurement_system_flag == "METRIC_UNITS", \
        #    f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
        #    got "{measurement_system_flag}" of type {type(measurement_system_flag)}. of type {type(measurement_system_flag)}'

        self.height = height
        #self.measurement_system_flag = measurement_system_flag
        
    def setHeight(self, height):
        assert type(height) == type(0.0), f"Height must be float, got type {type(height)}"
        self.height = height
    def getHeight(self):
        return self.height

class Schedule:
    #3 seperate lists representing each schedule
    listOfWallTypes = []
    listOfDoorTypes = []
    listOfWindowTypes = []

    def __init__(self):
        self.listOfWallTypes = []
        self.listOfDoorTypes = []
        self.listOfWindowTypes = []

    #Takes in WallType, DoorType, or WindowType class and adds it to the schedule
    #Do not add types with a type number of -1
    def append(self, element):
        assert self.searchByType(element.typeNumber) == -1

        if type(element) == type(WallType()):
            assert element.typeNumber != -1, f"WallType must have positive integer typeNumber to append to schedule, got {element.wallType}"
            self.listOfWallTypes.append(element)
            return 0;

        if type(element) == type(DoorType()):
            assert element.typeNumber != -1, f"DoorType must have positive integer typeNumber to append to schedule, got {element.doorType}"
            self.listOfDoorTypes.append(element)
            return 0;

        if type(element) == type(WindowType()):
            assert element.typeNumber != -1, f"WindowType must have positive integer typeNumber to append to schedule, got {element.windowType}"
            self.listOfWindowTypes.append(element)
            return 0;

        raise Exception("Incompatiable object passed to append to schedule")

    #Takes in type identification number and returns corresponding type, returns -1 if not found
    def searchByType(self, typeNumber):

        assert type(typeNumber) == type(0)

        for element in self.listOfWallTypes:
            if element.typeNumber == typeNumber:
                return element

        for element in self.listOfDoorTypes:
            if element.typeNumber == typeNumber:
                return element

        for element in self.listOfWindowTypes:
            if element.typeNumber == typeNumber:
                return element
        return -1

    def searchByName(self, string):

        assert type(string) == type("")

        for element in self.listOfWallTypes:
            if element.name == string:
                return element

        for element in self.listOfDoorTypes:
            if element.name == string:
                return element

        for element in self.listOfWindowTypes:
            if element.name == string:
                return element
        return -1

    #Takes in type identification number and deletes
    def deleteByType(self, typeNumber):

        assert type(typeNumber) == type(0)

        for element in self.listOfWallTypes:
            if element.typeNumber == typeNumber:
                listOfWallTypes.remove(element)
                return 0;

        for element in self.listOfDoorTypes:
            if element.typeNumber == typeNumber:
                listOfDoorTypes.remove(element)
                return 0

        for element in self.listOfWindowTypes:
            if element.typeNumber == typeNumber:
                listOfWindowTypes.remove(element)
                return 0
        return -1

class WallType:

    #Integer representing wall type
    typeNumber = -1
    name = ""
    thickness = -1.0

    #Str array of info about wall type
    information = []
    #measurement_system_flag = "IMPERIAL_UNITS"

    #Takes in int, string, float, string
    def __init__(self, \
                typeNumber=-1, \
                name="Nameless", \
                thickness=-1.0):
                #measurement_system_flag="IMPERIAL_UNITS"):

        #Bound and type checking goes here
        assert type(typeNumber) == type(1), f"Wall type must be integer, got {type(typeNumber)}."
        assert typeNumber >= -1 and typeNumber != 0, f"typeNumber must be positive."

        assert type(name) == type(""), f"Name must be type string, got type {type(name)}."

        assert type(thickness) == type(1.0), f"thickness must be a float, got type {type(thickness)}."
        assert thickness > 0.0 or thickness == -1.0, f"Thickness must be positive."

        #assert measurement_system_flag == "IMPERIAL_UNITS" or \
        #    measurement_system_flag == "METRIC_UNITS", \
        #    f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
        #    got "{measurement_system_flag}" of type {type(measurement_system_flag)}.'

        self.typeNumber = typeNumber
        self.name = name
        self.thickness = thickness
        #self.measurement_system_flag = measurement_system_flag

class DoorType:

    #Integer representing door type
    typeNumber = -1
    name = ""
    height = 0.0;
    width = 0.0;

    #Str array of info about wall type
    information = []
    #measurement_system_flag = "IMPERIAL_UNITS"

    def __init__(self, \
                typeNumber=-1, \
                name="Nameless", \
                height=-1.0, \
                width=-1.0):
                #measurement_system_flag="IMPERIAL_UNITS"):

        #Bound and type checking goes here
        assert type(typeNumber) == type(1), f"typeNumber must be integer {type(typeNumber)}."
        assert typeNumber >= -1 and typeNumber != 0, f"typeNumber must be positive."

        assert type(name) == type(""), f"Name must be type string, got type {type(name)}."

        assert type(height) == type(1.0), f"height must be a float, got type {type(height)}."
        assert height > 0.0 or height == -1.0, f"height must be positive."

        assert type(width) == type(1.0), f"width must be a float, got type {type(width)}."
        assert width > 0.0 or width == -1.0, f"width must be positive."

        #assert measurement_system_flag == "IMPERIAL_UNITS" or \
        #    measurement_system_flag == "METRIC_UNITS", \
        #    f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
        #    got "{measurement_system_flag}" of type {type(measurement_system_flag)}. of type {type(measurement_system_flag)}'

        self.typeNumber = typeNumber
        self.name = name
        self.height = height
        self.width = width
        #self.measurement_system_flag = measurement_system_flag

class WindowType:

    #Integer representing door type
    typeNumber = -1
    name = ""
    height = 0.0;
    width = 0.0;
    sillHeight = 0.0

    #Str array of info about wall type
    information = []
    #measurement_system_flag = "IMPERIAL_UNITS"

    def __init__(self, \
                typeNumber=-1, \
                name="Nameless", \
                height=-1.0, \
                width=-1.0, \
                sillHeight=-1.0):
                #measurement_system_flag="IMPERIAL_UNITS"):

        #Bound and type checking goes here
        assert type(typeNumber) == type(1), f"typeNumber must be integer {type(typeNumber)}."
        assert typeNumber >= -1 and typeNumber != 0, f"typeNumber must be positive."

        assert type(name) == type(""), f"Name must be type string, got type {type(name)}."

        assert type(height) == type(1.0), f"height must be a float, got type {type(height)}."
        assert height > 0.0 or height == -1.0, f"height must be positive."

        assert type(width) == type(1.0), f"width must be a float, got type {type(width)}."
        assert width > 0.0 or width == -1.0, f"width must be positive."

        assert type(sillHeight) == type(1.0), f"sillHeight must be a float, got type {type(sillHeight)}."
        assert sillHeight > 0.0 or sillHeight == -1.0, f"sillHeight must be positive."

        #assert measurement_system_flag == "IMPERIAL_UNITS" or \
        #    measurement_system_flag == "METRIC_UNITS", \
        #    f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
        #    got "{measurement_system_flag}" of type {type(measurement_system_flag)}. of type {type(measurement_system_flag)}'

        self.typeNumber = typeNumber
        self.name = name
        self.height = height
        self.width = width
        self.sillHeight = sillHeight
        #self.measurement_system_flag = measurement_system_flag

class Story:

    bottomElevation = -1
    topElevation = -1
    listOfWalls = -1
    listOfWallJoins = []

    #TODO type checking
    #todo update this
    def __init__(self, bottomElevation=-1, topElevation=-1):
        self.bottomElevation = bottomElevation
        self.topElevation = topElevation
        self.listOfWalls = []
        self.listOfWallJoins = []
        assert type(bottomElevation) == type(Elevation()), f"bottomElevation must be elevation, got type {type(bottomElevation)}."
        assert type(topElevation) == type(Elevation()), f"topElevation must be elevation, got type {type(topElevation)}."

    #TODO append delete search return functions for all 3 lists

    #Takes in Wall, Door or Window object and adds it to the story
    def append(self, element):
        if type(element) == type(Wall()):
            self.listOfWalls.append(element)
            return 0;

        raise Exception("Incompatiable object passed to append to schedule")

    #Meaningless functions until I implement elevations
    def getBottomElevation(self):
        return self.bottomElevation

    def getTopElevation(self):
        return self.topElevation

    def setBottomElevation(self, bottomElevation):
        self.bottomElevation = bottomElevation
    
    def setTopElevation(self, topElevation):
        self.topElevation = topElevation

    def updateTopElevation(self, height):
        self.topElevation.setHeight(height)
        
    def updateBottomElevation(self, height):
        self.bottomElevation.setHeight(height)
        
    def findWallJoins(self):
        for i in range(len(self.listOfWalls)):
            for j in range(i + 1, len(self.listOfWalls)):
                if self.findWallJoinsAssit(self.listOfWalls[i], self.listOfWalls[j]):
                    self.listOfWallJoins.append((self.listOfWalls[i], self.listOfWalls[j]))
    
    #Uses triangle method to find if any corner of either will is inside the other wall
    #Potentially unstable due to floating point math
    def findWallJoinsAssit(self, wallOne, wallTwo):
        
        #Finds the corners of the wall by going out the length of the wall from the center and adding or subtracting the thickness
        wallOnePointscB = (round(wallOne.xPos + wallOne.length/2 * np.cos(wallOne.angle*np.pi/180) + wallOne.getThickness() * np.sin(wallOne.angle*np.pi/180), 4)\
                       , round(wallOne.yPos + wallOne.length/2 * np.sin(wallOne.angle*np.pi/180) + wallOne.getThickness() * np.cos(wallOne.angle*np.pi/180), 4))       
        wallOnePointscC = (round(wallOne.xPos + wallOne.length/2 * np.cos(wallOne.angle*np.pi/180) - wallOne.getThickness() * np.sin(wallOne.angle*np.pi/180), 4)\
                       , round(wallOne.yPos + wallOne.length/2 * np.sin(wallOne.angle*np.pi/180) - wallOne.getThickness() * np.cos(wallOne.angle*np.pi/180), 4))        
        wallOnePointscA = (round(wallOne.xPos - wallOne.length/2 * np.cos(wallOne.angle*np.pi/180) + wallOne.getThickness() * np.sin(wallOne.angle*np.pi/180), 4)\
                       , round(wallOne.yPos - wallOne.length/2 * np.sin(wallOne.angle*np.pi/180) + wallOne.getThickness() * np.cos(wallOne.angle*np.pi/180), 4))
        wallOnePointscD = (round(wallOne.xPos - wallOne.length/2 * np.cos(wallOne.angle*np.pi/180) - wallOne.getThickness() * np.sin(wallOne.angle*np.pi/180), 4)\
                       , wallOne.yPos - wallOne.length/2 * np.sin(wallOne.angle*np.pi/180) - wallOne.getThickness() * np.cos(wallOne.angle*np.pi/180))
        wallOnePoints = (wallOnePointscA, wallOnePointscB, wallOnePointscC, wallOnePointscD)
                        
                        
        wallTwoPointscB = (round(wallTwo.xPos + wallTwo.length/2 * np.cos(wallTwo.angle*np.pi/180) + wallTwo.getThickness() * np.sin(wallTwo.angle*np.pi/180), 4)\
                       , round(wallTwo.yPos + wallTwo.length/2 * np.sin(wallTwo.angle*np.pi/180) + wallTwo.getThickness() * np.cos(wallTwo.angle*np.pi/180), 4))
        wallTwoPointscC = (round(wallTwo.xPos + wallTwo.length/2 * np.cos(wallTwo.angle*np.pi/180) - wallTwo.getThickness() * np.sin(wallTwo.angle*np.pi/180), 4)\
                       , round(wallTwo.yPos + wallTwo.length/2 * np.sin(wallTwo.angle*np.pi/180) - wallTwo.getThickness() * np.cos(wallTwo.angle*np.pi/180), 4))    
        wallTwoPointscA = (round(wallTwo.xPos - wallTwo.length/2 * np.cos(wallTwo.angle*np.pi/180) + wallTwo.getThickness() * np.sin(wallTwo.angle*np.pi/180), 4)\
                       , round(wallTwo.yPos - wallTwo.length/2 * np.sin(wallTwo.angle*np.pi/180) + wallTwo.getThickness() * np.cos(wallTwo.angle*np.pi/180), 4))   
        wallTwoPointscD = (round(wallTwo.xPos - wallTwo.length/2 * np.cos(wallTwo.angle*np.pi/180) - wallTwo.getThickness() * np.sin(wallTwo.angle*np.pi/180), 4)\
                       , round(wallTwo.yPos - wallTwo.length/2 * np.sin(wallTwo.angle*np.pi/180) - wallTwo.getThickness() * np.cos(wallTwo.angle*np.pi/180), 4))
        wallTwoPoints = (wallTwoPointscA, wallTwoPointscB, wallTwoPointscC, wallTwoPointscD)
        
        #Check each point against the opposing rectangle
        
        for p in wallTwoPoints:
            ret = self.isInsideSquare(wallOnePoints, p)
            if ret == True:
                return ret
        for p in wallOnePoints:
            ret = self.isInsideSquare(wallTwoPoints, p)
            if ret == True:
                return ret
        return False
        
    def triangleArea(self, A, B, C):
        ret = (C[0]*B[1] - B[0]*C[1]) - (C[0]*A[1] - A[0]*C[1]) + (B[0]*A[1] - A[0]*B[1]) > 0
        return(ret)
    
    def isInsideSquare(self, square, p):
        a, b, c, d = square
        if self.triangleArea(a,b,p) or \
           self.triangleArea(b,c,p) or \
           self.triangleArea(c,d,p) or \
           self.triangleArea(d,a,p):
            return False
        return True
class Wall:

    def append(self, element):
        if type(element) == type(Door()):
            self.listOfDoors.append(element)
            return 0;
        if type(element) == type(Window()):
            self.listOfWindows.append(element)
            return 0;
        raise Exception("Incompatiable object passed to append to wall")


    #Position of the center of the wall
    xPos = np.inf
    yPos = np.inf

    #Overall length of the wall
    length = np.inf

    #refers to the angle normal vector, such that,
    #0.0 represents horizontal wall
    #90.0 represents vertical wall
    #Angles rotate counterclockwise as per the unit circle
    angle = np.inf

    #Reference to WallType object
    wallType = -1

    #Optional field, if left empty will default to the distance between elevation markers
    #TODO add support for this lmao
    height = np.inf

    #Str array of info about wall
    #Includes tags
    information = []

    def __init__(self, \
                pos=(np.inf, np.inf), \
                length=np.inf, \
                angle=np.inf, \
                wallType=WallType()):

        X, Y = pos

        assert type(X) == type(0.0) and type(Y) == type(0.0), f"pos must be a tuple of floats, got {type(X)} and {type(Y)}."
        assert type(length) == type(0.0), f"length must be a type float, got type {type(length)}."
        assert type(angle) == type(0.0), f"angle must be type float, got type {type(angle)}."
        assert type(wallType) == type(WallType()), f"wallType must be WallType object, got type {type(wallType)}."

        self.xPos, self.yPos = pos
        self.length = length
        self.angle = angle
        self.wallType = wallType

        self.listOfDoors = []
        self.listOfWindows = []

    #Returns tuple of coordiantes of the door
    def getPos(self):
        return (self.xPos, self.yPos)

    def setPos(self, cood):
        self.xPos, self.yPos = cood

    def getThickness(self):
        return self.wallType.thickness

class Door:

    #Position from centerpoint of the wall, can be positive or negative
    position = np.inf

    #hinges rotate counterclockwise
    #Where is the hinge on the door
    hingePos = -1

    #Reference to DoorType object
    doorType = -1

    #Str array of info about wall
    #Includes tags
    information = []

    def __init__(self, \
                position=np.inf, \
                hingePos=-1, \
                doorType=DoorType()):

        assert type(position) == type(0.0), f"position must be type float, got type {type(position)}."
        assert type(hingePos) == type(0), f"hingePost must be a type int, got type {type(hingePos)}."
        assert type(doorType) == type(DoorType()), f"doorType must be DoorType object, got type {type(doorType)}."

        self.position = position
        self.hingePos = hingePos
        self.doorType = doorType

class Window:

    #Position from centerpoint of the wall, can be positive or negative
    position = np.inf
    sillHeight = np.inf

    #Which direction is the window facing
    #May end up not being needed
    directionFacing = -1

    #Reference to WindowType object
    windowType = -1

    #Str array of info about wall
    #Includes tags
    information = []

    def __init__(self, \
                position=np.inf, \
                sillHeight=np.inf, \
                directionFacing=-1, \
                windowType=WindowType()):

        assert type(position) == type(0.0), f"position must be type float, got type {type(position)}."
        assert type(sillHeight) == type(0.0), f"sillHeight must be type float, got type {type(sillHeight)}."
        assert type(directionFacing) == type(0), f"directionFacing must be a type int, got type {type(directionFacing)}."
        assert type(windowType) == type(WindowType()), f"windowType must be WindowType object, got type {type(windowType)}."

        self.position = position
        self.sillHeight = sillHeight
        self.directionFacing = directionFacing
        self.windowType = windowType

buildingData = BuildingData()
#horizontal
buildingData.appendGridline((0.0,0.0), (2000.0,0.0))
buildingData.appendGridline((0.0,1000.0), (2000.0,1000.0))
#vertical
buildingData.appendGridline((0.0,0.0), (0.0,1000.0))
buildingData.appendGridline((2000.0,0.0), (2000.0,1000.0))
assert len(buildingData.listOfGridlines) == 4
assert buildingData.listOfGridlines[0].cood0 == (0.0,0.0)
assert buildingData.listOfGridlines[1].cood0 == (0.0,1000.0)
assert buildingData.listOfGridlines[1].cood1 == (2000.0,1000.0)

#negative example
try:
    buildingData.appendGridline((0,0), (2000,0))
    print("You aren't supposed to see this.")
except:
    3


buildingData.appendElevation(0.0)

buildingData.appendElevation(96.0)

assert len(buildingData.listOfElevations) == 2
assert buildingData.listOfElevations[0].height == 0.0
assert buildingData.listOfElevations[1].height == 96.0

buildingData.buildingSchedule.append(WallType(typeNumber=1, \
                                            name="das conk creet baybee", \
                                            thickness=8.0))

buildingData.buildingSchedule.append(DoorType(typeNumber=2, \
                                            name="the Pearly Gates", \
                                            height=84.0, \
                                            width=36.0))

buildingData.buildingSchedule.append(WindowType(typeNumber=3, \
                                            name="the Pearly window", \
                                            height=24.0, \
                                            width=24.0, \
                                            sillHeight=12.0))

buildingData.appendStory(bottomElevation = buildingData.listOfElevations[0], \
                        topElevation = buildingData.listOfElevations[1])
                        
buildingData.listOfStories[0].updateTopElevation(120.0)

assert buildingData.listOfStories[0].getTopElevation().getHeight() == 120.0

#South wall
buildingData.listOfStories[0].append(Wall(pos=(120.0, 4.0), length=240.0, angle=0.0,\
                                        wallType=buildingData.buildingSchedule.searchByType(1)))

#East wall
buildingData.listOfStories[0].append(Wall(pos=(4.0, 120.0), length=240.0, angle=90.0,\
                                        wallType=buildingData.buildingSchedule.searchByType(1)))

#North wall
buildingData.listOfStories[0].append(Wall(pos=(236.0, 120.0), length=240.0, angle=90.0,\
                                        wallType=buildingData.buildingSchedule.searchByType(1)))

#West wall
buildingData.listOfStories[0].append(Wall(pos=(120.0, 236.0), length=240.0, angle=0.0, \
                                        wallType=buildingData.buildingSchedule.searchByType(1)))

buildingData.listOfStories[0].listOfWalls[0].append(Door(position = 20.0, hingePos = 1, doorType = buildingData.buildingSchedule.searchByType(2)))

buildingData.listOfStories[0].listOfWalls[0].append(Window(position = -40.0, directionFacing = 0, windowType = buildingData.buildingSchedule.searchByType(3)))

buildingData.findWallJoinsHelper()
for join in buildingData.listOfStories[0].listOfWallJoins:
    print(join[0].getPos(), join[1].getPos())

ifc_compiler.compile(buildingData)

print("done!")
