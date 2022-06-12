import uuid
import string
import math
import building_data

# TODO ensure output file goes to correct location
filename = "default_filename.ifc"

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

def compileStory(f, Story, ifcPointer):
    # Placeholder Variables
    PLACEHOLDER_ELEVATION = 0.0

    storyPointer = ifcPointer;
    storyLocalPlacement = ifcPointer+3;

    f.write("#" + str(ifcPointer) + "= IFCBUILDINGSTOREY('" + getGUID() + "',$,'Level 1',$,'Level:Level 1',#" + str(storyLocalPlacement) + ",$,'Level 1',.ELEMENT.,0.);\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINT((0.,0.,"+ str(PLACEHOLDER_ELEVATION) + "));\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCAXIS2PLACEMENT3D(#" + str(ifcPointer-1) + ",$,$);\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCLOCALPLACEMENT(#11,#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCRELAGGREGATES('" + getGUID() + "',$,$,$,#7,(#" + str(storyPointer) + "));\n")
    ifcPointer +=1

    for Wall in Story.listOfWalls:
        ifcPointer = compileWall(f, Wall, ifcPointer, storyPointer, storyLocalPlacement)

    return ifcPointer

def getWallCoords(Wall):
    xZero = Wall.xZero / 12
    yZero = Wall.yZero / 12
    xOne = Wall.xOne / 12
    yOne = Wall.yOne / 12
    thickness = Wall.getThickness() / 12
    length = math.sqrt((xZero - xOne)**2 + (yZero - yOne)**2)
    offsetRatio = thickness / (2 * length)

    x1 = xZero + ((yZero - yOne) * offsetRatio)
    x2 = xZero - ((yZero - yOne) * offsetRatio)
    x3 = xOne  + ((yZero - yOne) * offsetRatio)
    x4 = xOne  - ((yZero - yOne) * offsetRatio)
    y1 = yZero + ((xZero - xOne) * offsetRatio)
    y2 = yZero - ((xZero - xOne) * offsetRatio)
    y3 = yOne  + ((xZero - xOne) * offsetRatio)
    y4 = yOne  - ((xZero - xOne) * offsetRatio)

    coords = "(%(x1)f,%(y1)f),(%(x2)f,%(y2)f),(%(x4)f,%(y4)f),(%(x3)f,%(y3)f),(%(x1)f,%(y1)f)" % locals()

    return coords

# TODO: Assign Cross Section Properties to Walls
def compileWall(f, Wall, ifcPointer, storyPointer, storyLocalPlacement):
    #200= IFCCARTESIANPOINTLIST2D(((12.,1.),(0.,1.),(0.,-1.),(12.,-1.),(12.,1.)));
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINTLIST2D((" + getWallCoords(Wall) + "));\n")
    ifcPointer +=1
    #201= IFCINDEXEDPOLYCURVE(#200, $, .F.);
    f.write("#" + str(ifcPointer) + "= IFCINDEXEDPOLYCURVE(#" + str(ifcPointer-1) + ", $, .F.);\n")
    ifcPointer +=1
    #202= IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,$,#201);
    f.write("#" + str(ifcPointer) + "= IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,$,#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    #203= IFCEXTRUDEDAREASOLID(#202, #2, #3, 8.);
    PLACEHOLDERHEIGHT = 8.0
    f.write("#" + str(ifcPointer) + "= IFCEXTRUDEDAREASOLID(#" + str(ifcPointer-1) + ", #2, #3, " + str(PLACEHOLDERHEIGHT) + ");\n") # INCOMPLETE, NEEDS WALL HEIGHT
    ifcPointer +=1
    #204= IFCSHAPEREPRESENTATION(#22, 'Body', 'SweptSolid', (#203));
    f.write("#" + str(ifcPointer) + "= IFCSHAPEREPRESENTATION(#22, 'Body', 'SweptSolid', (#" + str(ifcPointer-1) + "));\n")
    ifcPointer +=1

    #220= IFCPRODUCTDEFINITIONSHAPE($,$,(#204));
    f.write("#" + str(ifcPointer) + "= IFCPRODUCTDEFINITIONSHAPE($,$,(#" + str(ifcPointer-1) + "));\n")
    ifcPointer +=1
    #221= IFCWALL('1btdOju4n3KfkQnsDbRkrg', $, $, $, $, #storyLocalPlacement, #220, '2712', .NOTDEFINED.);
    f.write("#" + str(ifcPointer) + "= IFCWALL('" + getGUID() + "', $, $, $, $, #" + str(storyLocalPlacement) + ", #" + str(ifcPointer-1) + ", '2712', .NOTDEFINED.);\n") # TODO figure out what 2712 means
    ifcPointer +=1
    #222= IFCRELCONTAINEDINSPATIALSTRUCTURE('1btdOju4n3KfkQns9bRk3f',$,$,$,(#221),#storyPointer);
    f.write("#" + str(ifcPointer) +"= IFCRELCONTAINEDINSPATIALSTRUCTURE('" + getGUID() + "',$,$,$,(#" + str(ifcPointer-1) + "),#" + str(storyPointer) + ");\n")
    ifcPointer +=1

    return ifcPointer

# Main Function Call
# buildingData is the data to be placed in the IFC
def compile(buildingData):
    # Initialize File and Building Data
    f = open(filename, "w")

    # Set up IFC Template
    f.write(ifcTemplate)
    # if(buildingData.measurement_system_flag == "IMPERIAL_UNITS"):
    # Placeholder used until measurement_system_flag functionality is clarified
    if(True):
        f.write(ifcImperial)
    else:
        f.write(ifcMetric)

    # Initialize pointer to track location in IFC file
    # Points to next available location in the IFC
    # 100 is the fist available location after the units are written to the file
    ifcPointer = 100

    for Story in buildingData.listOfStories:
        ifcPointer = compileStory(f, Story, ifcPointer)

    # Add closing lines to IFC file
    f.write(ifcCloser)
    # Close IFC File, end of function
    f.close()
