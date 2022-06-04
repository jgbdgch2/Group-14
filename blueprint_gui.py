import PySimpleGUI as sg
import os.path
import PIL.Image
import io
import base64
import ctypes
import platform
import zipfile
from pdf2image import convert_from_path, convert_from_bytes
# import building_data as bd


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

def get_user_digit(message):
    page_num = sg.popup_get_text(message)
    if page_num is not None and page_num.isdigit():
        return int(page_num)
    else:
        sg.Popup('Invalid input')
        return None

def get_pdf_as_image(new_size):
    try:
        filename = sg.popup_get_file('Will not see this message', no_window=True)
        if filename is '':
            return None
        elif(filename.lower()[-4:] != ".pdf"):
            sg.popup("The selected file is not a PDF file!")
        else:
            temp_image = page_num = None
            page_num = get_user_digit('Enter Blueprint Page Number:')
            if not page_num:
                return None
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
        print('** Error {} **'.format(E))
        pass        # get file popup was cancelled
    os.remove(zip_folder)
    return temp_image

make_dpi_aware()  # This makes the resolution better for high res screens

# --------------------------------- Define Layout ---------------------------------
# Right click menu for graphs
graph1_menu_def = ['&Right', ['Rotate', '!&Click', 'Set Distance', 'E&xit']]
graph2_menu_def = ['&Right', ['Delete', '!&Click', 'Insert', 'E&xit']]
# First is the top menu
menu_def = [['&File', ['&Open     Ctrl-O', '&Save      Ctrl-S', 'E&xit']],
            ['&Edit', ['Thing1', 'Thing2']]]

# Second the window layout...2 columns
left_col = [[sg.Text('Feature List', size=(30, 1), key='-FOLDER-')],
            [sg.Listbox(values=[], enable_events=True, size=(30,20),key='-FILE LIST-')],# This creates a listbox for the images in the folder
            [sg.Button('add feature', key='-Feature-')], # This allows the features to be added to the converted blueprint
            [sg.Button('Convert', key='-Convert-')]]

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


# ----- Full layout -----
layout = [[sg.Menu(menu_def, tearoff=False, key='-MENU BAR-')],
          [sg.vtop(sg.Column(left_col, element_justification='c')), sg.VSeperator(),sg.Column(images_col, element_justification='c')]]

# --------------------------------- Create Window ---------------------------------
window = sg.Window('Blueprint Conversion', layout, resizable=True)

# --------------------------------- Add feature objects ---------------------------
folder = os.getcwd()
folder = os.path.join(folder, 'blueprint_features')
try:
    file_list = os.listdir(folder)         # get list of files in folder
except:
    file_list = []
fnames = [f for f in file_list if os.path.isfile(
    os.path.join(folder, f)) and f.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".bmp"))]

window.finalize()
window['-FILE LIST-'].update(fnames)

# ----- Run the Event Loop -----
dragging1 = dragging2 = crop = set_distance = False
graph1 = window["-GRAPH1-"]
#help(graph1)
#exit(0)
graph1.bind('<Button-3>', '+RIGHT1+')
graph2 = window["-GRAPH2-"]
graph2.bind('<Button-3>', '+RIGHT2+')
start_point = end_point = filename = feature_name = None
select_fig = img = orig_img = a_set = None
# --------------------------------- Event Loop ---------------------------------
while True:
    event, values = window.read()
    #if event in (sg.WIN_CLOSED, 'Exit'): # Both of these exit lines do the same thing
        #break
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Open     Ctrl-O':
        temp_img = None
        new_size = 1000
        # TODO set this up as a thread
        temp_img = get_pdf_as_image(new_size)
        if temp_img is not None:
            img = orig_img = temp_img
            graph1 = window["-GRAPH1-"]  # type: sg.Graph
            graph1.erase()
            graph1.set_size(img.size)
            graph1.change_coordinates((0,0), (img.size[0], img.size[1]))
            graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
            window['-Hdivider-'].update('_'*int(new_size/16))
            window['-TOUT-'].update('')
            sg.popup('Select the area of interest.')
            crop = True
    elif event == '-FILE LIST-':    # A file was chosen from the listbox
        try:
            feature_name = os.path.join(folder, values['-FILE LIST-'][0])
        except Exception as E:
            print('** Error {} **'.format(E))
            pass        # something weird happened making the full filename
    elif event == '-Convert-' and img is not None:    # There is a file to be converted
        graph2 = window["-GRAPH2-"]  # type: sg.Graph
        graph2.set_size(img.size)
        graph2.change_coordinates((0,0), (img.size[0], img.size[1]))
        graph2.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
    elif event == "-Feature-" and feature_name is not None:
        new_size = 100
        img = image_formating(feature_name, resize=(new_size, new_size))
        graph2 = window["-GRAPH2-"]  # type: sg.Graph
        graph2.draw_image(data=convert_to_bytes(img), location=(300, img.size[1]))
    elif event == "-GRAPH1-":  # if there's a "Graph" event, then it's a mouse
        x, y = values["-GRAPH1-"]
        if not dragging1:
            start_point1 = (x, y)
            drag_figures = graph1.get_figures_at_location((x,y))
            dragging1 = True
            last1xy = x, y
        else:
            end_point1 = (x, y)
        delta_x, delta_y = x - last1xy[0], y - last1xy[1]
        last1xy = x,y
        if len(drag_figures) > 0:
            select_fig = drag_figures[0] # This will always be the blueprint
        if select_fig is not None and not crop and not set_distance:
            graph1.move_figure(select_fig, delta_x, delta_y)
            graph1.update()
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
        select_fig = drag_figures[-1] # This will always be the figure on top
        if select_fig == drag_figures[0]: # The bottom figure will always be the initial blueprint
            select_fig = None
        if select_fig is not None:
            graph2.move_figure(select_fig, delta_x, delta_y)
            graph2.update()
    elif event.endswith('+UP'):  # The dragging has ended because mouse up
        if dragging1:
            x, y = values["-GRAPH1-"]
            end_point1 = (x, y)
            start1_x, start1_y = start_point1
            if crop:
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
                img = img.crop((left, top, right, bottom))
                img = resize_img(img, (new_size, new_size))
                graph1 = window["-GRAPH1-"]  # type: sg.Graph
                graph1.erase()
                graph1.set_size(img.size)
                graph1.change_coordinates((0,0), (img.size[0], img.size[1]))
                graph1.draw_image(data=convert_to_bytes(img), location=(0, img.size[1]))
                window['-Hdivider-'].update('_'*int(new_size/16))
                crop = False
            elif set_distance:
                if not a_set:
                    a_set = end_point1
                    sg.Popup('Select point B')
                else:
                    x_distance, y_distance = end_point1[0] - a_set[0], end_point1[1] - a_set[1]
                    if x_distance < 0:
                        x_distance = x_distance*-1
                    if y_distance < 0:
                        y_distance = y_distance*-1
                    if x_distance > y_distance:
                        user_distance = get_user_digit('Input x-axis distance')
                        if user_distance:
                            x_pixel_ratio = user_distance / x_distance
                            sg.Popup('x-axis set')
                            print(x_pixel_ratio)
                    else:
                        user_distance = get_user_digit('Input y-axis distance')
                        if user_distance:
                            y_pixel_ratio = user_distance / y_distance
                            sg.Popup('y-axis set')
                            print(y_pixel_ratio)
                    a_set = None
                    set_distance = False
            info = 'start X: {} start Y: {}\nend X: {}  end Y: {}'.format(start1_x, start1_y, x, y)
            # sg.popup('Dragging Done!\n{}'.format(info)) # This line can be used for trouble shooting mouse positions
            dragging1 = False
        else:
            x, y = values["-GRAPH2-"]
            end_point2 = (x, y)
            start2_x, start2_y = start_point2
            info = 'start X: {} start Y: {}\nend X: {}  end Y: {}'.format(start2_x, start2_y, x, y)
            # sg.popup('Dragging Done!\n{}'.format(info)) # This line can be used for trouble shooting mouse positions
            dragging2 = False
    elif event.endswith('+RIGHT2+'): # Right click on graph
        x, y = values["-GRAPH2-"]
        fig = graph2.get_figures_at_location((x,y))
        select_fig = fig[-1]
        if select_fig == fig[0]: # The bottom figure will always be the initial blueprint
            select_fig = None
        else:
            bounds = graph2.get_bounding_box(select_fig)
    elif  event == 'Delete':
        if select_fig is not None:
            graph2.delete_figure(select_fig)
            select_fig = None
    elif event == 'Insert' and feature_name is not None:
        new_size = 100
        img = image_formating(feature_name, resize=(new_size, new_size))
        graph2 = window["-GRAPH2-"]  # type: sg.Graph
        graph2.draw_image(data=convert_to_bytes(img), location=(x, y))
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
# --------------------------------- Close & Exit ---------------------------------
window.close()
