import PySimpleGUI as sg
import os.path
import PIL.Image
import io
import base64
import ctypes
import platform
import zipfile
from pdf2image import convert_from_path, convert_from_bytes
import tkinter
import copy
import math
import cv2

import building_data as bd
import ifc_compiler as ifc
import measurement_marker_detector as mmd

wall_objects = ('Door', 'Window') # This doesn't change and is used throughout the GUI

def create_feature(info_dict, buildingData, story_id):
    type = info_dict['-FEATURE TYPE-']
    if type == 'Wall':
        # make a wall object
        wall_type = bd.WallType(1, name=info_dict['-FEATURE NAME-'],
                                thickness=info_dict['-FEATURE WIDTH-'])
        wall = bd.Wall(pos=(120.0, 4.0), length=info_dict['-FEATURE LENGTH-'],
                       angle=info_dict['-FEATURE ANGLE-'], wallType=wall_type)
        buildingData.listOfStories[story_id].append(wall)
        return wall
    elif type == 'Door':
        # make a door object
        door_type = bd.DoorType(typeNumber=1, name=info_dict['-FEATURE NAME-'],
                    height=1.0, width=info_dict['-FEATURE WIDTH-'])
        door = bd.Door(position=1.5, hingePos=1, doorType=door_type)
        wall_attach = info_dict['-Wall-']
        wall_attach.append(door)
    elif type == 'Window':
        # make a window object
        window_type = bd.WindowType(typeNumber=1, name=info_dict['-FEATURE NAME-'],
                                    height=1.0, sillHeight=1.0)
        window = bd.Window(position=1.5, sillHeight=1.0, directionFacing=1,
                           windowType=window_type)
        wall_attach = info_dict['-Wall-']
        wall_attach.append(window)

def make_black(image):
    image = image.convert('RGBA')

    # Transparency
    newImage = []
    for item in image.getdata():
        if item == (0 ,0, 0, 0):
            newImage.append((255, 255, 255, 0))
        elif item < (255, 255, 255, 255):
            newImage.append((0, 0, 0, 255))
        else:
            newImage.append(item)

    image.putdata(newImage)
    return image

def make_transparent_edges(image):
    # Transparency
    newImage = []
    for item in image.getdata():
        if item[:3] == (250, 150, 50):
            newImage.append((255, 255, 255, 0))
        else:
            newImage.append(item)

    image.putdata(newImage)
    return image

def resize_img(img, resize):
    cur_width, cur_height = img.size
    new_width, new_height = resize
    scale = min(new_height/cur_height, new_width/cur_width)
    img = img.resize((int(cur_width*scale), int(cur_height*scale)), PIL.Image.ANTIALIAS)
    return img

# function for DPI awareness for increasing GUI resolution
def make_dpi_aware():
    if int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

# Image handling resize
def image_formating(file_or_bytes, resize=None):
    '''
    Turns into  PNG format so that it can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    '''
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(dataBytesIO)

    if resize:
        img = resize_img(img, resize)

    return img

# Image handling
def convert_to_bytes(img):
    '''
    Will convert into bytes.
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    '''
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

def popup_text(msg):
    layout = [[sg.Text(msg)],
              [sg.Input(key='-IN-')],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('Page Number', layout, finalize=True)

    window['-IN-'].set_focus()
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'):
        return ''
    window.close()

    return values['-IN-']

def get_user_digit(message):
    page_num = popup_text(message)
    if page_num != '' and page_num.isdigit():
        return int(page_num)
    else:
        popup_info('Page Number Required!')
        return None

def get_folder_name(name):
    if '\\' in name:
        folder = name.split('\\')
    else:
        folder = name.split('/')
    return folder[-1]

def get_file_name(test_name=''):
    folder = os.getcwd()
    layout = [[sg.Text('Folder:', size =(6, 1)),
               sg.Text(get_folder_name(folder), size =(60, 1), key='-NAME-')],
              [sg.Text('File Name:', size =(10, 1)), sg.Input(test_name, key='-FILE NAME-'),
               sg.Text('.ifc', size =(4, 1)), sg.FolderBrowse(target='-FOLDER NAME-')],
              [sg.Input(key='-FOLDER NAME-', enable_events=True, visible=False)], # This allows for events on folder browse!!
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('Export IFC File', layout).finalize()

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel') or event == None:
            window.close()
            return None
        elif event == 'Submit':
            break
        elif event == '-FOLDER NAME-':
            folder = values['-FOLDER NAME-']
            window['-NAME-'].update(get_folder_name(values['-FOLDER NAME-']))
            window.refresh()

    window.close()
    folder = folder.replace('/', '\\')
    file = values['-FILE NAME-']
    if event in (sg.WIN_CLOSED, 'Exit', 'Cancel') or file == None or file == '':
        return None
    elif not file.endswith('.ifc'):
        values['-FILE NAME-'] = file + '.ifc'
    return os.path.join(folder, values['-FILE NAME-'])

def popup_info(info):
    count = 0
    max = 0
    max_width = 75
    min_width = 20
    for char in info:
        if char != '\n':
            count += 1
            if count > max:
                max = count
        else:
            count = 0
    wide = max
    if wide > max_width:
        wide = max_width
    if wide < min_width:
        wide = min_width
    long = len(info) // max_width
    long += 1 + info.count('\n')
    layout = [[sg.Text(info, size =(wide, long))],
              [sg.Button(' OK ')]]

    window = sg.Window('Window', layout, element_justification='c',
                       return_keyboard_events=True, keep_on_top=True).finalize()
    event, values = window.read()
    window.close()

def get_pdf_name():
    # PDF file_types does not work on macs (according to stackoverflow)
    filename = sg.popup_get_file('Will not see this message', no_window=True, file_types=(("PDF Files", "*.pdf"),))
    if filename == '':
        return None
    else:
        return filename

def get_pdf_as_image(new_size, filename, page_num):
    try:
        temp_image = None
        images = convert_from_path(filename, size=new_size)
        zip_name = "{}1.zip".format(filename[:-4])
        with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as new_zip:
            for i, page in enumerate(images):
                png_name = "{}1_{}.png".format(filename[:-4], i+1)
                png_folder = os.path.join(filename, '..', png_name)
                zip_folder = os.path.join(filename, '..', zip_name)
                if i+1 == page_num:
                    page.save(png_name, "PNG")
                    new_zip.write(png_name, arcname=png_name)
                    temp_image = image_formating(png_folder, resize=(new_size, new_size))
                    os.remove(png_folder)
                    break
    except Exception as E:
        print('** Error {} **'.format(E))# get file popup was cancelled
    os.remove(zip_folder)
    return temp_image

def convert_to_centimeters(str):
    value = []
    if str == '' or not str[0].isdigit() or not str[-1] in ('M', 'm'):
        return 0.0
    for char in str:
        if char.isdigit() or char == '.':
            value.append(char)
        elif str.endswith('MM') or str.endswith('mm'):
            return float(''.join(value)) / 1000
        elif str.endswith('CM') or str.endswith('cm'):
            return float(''.join(value))
        elif str.endswith('M') or str.endswith('m'):
            return float(''.join(value)) * 100
        else:
            return 0.0

def convert_to_inches(str):
    feet = []
    inches = []
    is_feet = True
    if str == '' or not str[0].isdigit():
        return 0.0
    if not "'" in str:
        is_feet = False
        if not '"' in str:
            return 0.0
    if str.endswith("'") and not '"' in str:
        if str[:-1].isdigit():
            return float(str[:-1]) * 12
    if str.endswith('"'):
        for char in str:
            if char.isdigit() and is_feet:
                feet.append(char)
            elif (char.isdigit() or char == '.') and not is_feet:
                inches.append(char)
            elif char == "'":
                is_feet = False
            elif char == '"':
                if len(feet) > 0:
                    return float(''.join(feet)) * 12 + float(''.join(inches))
                return float(''.join(inches))
    return 0.0

def feature_extractor_window(available_features):
    layout = [[sg.Text('Information Required for Feature Extraction')],
              [sg.Text('Feature Name', size =(15, 1)), sg.InputText(key='-FEATURE NAME-')],
              [sg.Text('Feature Type:          '), sg.Combo(available_features, size=(10, 15),
               key='-FEATURE TYPE-', readonly=True)],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('Feature Extraction Tool', layout)
    event, values = window.read()
    window.close()
    if event in (sg.WIN_CLOSED, 'Exit', 'Cancel') or values['-FEATURE TYPE-'] == '':
        return None
    return values

def story_input_tool(name):
    layout = [[sg.Text('Please enter the new story information')],
              [sg.Text('Story Name', size =(15, 1)), sg.InputText(name, key='-STORY NAME-')],
              [sg.Text('Bottom Elevation', size =(15, 1)), sg.InputText(key='-BOTTOM ELEVATION-'),
                        sg.Radio('Imperial', "LENGTH1", default=True, key='-BOTTOM IS IMPERIAL-'),
                        sg.Radio('Metric', "LENGTH1", default=False)],
              [sg.Text('Top Elevation', size =(15, 1)), sg.InputText(key='-TOP ELEVATION-'),
                        sg.Radio('Imperial', "LENGTH2", default=True, key='-TOP IS IMPERIAL-'),
                        sg.Radio('Metric', "LENGTH2", default=False)],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('Story Input Tool', layout)
    event, values = window.read()
    window.close()
    if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
        return None
    if not values['-BOTTOM IS IMPERIAL-']:
        values['-BOTTOM ELEVATION-'] = convert_to_centimeters(values['-BOTTOM ELEVATION-'])
        values['-BOTTOM ELEVATION-'] *= 0.393701
    else:
        values['-BOTTOM ELEVATION-'] = convert_to_inches(values['-BOTTOM ELEVATION-'])
    if not values['-TOP IS IMPERIAL-']:
        values['-TOP ELEVATION-'] = convert_to_centimeters(values['-TOP ELEVATION-'])
        values['-TOP ELEVATION-'] *= 0.393701
    else:
        values['-TOP ELEVATION-'] = convert_to_inches(values['-TOP ELEVATION-'])
    return values

def measure_tool_input_window(message):
    layout = [[sg.Text(message)],
              [sg.Text('Length', size =(15, 1)), sg.InputText(key='-TOOL LENGTH-'),
                        sg.Radio('Imperial', "LENGTH", default=True, key='-LENGTH IS IMPERIAL-'),
                        sg.Radio('Metric', "LENGTH", default=False)],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('Distance Input', layout)
    event, values = window.read()
    window.close()
    if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
        return None
    if not values['-LENGTH IS IMPERIAL-']:
        values['-TOOL LENGTH-'] = convert_to_centimeters(values['-TOOL LENGTH-'])
        values['-TOOL LENGTH-'] *= 0.393701
    else:
        values['-TOOL LENGTH-'] = convert_to_inches(values['-TOOL LENGTH-'])
    return values

def feature_input_window(feat_list, feature_name):
    message = ('Please enter {} information').format(feature_name)
    layout = [[sg.Text(message)],
              [sg.Text('Feature Name', size =(15, 1)), sg.InputText(key='-FEATURE NAME-')],
              [sg.Text('Length', size =(15, 1)), sg.InputText(key='-FEATURE LENGTH-'),
                        sg.Radio('Imperial', "LENGTH", default=True, key='-LENGTH IS IMPERIAL-'),
                        sg.Radio('Metric', "LENGTH", default=False)],
              [sg.Text('Width', size =(15, 1)), sg.InputText(key='-FEATURE WIDTH-'),
                        sg.Radio('Imperial', "WIDTH", default=True, key='-WIDTH IS IMPERIAL-'),
                        sg.Radio('Metric', "WIDTH", default=False)],
              [sg.Text('Angle', size =(15, 1)), sg.InputText(key='-FEATURE ANGLE-')],
              [sg.Text('Feature Type:          '), sg.Combo(feat_list[feature_name], size=(10, 15),
               key='-FEATURE TYPE-', readonly=True)],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('New Feature', layout)
    event, values = window.read()
    window.close()
    if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
        return None
    if not values['-LENGTH IS IMPERIAL-']:
        values['-FEATURE LENGTH-'] = convert_to_centimeters(values['-FEATURE LENGTH-'])
        values['-FEATURE LENGTH-'] *= 0.393701
    else:
        values['-FEATURE LENGTH-'] = convert_to_inches(values['-FEATURE LENGTH-'])
    if not values['-WIDTH IS IMPERIAL-']:
        values['-FEATURE WIDTH-'] = convert_to_centimeters(values['-FEATURE WIDTH-'])
        values['-FEATURE WIDTH-'] *= 0.393701
    else:
        values['-FEATURE WIDTH-'] = convert_to_inches(values['-FEATURE WIDTH-'])
    return values

def get_window_settings(settings):
    layout = [[sg.Text('Window Width Percent:', size =(20, 1))],
              [sg.Slider(range=(25, 100), default_value=settings[0]*100, size=(50, 10), orientation="h",
                         enable_events=True, key='-WIDTH PERCENT-')],
              [sg.Text('Window Height Percent:', size =(20, 1))],
              [sg.Slider(range=(25, 100), default_value=settings[1]*100, size=(50, 10), orientation="h",
                         enable_events=True, key='-HEIGHT PERCENT-')],
              [sg.Text('Blueprint Scaling (Only applied when importing):', size =(50, 1))],
              [sg.Slider(range=(25, 200), default_value=settings[2]*100, size=(50, 10), orientation="h",
                         enable_events=True, key='-IMAGE WINDOW PERCENT-')],
              [sg.Text('Blueprint Import Resolution (Only applied when importing):', size =(50, 1))],
              [sg.Slider(range=(1000, 10000), default_value=settings[3], size=(50, 10), orientation="h",
                         enable_events=True, key='-IMAGE RESOLUTION-')],
              [sg.Button('Reset to Default', key='-RESET-')],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('Window Settings', layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
            window.close()
            return None
        elif event == '-RESET-':
            window.close()
            return ''
        elif event == 'Submit':
            break

    window.close()
    values['-WIDTH PERCENT-']        = values['-WIDTH PERCENT-'] / 100
    values['-HEIGHT PERCENT-']       = values['-HEIGHT PERCENT-'] / 100
    values['-IMAGE WINDOW PERCENT-'] = values['-IMAGE WINDOW PERCENT-'] / 100
    values['-IMAGE RESOLUTION-']     = int(values['-IMAGE RESOLUTION-'])

    return values

def machine_learning_features(img, buildingData, y_pixel_ratio): # Testing code for machine learning extraction
    data = bd.testCode()
    for wall in data.listOfStories[0].listOfWalls:
        buildingData.listOfStories[0].append(wall)
    return buildingData

def get_feature_info(feature, wall_feature, wall_info):
    wall_feature['-DISTANCE-'] = feature.position
    wall_feature['-FEATURE ANGLE-'] = wall_info['-FEATURE ANGLE-']
    wall_feature['-X POS-'] = wall_info['-X POS-']
    wall_feature['-Y POS-'] = wall_info['-Y POS-']
    if wall_feature['-FEATURE-'] == 'Window':
        wall_feature['-FEATURE LENGTH-'] = feature.windowType.width
    elif wall_feature['-FEATURE-'] == 'Door':
        wall_feature['-FEATURE LENGTH-'] = feature.doorType.width
    else:
        print('Feature not supported in DRAW')
        exit(0)
    return wall_feature

def get_building_wall_info(building_wall):
    feature_info = {'-X POS-': building_wall.xPos,
                    '-Y POS-': building_wall.yPos,
                    '-FEATURE ANGLE-': building_wall.angle,
                    '-FEATURE LENGTH-': building_wall.length,
                   }
    return feature_info

def graph_draw_from_data(story, graph, feature_dict, pixel_ratio, folder, feature_images):
    for wall in story.listOfWalls:
        draw_wall_and_other(graph, folder, feature_images, wall, feature_dict, pixel_ratio)

def draw_wall_and_other(graph, folder, feature_images, wall, feature_dict, pixel_ratio):
    wall_info = get_building_wall_info(wall)
    wall_info['-FEATURE-'] = 'Wall'
    fig_id = draw_feature(graph, folder, feature_images, wall_info, pixel_ratio)
    feature_dict[fig_id] = wall
    door_info = {}
    window_info = {}
    door_info['-FEATURE-'] = 'Door'
    window_info['-FEATURE-'] = 'Window'
    for door in wall.listOfDoors:
        door_info = get_feature_info(door, door_info, wall_info)
        fig_id = draw_feature(graph, folder, feature_images, door_info, pixel_ratio)
        feature_dict[fig_id] = door
    for window in wall.listOfWindows:
        window_info = get_feature_info(window, window_info, wall_info)
        fig_id = draw_feature(graph, folder, feature_images, window_info, pixel_ratio)
        feature_dict[fig_id] = window

def draw_feature(graph, folder, feature_images, feature_info, pixel_ratio):
    feature_size = int(feature_info['-FEATURE LENGTH-'] * pixel_ratio)
    x = feature_info['-X POS-'] * pixel_ratio
    y = feature_info['-Y POS-'] * pixel_ratio
    rotate_angle = feature_info['-FEATURE ANGLE-']
    shape = feature_size, feature_size
    feature_path = os.path.join(folder, feature_images[feature_info['-FEATURE-']])
    image_in = image_formating(feature_path, resize=shape)
    feature = resize_img(image_in, shape)
    feature = make_black(feature)
    feature = feature.rotate(rotate_angle, fillcolor=(250, 150, 50), expand=True)
    shift = get_distance_from_center(feature)

    if rotate_angle % 90 != 0:
        feature = make_transparent_edges(feature)

    if feature_info['-FEATURE-'] in wall_objects:
        x, y = get_coord(x, y, rotate_angle, feature_info['-DISTANCE-'] * pixel_ratio)

    fig_id = graph.draw_image(data=convert_to_bytes(feature),
                              location=((x - shift[0]), (y + shift[1])))
    return fig_id

def get_coord(x, y, rotate_angle, distance):
    angle = math.radians(rotate_angle)
    x_pos = math.cos(angle) * distance
    y_pos = math.sin(angle) * distance
    x += int(x_pos)
    y += int(y_pos)
    return x, y

def get_distance_from_center(img):
    return img.size[0] // 2, img.size[1] // 2

def switch_to_other_graph(window, name1, graph1, name2, graph2, window_size):
    graph1.set_size((0,0)) # This will free up the space for graph2
    graph2.set_size(window_size)
    window.refresh() # This must be refreshed before making anything invisible
    window.Element(name1).Update(visible=False)
    window.Element(name2).Update(visible=True)

def main_gui():
    # --------------------------------- Define Layout ---------------------------------
    # Right click menu for graphs
    graph1_menu_def = ['&Right', ['Rotate', 'Set Distance']]
    graph2_menu_def = ['&Right', ['Edit', 'Duplicate', 'Insert', 'Delete', 'Toggle']]
    # First is the top menu
    menu_def = [['&File', ['&New       ALT-N', '&Save      ALT-S', '&Load Recent', 'E&xit']],
                ['&Edit', ['Extract Feature', '!Add Story']],
                ['Se&ttings', ['&Window Settings', '!Help']]]

    # Second the window layout...2 columns
    left_col = [[sg.Text('Feature List', size=(30, 1), key='-FOLDER-')],
                [sg.Listbox(values=[], enable_events=True, size=(30,20),key='-FILE LIST-')],# This creates a listbox for the images in the folder
                [sg.Button('add feature', key='-Feature-')], # This allows the features to be added to the converted blueprint
                [sg.Button('Convert', key='-Convert-')],
                [sg.Listbox(values=[], enable_events=True, size=(30,5),key='-STORY LIST-')],
                [sg.Button('Export .ifc', key='-EXPORT IFC-')]]

    # Creates the column for the image
    images_col = [[sg.Push(), sg.Text('Open a new project', key='-TOUT-'), sg.Push()],
                  [sg.Graph(
                      canvas_size=(0, 0),
                      graph_bottom_left=(0, 0),
                      graph_top_right=(0, 0),
                      key="-GRAPH1-",
                      change_submits=True,  # mouse click events
                      right_click_menu=graph1_menu_def,
                      background_color='white',
                      drag_submits=True)],
                 # [sg.Text('_'*60, key='-Hdivider-')],
                  [sg.Graph(
                      canvas_size=(0, 0),
                      graph_bottom_left=(0, 0),
                      graph_top_right=(0, 0),
                      key="-GRAPH2-",
                      change_submits=True,  # mouse click events
                      right_click_menu=graph2_menu_def,
                      background_color='white',
                      drag_submits=True)]]


    # -------------------------------- Full layout ------------------------------------
    layout = [[sg.Menu(menu_def, tearoff=False, key='-MENU BAR-')],
              [sg.vtop(sg.Column(left_col, element_justification='c')), sg.VSeperator(),
               sg.Column(images_col, element_justification='c')]]

    # --------------------------------- Create Window ---------------------------------
    window = sg.Window('Blueprint Conversion', layout, resizable=False).finalize()
    window.Maximize()
    window.Element('-STORY LIST-').Update(visible=False)
    window.Element('-GRAPH1-').Update(visible=False)
    window.Element('-GRAPH2-').Update(visible=False)
    window.Element('-Convert-').Update(visible=False)
    window.Element('-EXPORT IFC-').Update(visible=False)

    # --------------------------------- Add feature objects ---------------------------
    story = 0
    buildingData = bd.BuildingData()
    feature_images = {'Door':'door_right.gif', 'Wall':'wall.gif', 'Window':'window.gif'}
    available_features = ['Wall', 'Door', 'Window']
    feat_list_wall = ['Concrete', 'Wood', 'Plaster']
    feat_list_door = ['Steel', 'Wood', 'Screen']
    feat_list_window = ['Single Pane', 'Double Pane', 'French']
    feat_types = {'Wall':feat_list_wall, 'Door':feat_list_door, 'Window':feat_list_window}

    folder = os.getcwd()
    folder = os.path.join(folder, 'blueprint_features')
    '''
    try:
        file_list = os.listdir(folder)         # get list of files in folder
    except:
        file_list = []
    fnames = [f for f in file_list if os.path.isfile(
        os.path.join(folder, f)) and f.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".bmp", ".gif"))] # .gif supports transparency
    '''
    window['-FILE LIST-'].update(available_features) # Add the list of available features

    # ----- Run the Event Loop -----
    graph1 = window["-GRAPH1-"]
    graph1.bind('<Button-3>', '+RIGHT1+')
    graph2 = window["-GRAPH2-"]
    graph2.bind('<Button-3>', '+RIGHT2+')
    # --------------------------------- Initialize Variables------------------------
    # sg.user_settings_delete_filename()
    if sg.user_settings_file_exists():
        settings = sg.UserSettings()
        width_percent = settings['-WIDTH PERCENT-']
        height_percent = settings['-HEIGHT PERCENT-']
        image_window_percent = settings['-IMAGE PERCENT-']
        image_resolution = settings['-IMAGE RESOLUTION-']
    else:
        settings = sg.UserSettings()
        settings['-WIDTH PERCENT-']    = width_percent        = 0.84     # What percent of the window width is graph
        settings['-HEIGHT PERCENT-']   = height_percent       = 0.94     # What percent of the window height is graph
        settings['-IMAGE PERCENT-']    = image_window_percent = 1.20     # Image scaling
        settings['-IMAGE RESOLUTION-'] = image_resolution     = 10000    # Blueprint original resolution

    window_width, window_height = window.get_screen_dimensions()
    window_size = (window_width * width_percent, window_height * height_percent)
    dragging1 = dragging2 = crop = set_distance = extract_feature = False
    start_point = end_point = filename = feature_name = select_fig = img = None
    orig_img = a_set = bound_top = bound_bottom = fig = a_point = y_pixel_ratio = None
    x_pixel_ratio = feature_path = user_distance = prior_rect = start_point1 = None
    end_point1 = graph2 = start_point2 = data = new_size = None
    feature_dict = {}
    # --------------------------------- Event Loop ---------------------------------
    while True:
        event, values = window.read()

        if bound_top and event != '-FILE LIST-': # delete the bounds if they exist
            # delete bounds
            graph2.delete_figure(bound_top)
            graph2.delete_figure(bound_bottom)
            bound_top = bound_bottom = None
        if event in (sg.WIN_CLOSED, 'Exit'): # Closes the App
            break
        if event == 'New       ALT-N': # Creates a new blueprint conversion environment
            new_size = int(window_size[1] * image_window_percent)
            mult = image_resolution // new_size
            pdf_file = get_pdf_name()
            if pdf_file:
                page_num = get_user_digit('Enter Blueprint Page Number:')
            if pdf_file and page_num:
                window.perform_long_operation(lambda :
                                  get_pdf_as_image(new_size*mult, pdf_file, page_num),
                                  '-LOADED PDF-')
                story_info = story_input_tool('First Floor')
                while not story_info or story_info['-BOTTOM ELEVATION-'] >= story_info['-TOP ELEVATION-']:
                    if story_info == None:
                        popup_info('Story Information must be correctly added')
                        story_info = story_input_tool('First Floor')
                    else:
                        story_info = story_input_tool(story_info['-STORY NAME-'])
                buildingData.appendStory(bottomElevation = story_info['-BOTTOM ELEVATION-'],
                                        topElevation = story_info['-TOP ELEVATION-'])
                popup_info('Searching for Blueprint...')
                start_point = end_point = filename = feature_name = select_fig = img = None
                orig_img = a_set = bound_top = bound_bottom = fig = a_point = y_pixel_ratio = None
                x_pixel_ratio = feature_path = user_distance = prior_rect = start_point1 = None
                end_point1 = None
                feature_dict = {}
        elif event == '-LOADED PDF-':
            if graph2:
                graph2 = None
                window.Element('-GRAPH2-').Update(visible=False)
            orig_img = values[event]
            if not orig_img:
                popup_info('Page Not Found!')
                continue
            img = resize_img(orig_img, (new_size, new_size))
            graph1 = window["-GRAPH1-"]  # type: sg.Graph
            graph1.erase()
            graph1.set_size(window_size)
            graph1.change_coordinates((0,0), window_size)
            graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
            window['-TOUT-'].update(visible=False)
            window.Element('-GRAPH1-').Update(visible=True)
            popup_info('Select the area of interest.')
            crop = True
        elif event == '-FILE LIST-':    # A file was chosen from the listbox
            try:
                feature_name = values['-FILE LIST-'][0]
                feature_path = os.path.join(folder, feature_images[feature_name])
            except Exception as E:
                print('** Error {} **'.format(E)) # something weird happened making the full filename
        elif event == '-Convert-' and img is not None:    # There is a file to be converted
            window.perform_long_operation(lambda :
                              machine_learning_features(img, buildingData, x_pixel_ratio),
                              '-LOADED EXTRACTION-')
            blueprint_2_image = copy.deepcopy(img)
            graph2 = window["-GRAPH2-"]  # type: sg.Graph
            graph2.set_size(window_size)
            graph2.change_coordinates((0,0), window_size)
            blueprint_2_ID = graph2.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
            switch_to_other_graph(window, '-GRAPH1-', graph1, '-GRAPH2-', graph2, window_size)
            window.Element('-Convert-').Update(visible=False)
            window.Element('-EXPORT IFC-').Update(visible=True)
        elif event == "-LOADED EXTRACTION-":
            popup_info('Blueprint feature extraction complete!')
            graph_draw_from_data(buildingData.listOfStories[story], window['-GRAPH2-'],
                                 feature_dict, x_pixel_ratio, folder, feature_images)
        elif event == "-GRAPH1-":  # if there's a "Graph" event, then it's a mouse
            x, y = values["-GRAPH1-"]
            if not dragging1:
                start_point1 = (x, y)
                dragging1 = True
            else:
                end_point1 = (x, y)
            graph1 = window["-GRAPH1-"]
            if prior_rect:
                graph1.delete_figure(prior_rect)
            if None not in (start_point1, end_point1) and (crop or extract_feature):
                prior_rect = graph1.draw_rectangle(start_point1, end_point1, line_width=4, line_color='red')
        elif event == "-GRAPH2-":  # if there's a "Graph" event, then it's a mouse
            x, y = values["-GRAPH2-"]
            if not dragging2:
                start_point2 = (x, y)
                drag_figures = graph2.get_figures_at_location((x,y))
                dragging2 = True
                last2xy = x, y
            else:
                end_point2 = (x, y)
            delta_x, delta_y = x - last2xy[0], y - last2xy[1]
            last2xy = x,y
            if len(drag_figures) > 0:
                select_fig = drag_figures[-1] # This will always be the figure on top
            else:
                select_fig = None
            if blueprint_2_ID and select_fig == blueprint_2_ID: # check if initial blueprint
                select_fig = None
            if select_fig is not None:
                graph2.BringFigureToFront(select_fig) # when dragging a feature bring it to front of all others not selected
                graph2.move_figure(select_fig, delta_x, delta_y)
                graph2.update()
        elif event.endswith('+UP'):  # The dragging has ended because mouse up
            if dragging1:
                x, y = values["-GRAPH1-"]
                end_point1 = (x, y)
                start1_x, start1_y = start_point1
                if crop or extract_feature:
                    if x < start1_x:
                        left = x
                        right = start1_x
                    else:
                        left = start1_x
                        right = x
                    if y < start1_y:
                        bottom = img.size[1] - y
                        top = img.size[1] - start1_y
                    else:
                        bottom = img.size[1] - start1_y
                        top = img.size[1] - y
                    graph1 = window["-GRAPH1-"]  # type: sg.Graph
                    if sg.popup_ok_cancel('Area selected\nPress Cancel to redraw') != 'OK':
                        graph1.delete_figure(prior_rect)
                        dragging1 = False
                        continue
                    if crop:
                        orig_img = orig_img.crop((left*mult, top*mult, right*mult, bottom*mult))
                        img = resize_img(orig_img, (new_size, new_size))
                        graph1.erase()
                        graph1.set_size(window_size)
                        graph1.change_coordinates((0,0), window_size)
                        '''
                        horz_center = 0
                        vert_center = 0
                        if window_size[0] > img.size[0] and window_size[1] > img.size[1]:
                            horz_center = (window_size[1] - img.size[1]) // 2
                            vert_center = (window_size[0] - img.size[0]) // 2
                            graph1.draw_image(data=convert_to_bytes(img), location=(vert_center, img.size[1] + horz_center))
                        '''
                        graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
                        crop = False
                        popup_info('Pixel Ratios not set!\nRight click on Blueprint to use measurement  \ntool and set distance')
                    else:
                        # feature selection gets sent to the feature extractor here
                        h = orig_img.size[0] / img.size[0]
                        v = orig_img.size[1] / img.size[1]
                        '''
                        # Used for trouble shooting
                        feature_img = orig_img.crop((int(left*h), int(top*v), int(right*h), int(bottom*v)))
                        temp_img = resize_img(feature_img, (new_size, new_size))
                        graph1.erase()
                        graph1.set_size(temp_img.size)
                        graph1.change_coordinates((0,0), (temp_img.size[0], temp_img.size[1]))
                        temp = graph1.draw_image(data=convert_to_bytes(temp_img), location=(0, temp_img.size[1]))'''
                        feature_info = feature_extractor_window(available_features)
                        '''
                        # Used for trouble shooting
                        graph1.delete_figure(temp)
                        graph1.set_size(img.size)
                        graph1.change_coordinates((0,0), (img.size[0], img.size[1]))
                        graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
                        '''
                        if not feature_info:
                            popup_info('Feature information required for feature extraction')
                            continue
                        # Extract features here
                        # image, bounds, pixel_ratio, wall_string
                        # return wall object with no wall type just a float
                        top_left = int(left*h), int(top*v)
                        bottom_right = int(right*h), int(bottom*v)
                        bounding_box = top_left, bottom_right
                        try:
                            send_img = cv2.imread("./blueprint_features/save.png")
                        except Exception as E:
                            print('** Error {} **'.format(E))
                        wall_object = mmd.feature_data_extractor(send_img,
                                                                 bounding_box,
                                                                 x_pixel_ratio,
                                                                 feature_info['-FEATURE TYPE-'])
                        print(wall_object)
                        # Features extracted
                        graph1.delete_figure(prior_rect)
                        switch_to_other_graph(window, '-GRAPH1-', graph1, '-GRAPH2-', graph2, window_size)
                        extract_feature = False
                elif set_distance:
                    if not a_set:
                        a_set = end_point1
                        a_point = graph1.DrawCircle(a_set, 4, line_color='black', fill_color='white')
                        popup_info('Select point B')
                    else:
                        x_distance, y_distance = end_point1[0] - a_set[0], end_point1[1] - a_set[1]
                        b_point = graph1.DrawCircle(end_point1, 4, line_color='black', fill_color='white')
                        if x_distance < 0:
                            x_distance = x_distance*-1
                        if y_distance < 0:
                            y_distance = y_distance*-1
                        if x_distance > y_distance:
                            while not user_distance or user_distance['-TOOL LENGTH-'] == 0:
                                user_distance = measure_tool_input_window('Input x-axis distance')
                                if user_distance == None:
                                    break
                            if user_distance:
                                x_pixel_ratio = x_distance / user_distance['-TOOL LENGTH-']
                                popup_info('x-axis set')
                                print(x_pixel_ratio)
                        else:
                            while not user_distance or user_distance['-TOOL LENGTH-'] == 0:
                                user_distance = measure_tool_input_window('Input y-axis distance')
                                if user_distance == None:
                                    break
                            if user_distance:
                                y_pixel_ratio = y_distance / user_distance['-TOOL LENGTH-']
                                popup_info('y-axis set')
                                print(y_pixel_ratio)
                        graph1.delete_figure(a_point)
                        graph1.delete_figure(b_point)
                        if y_pixel_ratio and x_pixel_ratio:
                            # Save
                            settings['-X RATIO-'] = x_pixel_ratio
                            settings['-Y RATIO-'] = y_pixel_ratio
                            orig_img.save('./blueprint_features/save.png')
                            window.Element('-Convert-').Update(visible=True)
                        a_set = a_point = b_point = user_distance = None
                        set_distance = False
                info = 'start X: {} start Y: {}\nend X: {}  end Y: {}'.format(start1_x, start1_y, x, y)
                # popup_info('Dragging Done!\n{}'.format(info)) # This line can be used for trouble shooting mouse positions
                dragging1 = False
            else:
                x, y = values["-GRAPH2-"]
                end_point2 = (x, y)
                if not start_point2:
                    continue
                start2_x, start2_y = start_point2
                if not fig:
                    fig = graph2.get_figures_at_location((x,y))
                    if len(fig) > 0:
                        select_fig = fig[-1]
                    else:
                        select_fig = None
                if blueprint_2_ID and select_fig == blueprint_2_ID: # check if initial blueprint
                    select_fig = None
                if select_fig:
                    # Draw the bounds around the image
                    bounds = graph2.get_bounding_box(select_fig)
                    bound_top = graph2.DrawCircle(bounds[0], 7, line_color='black', fill_color='white')
                    bound_bottom = graph2.DrawCircle(bounds[1], 7, line_color='black', fill_color='white')
                info = 'start X: {} start Y: {}\nend X: {}  end Y: {}'.format(start2_x, start2_y, x, y)
                # popup_info('Dragging Done!\n{}'.format(info)) # This line can be used for trouble shooting mouse positions
                dragging2 = False
        elif event.endswith('+RIGHT2+'): # Right click on graph 2
            x, y = values["-GRAPH2-"]
            fig = graph2.get_figures_at_location((x,y))
            if len(fig) > 0:
                select_fig = fig[-1]
            else:
                select_fig = None
            if select_fig == blueprint_2_ID: # check if initial blueprint
                select_fig = None
            else:
                bounds = graph2.get_bounding_box(select_fig)
                bound_top = graph2.DrawCircle(bounds[0], 7, line_color='black', fill_color='white')
                bound_bottom = graph2.DrawCircle(bounds[1], 7, line_color='black', fill_color='white')
        elif  event == 'Delete':
            if select_fig is not None:
                graph2.delete_figure(select_fig)
                select_fig = None
        elif  event == 'Duplicate':
            if select_fig is None:
                popup_info('No Feature selected')
            else:
                print('this works')
        elif  event == 'Edit':
            if select_fig is None:
                popup_info('No Feature selected')
            else:
                print('this works')
        elif event in ('Insert', "-Feature-") and graph2 and feature_name:
            # Get the user input for the object by creating another window
            # Returns a dictionary of strings (if a key is not used: in list format)
            if feature_name in wall_objects and (not select_fig or type(feature_dict[select_fig]) != type(bd.Wall())):
                popup_info('Please select a Wall for inserting Doors and windows')
                continue
            feature_info = feature_input_window(feat_types, feature_name)
            if (feature_info == None or feature_info['-FEATURE LENGTH-'] == 0
                or feature_info['-FEATURE WIDTH-'] == 0):
                popup_info('Feature Length and Width Required')
                continue
            if feature_info['-FEATURE ANGLE-'] == '':
                feature_info['-FEATURE ANGLE-'] = 0.0
            else:
                feature_info['-FEATURE ANGLE-'] = float(feature_info['-FEATURE ANGLE-'])
            feature_info['-FEATURE TYPE-'] = feature_name
            if feature_name in wall_objects:
                feature_info['-Wall-'] = feature_dict[select_fig]
            rotate_angle = float(feature_info['-FEATURE ANGLE-'])
            feature_size = int(feature_info['-FEATURE LENGTH-'] * x_pixel_ratio)
            shape = feature_size, feature_size
            image_in = image_formating(feature_path, resize=shape)
            feature = resize_img(image_in, shape)
            feature = make_black(feature)
            feature = feature.rotate(rotate_angle, fillcolor=(250, 150, 50), expand=True)
            if rotate_angle % 90 != 0:
                feature = make_transparent_edges(feature)
            if event == 'Insert':
                fig_id = graph2.draw_image(data=convert_to_bytes(feature), location=(x, y))
            else:
                fig_id = graph2.draw_image(data=convert_to_bytes(feature), location=(300, feature.size[1]))
            feature_dict[fig_id] = create_feature(feature_info, buildingData, story)
        elif  event == 'Rotate' and not graph2 and not crop:
            img = img.transpose(PIL.Image.ROTATE_90)
            graph1 = window["-GRAPH1-"]  # type: sg.Graph
            graph1.erase()
            graph1.set_size(window_size)
            graph1.change_coordinates((0,0), window_size)
            graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
        elif  event == 'Set Distance':
            if crop:
                popup_info('Area of interest not selected!')
                continue
            set_distance = True
            popup_info('Select point A')
        elif  event == 'Extract Feature' and graph2: # not set_distance
            switch_to_other_graph(window, '-GRAPH2-', graph2, '-GRAPH1-', graph1, window_size)
            popup_info('Select the feature to be extracted')
            extract_feature = True
        elif  event == 'Toggle':
            if blueprint_2_ID:
                graph2.delete_figure(blueprint_2_ID)
                blueprint_2_ID = None
            else:
                blueprint_2_ID = graph2.draw_image(data=convert_to_bytes(blueprint_2_image),
                                                   location=(0, blueprint_2_image.size[1]))
                graph2.send_figure_to_back(blueprint_2_ID)
        elif  event == 'Window Settings':
            if graph2:
                popup_info('Window Settings cannot be changed after using the Convert tool')
                continue
            window_settings = [width_percent, height_percent, image_window_percent, image_resolution]
            window_settings = get_window_settings(window_settings)

            if window_settings == None:
                continue
            if window_settings == '': # The empty string is used here to indicate to reset to default
                width_percent        = 0.84     # What percent of the window width is graph
                height_percent       = 0.94     # What percent of the window height is graph
                image_window_percent = 1.20     # Image scaling
                image_resolution     = 10000    # Blueprint original resolution
            else:
                width_percent        = window_settings['-WIDTH PERCENT-']
                height_percent       = window_settings['-HEIGHT PERCENT-']
                image_window_percent = window_settings['-IMAGE WINDOW PERCENT-']
                image_resolution     = window_settings['-IMAGE RESOLUTION-']
            settings['-WIDTH PERCENT-']    = width_percent
            settings['-HEIGHT PERCENT-']   = height_percent
            settings['-IMAGE PERCENT-']    = image_window_percent
            settings['-IMAGE RESOLUTION-'] = image_resolution
            window_size = (window_width * width_percent, window_height * height_percent)

            if graph1:
                graph1.set_size(window_size)
                graph1.change_coordinates((0,0), window_size)
                window.refresh()
                a_set = a_point = b_point = user_distance = None
                y_pixel_ratio = x_pixel_ratio = None

        elif  event == '-EXPORT IFC-':
            save_file = get_file_name()
            window.perform_long_operation(lambda :
                              ifc.compile(buildingData, save_file),
                              '-EXPORT-')
        elif  event == '-EXPORT-':
            success = values[event]
            if success:
                popup_info('Successfully Exported!')
                continue
            popup_info('Export Failed!')
        elif  event == 'Load Recent' and new_size and not graph2:
            try:
                orig_img = PIL.Image.open(r"./blueprint_features/save.png")
                img = resize_img(orig_img, (new_size, new_size))
                x_pixel_ratio = settings['-X RATIO-']
                y_pixel_ratio = settings['-Y RATIO-']
                window.Element('-Convert-').Update(visible=True)
                graph1.erase()
                graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
                if crop:
                    crop = False
            except Exception as E:
                print('** Error {} **'.format(E))

    # --------------------------------- Close & Exit ---------------------------------
    window.close()

make_dpi_aware()  # This makes the resolution better for high res screens
main_gui()
