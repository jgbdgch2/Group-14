# TODO: Set Up IFCUNITASSIGNMENT
# TODO: set up GUID generation
# TODO: Walls
# TODO: Assign Cross Section Properties to Walls
# TODO: Doors
# TODO: Windows

import building_data
import uuid
import string

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

# GUIDS for template use
projectID = getGUID()
siteID = getGUID()
buildingID = getGUID()
rel1ID = getGUID()
rel2ID = getGUID()

# #99 references IFCUNITASSIGNMENT
ifcTemplate = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('%(filename)s','',(''),(''),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1= IFCCARTESIANPOINT((0.,0.,0.));
#2= IFCAXIS2PLACEMENT3D(#1,$,$);

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

# TODO set up IFC Units
# IFC units shall be contained within positions #25-#99
ifcImperail = """
#99= IFCUNITASSIGNMENT(());
"""

ifcMetric = """
#25=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#99= IFCUNITASSIGNMENT((#25));
"""

def compileStory(Story, ifcPointer):
    # Placeholder Variables
    PLACEHOLDER_ELEVATION = 0

    storyPointer = ifcPointer;
    storyLocalPlacement = ifcPointer+3;

    f.write("#" + str(ifcPointer) + "= IFCBUILDINGSTOREY('" + getGUID() + "',$,'Level 1',$,'Level:Level 1, #" + str(storyLocalPlacement) + ",$,'Level 1',.ELEMENT.,0.);\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCCARTESIANPOINT((0.,0.,"+ str(PLACEHOLDER_ELEVATION) + ".));\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCAXIS2PLACEMENT3D(#" + str(ifcPointer-1) + ",$,$);\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCLOCALPLACEMENT(#11,#" + str(ifcPointer-1) + ");\n")
    ifcPointer +=1
    f.write("#" + str(ifcPointer) + "= IFCRELAGGREGATES('" + getGUID() + "'),$,$,$,#7,#" + str(storyPointer) + "));\n")
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
        f.write("ifcImperial")
    else:
        f.write("ifcMetric")

    # Initialize pointer to track location in IFC file
    # Points to next available location in the IFC
    # 100 is the fist available location after the units are written to the file
    ifcPointer = 100

    for Story in buildingData.listOfStories:
        ifcPointer = compileStory(Story, ifcPointer)



    # Close IFC File, end of function
    f.close()

# Test Code
buildingData = building_data.BuildingData()

# Need help with line 103, measurement_system_flag should be unique to the project probably?
# How do obtain the value of measurement_system_flag from the buildingdata?
# Clarify how elevations interract with storys.
# My functionality will be to have the bottom elevation of each story be used as the actual story height and be the story with all the information
# The top elevation will be added in as an IFCBUILDINGSTOREY but it will not contain any actual building elements and exists to be displayed in revit
# Decide on naming structure for the elevations
compile(buildingData)
