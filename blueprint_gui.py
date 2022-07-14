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

import building_data as bd

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
        sg.Popup('Page Number Required!')
        return None

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
        if temp_image is None:
            sg.popup('Page Not Found!!')
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

def main_gui():
    # --------------------------------- Define Layout ---------------------------------
    # Right click menu for graphs
    graph1_menu_def = ['&Right', ['Rotate', 'Set Distance']]
    graph2_menu_def = ['&Right', ['Delete', 'Edit', 'Insert', 'Toggle']]
    # First is the top menu
    menu_def = [['&File', ['&New       ALT-N', '&Save      ALT-S', 'E&xit']],
                ['&Edit', ['Extract Feature', '!Add Story']]]

    # Second the window layout...2 columns
    left_col = [[sg.Text('Feature List', size=(30, 1), key='-FOLDER-')],
                [sg.Listbox(values=[], enable_events=True, size=(30,20),key='-FILE LIST-')],# This creates a listbox for the images in the folder
                [sg.Button('add feature', key='-Feature-')], # This allows the features to be added to the converted blueprint
                [sg.Button('Convert', key='-Convert-')],
                [sg.Listbox(values=[], enable_events=True, size=(30,10),key='-STORY LIST-')]]

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
                  [sg.Text('_'*60, key='-Hdivider-')],
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

    # -------------------------------- Get Monitor info --------------------------------
    temp = sg.Window('', [[sg.Text('')]]).finalize()
    root = tkinter.Tk()
    temp.close()
    window_width = root.winfo_screenwidth()
    window_height = root.winfo_screenheight()
    root.destroy()
    print('{}\n{}'.format(window_width, window_height))
    # --------------------------------- Create Window ---------------------------------
    window = sg.Window('Blueprint Conversion', layout, resizable=False).finalize()
    window.Maximize()
    window.Element('-STORY LIST-').Update(visible=False)
    window.Element('-GRAPH1-').Update(visible=False)
    window.Element('-GRAPH2-').Update(visible=False)
    window.Element('-Convert-').Update(visible=False)

    # --------------------------------- Add feature objects ---------------------------
    story = 0
    buildingData = bd.BuildingData()
    wall_objects = ('Door', 'Window')
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
    window['-FILE LIST-'].update(available_features) # door_right.gif

    # ----- Run the Event Loop -----
    dragging1 = dragging2 = crop = set_distance = extract_feature = False
    graph1 = window["-GRAPH1-"]
    #help(graph1)
    #exit(0)
    graph1.bind('<Button-3>', '+RIGHT1+')
    graph2 = window["-GRAPH2-"]
    graph2.bind('<Button-3>', '+RIGHT2+')
    start_point = end_point = filename = feature_name = select_fig = img = None
    orig_img = a_set = bound_top = bound_bottom = fig = a_point = y_pixel_ratio = None
    x_pixel_ratio = feature_path = user_distance = prior_rect = start_point1 = None
    end_point1 = graph2 = None
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
            mult = 10
            new_size = 1000
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
                        sg.Popup('Story Information must be correctly added')
                        story_info = story_input_tool('First Floor')
                    else:
                        story_info = story_input_tool(story_info['-STORY NAME-'])
                buildingData.appendStory(bottomElevation = bd.Elevation(story_info['-BOTTOM ELEVATION-']), \
                                        topElevation = bd.Elevation(story_info['-TOP ELEVATION-']))
                sg.Popup('Blueprint is loading...')
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
            if orig_img:
                img = resize_img(orig_img, (new_size, new_size))
                graph1 = window["-GRAPH1-"]  # type: sg.Graph
                graph1.erase()
                graph1.set_size(img.size)
                graph1.change_coordinates((0,0), (img.size[0], img.size[1]))
                graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
                window['-Hdivider-'].update('_'*int(new_size/16))
                window['-TOUT-'].update(visible=False)
                window.Element('-GRAPH1-').Update(visible=True)
                sg.popup('Select the area of interest.')
                crop = True
        elif event == '-FILE LIST-':    # A file was chosen from the listbox
            try:
                feature_name = values['-FILE LIST-'][0]
                feature_path = os.path.join(folder, feature_images[feature_name])
            except Exception as E:
                print('** Error {} **'.format(E)) # something weird happened making the full filename
        elif event == '-Convert-' and img is not None:    # There is a file to be converted
            blueprint_2_image = copy.deepcopy(img)
            graph2 = window["-GRAPH2-"]  # type: sg.Graph
            graph2.set_size(img.size)
            graph2.change_coordinates((0,0), (img.size[0], img.size[1]))
            blueprint_2_ID = graph2.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
            window.Element('-GRAPH2-').Update(visible=True)
            window.Element('-Convert-').Update(visible=False)
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
                    new_size = 1000
                    graph1 = window["-GRAPH1-"]  # type: sg.Graph
                    if sg.popup_ok_cancel('Area selected\nPress Cancel to redraw') != 'OK':
                        graph1.delete_figure(prior_rect)
                        dragging1 = False
                        continue
                    if crop:
                        orig_img = orig_img.crop((left*mult, top*mult, right*mult, bottom*mult))
                        img = resize_img(orig_img, (new_size, new_size))
                        graph1.erase()
                        graph1.set_size(img.size)
                        graph1.change_coordinates((0,0), (img.size[0], img.size[1]))
                        graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
                        window['-Hdivider-'].update('_'*int(new_size/16))
                        crop = False
                        sg.popup('Pixel Ratios not set!\nRight click on Blueprint to use measurement\ntool and set distance')
                    else:
                        # feature selection gets sent to the feature extractor here
                        h = orig_img.size[0] / img.size[0]
                        v = orig_img.size[1] / img.size[1]
                        feature_img = orig_img.crop((int(left*h), int(top*v), int(right*h), int(bottom*v)))
                        '''
                        # Used for trouble shooting
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
                            sg.Popup('Feature information required for feature extraction')
                        else:
                            print('Extract Feature')
                        graph1.delete_figure(prior_rect)
                        extract_feature = False
                elif set_distance:
                    if not a_set:
                        a_set = end_point1
                        a_point = graph1.DrawCircle(a_set, 4, line_color='black', fill_color='white')
                        sg.Popup('Select point B')
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
                                sg.Popup('x-axis set')
                                print(x_pixel_ratio)
                        else:
                            while not user_distance or user_distance['-TOOL LENGTH-'] == 0:
                                user_distance = measure_tool_input_window('Input y-axis distance')
                                if user_distance == None:
                                    break
                            if user_distance:
                                y_pixel_ratio = y_distance / user_distance['-TOOL LENGTH-']
                                sg.Popup('y-axis set')
                                print(y_pixel_ratio)
                        graph1.delete_figure(a_point)
                        graph1.delete_figure(b_point)
                        if y_pixel_ratio and x_pixel_ratio:
                            window.Element('-Convert-').Update(visible=True)
                        a_set = a_point = b_point = user_distance = None
                        set_distance = False
                info = 'start X: {} start Y: {}\nend X: {}  end Y: {}'.format(start1_x, start1_y, x, y)
                # sg.popup('Dragging Done!\n{}'.format(info)) # This line can be used for trouble shooting mouse positions
                dragging1 = False
            else:
                x, y = values["-GRAPH2-"]
                end_point2 = (x, y)
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
                # sg.popup('Dragging Done!\n{}'.format(info)) # This line can be used for trouble shooting mouse positions
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
        elif  event == 'Edit':
            if select_fig is None:
                sg.Popup('No Feature selected')
            else:
                print('this works')
        elif event in ('Insert', "-Feature-") and graph2 and feature_name:
            # Get the user input for the object by creating another window
            # Returns a dictionary of strings (if a key is not used: in list format)
            if feature_name in wall_objects and (not select_fig or type(feature_dict[select_fig]) != type(bd.Wall())):
                sg.Popup('Please select a Wall for inserting Doors and windows')
                continue
            feature_info = feature_input_window(feat_types, feature_name)
            if (feature_info == None or feature_info['-FEATURE LENGTH-'] == 0
                or feature_info['-FEATURE WIDTH-'] == 0):
                sg.Popup('Feature Length and Width Required')
                continue
            if feature_info['-FEATURE ANGLE-'] == '':
                feature_info['-FEATURE ANGLE-'] = 0.0
            else:
                feature_info['-FEATURE ANGLE-'] = float(feature_info['-FEATURE ANGLE-'])
            feature_info['-FEATURE TYPE-'] = feature_name
            if feature_name in wall_objects:
                feature_info['-Wall-'] = feature_dict[select_fig]
            rotate_angle = float(feature_info['-FEATURE ANGLE-'])
            new_size = feature_info['-FEATURE LENGTH-'] // x_pixel_ratio
            shape = new_size, new_size
            image_in = image_formating(feature_path, resize=(shape))
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
        elif  event == 'Rotate':
            new_size = 1000
            img = img.transpose(PIL.Image.ROTATE_90)
            graph1 = window["-GRAPH1-"]  # type: sg.Graph
            graph1.erase()
            graph1.set_size(img.size)
            graph1.change_coordinates((0,0), (img.size[0], img.size[1]))
            graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
            window['-Hdivider-'].update('_'*int(new_size/16))
        elif  event == 'Set Distance':
            set_distance = True
            sg.Popup('Select point A')
        elif  event == 'Extract Feature' and graph2:
            sg.Popup('Select the feature to be extracted')
            extract_feature = True
        elif  event == 'Toggle':
            if blueprint_2_ID:
                graph2.delete_figure(blueprint_2_ID)
                blueprint_2_ID = None
            else:
                blueprint_2_ID = graph2.draw_image(data=convert_to_bytes(blueprint_2_image),
                                                   location=(0, blueprint_2_image.size[1]))

    # --------------------------------- Close & Exit ---------------------------------
    window.close()

make_dpi_aware()  # This makes the resolution better for high res screens
main_gui()
