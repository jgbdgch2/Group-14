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

#Will added this
import importlib

wall_objects = ('Door', 'Window') # This doesn't change and is used throughout the GUI

def create_feature(info_dict, buildingData, story_id, x, y, pixel_ratio, type_name):
    type = info_dict['-FEATURE-']
    if type == 'Wall':
        # make a wall object
        wall_type = buildingData.buildingSchedule.searchByName(type_name)
        wall = bd.Wall(pos=(x / pixel_ratio, y / pixel_ratio), length=info_dict['-FEATURE LENGTH-'],
                       angle=info_dict['-FEATURE ANGLE-'], wallType=wall_type)
        wall.typeNumber = wall_type.typeNumber
        buildingData.listOfStories[story_id].append(wall)
        return wall
    elif type == 'Door':
        # make a door object
        door_type = buildingData.buildingSchedule.searchByName(type_name)
        door = bd.Door(position=info_dict['-FEATURE LENGTH-'], hingePos=1, doorType=door_type)
        door.typeNumber = door_type.typeNumber
        wall_attach = info_dict['-Wall-']
        wall_attach.append(door)
        return door
    elif type == 'Window':
        # make a window object
        window_type = buildingData.buildingSchedule.searchByName(type_name)
        window = bd.Window(position=info_dict['-FEATURE LENGTH-'], sillHeight=1.0, directionFacing=1,
                           windowType=window_type)
        window.typeNumber = window_type.typeNumber
        wall_attach = info_dict['-Wall-']
        wall_attach.append(window)
        return window

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
    mult = 1
    if len(str) < 1:
        return 0.0
    if str[0] == '-':
        str = str[1:]
        mult = -1
    if str == '' or not str[0].isdigit() or not str[-1] in ('M', 'm'):
        return 0.0
    for char in str:
        if char.isdigit() or char == '.':
            value.append(char)
        elif str.endswith('MM') or str.endswith('mm'):
            return (float(''.join(value)) / 1000) * mult
        elif str.endswith('CM') or str.endswith('cm'):
            return (float(''.join(value))) * mult
        elif str.endswith('M') or str.endswith('m'):
            return (float(''.join(value)) * 100) * mult
        else:
            return 0.0

def convert_to_inches(str):
    feet = []
    inches = []
    is_feet = True
    mult = 1
    if len(str) < 1:
        return 0.0
    if str[0] == '-':
        str = str[1:]
        mult = -1
    if str == '' or not str[0].isdigit():
        return 0.0
    if not "'" in str:
        is_feet = False
        if not '"' in str:
            return 0.0
    if str.endswith("'") and not '"' in str:
        if str[:-1].isdigit():
            return (float(str[:-1]) * 12) * mult
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
                    return (float(''.join(feet)) * 12 + float(''.join(inches))) * mult
                return (float(''.join(inches))) * mult
    return 0.0

def convert_to_feet_string(input_inches):
    negative = False
    if input_inches < 0:
        input_inches *= -1
        negative = True
    feet = input_inches / 12
    front = int(feet)
    back = (feet - front) * 12
    inches = int(back)
    back = float(back) - inches
    test = back * 1000000
    test = test - int(test)
    # This is used for rounding
    if test >= 0.5:
        back += 0.000001
        inches += int(back)
    back = str(float(back))
    back = back[1:]
    if len(back) > 5:
        back = back[:5]
    back = back + '"'
    if negative:
        return '-' + str(front) + '\'' + str(inches) + back
    return str(front) + '\'' + str(inches) + back

def convert_to_meters_string(value):
    negative = False
    if value < 0:
        value *= -1
        negative = True
    centimeters = value * 2.54
    if centimeters >= 100:
        meters = centimeters / 100
        front = int(meters)
        back = meters - front
        back = str(float(back))
        back = back[1:]
        if len(back) > 7:
            back = back[:7]
        back = back + 'm'
    elif centimeters < 1:
        meters = centimeters * 10
        front = int(meters)
        back = meters - front
        back = str(float(back))
        back = back[1:]
        if len(back) > 7:
            back = back[:7]
        back = back + 'mm'
    else:
        meters = centimeters
        front = int(meters)
        back = meters - front
        back = str(float(back))
        back = back[1:]
        if len(back) > 7:
            back = back[:7]
        back = back + 'cm'
    if negative:
        return '-' + str(front) + back
    return str(front) + back

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

def feature_input_window(building_schedule, feature_name):
    schedule_names = get_all_schedule_names(building_schedule)
    length_name = 'Distance from Center'
    if feature_name == 'Wall':
        length_name = 'Length'
        list = schedule_names['-WALL NAMES-']
        schedule = building_schedule.searchByName(list[0])
        str = convert_to_feet_string(schedule.thickness)
        info = [sg.Text('Thickness', size =(15, 1)), sg.Text(str, size =(15, 1), key='-THICKNESS-'),
                sg.Radio('Imperial', "T", default=True, key='-T IS IMPERIAL-'),
                sg.Radio('Metric', "T", default=False)]
    elif feature_name == 'Window':
        list = schedule_names['-WINDOW NAMES-']
        schedule = building_schedule.searchByName(list[0])
        height = convert_to_feet_string(schedule.height)
        width = convert_to_feet_string(schedule.width)
        sill_height = convert_to_feet_string(schedule.sillHeight)
        info = [[sg.Text('Height', size =(17, 1)), sg.Text(height, size =(15, 1), key='-HEIGHT-'),
                sg.Radio('Imperial', "H", default=True, key='-H IS IMPERIAL-'),
                sg.Radio('Metric', "H", default=False)],
                #------------------------------------------------------------------------
               [sg.Text('Width', size =(17, 1)), sg.Text(width, size =(15, 1), key='-WIDTH-'),
                sg.Radio('Imperial', "W", default=True, key='-W IS IMPERIAL-'),
                sg.Radio('Metric', "W", default=False)],
                #------------------------------------------------------------------------
               [sg.Text('Sill Height', size =(17, 1)), sg.Text(sill_height, size =(15, 1), key='-SILL HEIGHT-'),
                sg.Radio('Imperial', "S", default=True, key='-S IS IMPERIAL-'),
                sg.Radio('Metric', "S", default=False)]]
    elif feature_name == 'Door':
        list = schedule_names['-DOOR NAMES-']
        schedule = building_schedule.searchByName(list[0])
        height = convert_to_feet_string(schedule.height)
        width = convert_to_feet_string(schedule.width)
        info = [[sg.Text('Height', size =(17, 1)), sg.Text(height, size =(15, 1), key='-HEIGHT-'),
                sg.Radio('Imperial', "H", default=True, key='-H IS IMPERIAL-'),
                sg.Radio('Metric', "H", default=False)],
                #------------------------------------------------------------------------
               [sg.Text('Width', size =(17, 1)), sg.Text(width, size =(15, 1), key='-WIDTH-'),
                sg.Radio('Imperial', "W", default=True, key='-W IS IMPERIAL-'),
                sg.Radio('Metric', "W", default=False)]]

    message = ('Please enter {} information').format(feature_name)
    layout = [[sg.Text(message)],
              [sg.Text(length_name, size =(17, 1)), sg.InputText(size=(30, 15), key='-FEATURE LENGTH-'),
                        sg.Radio('Imperial', "LENGTH", default=True, key='-LENGTH IS IMPERIAL-'),
                        sg.Radio('Metric', "LENGTH", default=False)],
              [sg.Text('Angle', size =(17, 1)), sg.InputText(size=(30, 15), key='-FEATURE ANGLE-')],
              [sg.Text('Schedule Name:', size =(17, 1)), sg.Combo(list, size=(29, 15),
               key='-SCHEDULE NAME-', readonly=True, enable_events=True)],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    layout.insert(4, info)
    window = sg.Window('New Feature', layout).finalize()
    window['-SCHEDULE NAME-'].update(list[0])
    if feature_name != 'Wall':
        window['-FEATURE ANGLE-'].update(visible=False)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
            window.close()
            return None
        elif event == 'Submit':
            break
        elif event == '-SCHEDULE NAME-':
            if feature_name == 'Wall':
                if values['-T IS IMPERIAL-']:
                    str = convert_to_feet_string(schedule.thickness)
                else:
                    str = convert_to_meters_string(schedule.thickness)
                window['-THICKNESS-'].update(str)
            elif feature_name == 'Window':
                if values['-W IS IMPERIAL-']:
                    str = convert_to_feet_string(schedule.width)
                else:
                    str = convert_to_meters_string(schedule.width)
                window['-WIDTH-'].update(str)
                if values['-H IS IMPERIAL-']:
                    str = convert_to_feet_string(schedule.height)
                else:
                    str = convert_to_meters_string(schedule.height)
                window['-HEIGHT-'].update(str)
                if values['-S IS IMPERIAL-']:
                    str = convert_to_feet_string(schedule.sillHeight)
                else:
                    str = convert_to_meters_string(schedule.sillHeight)
                window['-SILL HEIGHT-'].update(str)
            elif feature_name == 'Door':
                if values['-W IS IMPERIAL-']:
                    str = convert_to_feet_string(schedule.width)
                else:
                    str = convert_to_meters_string(schedule.width)
                window['-WIDTH-'].update(str)
                if values['-H IS IMPERIAL-']:
                    str = convert_to_feet_string(schedule.height)
                else:
                    str = convert_to_meters_string(schedule.height)
                window['-HEIGHT-'].update(str)
    window.close()
    if not values['-LENGTH IS IMPERIAL-']:
        values['-FEATURE LENGTH-'] = convert_to_centimeters(values['-FEATURE LENGTH-'])
        values['-FEATURE LENGTH-'] *= 0.393701
    else:
        values['-FEATURE LENGTH-'] = convert_to_inches(values['-FEATURE LENGTH-'])
    return values

def edit_blueprint_wall_attachment(feature, pixel_ratio, wall_info, schedule_names):
    attachment_info = {}
    if type(feature) == type(bd.Door()):
        schedule_name = feature.doorType.name
        attachment_info['-FEATURE-'] = 'Door'
        list = schedule_names['-DOOR NAMES-']
    elif type(feature) == type(bd.Window()):
        schedule_name = feature.windowType.name
        attachment_info['-FEATURE-'] = 'Window'
        list = schedule_names['-WINDOW NAMES-']
    feature_info = get_feature_info(feature, attachment_info, wall_info)
    length = convert_to_feet_string(wall_info['-FEATURE LENGTH-'])
    width = convert_to_feet_string(wall_info['-FEATURE WIDTH-'])
    x_pos = convert_to_feet_string(wall_info['-X POS-'] * pixel_ratio)
    y_pos = convert_to_feet_string(wall_info['-Y POS-'] * pixel_ratio)
    angle = wall_info['-FEATURE ANGLE-']
    center_distance = convert_to_feet_string(feature_info['-DISTANCE-'])
    attachment_width = convert_to_feet_string(feature_info['-FEATURE LENGTH-'])
    attachment_height = convert_to_feet_string(feature_info['-HEIGHT-'])
    layout = [[sg.Text('Edit attachment information')],
              [sg.Text('Wall Length', size =(25, 1)), sg.Text(length, size =(15, 1), key='-FEATURE LENGTH-'),
                        sg.Radio('Imperial', "LENGTH", default=True, enable_events=True, key='-LENGTH IS IMPERIAL-'),
                        sg.Radio('Metric', "LENGTH", default=False, enable_events=True, key='-LENGTH IS NOT IMPERIAL-')],
              [sg.Text('Wall Width', size =(25, 1)), sg.Text(width, size =(15, 1), key='-FEATURE WIDTH-'),
                        sg.Radio('Imperial', "WIDTH", default=True, enable_events=True, key='-WIDTH IS IMPERIAL-'),
                        sg.Radio('Metric', "WIDTH", default=False, enable_events=True, key='-WIDTH IS NOT IMPERIAL-')],
              [sg.Text('Wall X Center Position', size =(25, 1)), sg.Text(x_pos, size =(15, 1), key='-X POS-'),
                        sg.Radio('Imperial', "X", default=True, enable_events=True, key='-X IS IMPERIAL-'),
                        sg.Radio('Metric', "X", default=False, enable_events=True, key='-X IS NOT IMPERIAL-')],
              [sg.Text('Wall Y Center Position', size =(25, 1)), sg.Text(y_pos, size =(15, 1), key='-Y POS-'),
                        sg.Radio('Imperial', "Y", default=True, enable_events=True, key='-Y IS IMPERIAL-'),
                        sg.Radio('Metric', "Y", default=False, enable_events=True, key='-Y IS NOT IMPERIAL-')],
              [sg.Text('Wall Angle', size =(25, 1)), sg.Text(angle)],
              [sg.Text('Frame Width', size =(25, 1)), sg.Text(attachment_width, size =(16, 1), key='-ATTACHMENT WIDTH-'),
                        sg.Radio('Imperial', "W", default=True, enable_events=True, key='-W IS IMPERIAL-'),
                        sg.Radio('Metric', "W", default=False, enable_events=True, key='-W IS NOT IMPERIAL-')],
              [sg.Text('Frame Height', size =(25, 1)), sg.Text(attachment_height, size =(16, 1), key='-HEIGHT-'),
                        sg.Radio('Imperial', "H", default=True, enable_events=True, key='-H IS IMPERIAL-'),
                        sg.Radio('Metric', "H", default=False, enable_events=True, key='-H IS NOT IMPERIAL-')],
              [sg.Text('Distance from Center of wall', size =(25, 1)), sg.InputText(center_distance, size =(16, 1), key='-DISTANCE-'),
                        sg.Radio('Imperial', "D", default=True, enable_events=True, key='-D IS IMPERIAL-'),
                        sg.Radio('Metric', "D", default=False, enable_events=True, key='-D IS NOT IMPERIAL-')],
              [sg.Text('Feature Type:', size =(25, 1)), sg.Combo(list, size=(24, 15),
               key='-SCHEDULE NAME-', readonly=True)],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('Edit Feature', layout).finalize()
    window['-SCHEDULE NAME-'].update(schedule_name)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
            window.close()
            return None
        if event == 'Submit':
            break
        elif event == '-LENGTH IS IMPERIAL-':
            str = convert_to_feet_string(wall_info['-FEATURE LENGTH-'])
            window['-FEATURE LENGTH-'].update(str)
        elif event == '-LENGTH IS NOT IMPERIAL-':
            str = convert_to_meters_string(wall_info['-FEATURE LENGTH-'])
            window['-FEATURE LENGTH-'].update(str)
        elif event == '-WIDTH IS IMPERIAL-':
            str = convert_to_feet_string(wall_info['-FEATURE WIDTH-'])
            window['-FEATURE WIDTH-'].update(str)
        elif event == '-WIDTH IS NOT IMPERIAL-':
            str = convert_to_meters_string(wall_info['-FEATURE WIDTH-'])
            window['-FEATURE WIDTH-'].update(str)
        elif event == '-X IS IMPERIAL-':
            str = convert_to_feet_string(wall_info['-X POS-'] * pixel_ratio)
            window['-X POS-'].update(str)
        elif event == '-X IS NOT IMPERIAL-':
            str = convert_to_meters_string(wall_info['-X POS-'] * pixel_ratio)
            window['-X POS-'].update(str)
        elif event == '-Y IS IMPERIAL-':
            str = convert_to_feet_string(wall_info['-Y POS-'] * pixel_ratio)
            window['-Y POS-'].update(str)
        elif event == '-Y IS NOT IMPERIAL-':
            str = convert_to_meters_string(wall_info['-Y POS-'] * pixel_ratio)
            window['-Y POS-'].update(str)
        elif event == '-D IS IMPERIAL-':
            str = convert_to_feet_string(feature_info['-DISTANCE-'])
            window['-DISTANCE-'].update(str)
        elif event == '-D IS NOT IMPERIAL-':
            str = convert_to_meters_string(feature_info['-DISTANCE-'])
            window['-DISTANCE-'].update(str)
        elif event == '-W IS IMPERIAL-':
            str = convert_to_feet_string(feature_info['-FEATURE LENGTH-'])
            window['-ATTACHMENT WIDTH-'].update(str)
        elif event == '-W IS NOT IMPERIAL-':
            str = convert_to_meters_string(feature_info['-FEATURE LENGTH-'])
            window['-ATTACHMENT WIDTH-'].update(str)
        elif event == '-H IS IMPERIAL-':
            str = convert_to_feet_string(feature_info['-HEIGHT-'])
            window['-HEIGHT-'].update(str)
        elif event == '-H IS NOT IMPERIAL-':
            str = convert_to_meters_string(feature_info['-HEIGHT-'])
            window['-HEIGHT-'].update(str)
    window.close()

    if not values['-D IS IMPERIAL-']:
        values['-DISTANCE-'] = convert_to_centimeters(values['-DISTANCE-'])
        values['-DISTANCE-'] *= 0.393701
    else:
        values['-DISTANCE-'] = convert_to_inches(values['-DISTANCE-'])
    if not values['-W IS IMPERIAL-']:
        values['-ATTACHMENT WIDTH-'] = convert_to_centimeters(values['-ATTACHMENT WIDTH-'])
        values['-ATTACHMENT WIDTH-'] *= 0.393701
    else:
        values['-ATTACHMENT WIDTH-'] = convert_to_inches(values['-ATTACHMENT WIDTH-'])
    if not values['-H IS IMPERIAL-']:
        values['-HEIGHT-'] = convert_to_centimeters(values['-HEIGHT-'])
        values['-HEIGHT-'] *= 0.393701
    else:
        values['-HEIGHT-'] = convert_to_inches(values['-HEIGHT-'])
    values['-FEATURE ANGLE-'] = float(values['-HEIGHT-'])
    return values

def edit_blueprint_wall(feature, pixel_ratio, list_wall_types):
    # feat_list
    feature_info = get_building_wall_info(feature)
    length = convert_to_feet_string(feature_info['-FEATURE LENGTH-'])
    width = convert_to_feet_string(feature_info['-FEATURE WIDTH-'])
    x_pos = convert_to_feet_string(feature_info['-X POS-'] * pixel_ratio)
    y_pos = convert_to_feet_string(feature_info['-Y POS-'] * pixel_ratio)
    angle = feature_info['-FEATURE ANGLE-']
    layout = [[sg.Text('Edit Wall information')],
              [sg.Text('Length', size =(15, 1)), sg.InputText(length, key='-FEATURE LENGTH-'),
                        sg.Radio('Imperial', "LENGTH", default=True, enable_events=True, key='-LENGTH IS IMPERIAL-'),
                        sg.Radio('Metric', "LENGTH", default=False, enable_events=True, key='-LENGTH IS NOT IMPERIAL-')],
              [sg.Text('X Center Position', size =(15, 1)), sg.InputText(x_pos, key='-X POS-'),
                        sg.Radio('Imperial', "X", default=True, enable_events=True, key='-X IS IMPERIAL-'),
                        sg.Radio('Metric', "X", default=False, enable_events=True, key='-X IS NOT IMPERIAL-')],
              [sg.Text('Y Center Position', size =(15, 1)), sg.InputText(y_pos, key='-Y POS-'),
                        sg.Radio('Imperial', "Y", default=True, enable_events=True, key='-Y IS IMPERIAL-'),
                        sg.Radio('Metric', "Y", default=False, enable_events=True, key='-Y IS NOT IMPERIAL-')],
              [sg.Text('Angle', size =(15, 1)), sg.InputText(angle, key='-FEATURE ANGLE-')],
              [sg.Text('Thickness', size =(15, 1)), sg.Text(width, size =(15, 1), key='-FEATURE WIDTH-'),
               sg.Radio('Imperial', "WIDTH", default=True, enable_events=True, key='-WIDTH IS IMPERIAL-'),
               sg.Radio('Metric', "WIDTH", default=False, enable_events=True, key='-WIDTH IS NOT IMPERIAL-')],
              [sg.Text('Schedule Type:', size =(15, 1)), sg.Combo(list_wall_types, size=(30, 10),
               key='-SCHEDULE NAME-', readonly=True)],
              [sg.Submit(bind_return_key=True), sg.Cancel()]]

    window = sg.Window('Edit Feature', layout).finalize()
    window['-SCHEDULE NAME-'].update(feature.wallType.name)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
            window.close()
            return None
        if event == 'Submit':
            break
        elif event == '-LENGTH IS IMPERIAL-':
            str = convert_to_feet_string(feature_info['-FEATURE LENGTH-'])
            window['-FEATURE LENGTH-'].update(str)
        elif event == '-LENGTH IS NOT IMPERIAL-':
            str = convert_to_meters_string(feature_info['-FEATURE LENGTH-'])
            window['-FEATURE LENGTH-'].update(str)
        elif event == '-WIDTH IS IMPERIAL-':
            str = convert_to_feet_string(feature_info['-FEATURE WIDTH-'])
            window['-FEATURE WIDTH-'].update(str)
        elif event == '-WIDTH IS NOT IMPERIAL-':
            str = convert_to_meters_string(feature_info['-FEATURE WIDTH-'])
            window['-FEATURE WIDTH-'].update(str)
        elif event == '-X IS IMPERIAL-':
            str = convert_to_feet_string(feature_info['-X POS-'] * pixel_ratio)
            window['-X POS-'].update(str)
        elif event == '-X IS NOT IMPERIAL-':
            str = convert_to_meters_string(feature_info['-X POS-'] * pixel_ratio)
            window['-X POS-'].update(str)
        elif event == '-Y IS IMPERIAL-':
            str = convert_to_feet_string(feature_info['-Y POS-'] * pixel_ratio)
            window['-Y POS-'].update(str)
        elif event == '-Y IS NOT IMPERIAL-':
            str = convert_to_meters_string(feature_info['-Y POS-'] * pixel_ratio)
            window['-Y POS-'].update(str)
    window.close()
    if not values['-LENGTH IS IMPERIAL-']:
        values['-FEATURE LENGTH-'] = convert_to_centimeters(values['-FEATURE LENGTH-'])
        values['-FEATURE LENGTH-'] *= 0.393701
    else:
        values['-FEATURE LENGTH-'] = convert_to_inches(values['-FEATURE LENGTH-'])
    if not values['-X IS IMPERIAL-']:
        values['-X POS-'] = convert_to_centimeters(values['-X POS-'])
        values['-X POS-'] *= 0.393701 / pixel_ratio
    else:
        values['-X POS-'] = convert_to_inches(values['-X POS-'])
        values['-X POS-'] /= pixel_ratio
    if not values['-Y IS IMPERIAL-']:
        values['-Y POS-'] = convert_to_centimeters(values['-Y POS-'])
        values['-Y POS-'] *= 0.393701 / pixel_ratio
    else:
        values['-Y POS-'] = convert_to_inches(values['-Y POS-'])
        values['-Y POS-'] /= pixel_ratio
    try:
        values['-FEATURE ANGLE-'] = float(values['-FEATURE ANGLE-'])
    except:
        values['-FEATURE ANGLE-'] = 0.0
    return values

def update_window(window, window_info):
    window.position = window_info['-DISTANCE-']
    #window.sillHeight = window_info['-SILL HEIGHT-']
    window.windowType = schedule.searchByName(window_info['-SCHEDULE NAME-'])
    #window.information = window_info['-WINDOW NOTES-']

def update_door(door, door_info, schedule):
    door.position = door_info['-DISTANCE-']
    #door.hingePos = door_info['-HINGE POSITION-']
    door.doorType = schedule.searchByName(door_info['-SCHEDULE NAME-'])
    #door.information = door_info['DOOR NOTES']

def update_wall(wall, wall_info, schedule):
    wall.length = wall_info['-FEATURE LENGTH-']
    wall.wallType = schedule.searchByName(wall_info['-SCHEDULE NAME-'])
    wall.xPos = wall_info['-X POS-']
    wall.yPos = wall_info['-Y POS-']
    wall.angle = wall_info['-FEATURE ANGLE-']

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

def get_all_schedule_names(building_schedule):
    wall_names = []
    window_names = []
    door_names = []
    for wall_type in building_schedule.listOfWallTypes:
        wall_names.append(wall_type.name)
    for window_type in building_schedule.listOfWindowTypes:
        window_names.append(window_type.name)
    for  door_type in building_schedule.listOfDoorTypes:
        door_names.append(door_type.name)
    names = {'-WALL NAMES-': wall_names, '-WINDOW NAMES-': window_names,
             '-DOOR NAMES-': door_names}
    return names

def get_schedule_number(building_schedule):
    wall_number = window_number = door_number = 0
    for wall_type in building_schedule.listOfWallTypes:
        if wall_type.typeNumber > wall_number:
            wall_number = wall_type.typeNumber
    for window_type in building_schedule.listOfWindowTypes:
        if window_type.typeNumber > window_number:
            window_number = window_type.typeNumber
    for  door_type in building_schedule.listOfDoorTypes:
        if door_type.typeNumber > door_number:
            door_number = door_type.typeNumber

    return max(wall_number, window_number, door_number)

def get_nearest_type(building_schedule, width, type):
    if type == 'Wall':
        val = abs(building_schedule.listOfWallTypes[0].thickness - width)
        for wall_type in building_schedule.listOfWallTypes:
            if abs(wall_type.thickness - width) <= val:
                val = abs(wall_type.thickness - width)
                select_type = wall_type
    elif type == 'Window':
        pass
    elif type == 'Door':
        pass

    return select_type

def blueprint_schedule_creator(building_schedule, add_only=True):
    schedule_type = get_all_schedule_names(building_schedule)
    type_number = get_schedule_number(building_schedule)
    left_col_schedule = [[sg.Text('', size =(35, 1), visible=True)], # Using this for padding control
                         [sg.Text('Wall Schedules:', size =(20, 1))],
                         [sg.Listbox(schedule_type['-WALL NAMES-'], enable_events=True,
                          size=(30,5),key='-WALL LIST-')],
                         [sg.Text('', size =(20, 1), visible=True)],
                         [sg.Text('Window Schedules:', size =(20, 1))],
                         [sg.Listbox(schedule_type['-WINDOW NAMES-'], enable_events=True,
                          size=(30,5),key='-WINDOW LIST-')],
                         [sg.Text('', size =(20, 1), visible=True)],
                         [sg.Text('Door Schedules:', size =(20, 1))],
                         [sg.Listbox(schedule_type['-DOOR NAMES-'], enable_events=True,
                          size=(30,5),key='-DOOR LIST-')],
                         ]

    right_col_schedule = [[sg.Text('Schedule Name', size =(17, 1)),
                           sg.InputText(size =(30, 1), key='-SCHEDULE NAME-')],
                          #---------------------------------------------------
                          [sg.Text('Schedule Width', size =(17, 1)),
                           sg.InputText(size =(30, 1), key='-SCHEDULE WIDTH-'),
                           sg.Radio('Imperial', "WIDTH", default=True, key='-W IS IMPERIAL-'),
                           sg.Radio('Metric', "WIDTH", default=False)],
                          #---------------------------------------------------
                          [sg.Text('Schedule Height', size =(17, 1)),
                           sg.InputText(size =(30, 1), key='-SCHEDULE HEIGHT-'),
                           sg.Radio('Imperial', "HEIGHT", default=True, key='-H IS IMPERIAL-'),
                           sg.Radio('Metric', "HEIGHT", default=False)],
                          #---------------------------------------------------
                          [sg.Text('Sill Height (Window)', size =(17, 1)),
                           sg.InputText(size =(30, 1), key='-SILL HEIGHT-'),
                           sg.Radio('Imperial', "SILL", default=True, key='-S IS IMPERIAL-'),
                           sg.Radio('Metric', "SILL", default=False)],
                          #---------------------------------------------------
                          [sg.Text('Schedule Type', size =(17, 1)),
                           sg.Combo(['Wall', 'Window', 'Door'], size=(10, 5),
                           key='-SCHEDULE TYPE-', readonly=True)],
                          [sg.Button('Add Schedule', key='-ADD SCHEDULE-')],
                          [sg.Button('Delete Schedule', key='-DELETE SCHEDULE-')]
                          ]

    layout = [[sg.Column(left_col_schedule), sg.Column(right_col_schedule)]]
    window = sg.Window('Building Schedule Tool', layout).finalize()
    window['-DELETE SCHEDULE-'].update(visible=False)
    window['-SCHEDULE TYPE-'].update('Wall')
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
            window.close()
            return
        if event == '-ADD SCHEDULE-' and values != None:
            schedule_type = get_all_schedule_names(building_schedule)
            if not values['-W IS IMPERIAL-']:
                values['-SCHEDULE WIDTH-'] = convert_to_centimeters(values['-SCHEDULE WIDTH-'])
                values['-SCHEDULE WIDTH-'] *= 0.393701
            else:
                values['-SCHEDULE WIDTH-'] = convert_to_inches(values['-SCHEDULE WIDTH-'])
            if not values['-H IS IMPERIAL-']:
                values['-SCHEDULE HEIGHT-'] = convert_to_centimeters(values['-SCHEDULE HEIGHT-'])
                values['-SCHEDULE HEIGHT-'] *= 0.393701
            else:
                values['-SCHEDULE HEIGHT-'] = convert_to_inches(values['-SCHEDULE HEIGHT-'])
            if not values['-S IS IMPERIAL-']:
                values['-SILL HEIGHT-'] = convert_to_centimeters(values['-SILL HEIGHT-'])
                values['-SILL HEIGHT-'] *= 0.393701
            else:
                values['-SILL HEIGHT-'] = convert_to_inches(values['-SILL HEIGHT-'])
            #--------------------------------------------------------------------------------------
            type_number += 1
            master_list = []
            for key in schedule_type:
                for list in schedule_type[key]:
                    master_list.append(list)
            if values['-SCHEDULE TYPE-'] == 'Wall':
                if values['-SCHEDULE NAME-'] in master_list:
                    popup_info('Name already exists!')
                    type_number -= 1
                    continue
                if values['-SCHEDULE NAME-'] == '' or values['-SCHEDULE WIDTH-'] <= 0:
                    continue
                schedule = bd.WallType(typeNumber=type_number,
                                       name=values['-SCHEDULE NAME-'],
                                       thickness=values['-SCHEDULE WIDTH-'])
            elif values['-SCHEDULE TYPE-'] == 'Window':
                if values['-SCHEDULE NAME-'] in master_list:
                    popup_info('Name already exists!')
                    type_number -= 1
                    continue
                if values['-SCHEDULE NAME-'] == '' or values['-SCHEDULE WIDTH-'] <= 0 or\
                   values['-SCHEDULE HEIGHT-'] <= 0 or values['-SILL HEIGHT-'] <= 0:
                    continue
                schedule = bd.WindowType(typeNumber=type_number,
                                         name=values['-SCHEDULE NAME-'],
                                         height=values['-SCHEDULE HEIGHT-'],
                                         width=values['-SCHEDULE WIDTH-'],
                                         sillHeight=values['-SILL HEIGHT-'])
            elif values['-SCHEDULE TYPE-'] == 'Door':
                if values['-SCHEDULE NAME-'] in master_list:
                    popup_info('Name already exists!')
                    type_number -= 1
                    continue
                if values['-SCHEDULE NAME-'] == '' or values['-SCHEDULE WIDTH-'] <= 0 or\
                   values['-SCHEDULE HEIGHT-'] <= 0:
                    continue
                schedule = bd.DoorType(typeNumber=type_number,
                                       name=values['-SCHEDULE NAME-'],
                                       height=values['-SCHEDULE HEIGHT-'],
                                       width=values['-SCHEDULE WIDTH-'])
            building_schedule.append(schedule)
            schedule_type = get_all_schedule_names(building_schedule)
            window['-WALL LIST-'].update(schedule_type['-WALL NAMES-'])
            window['-WINDOW LIST-'].update(schedule_type['-WINDOW NAMES-'])
            window['-DOOR LIST-'].update(schedule_type['-DOOR NAMES-'])
        elif event in ('-WALL LIST-', '-WINDOW LIST-', '-DOOR LIST-'):
            if not add_only:
                window['-DELETE SCHEDULE-'].update(visible=True)
            if event == '-WALL LIST-':
                window['-WINDOW LIST-'].set_value([])
                window['-DOOR LIST-'].set_value([])
                if len(values['-WALL LIST-']) > 0:
                    wall_type = building_schedule.searchByName(values['-WALL LIST-'][0])
                    window['-SCHEDULE NAME-'].update(wall_type.name)
                    if values['-W IS IMPERIAL-']:
                        str = convert_to_feet_string(wall_type.thickness)
                    else:
                        str = convert_to_meters_string(wall_type.thickness)
                    window['-SCHEDULE WIDTH-'].update(str)
                    window['-SCHEDULE TYPE-'].update('Wall')
                    window['-SCHEDULE HEIGHT-'].update('')
                    window['-SILL HEIGHT-'].update('')
            elif event == '-WINDOW LIST-':
                window['-WALL LIST-'].set_value([])
                window['-DOOR LIST-'].set_value([])
                if len(values['-WINDOW LIST-']) > 0:
                    window_type = building_schedule.searchByName(values['-WINDOW LIST-'][0])
                    window['-SCHEDULE NAME-'].update(window_type.name)
                    if values['-W IS IMPERIAL-']:
                        str = convert_to_feet_string(window_type.width)
                    else:
                        str = convert_to_meters_string(window_type.width)
                    window['-SCHEDULE WIDTH-'].update(str)
                    if values['-H IS IMPERIAL-']:
                        str = convert_to_feet_string(window_type.height)
                    else:
                        str = convert_to_meters_string(window_type.height)
                    window['-SCHEDULE HEIGHT-'].update(str)
                    if values['-S IS IMPERIAL-']:
                        str = convert_to_feet_string(window_type.sillHeight)
                    else:
                        str = convert_to_meters_string(window_type.sillHeight)
                    window['-SILL HEIGHT-'].update(str)
                    window['-SCHEDULE TYPE-'].update('Window')
            elif event == '-DOOR LIST-':
                window['-WINDOW LIST-'].set_value([])
                window['-WALL LIST-'].set_value([])
                if len(values['-DOOR LIST-']) > 0:
                    door_type = building_schedule.searchByName(values['-DOOR LIST-'][0])
                    window['-SCHEDULE NAME-'].update(door_type.name)
                    if values['-W IS IMPERIAL-']:
                        str = convert_to_feet_string(door_type.width)
                    else:
                        str = convert_to_meters_string(door_type.width)
                    window['-SCHEDULE WIDTH-'].update(str)
                    if values['-H IS IMPERIAL-']:
                        str = convert_to_feet_string(door_type.height)
                    else:
                        str = convert_to_meters_string(door_type.height)
                    window['-SCHEDULE HEIGHT-'].update(str)
                    window['-SCHEDULE TYPE-'].update('Door')
                    window['-SILL HEIGHT-'].update('')
        elif event == '-DELETE SCHEDULE-':
            if len(values['-WALL LIST-']) > 0:
                wall_type = building_schedule.searchByName(values['-WALL LIST-'][0])
                building_schedule.deleteByType(wall_type.typeNumber)
            elif len(values['-WINDOW LIST-']) > 0:
                window_type = building_schedule.searchByName(values['-WINDOW LIST-'][0])
                building_schedule.deleteByType(window_type.typeNumber)
            elif len(values['-DOOR LIST-']) > 0:
                door_type = building_schedule.searchByName(values['-DOOR LIST-'][0])
                building_schedule.deleteByType(door_type.typeNumber)
            schedule_type = get_all_schedule_names(building_schedule)
            window['-WALL LIST-'].update(schedule_type['-WALL NAMES-'])
            window['-WINDOW LIST-'].update(schedule_type['-WINDOW NAMES-'])
            window['-DOOR LIST-'].update(schedule_type['-DOOR NAMES-'])
            window['-DELETE SCHEDULE-'].update(visible=False)

def machine_learning_features(img, buildingData, y_pixel_ratio): # Testing code for machine learning extraction
    data = mmd.machine_learning_feature_data_extractor(img, y_pixel_ratio)
    if data == None:
        return buildingData
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
        wall_feature['-HEIGHT-'] = feature.windowType.height
    elif wall_feature['-FEATURE-'] == 'Door':
        wall_feature['-HEIGHT-'] = feature.doorType.height
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
                    '-FEATURE WIDTH-': building_wall.wallType.thickness,
                   }
    return feature_info

def graph_draw_from_data(story, graph, feature_dict, pixel_ratio, folder, feature_images):
    for wall in story.listOfWalls:
        draw_wall_and_attachments(graph, folder, feature_images, wall, pixel_ratio, feature_dict=feature_dict)

def draw_wall_and_attachments(graph, folder, feature_images, wall, pixel_ratio, feature_dict=None):
    wall_info = get_building_wall_info(wall)
    wall_info['-FEATURE-'] = 'Wall'
    wall_id = draw_feature(graph, folder, feature_images, wall_info, pixel_ratio)
    if feature_dict != None:
        feature_dict[wall_id] = wall
    door_info = {}
    window_info = {}
    door_info['-FEATURE-'] = 'Door'
    window_info['-FEATURE-'] = 'Window'
    for door in wall.listOfDoors:
        door.parentID = wall_id
        door_info = get_feature_info(door, door_info, wall_info)
        fig_id = draw_feature(graph, folder, feature_images, door_info, pixel_ratio)
        if feature_dict:
            feature_dict[fig_id] = door
    for window in wall.listOfWindows:
        window.parentID = wall_id
        window_info = get_feature_info(window, window_info, wall_info)
        fig_id = draw_feature(graph, folder, feature_images, window_info, pixel_ratio)
        if feature_dict:
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

def get_center_coordinates(graph, fig_id):
    top_left, bottom_right = graph.get_bounding_box(fig_id)
    distance = (bottom_right[0] - top_left[0])/2, (top_left[1] - bottom_right[1])/2
    return top_left[0] + distance[0], top_left[1] - distance[1]

def switch_to_other_graph(window, name1, graph1, name2, graph2, window_size):
    graph1.set_size((0,0)) # This will free up the space for graph2
    graph2.set_size(window_size)
    window.refresh() # This must be refreshed before making anything invisible
    window.Element(name1).Update(visible=False)
    window.Element(name2).Update(visible=True)

def erase_wall_attachment(graph, feature_dict, attachment):
    feature_ID = [k for k, v in feature_dict.items() if v == attachment]
    if len(feature_ID) == 1:
        feature_ID = feature_ID[0]
    else:
        print('Something went wrong deleting')
        exit(0)
    graph.delete_figure(feature_ID)
    feature_dict.pop(feature_ID)

def erase_wall(graph, feature_dict, wall_id):
    wall = feature_dict[wall_id]
    for door in wall.listOfDoors:
        erase_wall_attachment(graph, feature_dict, door)
    for window in wall.listOfWindows:
        erase_wall_attachment(graph, feature_dict, window)
    graph.delete_figure(wall_id)
    feature_dict.pop(wall_id)

def delete_wall(graph, feature_dict, wall_id, list_of_walls):
    wall = feature_dict[wall_id]
    for door in wall.listOfDoors:
        delete_wall_attachment(graph, feature_dict, door, wall.listOfDoors)
    for window in wall.listOfWindows:
        delete_wall_attachment(graph, feature_dict, window, wall.listOfWindows)
    graph.delete_figure(wall_id)
    feature_dict.pop(wall_id)
    del list_of_walls[list_of_walls.index(wall)]

def delete_wall_attachment(graph, feature_dict, attachment, list_attachment):
    feature_ID = [k for k, v in feature_dict.items() if v == attachment]
    if len(feature_ID) == 1:
        feature_ID = feature_ID[0]
    else:
        print('Something went wrong deleting')
        exit(0)
    graph.delete_figure(feature_ID)
    feature_dict.pop(feature_ID)
    del list_attachment[list_attachment.index(attachment)]

def dist(one, two):
    return math.sqrt( (two[0] - one[0])**2 + (two[1] - one[1])**2 )

def attachment_translate_with_wall(graph, feature_dict, delta_x, delta_y, wall_id):
    # Get all the feature IDs from any attachments with the parent ID of the wall
    feature_IDs = [k for k, v in feature_dict.items() if (type(v) == type(bd.Door()) or
                                                          type(v) == type(bd.Window()))
                                                          and v.parentID == wall_id]
    for fig_id in feature_IDs:
        graph.BringFigureToFront(fig_id)
        graph.move_figure(fig_id, delta_x, delta_y)

def attachment_translate_along_wall(graph, feature_dict, delta_x, delta_y, fig_id, pixel_ratio):
        feature = feature_dict[fig_id]
        wall = feature_dict[feature.parentID]
        angle = wall.angle % 360
        rotate_angle = math.radians(angle)
        slope = math.tan(rotate_angle)
        center = get_center_coordinates(graph, fig_id)
        pos = center[0] + delta_x, center[1] + delta_y
        distance = dist([wall.xPos * pixel_ratio, wall.yPos * pixel_ratio], [pos[0], pos[1]])
        if distance >= wall.length / 2 * pixel_ratio:
            return
        if (angle <= 225 and angle >= 135) or (angle <= 45 and angle >= 0) or \
            (angle <= 360 and angle >= 315): # Angle is more horizontal
            delta_y = slope * delta_x
        else: # Angle is more vertical
            delta_x = delta_y / slope
        graph.move_figure(fig_id, delta_x, delta_y)
        center = get_center_coordinates(graph, fig_id)
        x_positive = center[0] - wall.xPos * pixel_ratio
        y_positive = center[1] - wall.yPos * pixel_ratio
        final_distance = dist([wall.xPos * pixel_ratio, wall.yPos * pixel_ratio], [center[0], center[1]])
        if x_positive > 0:
            x_positive = True
        else:
            x_positive = False
        if y_positive > 0:
            y_positive = True
        else:
            y_positive = False

        #-----------------------
        # Logic for positive or negative distance values
        #-----------------------
        if x_positive and (angle < 270 and angle > 90):
            final_distance *= -1
        elif not x_positive and (angle < 90 and angle > 270):
            final_distance *= -1
        elif not y_positive and angle == 90:
            final_distance *= -1
        elif y_positive and angle == 270:
            final_distance *= -1
        return final_distance

def main_gui():
    # --------------------------------- Define Layout ---------------------------------
    # Right click menu for graphs
    graph1_menu_def = ['&Right', ['Rotate', 'Set Distance']]
    graph2_menu_def = ['&Right', ['Edit', 'Duplicate', 'Insert', 'Delete', 'Toggle']]
    # First is the top menu
    menu_def = [['&File', ['&New       ALT-N', '&Quick Save', '&Load Recent', 'E&xit']],
                ['&Edit', ['Extract Feature', '!Add Story', 'Add To Schedule']],
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
    end_point1 = graph2 = start_point2 = data = new_size = save_convert = None
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
            save_convert = False
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
                #buildingData = bd.BuildingData()
                feature_dict = {}
        elif event == '-LOADED PDF-':
            if graph2:
                graph2.erase()
                graph2 = None
                window.Element('-GRAPH2-').Update(visible=False)
            orig_img = values[event]
            if not orig_img:
                popup_info('Page Not Found!')
                continue
            blueprint_schedule_creator(buildingData.buildingSchedule, add_only=False)
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
            save_convert = True
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
            prev_x, prev_y = last2xy
            last2xy = x,y
            if len(drag_figures) > 0:
                select_fig = drag_figures[-1] # This will always be the figure on top
            else:
                select_fig = None
            if blueprint_2_ID and select_fig == blueprint_2_ID: # check if initial blueprint
                select_fig = None
            if select_fig is not None:
                graph2.BringFigureToFront(select_fig) # when dragging a feature bring it to front of all others not selected
                feature = feature_dict[select_fig]
                if type(feature) == type(bd.Wall()): # Walls need there features moved up
                    graph2.move_figure(select_fig, delta_x, delta_y)
                    attachment_translate_with_wall(graph2, feature_dict, delta_x, delta_y, select_fig)
                    center = get_center_coordinates(graph2, select_fig)
                    feature.xPos = center[0] / x_pixel_ratio
                    feature.yPos = center[1] / x_pixel_ratio
                elif type(feature) == type(bd.Door()) or type(feature) == type(bd.Window()):
                    distance = attachment_translate_along_wall(graph2, feature_dict, delta_x, delta_y, select_fig, x_pixel_ratio)
                    if distance:
                        feature.position = distance / x_pixel_ratio
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
                        #Will added this
                        #Allows me to modify wall detector without reloading blueprint_gui.py
                        importlib.reload(mmd)
                        try:
                            result = mmd.feature_data_extractor(send_img,
                                                                     bounding_box,
                                                                     x_pixel_ratio * h,
                                                                     feature_info['-FEATURE TYPE-'])
                        except:
                            result = None
                        # Features extracted
                        graph1.delete_figure(prior_rect)
                        switch_to_other_graph(window, '-GRAPH1-', graph1, '-GRAPH2-', graph2, window_size)
                        extract_feature = False
                        if result:
                            wall_object, width = result
                            wall_object.wallType = get_nearest_type(buildingData.buildingSchedule,
                                                                    width, feature_info['-FEATURE TYPE-'])
                            wall_object.typeNumber = wall_object.wallType.typeNumber
                            buildingData.listOfStories[story].append(wall_object)
                            draw_wall_and_attachments(window['-GRAPH2-'], folder, feature_images,
                                                wall_object, x_pixel_ratio, feature_dict=feature_dict)
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
                if type(feature_dict[select_fig]) == type(bd.Wall()):
                    list_of_walls = buildingData.listOfStories[story].listOfWalls
                    delete_wall(graph2, feature_dict, select_fig, list_of_walls)
                else:
                    attachment = feature_dict[select_fig]
                    parentID = attachment.parentID
                    parent = feature_dict[parentID] # This will be the wall object
                    if type(attachment) == type(bd.Door()):
                        list = parent.listOfDoors
                    elif type(attachment) == type(bd.Window()):
                        list = parent.listOfWindows
                    else:
                        print('Type not supported for delete')
                    delete_wall_attachment(graph2, feature_dict, attachment, list)
                select_fig = None
        elif  event == 'Duplicate':
            if select_fig is None:
                popup_info('No Feature selected')
            else:
                print('this works')
        elif  event == 'Edit':
            if select_fig is None:
                popup_info('No Feature selected')
                continue
            edit_feature = feature_dict[select_fig]
            schedule_names = get_all_schedule_names(buildingData.buildingSchedule)
            if type(edit_feature) == type(bd.Wall()):
                new_info = edit_blueprint_wall(edit_feature, x_pixel_ratio,
                                               schedule_names['-WALL NAMES-'])
                if new_info != None:
                    update_wall(edit_feature, new_info, buildingData.buildingSchedule)
                    erase_wall(graph2, feature_dict, select_fig)
                    draw_wall_and_attachments(graph2, folder, feature_images,
                                        edit_feature, x_pixel_ratio, feature_dict=feature_dict)
            elif type(edit_feature) == type(bd.Door()):
                wall_info = get_building_wall_info(feature_dict[edit_feature.parentID])
                new_info = edit_blueprint_wall_attachment(edit_feature, x_pixel_ratio, wall_info, schedule_names)
                if new_info != None:
                    update_door(edit_feature, new_info)
                    erase_wall_attachment(graph2, feature_dict, edit_feature)
                    door_info = {}
                    door_info['-FEATURE-'] = 'Door'
                    feature_info = get_feature_info(edit_feature, door_info, wall_info)
                    edit_id = draw_feature(graph2, folder, feature_images, feature_info, x_pixel_ratio)
                    feature_dict[edit_id] = edit_feature
            elif type(edit_feature) == type(bd.Window()):
                wall_info = get_building_wall_info(feature_dict[edit_feature.parentID])
                new_info = edit_blueprint_wall_attachment(edit_feature, x_pixel_ratio, wall_info, schedule_names)
                if new_info != None:
                    update_window(edit_feature, new_info)
                    erase_wall_attachment(graph2, feature_dict, edit_feature)
                    window_info = {}
                    window_info['-FEATURE-'] = 'Window'
                    feature_info = get_feature_info(edit_feature, window_info, wall_info)
                    edit_id = draw_feature(graph2, folder, feature_images, feature_info, x_pixel_ratio)
                    feature_dict[edit_id] = edit_feature
        elif event in ('Insert', "-Feature-") and graph2 and feature_name:
            # Get the user input for the object by creating another window
            # Returns a dictionary of strings (if a key is not used: in list format)
            if feature_name in wall_objects and (not select_fig or type(feature_dict[select_fig]) != type(bd.Wall())):
                popup_info('Please select a Wall for inserting Doors and windows')
                continue
            feature_info = feature_input_window(buildingData.buildingSchedule, feature_name)
            if feature_info == None:
                continue
            if feature_info['-FEATURE LENGTH-'] == 0:
                popup_info('Feature Length Required')
                continue
            if feature_name == 'Wall':
                if feature_info['-FEATURE ANGLE-'] == '' or not feature_info['-FEATURE ANGLE-'].isdigit():
                    feature_info['-FEATURE ANGLE-'] = 0.0
                else:
                    feature_info['-FEATURE ANGLE-'] = float(feature_info['-FEATURE ANGLE-'])
            feature_info['-FEATURE-'] = feature_name
            if feature_name in wall_objects:
                wall = feature_dict[select_fig]
                wall_info = get_building_wall_info(wall)
                wall_info['-FEATURE-'] = 'Wall'
                feature_info['-Wall-'] = wall
            if event == "-Feature-":
                x, y = window_width / 2, window_height / 2
            feature_object = create_feature(feature_info, buildingData, story, x, y,
                                            x_pixel_ratio, feature_info['-SCHEDULE NAME-'])
            if feature_name in wall_objects:
                feature_object.parentID = select_fig
                feature_info = get_feature_info(feature_object, feature_info, wall_info)
                fig_id = draw_feature(graph2, folder, feature_images, feature_info, x_pixel_ratio)
                feature_dict[fig_id] = feature_object
            else:
                draw_wall_and_attachments(graph2, folder, feature_images, feature_object, x_pixel_ratio, feature_dict=feature_dict)
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
        elif  event == 'Load Recent':
            orig_img = PIL.Image.open(r"./blueprint_features/save.png")
            new_size = int(window_size[1] * image_window_percent)
            mult = image_resolution // new_size
            img = resize_img(orig_img, (new_size, new_size))
            x_pixel_ratio = settings['-X RATIO-']
            y_pixel_ratio = settings['-Y RATIO-']
            img = resize_img(orig_img, (new_size, new_size))
            graph1 = window["-GRAPH1-"]  # type: sg.Graph
            graph1.erase()
            graph1.set_size(window_size)
            graph1.change_coordinates((0,0), window_size)
            graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
            window['-TOUT-'].update(visible=False)
            window.Element('-GRAPH1-').Update(visible=True)
            window.Element('-Convert-').Update(visible=True)
            graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
            crop = False
            buildingData = bd.readJSON("save.json")
            blueprint_schedule_creator(buildingData.buildingSchedule, add_only=False)
            if settings['-SAVE CONVERT-']:
                save_convert = True
                graph2 = window["-GRAPH2-"]  # type: sg.Graph
                graph2.set_size(window_size)
                graph2.change_coordinates((0,0), window_size)
                blueprint_2_ID = graph2.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
                switch_to_other_graph(window, '-GRAPH1-', graph1, '-GRAPH2-', graph2, window_size)
                window.Element('-Convert-').Update(visible=False)
                window.Element('-EXPORT IFC-').Update(visible=True)
                graph_draw_from_data(buildingData.listOfStories[story], graph2,
                                     feature_dict, x_pixel_ratio, folder, feature_images)
        elif  event == 'Quick Save':
            settings['-SAVE CONVERT-'] = save_convert
            settings['-X RATIO-'] = x_pixel_ratio
            settings['-Y RATIO-'] = y_pixel_ratio
            orig_img.save('./blueprint_features/save.png')
            bd.writeJSON(buildingData, "save.json")
            popup_info('Saved!')
        elif  event == 'Add To Schedule':
            blueprint_schedule_creator(buildingData.buildingSchedule)
    # --------------------------------- Close & Exit ---------------------------------
    window.close()

make_dpi_aware()  # This makes the resolution better for high res screens
main_gui()
