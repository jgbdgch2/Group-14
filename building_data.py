import numpy as np
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
    
    def __init__(self):
        self.buildingSchedule = Schedule()
        self.listOfStories = []
        self.listOfGridlines = []
        self.listOfElevations = []
        
    #TODO delete, search functions
        
    def appendGridline(self, cood0, cood1, measurement_system_flag="IMPERIAL_UNITS"):
        buffer = Gridline(cood0, cood1, measurement_system_flag)
        self.listOfGridlines.append(buffer)
        
    #TODO check if elevation already exists, if it does ignore it
    def appendElevation(self, height, measurement_system_flag="IMPERIAL_UNITS"):
        buffer = Elevation(height, measurement_system_flag)
        self.listOfElevations.append(buffer)
        
    def appendStory(self, bottomElevation, topElevation):
        buffer = Story(bottomElevation, topElevation)
        self.listOfStories.append(buffer)
        
class Gridline:
    #The thing that goes inside the bubble
    name=""
    
    cood0 = (np.inf, np.inf)
    cood1 = (np.inf, np.inf)
    
    measurement_system_flag = "IMPERIAL_UNITS"
    
    def __init__(self, cood0=(np.inf, np.inf), cood1=(np.inf, np.inf), measurement_system_flag="IMPERIAL_UNITS"):
        
        X0, Y0 = cood0
        X1, Y1 = cood1
        #type and bounds checking
        assert type(X0) == type(0.0) and type(Y0) == type(0.0), f"cood0 must be a tuple of floats, got {type(X0)} and {type(Y0)}."
        assert type(X1) == type(0.0) and type(Y1) == type(0.0), f"cood1 must be a tuple of floats, got {type(X1)} and {type(Y1)}."
        assert measurement_system_flag == "IMPERIAL_UNITS" or \
            measurement_system_flag == "METRIC_UNITS", \
            f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
            got "{measurement_system_flag}" of type {type(measurement_system_flag)}. of type {type(measurement_system_flag)}'
            
        self.cood0 = cood0
        self.cood1 = cood1
        self.measurement_system_flag = measurement_system_flag
   
class Elevation:

    name=""
    height = 0.0
    measurement_system_flag = "IMPERIAL_UNITS"
    
    def __init__(self, \
                height=-0.0, \
                measurement_system_flag="IMPERIAL_UNITS"):
        #type checking
        assert type(height) == type(0.0), f"Height must be float, got type {type(height)}"
        assert measurement_system_flag == "IMPERIAL_UNITS" or \
            measurement_system_flag == "METRIC_UNITS", \
            f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
            got "{measurement_system_flag}" of type {type(measurement_system_flag)}. of type {type(measurement_system_flag)}'
        
        self.height = height
        self.measurement_system_flag = measurement_system_flag
    
class Schedule:
    #3 seperate lists representing each schedule
    listOfWallTypes = []
    listOfDoorTypes = []
    listOfWindowTypes = []
    
    def __init__(self):
        listOfWallTypes = []
        listOfDoorTypes = []
        listOfWindowTypes = []
        
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
    measurement_system_flag = "IMPERIAL_UNITS"
    
    #Takes in int, string, float, string
    def __init__(self, \
                typeNumber=-1, \
                name="Nameless", \
                thickness=-1.0, \
                measurement_system_flag="IMPERIAL_UNITS"):
                
        #Bound and type checking goes here
        assert type(typeNumber) == type(1), f"Wall type must be integer, got {type(typeNumber)}."
        assert typeNumber >= -1 and typeNumber != 0, f"typeNumber must be positive."
        
        assert type(name) == type(""), f"Name must be type string, got type {type(name)}." 
        
        assert type(thickness) == type(1.0), f"thickness must be a float, got type {type(thickness)}."
        assert thickness > 0.0 or thickness == -1.0, f"Thickness must be positive."
        
        assert measurement_system_flag == "IMPERIAL_UNITS" or \
            measurement_system_flag == "METRIC_UNITS", \
            f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
            got "{measurement_system_flag}" of type {type(measurement_system_flag)}.'
        
        self.typeNumber = typeNumber
        self.name = name
        self.thickness = thickness
        self.measurement_system_flag = measurement_system_flag

class DoorType:

    #Integer representing door type
    typeNumber = -1
    name = ""
    height = 0.0;
    width = 0.0;
    
    #Str array of info about wall type
    information = []
    measurement_system_flag = "IMPERIAL_UNITS"
    
    def __init__(self, \
                typeNumber=-1, \
                name="Nameless", \
                height=-1.0, \
                width=-1.0, \
                measurement_system_flag="IMPERIAL_UNITS"):
                
        #Bound and type checking goes here
        assert type(typeNumber) == type(1), f"typeNumber must be integer {type(typeNumber)}."
        assert typeNumber >= -1 and typeNumber != 0, f"typeNumber must be positive."
        
        assert type(name) == type(""), f"Name must be type string, got type {type(name)}." 
        
        assert type(height) == type(1.0), f"height must be a float, got type {type(height)}."
        assert height > 0.0 or height == -1.0, f"height must be positive."
        
        assert type(width) == type(1.0), f"width must be a float, got type {type(width)}."
        assert width > 0.0 or width == -1.0, f"width must be positive."
        
        assert measurement_system_flag == "IMPERIAL_UNITS" or \
            measurement_system_flag == "METRIC_UNITS", \
            f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
            got "{measurement_system_flag}" of type {type(measurement_system_flag)}. of type {type(measurement_system_flag)}'
        
        self.typeNumber = typeNumber
        self.name = name
        self.height = height
        self.width = width
        self.measurement_system_flag = measurement_system_flag
        
class WindowType:

    #Integer representing door type
    typeNumber = -1
    name = ""
    height = 0.0;
    width = 0.0;
    sillHeight = 0.0
    
    #Str array of info about wall type
    information = []
    measurement_system_flag = "IMPERIAL_UNITS"
    
    def __init__(self, \
                typeNumber=-1, \
                name="Nameless", \
                height=-1.0, \
                width=-1.0, \
                sillHeight=-1.0, \
                measurement_system_flag="IMPERIAL_UNITS"):
            
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
        
        assert measurement_system_flag == "IMPERIAL_UNITS" or \
            measurement_system_flag == "METRIC_UNITS", \
            f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", \
            got "{measurement_system_flag}" of type {type(measurement_system_flag)}. of type {type(measurement_system_flag)}'
            
        self.typeNumber = typeNumber
        self.name = name
        self.height = height
        self.width = width
        self.sillHeight = sillHeight
        self.measurement_system_flag = measurement_system_flag
        
class Story:
    listOfWalls = []
    listOfDoors = []
    listOfWindows = []
    
    bottomElevation = -1
    topElevation = -1
    
    #TODO type checking
    #todo update this
    def __init__(self, bottomElevation=-1, topElevation=-1):
        self.bottomElevation = bottomElevation
        self.topElevation = topElevation
        
        assert type(bottomElevation) == type(Elevation()), f"bottomElevation must be elevation, got type {type(bottomElevation)}."
        assert type(topElevation) == type(Elevation()), f"topElevation must be elevation, got type {type(topElevation)}."
        
    #TODO append delete search return functions for all 3 lists
    
    #Takes in Wall, Door or Window object and adds it to the story
    def append(self, element):
        if type(element) == type(Wall()):
            self.listOfWalls.append(element)
            return 0;
            
        if type(element) == type(Door()):
            self.listOfDoors.append(element)
            return 0;
            
        if type(element) == type(Window()):
            self.listOfWindows.append(element)
            return 0;
            
        raise Exception("Incompatiable object passed to append to schedule")
        
    #Meaningless functions until I implement elevations
    def getBottomElevation(self):
        return this.bottomElevation
        
    def getTopElevation(self):
        return this.topElevation
        
    def setBottomElevation(self, bottomElevation):
        this.bottomElevation = bottomElevation
        
    def setTopElevation(self, topElevation):
        this.topElevation = topElevation
        
class Wall:

    xZero = np.inf
    yZero = np.inf
    
    xOne = np.inf
    yOne = np.inf
    
    #Reference to WallType object
    wallType = -1
    
    #Optional field, if left empty will default to the distance between elevation markers
    #TODO add support for this lmao
    height = np.inf
    
    #Str array of info about wall
    #Includes tags
    information = []
    
    def __init__(self, \
                cood0=(np.inf, np.inf), \
                cood1=(np.inf, np.inf), \
                wallType=WallType(), \
                height=np.inf):
                
        X0, Y0 = cood0
        X1, Y1 = cood1
                
        assert type(X0) == type(0.0) and type(Y0) == type(0.0), f"cood0 must be a tuple of floats, got {type(X0)} and {type(Y0)}."
        assert type(X1) == type(0.0) and type(Y1) == type(0.0), f"cood1 must be a tuple of floats, got {type(X1)} and {type(Y1)}."
        assert type(wallType) == type(WallType()), f"wallType must be WallType object, got type {type(wallType)}."       
        
        self.xZero, self.xZero = cood0
        self.xOne, self.yOne = cood1
        self.wallType = wallType
        self.height = height
    
    #Returns tuple of coordinate of one end of the wall
    def getPosZero(self):
        return (self.xZero, self.yZero)
        
    #Returns tuple of coordinate of the other end of the wall
    def getPosOne(self):
        return (self.xOne, self.yOne)

    def getThickness(self):
        return self.wallType.getThickness()
        
    def setPosZero(self, cood):
        self.xZero, self.yZero = cood
        
    def setPosOne(self, cood):
        self.xOne, self.yOne = cood
        
class Door:

    #Position from the center of the door frame
    xPos = np.inf
    yPos = np.inf
    
    #refers to the angle normal vector, such that,
    #0.0 represents pointing right, and the outside face of the door is pointing left
    #90.0 represents pointing down, and the outside face of the door is pointing up
    #doors "swing" out, always
    normalVector = np.inf
    
    #Reference to DoorType object
    doorType = -1
    
    #Reference to Wall object
    #Consider removing
    embededWall = np.inf
    
    #Str array of info about wall
    #Includes tags
    information = []
    
    def __init__(self, \
                pos=(np.inf, np.inf), \
                normalVector=np.inf, \
                doorType=DoorType(), \
                embededWall=np.inf):

        X, Y = pos
        
        assert type(X) == type(0.0) and type(Y) == type(0.0), f"pos must be a tuple of floats, got {type(X)} and {type(Y)}."
        assert type(normalVector) == type(0.0), f"normalVector must be type float, got type {type(normalVector)}."
        assert type(doorType) == type(DoorType()), f"doorType must be DoorType object, got type {type(doorType)}."
        
        self.xPos, self.yPos = pos
        self.normalVector = normalVector
        self.doorType = doorType
        self.embededWall = embededWall
        
    #Returns tuple of coordiantes of the door
    def getPos(self):
        return (self.xPos, self.yPos)
        
    def setPos(self, cood):
        self.xPos, self.yPos = cood

class Window:

    #Position from the center of the window
    xPos = np.inf
    yPos = np.inf
    
    #refers to the angle normal vector, such that,
    #0.0 represents pointing right, and the outside face of the window is pointing left
    #90.0 represents pointing down, and the outside face of the window is pointing up
    normalVector = np.inf
    
    #Reference to WindowType object
    windowType = -1
    
    #Reference to Wall object
    #Consider removing
    embededWall = -1
    
    #Str array of info about wall
    #Includes tags
    information = []
    
    def __init__(self, \
                pos=(np.inf, np.inf), \
                normalVector=np.inf, \
                windowType=WindowType(), \
                embededWall=-1):
        
        X, Y = pos
        
        assert type(X) == type(0.0) and type(Y) == type(0.0), f"pos must be a tuple of floats, got {type(X)} and {type(Y)}."
        assert type(normalVector) == type(0.0), f"normalVector must be type float, got type {type(normalVector)}."
        assert type(windowType) == type(WindowType()), f"windowType must be WindowType object, got type {type(windowType)}."
        
        self.xPos, self.yPos = pos
        self.normalVector = normalVector
        self.windowType = windowType
        self.embededWall = embededWall
        
    #Returns tuple of coordinate of the window
    def getPos(self):
        return (self.xPos, self.yPos)
        
    def setPos(self, cood):
        self.xPos, self.yPos = cood
        
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
    
buildingData.appendElevation(0.0, measurement_system_flag="METRIC_UNITS")
buildingData.appendElevation(400.0, measurement_system_flag="METRIC_UNITS")

assert len(buildingData.listOfElevations) == 2
assert buildingData.listOfElevations[0].height == 0.0
assert buildingData.listOfElevations[1].height == 400.0

buildingData.buildingSchedule.append(WallType(typeNumber=1, \
                                            name="das conk creet baybee", \
                                            thickness=50.0, \
                                            measurement_system_flag="METRIC_UNITS"))
buildingData.buildingSchedule.append(DoorType(typeNumber=2, \
                                            name="the Pearly Gates", \
                                            height=200.0, \
                                            width=120.0, \
                                            measurement_system_flag="METRIC_UNITS"))
buildingData.buildingSchedule.append(WindowType(typeNumber=3, \
                                            name="the Pearly Gates", \
                                            height=100.0, \
                                            width=100.0, \
                                            sillHeight=40.0, \
                                            measurement_system_flag="METRIC_UNITS"))
                                            
buildingData.appendStory(bottomElevation = buildingData.listOfElevations[0], \
                        topElevation = buildingData.listOfElevations[1])
                        
#South wall
buildingData.listOfStories[0].append(Wall(cood0=(0.0, 25.0), cood1=(1050.0, 25.0), \
                                        wallType=buildingData.buildingSchedule.searchByType(1)))

#East wall
buildingData.listOfStories[0].append(Wall(cood0=(1025.0, 0.0), cood1=(1025.0, 550.0), \
                                        wallType=buildingData.buildingSchedule.searchByType(1)))

#North wall
buildingData.listOfStories[0].append(Wall(cood0=(0.0, 525.0), cood1=(1050.0, 525.0), \
                                        wallType=buildingData.buildingSchedule.searchByType(1)))

#West wall
buildingData.listOfStories[0].append(Wall(cood0=(25.0, 0.0), cood1=(25.0, 550.0), \
                                        wallType=buildingData.buildingSchedule.searchByType(1)))
                                        
#Door on north wall
buildingData.listOfStories[0].append(Door(pos=(645.0, 525.0), normalVector=90.0, \
                                        doorType=buildingData.buildingSchedule.searchByType(2)))

#Window on west wall
buildingData.listOfStories[0].append(Window(pos=(25.0, 365.0), normalVector=0.0, \
                                        windowType=buildingData.buildingSchedule.searchByType(3)))

#Window on east wall
#Set slightly off of wall, intentionally
buildingData.listOfStories[0].append(Window(pos=(1045.0, 365.0), normalVector=180.0, \
                                        windowType=buildingData.buildingSchedule.searchByType(3)))


print("done!")