import uuid
import string
import math

filename = "default_filename.ifc"

# Initialize pointer to track location in IFC file
# Points to next available location in the IFC
# 100 is the fist available location after the units are written to the file
ifcPointer = 100

# Returns a unique string 22 characters long to be used as an IFC compliant GUID
# Created using code from IfcOpenShell
# (May need to rework this to credit IfcOpenShell or import directly somehow)
def getGUID():
    chars = string.digits + string.ascii_uppercase + string.ascii_lowercase + "_$"
    def compress(g):
        bs = [int(g[i : i + 2], 16) for i in range(0, len(g), 2)]

        def b64(v, l=4):
            return "".join([chars[(v // (64 ** i)) % 64] for i in range(l)][::-1])

        return "".join([b64(bs[0], 2)] + [b64((bs[i] << 16) + (bs[i + 1] << 8) + bs[i + 2]) for i in range(1, 16, 3)])
    return compress(uuid.uuid4().hex)

# generate GUIDS for ifcTemplate
projectID = getGUID()
siteID = getGUID()
buildingID = getGUID()
rel1ID = getGUID()
rel2ID = getGUID()

# #99 references IFCUNITASSIGNMENT
# #3 is used for vertical extrusions
ifcTemplate = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('%(filename)s','',(''),(''),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1= IFCCARTESIANPOINT((0.,0.,0.));
#2= IFCAXIS2PLACEMENT3D(#1,$,$);
#3= IFCDIRECTION((0., 0., 1.));

#4= IFCPOSTALADDRESS($,$,$,$,(),$,'','','','');
#5= IFCPROJECT('%(projectID)s', $, '', '', $, '', '',(#22), #99);
#6= IFCSITE('%(siteID)s',$,'',$,$,#10,$,$,.ELEMENT.,$,$,0.,$,$);
#7= IFCBUILDING('%(buildingID)s',$,'',$,$,#11,$,'',.ELEMENT.,$,$,#4);

#10= IFCLOCALPLACEMENT($,#2);
#11= IFCLOCALPLACEMENT(#10,#2);

#13= IFCRELAGGREGATES('%(rel1ID)s',$,$,$,#5,(#6));
#14= IFCRELAGGREGATES('%(rel2ID)s',$,$,$,#6,(#7));

#20= IFCDIRECTION((0.,1.));
#21= IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,0.01,#2,#20);
#22= IFCGEOMETRICREPRESENTATIONSUBCONTEXT('Body','Model',*,*,*,*,#21,$,.MODEL_VIEW.,$);
""" % locals()

ifcCloser = """ENDSEC;

END-ISO-10303-21;
"""

# IFC units shall be contained within positions #25-#99
ifcImperial = """
#25=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#26= IFCDIMENSIONALEXPONENTS(1,0,0,0,0,0,0);
#27= IFCMEASUREWITHUNIT(IFCRATIOMEASURE(0.3048),#25);
#28= IFCCONVERSIONBASEDUNIT(#26,.LENGTHUNIT.,'FOOT',#27);
#99= IFCUNITASSIGNMENT((#28));
"""

ifcMetric = """
#25=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#99= IFCUNITASSIGNMENT((#25));
"""

def getWindowCoords(Window):
    global unitModifier
    x = Window.windowType.width / (unitModifier*2)
    sill = Window.windowType.sillHeight / unitModifier
    y = (Window.windowType.height / unitModifier) + sill
    return "(({:.6f},-{:.6f}),({:.6f},{:.6f}),({:.6f},{:.6f}),({:.6f},-{:.6f}),({:.6f},-{:.6f}))".format(sill,x,sill,x,y,x,y,x,sill,x)

def getDoorCoords(Door):
    global unitModifier
    x = Door.doorType.width / (unitModifier*2)
    y = Door.doorType.height / unitModifier
    return "((0.0,-{:.6f}),(0.0,{:.6f}),({:.6f},{:.6f}),({:.6f},-{:.6f}),(0.0,-{:.6f}))".format(x,x,y,x,y,x,x)

def locationOnWall(distance, Wall, hingeToggle, elementThickness):
    global unitModifier
    distance = distance / unitModifier
    thickness = Wall.getThickness() / (unitModifier*2)
    if(hingeToggle):
        thickness = thickness * -1 + elementThickness
    angle = math.radians(Wall.angle)
    xPos = Wall.xPos / unitModifier
    yPos = Wall.yPos / unitModifier

    x = xPos + distance * math.cos(angle) + thickness * math.sin(angle)
    y = yPos + distance * math.sin(angle) - thickness * math.cos(angle)

    return "({:.6f}, {:.6f}, 0.0)".format(x, y)


def getExtrudeDir(wallAngle):
    x = math.cos(math.radians(wallAngle + 90.0))
    y = math.sin(math.radians(wallAngle + 90.0))
    return "({:.6f}, {:.6f}, 0.0)".format(x, y)

def printPerpendicularShapeDef(f, coords, thickness, extrudeDir):
    global ifcPointer
    #200= IFCCARTESIANPOINTLIST2D(((12.,1.),(0.,1.),(0.,-1.),(12.,-1.),(12.,1.)));
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINTLIST2D(" + coords + ");\n")
    ifcPointer +=1
    #201= IFCINDEXEDPOLYCURVE(#200, $, .F.);
    f.write("#" + str(ifcPointer) + "= IFCINDEXEDPOLYCURVE(#" + str(ifcPointer-1) + ", $, .F.);\n")
    ifcPointer +=1
    #202= IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,$,#201);
    f.write("#" + str(ifcPointer) + "= IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,$,#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    #18= IFCDIRECTION((0.,-1.,0.));
    f.write("#" + str(ifcPointer) + "= IFCDIRECTION(" + extrudeDir + ");\n")
    ifcPointer +=1
    #603= IFCAXIS2PLACEMENT3D(#6,#18,#20);
    f.write("#" + str(ifcPointer) + "= IFCAXIS2PLACEMENT3D(#1,#" + str(ifcPointer-1) + ",#3);\n")
    ifcPointer +=1
    #604= IFCEXTRUDEDAREASOLID(#602,#603,#20,0.666666666666667);
    f.write("#" + str(ifcPointer) + "= IFCEXTRUDEDAREASOLID(#" + str(ifcPointer-3) + ", #" + str(ifcPointer-1) + ", #3, " + str(thickness) + ");\n")
    ifcPointer +=1
    #605= IFCSHAPEREPRESENTATION(#127,'Body','SweptSolid',(#604));
    f.write("#" + str(ifcPointer) + "= IFCSHAPEREPRESENTATION(#22, 'Body', 'SweptSolid', (#" + str(ifcPointer-1) + "));\n")
    ifcPointer +=1
    #607= IFCPRODUCTDEFINITIONSHAPE($,$,(#605));
    f.write("#" + str(ifcPointer) + "= IFCPRODUCTDEFINITIONSHAPE($,$,(#" + str(ifcPointer-1) + "));\n")
    ifcPointer +=1

def getWallCoords(Wall):
    global unitModifier
    thickness = Wall.getThickness() / (unitModifier*2)
    length = Wall.length / (unitModifier*2)
    angle = math.radians(Wall.angle)
    xPos = Wall.xPos / unitModifier
    yPos = Wall.yPos / unitModifier

    x1 = xPos + length * math.cos(angle) + thickness * math.sin(angle)
    y1 = yPos + length * math.sin(angle) - thickness * math.cos(angle)
    x2 = xPos + length * math.cos(angle) - thickness * math.sin(angle)
    y2 = yPos + length * math.sin(angle) + thickness * math.cos(angle)
    x3 = xPos - length * math.cos(angle) - thickness * math.sin(angle)
    y3 = yPos - length * math.sin(angle) + thickness * math.cos(angle)
    x4 = xPos - length * math.cos(angle) + thickness * math.sin(angle)
    y4 = yPos - length * math.sin(angle) - thickness * math.cos(angle)

    #((12.,1.),(0.,1.),(0.,-1.),(12.,-1.),(12.,1.))

    coords = "(({:.6f}, {:.6f}), ({:.6f}, {:.6f}), ({:.6f}, {:.6f}), ({:.6f}, {:.6f}), ({:.6f}, {:.6f}))".format(x1, y1, x2, y2, x3, y3, x4, y4, x1, y1)

    return coords

def printVerticalShapeDef(f, coords, height):
    global ifcPointer
    #200= IFCCARTESIANPOINTLIST2D(((12.,1.),(0.,1.),(0.,-1.),(12.,-1.),(12.,1.)));
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINTLIST2D(" + coords + ");\n")
    ifcPointer +=1
    #201= IFCINDEXEDPOLYCURVE(#200, $, .F.);
    f.write("#" + str(ifcPointer) + "= IFCINDEXEDPOLYCURVE(#" + str(ifcPointer-1) + ", $, .F.);\n")
    ifcPointer +=1
    #202= IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,$,#201);
    f.write("#" + str(ifcPointer) + "= IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,$,#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    #203= IFCEXTRUDEDAREASOLID(#202, #2, #3, 8.);
    f.write("#" + str(ifcPointer) + "= IFCEXTRUDEDAREASOLID(#" + str(ifcPointer-1) + ", #2, #3, " + str(height) + ");\n")
    ifcPointer +=1
    #204= IFCSHAPEREPRESENTATION(#22, 'Body', 'SweptSolid', (#203));
    f.write("#" + str(ifcPointer) + "= IFCSHAPEREPRESENTATION(#22, 'Body', 'SweptSolid', (#" + str(ifcPointer-1) + "));\n")
    ifcPointer +=1
    #220= IFCPRODUCTDEFINITIONSHAPE($,$,(#204));
    f.write("#" + str(ifcPointer) + "= IFCPRODUCTDEFINITIONSHAPE($,$,(#" + str(ifcPointer-1) + "));\n")
    ifcPointer +=1
    return (ifcPointer-1)

def compileWindow(f, Window, Wall, ifcWallPointer, storyLocalPlacement):
    global ifcPointer
    global unitModifier
    printPerpendicularShapeDef(f, getWindowCoords(Window), Wall.getThickness()/unitModifier, getExtrudeDir(Wall.angle))
    shapeDef = ifcPointer-1
    #610= IFCCARTESIANPOINT((7.5,0.333333333333313,0.));
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINT(" + locationOnWall(Window.position, Wall, False, 0.0) +");\n")
    ifcPointer +=1
    #612= IFCAXIS2PLACEMENT3D(#610,$,$);
    f.write("#" + str(ifcPointer) + "= IFCAXIS2PLACEMENT3D(#" + str(ifcPointer-1) + ",$,$);\n")
    ifcPointer +=1
    #613= IFCLOCALPLACEMENT(#201,#612);
    f.write("#" + str(ifcPointer) + "= IFCLOCALPLACEMENT(#" + str(storyLocalPlacement) + ",#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    #615= IFCOPENINGELEMENT('0DzNJ20FL0ZQlbjUb8770P',#42,'Single-Flush:36" x 84":285019:1',$,$,#613,#607,'285019',.OPENING.);
    f.write("#" + str(ifcPointer) + "= IFCOPENINGELEMENT('" + getGUID() + "', $, $, $, $,#" + str(ifcPointer-1) +",#" + str(shapeDef) + ",$,.OPENING.);\n")
    ifcOpeningPointer = ifcPointer
    ifcPointer +=1

    defaultWindowThickness = 0.125 #translates to 1.5 inches
    faceToggle = False # used to make door's 3d model appear on the correct side of the opening
    if(Window.directionFacing == 1): # change this if statement once hingepos system is finalized
        faceToggle = True
    printPerpendicularShapeDef(f, getWindowCoords(Window), defaultWindowThickness, getExtrudeDir(Wall.angle))
    shapeDef = ifcPointer-1
    #610= IFCCARTESIANPOINT((7.5,0.333333333333313,0.));
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINT(" + locationOnWall(Window.position, Wall, faceToggle, defaultWindowThickness) +");\n")
    ifcPointer +=1
    #612= IFCAXIS2PLACEMENT3D(#610,$,$);
    f.write("#" + str(ifcPointer) + "= IFCAXIS2PLACEMENT3D(#" + str(ifcPointer-1) + ",$,$);\n")
    ifcPointer +=1
    #613= IFCLOCALPLACEMENT(#201,#612);
    f.write("#" + str(ifcPointer) + "= IFCLOCALPLACEMENT(#" + str(storyLocalPlacement) + ",#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    #1927= IFCWINDOW('1egRXnmeDArvJcnh5AE0Rg',$,$,$,$,#26299,#1920,'288433',3.83333333333332,2.5,.WINDOW.,.NOTDEFINED.,$);
    f.write("#" + str(ifcPointer) + "= IFCWINDOW('" + getGUID() + "',$,'" + Window.windowType.name + "',$,$,#" + str(ifcPointer-1) + ",#" + str(shapeDef) + ",$,"\
        + str(Window.windowType.height/unitModifier) + "," + str(Window.windowType.width/unitModifier) + ",.WINDOW.,.NOTDEFINED.,$);\n")
    ifcWindowPointer = ifcPointer
    ifcPointer +=1
    #620= IFCRELVOIDSELEMENT('0DzNJ20FL0ZQlbjUv8770P',#42,$,$,#238,#615);
    f.write("#" + str(ifcPointer) + "= IFCRELVOIDSELEMENT('" + getGUID() + "',$,$,$,#" + str(ifcWallPointer) + ",#" + str(ifcOpeningPointer) + ");\n")
    ifcPointer +=1
    #632= IFCRELFILLSELEMENT('396YOskxfCdhVuHlpB3O$6',#42,$,$,#615,#474);
    f.write("#" + str(ifcPointer) + "= IFCRELFILLSELEMENT('" + getGUID() + "',$,$,$,#" + str(ifcOpeningPointer) + ",#" + str(ifcWindowPointer) + ");\n")
    ifcPointer +=1
    returnString = "#" + str(ifcWindowPointer) + ","
    return returnString

def compileDoor(f, Door, Wall, ifcWallPointer, storyLocalPlacement):
    global ifcPointer
    global unitModifier
    printPerpendicularShapeDef(f, getDoorCoords(Door), Wall.getThickness()/unitModifier, getExtrudeDir(Wall.angle))
    shapeDef = ifcPointer-1
    #610= IFCCARTESIANPOINT((7.5,0.333333333333313,0.));
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINT(" + locationOnWall(Door.position, Wall, False, 0.0) +");\n")
    ifcPointer +=1
    #612= IFCAXIS2PLACEMENT3D(#610,$,$);
    f.write("#" + str(ifcPointer) + "= IFCAXIS2PLACEMENT3D(#" + str(ifcPointer-1) + ",$,$);\n")
    ifcPointer +=1
    #613= IFCLOCALPLACEMENT(#201,#612);
    f.write("#" + str(ifcPointer) + "= IFCLOCALPLACEMENT(#" + str(storyLocalPlacement) + ",#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    #615= IFCOPENINGELEMENT('0DzNJ20FL0ZQlbjUb8770P',#42,'Single-Flush:36" x 84":285019:1',$,$,#613,#607,'285019',.OPENING.);
    f.write("#" + str(ifcPointer) + "= IFCOPENINGELEMENT('" + getGUID() + "', $, $, $, $,#" + str(ifcPointer-1) +",#" + str(shapeDef) + ",$,.OPENING.);\n")
    ifcOpeningPointer = ifcPointer
    ifcPointer +=1

    defaultDoorThickness = 0.125 #translates to 1.5 inches
    hingeToggle = False # used to make door's 3d model appear on the correct side of the opening
    if(Door.hingePos == 1): # change this if statement once hingepos system is finalized
        hingeToggle = True
    printPerpendicularShapeDef(f, getDoorCoords(Door), defaultDoorThickness, getExtrudeDir(Wall.angle))
    shapeDef = ifcPointer-1
    #610= IFCCARTESIANPOINT((7.5,0.333333333333313,0.));
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINT(" + locationOnWall(Door.position, Wall, hingeToggle, defaultDoorThickness) +");\n")
    ifcPointer +=1
    #612= IFCAXIS2PLACEMENT3D(#610,$,$);
    f.write("#" + str(ifcPointer) + "= IFCAXIS2PLACEMENT3D(#" + str(ifcPointer-1) + ",$,$);\n")
    ifcPointer +=1
    #613= IFCLOCALPLACEMENT(#201,#612);
    f.write("#" + str(ifcPointer) + "= IFCLOCALPLACEMENT(#" + str(storyLocalPlacement) + ",#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    #474= IFCDOOR('0DzNJ20FL0ZQlbjVf8770P',#42,'Single-Flush:36" x 84":285019',$,'Single-Flush:36" x 84"',#636,#467,'285019',7.,3.,.DOOR.,.NOTDEFINED.,$);
    f.write("#" + str(ifcPointer) + "= IFCDOOR('" + getGUID() + "',$,'" + Door.doorType.name + "',$,$,#" + str(ifcPointer-1) + ",#" + str(shapeDef) + ",$,"\
        + str(Door.doorType.height/unitModifier) + "," + str(Door.doorType.width/unitModifier) + ",.DOOR.,.NOTDEFINED.,$);\n")
    ifcDoorPointer = ifcPointer
    ifcPointer +=1
    #620= IFCRELVOIDSELEMENT('0DzNJ20FL0ZQlbjUv8770P',#42,$,$,#238,#615);
    f.write("#" + str(ifcPointer) + "= IFCRELVOIDSELEMENT('" + getGUID() + "',$,$,$,#" + str(ifcWallPointer) + ",#" + str(ifcOpeningPointer) + ");\n")
    ifcPointer +=1
    #632= IFCRELFILLSELEMENT('396YOskxfCdhVuHlpB3O$6',#42,$,$,#615,#474);
    f.write("#" + str(ifcPointer) + "= IFCRELFILLSELEMENT('" + getGUID() + "',$,$,$,#" + str(ifcOpeningPointer) + ",#" + str(ifcDoorPointer) + ");\n")
    ifcPointer +=1
    returnString = "#" + str(ifcDoorPointer) + ","
    return returnString

def compileWall(f, Wall, storyLocalPlacement):
    global ifcPointer
    printVerticalShapeDef(f, getWallCoords(Wall), 8.0)
    #221= IFCWALL('1btdOju4n3KfkQnsDbRkrg', $, $, $, $, #storyLocalPlacement, #220, '2712', .NOTDEFINED.);
    f.write("#" + str(ifcPointer) + "= IFCWALL('" + getGUID() + "', $, '" + Wall.wallType.name + "', $, $, #" + str(storyLocalPlacement) + ", #" + str(ifcPointer-1) + ", $, .NOTDEFINED.);\n")
    ifcWallPointer = ifcPointer
    Wall.ifcName = "#" + str(ifcWallPointer)
    ifcPointer +=1
    #549= IFCRELASSOCIATESMATERIAL('2R$msq7Cf1IwcXgYEmhjOH',$,$,$,(#184),#406);
    f.write("#" + str(ifcPointer) + "= IFCRELASSOCIATESMATERIAL('" + getGUID() + "',$,$,$,(#" + str(ifcWallPointer) + "),#" + str(Wall.wallType.ifcName) + ");\n")
    ifcPointer +=1
    returnString = "#" + str(ifcWallPointer) + ","
    for Door in Wall.listOfDoors:
        returnString = returnString + compileDoor(f, Door, Wall, ifcWallPointer, storyLocalPlacement)
    for Window in Wall.listOfWindows:
        returnString = returnString + compileWindow(f, Window, Wall, ifcWallPointer, storyLocalPlacement)
    return returnString

def compileStory(f, Story, storyNumber):
    global ifcPointer
    storyPointer = ifcPointer;
    storyLocalPlacement = ifcPointer+3;
    storyElements = ""

    # Declare bottom elevation of the story where all the elements are listed
    f.write("#" + str(ifcPointer) + "= IFCBUILDINGSTOREY('" + getGUID() + "',$,'Story " + str(storyNumber) + \
    " Base',$,$,#" + str(storyLocalPlacement) + ",$,'Story " + str(storyNumber) + " Base',.ELEMENT.," + str(Story.bottomElevation.height) + ");\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINT((0.,0.,"+ str(Story.bottomElevation.height) + "));\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCAXIS2PLACEMENT3D(#" + str(ifcPointer-1) + ",$,$);\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCLOCALPLACEMENT(#11,#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCRELAGGREGATES('" + getGUID() + "',$,$,$,#7,(#" + str(storyPointer) + "));\n")
    ifcPointer +=1

    for Wall in Story.listOfWalls:
        storyElements = storyElements + compileWall(f, Wall, storyLocalPlacement)

    storyElements = storyElements[:len(storyElements)-1] # Removes extra , from end of string

    #222= IFCRELCONTAINEDINSPATIALSTRUCTURE('1btdOju4n3KfkQns9bRk3f',$,$,$,(#221),#storyPointer);
    f.write("#" + str(ifcPointer) +"= IFCRELCONTAINEDINSPATIALSTRUCTURE('" + getGUID() + "',$,$,$,(" + storyElements + "),#" + str(storyPointer) + ");\n")
    ifcPointer +=1

# Main Function Call
# buildingData is the data to be placed in the IFC
def compile(buildingData):
    # Initialize File and Building Data
    f = open(filename, "w")
    global unitModifier
    global ifcPointer
    # Set up IFC Template
    f.write(ifcTemplate)

    if(buildingData.isImperial):
        unitModifier = 12.0
        f.write(ifcImperial)
    else:
        f.write(ifcMetric)
        unitModifier = 100.0

    for type in buildingData.buildingSchedule.listOfWallTypes:
        #297= IFCMATERIAL('Default Wall',$,'Materials');
        f.write("#" + str(ifcPointer) + "= IFCMATERIAL('" + type.name + "',$,'Materials');\n")
        ifcPointer +=1
        #313= IFCMATERIALLAYER(#297,0.666666666666667,$,'Layer',$,'Materials',$);
        f.write("#" + str(ifcPointer) + "= IFCMATERIALLAYER(#" + str(ifcPointer-1) + "," + str(type.thickness/unitModifier) + ",$,'Layer',$,'Materials',$);\n")
        ifcPointer +=1
        #315= IFCMATERIALLAYERSET((#313),'Basic Wall:Generic - 8"',$);
        f.write("#" + str(ifcPointer) + "= IFCMATERIALLAYERSET((#"+ str(ifcPointer-1) + "),'" + type.name + "',$);\n")
        ifcPointer +=1
        #406= IFCMATERIALLAYERSETUSAGE(#315,.AXIS2.,.NEGATIVE.,0.333333333333333,$);
        f.write("#" + str(ifcPointer) + "= IFCMATERIALLAYERSETUSAGE(#" + str(ifcPointer-1) + ",.AXIS2.,.NEGATIVE.," + str(type.thickness/(unitModifier*2)) + ",$);\n")
        type.ifcName = ifcPointer
        ifcPointer +=1

    i = 0
    for Story in buildingData.listOfStories:
        i += 1
        compileStory(f, Story, i)

    # Add closing lines to IFC file
    f.write(ifcCloser)
    # Close IFC File, end of function
    f.close()
