import numpy as np
#TODO Gridlines, elevations, BuildingData Class
#TODO use assert statements in place of if statements

class Schedule:
    listOfWallTypes = []
    listOfDoorTypes = []
    listOfWindowTypes = []
    
    def __init__(self):
        listOfWallTypes = []
        listOfDoorTypes = []
        listOfWindowTypes = []
        
    def append(self, element):
        if type(element) == type(WallType()):
            self.listOfWallTypes.append(element)
            return 0;
            
        if type(element) == type(DoorType()):
            self.listOfDoorTypes.append(element)
            return 0;
            
        if type(element) == type(WindowType()):
            self.listOfWindowTypes.append(element)
            return 0;
            
        raise Exception("Incompatiable object passed to append to schedule")
        
    def searchByType(self, typeNumber):
    
        assert type(typeNumber) == type(0)
        
        for element in self.listOfWallTypes:
            if element.wallType == typeNumber:
                return element
                
        for element in self.listOfDoorTypes:
            if element.doorType == typeNumber:
                return element
                
        for element in self.listOfWindowTypes:
            if element.windowType == typeNumber:
                return element
        return -1
                
    def deleteByType(self, typeNumber):
        
        assert type(typeNumber) == type(0)
    
        for element in self.listOfWallTypes:
            if element.wallType == typeNumber:
                listOfWallTypes.remove(element)
                return 0;
                
        for element in self.listOfDoorTypes:
            if element.doorType == typeNumber:
                listOfDoorTypes.remove(element)
                return 0
                
        for element in self.listOfWindowTypes:
            if element.windowType == typeNumber:
                listOfWindowTypes.remove(element)
                return 0
        return -1
        
class WallType:

    #integer representing wall type
    wallType = np.empty
    name = ""
    thickness = -1.0
    
    #str array of info about wall type
    information = []
    measurement_system_flag = "IMPERIAL_UNITS"
    
    def __init__(self, \
                wallType=-1, \
                name="Nameless", \
                thickness=-1.0, \
                measurement_system_flag="IMPERIAL_UNITS"):
                
        #bound and type checking goes here
        #TODO finish type checking and bounds checking
        
        assert type(thickness) == type(1.0), f"Thickness must be a float, got type {type(thickness)}"
        assert measurement_system_flag == "IMPERIAL_UNITS" or \
            measurement_system_flag == "METRIC_UNITS", \
            f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", got "{measurement_system_flag}" of type {type(measurement_system_flag)}'
        
        self.wallType = wallType
        self.name = name
        self.thickness = thickness
        self.measurement_system_flag = measurement_system_flag

class DoorType:

    #integer representing door type
    doorType = np.empty
    name = ""
    height = 0.0;
    width = 0.0;
    
    #str array of info about wall type
    information = []
    measurement_system_flag = "IMPERIAL_UNITS"
    
    def __init__(self, \
                doorType=-1, \
                name="Nameless", \
                height=-1.0, \
                width=-1.0, \
                measurement_system_flag="IMPERIAL_UNITS"):
                
        #bound and type checking goes here
        #TODO finish type checking and bounds checking
        assert type(height) == type(1.0), f"Height must be a float, got type {type(height)}"
        assert type(width) == type(1.0), f"Width must be a float, got type {type(width)}"
        assert measurement_system_flag == "IMPERIAL_UNITS" or \
            measurement_system_flag == "METRIC_UNITS", \
            f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", got "{measurement_system_flag}" of type {type(measurement_system_flag)}'
        
        self.doorType = doorType
        self.name = name
        self.height = height
        self.width = width
        self.measurement_system_flag = measurement_system_flag
        
class WindowType:

    #integer representing door type
    windowType = np.empty
    name = ""
    height = 0.0;
    width = 0.0;
    stillHeight = 0.0
    
    #str array of info about wall type
    information = []
    measurement_system_flag = "IMPERIAL_UNITS"
    
    def __init__(self, \
                windowType=-1, \
                name="Nameless", \
                height=-1.0, \
                width=-1.0, \
                stillHeight=-1.0, \
                measurement_system_flag="IMPERIAL_UNITS"):
            
        #bound and type checking goes here
        #TODO finish type checking and bounds checking
        assert type(height) == type(1.0), f"Height must be a float, got type {type(height)}"
        assert type(width) == type(1.0), f"Width must be a float, got type {type(width)}"
        assert type(stillHeight) == type(1.0), f"Still height must be a float, got type {type(stillHeight)}"
        assert measurement_system_flag == "IMPERIAL_UNITS" or \
            measurement_system_flag == "METRIC_UNITS", \
            f'Measurement system must be "IMPERIAL_UNITS" or "METRIC_UNITS", got "{measurement_system_flag}" of type {type(measurement_system_flag)}'
        
        self.windowType = windowType
        self.name = name
        self.height = height
        self.width = width
        self.stillHeight = stillHeight
        self.measurement_system_flag = measurement_system_flag
        
class Story:
    listOfWalls = []
    listOfDoors = []
    listOfWindows = []
    
    bottomElevation = -1
    topElevation = -1
    
    #TODO type checking
    def __init__(self, bottomElevation=-1, topElevation=-1):
        self.bottomElevation = bottomElevation
        self.topElevation = topElevation
        
    #TODO append delete search return functions for all 3 lists
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
        
    def getBottomElevation(self):
        return this.bottomElevation
        
    def getTopElevation(self):
        return this.topElevation
        
    def setBottomElevation(self, bottomElevation):
        this.bottomElevation = bottomElevation
        
    def setTopElevation(self, topElevation):
        this.topElevation = topElevation
        
class Wall:

    xZero = -1
    yZero = -1
    
    xOne = -1
    yOne = -1
    
    #reference to WallType object
    wallType = -1
    
    #optional field, if left empty will default to the distance between elevation markers
    height = -1
    
    #str array of info about wall
    #includes tags
    information = []
    
    def __init__(self, \
                cood0=(-1, -1), \
                cood1=(-1, -1), \
                wallType=-1, \
                height=-1):
                
        self.xZero, self.xZero = cood0
        self.xOne, self.yOne = cood1
        self.wallType = wallType
    
    def getPosZero(self):
        return (self.xZero, self.yZero)
        
    def getPosOne(self):
        return (self.xOne, self.yOne)
        
    # TODO return thickness
    def getThickness(self):
        return self.wallType.getThickness()
        
    def setPosZero(self, cood):
        self.xZero, self.yZero = cood
        
    def setPosOne(self, cood):
        self.xOne, self.yOne = cood
        
class Door:

    xPos = -1
    yPos = -1
    normalVector = -1.0
    
    #reference to DoorType object
    doorType = -1
    
    #reference to Wall object
    #consider removing
    embededWall = -1
    
    #str array of info about wall
    #includes tags
    information = []
    
    def __init__(self, \
                pos=(-1, -1), \
                normalVector=-1.0, \
                doorType=-1, \
                embededWall=-1):
        
        #TODO bounds and type checks
        
        self.xPos, self.yPos = pos
        self.normalVector = normalVector
        self.doorType = doorType
        self.embededWall = embededWall
        
    def getPos(self):
        return (self.xPos, self.yPos)
        
    def setPos(self, cood):
        self.xPos, self.yPos = cood

class Window:

    xPos = -1
    yPos = -1
    normalVector = -1.0
    
    #reference to WindowType object
    windowType = -1
    
    #reference to Wall object
    #consider removing
    embededWall = -1
    
    #str array of info about wall
    #includes tags
    information = []
    
    def __init__(self, \
                pos=(-1, -1), \
                normalVector=-1.0, \
                windowType=-1, \
                embededWall=-1):
        
        #TODO bounds and type checks
        
        self.xPos, self.yPos = pos
        self.normalVector = normalVector
        self.windowType = windowType
        self.embededWall = embededWall
        
    def getPos(self):
        return (self.xPos, self.yPos)
        
    def setPos(self, cood):
        self.xPos, self.yPos = cood
        
        
#assertion statements to make sure everything works properly
buildingSchedule = Schedule()

timWallType = WallType(wallType=17, name="8 inches of tungsten", thickness=8.0)
tomDoorType = DoorType(doorType=34, name="a single sheet of paper", height=60.0, width=40.0)
dimaWindowType = WindowType(windowType=98, name="German Window", height=80.0, width=20.0, stillHeight=80.0)

buildingSchedule.append(timWallType)
buildingSchedule.append(tomDoorType)
buildingSchedule.append(dimaWindowType)

assert len(buildingSchedule.listOfDoorTypes) == 1
assert len(buildingSchedule.listOfWallTypes) == 1
assert len(buildingSchedule.listOfWindowTypes) == 1

assert type(buildingSchedule.searchByType(17)) == type(WallType())
assert type(buildingSchedule.searchByType(34)) == type(DoorType())
assert type(buildingSchedule.searchByType(98)) == type(WindowType())

firstFloor = Story(topElevation=-1, bottomElevation=-1)

jacksonWall = Wall()
johnsonDoor = Door()
grantWindow = Window()

firstFloor.append(jacksonWall)
firstFloor.append(johnsonDoor)
firstFloor.append(grantWindow)

assert len(firstFloor.listOfDoors) == 1
assert len(firstFloor.listOfWalls) == 1
assert len(firstFloor.listOfWindows) == 1