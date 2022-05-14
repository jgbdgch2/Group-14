import numpy as np
#TODO Gridlines, elevations, BuildingData Class

class Schedule:
    listOfWallTypes = []
    listOfDoorTypes = []
    listOfWindowTypes = []
    
    #TODO init function
    #TODO append delete function for all lists
        
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
        if (type(thickness) != type(1.0)):
            raise Exception("Thickness must be a float")
            
        if (measurement_system_flag != "IMPERIAL_UNITS" && measurement_system_flag != "METRIC_UNITS"):
            raise Exception("Measurement system must be 'IMPERIAL_UNITS' or 'METRIC_UNITS'")
        
        self.wallType = wallType
        self.name = name
        self.thickness = thickness

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
        if (type(height) != type(1.0)):
            raise Exception("Height must be a float")
            
        if (type(width) != type(1.0)):
            raise Exception("Width must be a float")
        
        if (measurement_system_flag != "IMPERIAL_UNITS" && measurement_system_flag != "METRIC_UNITS"):
            raise Exception("Measurement system must be 'IMPERIAL_UNITS' or 'METRIC_UNITS'")
        
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
        if (type(height) != type(1.0)):
            raise Exception("Height must be a float")
            
        if (type(width) != type(1.0)):
            raise Exception("Width must be a float")
            
        if (type(stillHeight) != type(1.0)):
            raise Exception("Still height must be a float")
            
        if (measurement_system_flag != "IMPERIAL_UNITS" && measurement_system_flag != "METRIC_UNITS"):
            raise Exception("Measurement system must be 'IMPERIAL_UNITS' or 'METRIC_UNITS'")
        
        self.doorType = windowType
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
        
    def getBottomElevation(self):
        return this.bottomElevation
        
    def getTopElevation(self):
        return this.topElevation
        
    def setBottomElevation(self, bottomElevation):
        this.bottomElevation = bottomElevation
        
    def setTopElevation(self, topElevation):
        this.topElevation = topElevation
        
    #TODO append delete search return functions for all 3 lists

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
    hinge = "left"
    
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
                hinge="left", \
                doorType=-1, \
                embededWall=-1);
        
        #TODO bounds and type checks
        
        self.xPos, self.yPos = pos
        self.normalVector = normalVector
        self.hinge = hinge
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
                doorType=-1, \
                embededWall=-1);
        
        #TODO bounds and type checks
        
        self.xPos, self.yPos = pos
        self.normalVector = normalVector
        self.doorType = doorType
        self.embededWall = embededWall
        
    def getPos(self):
        return (self.xPos, self.yPos)
        
    def setPos(self, cood):
        self.xPos, self.yPos = cood
        
Tim = WallType(wallType=17, name="das conk creet baybee", thickness = 12.0)
Dima = Wall(wallType = Tim)
print(Dima.wallType.name)