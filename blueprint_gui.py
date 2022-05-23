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

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), PIL.Image.ANTIALIAS)

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

def get_pdf_as_image(new_size):
    try:
        filename = sg.popup_get_file('Will not see this message', no_window=True)
        if filename is '':
            return None
        elif(filename.lower()[-4:] != ".pdf"):
            sg.popup("The selected file is not a PDF file!")
        else:
            page_num = None
            page_num = sg.popup_get_text('Enter Page Number:')
            if page_num is not None and page_num.isdigit():
                page_num = int(page_num)
            else:
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
# Right click menu for graph
graph_menu_def = ['&Right', ['Delete', '!&Click', 'Insert', 'E&xit']]
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
              [sg.Image(key='-IMAGE1-')],
              [sg.Text('_'*60, key='-Hdivider-')],
              [sg.Graph(
                  canvas_size=(0, 0),
                  graph_bottom_left=(0, 0),
                  graph_top_right=(0, 0),
                  key="-GRAPH-",
                  change_submits=True,  # mouse click events
                  right_click_menu=graph_menu_def,
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
dragging = False
graph = window["-GRAPH-"]
#help(graph)
#exit(0)
graph.bind('<Button-3>', '+RIGHT+')
start_point = end_point = filename = feature_name = select_fig = img = None
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
            img = temp_img
        window['-IMAGE1-'].update(data=convert_to_bytes(img))
        window['-Hdivider-'].update('_'*int(new_size/16))
        window['-TOUT-'].update('')
        # TODO select area of interest, change image to graph
    elif event == '-FILE LIST-':    # A file was chosen from the listbox
        try:
            feature_name = os.path.join(folder, values['-FILE LIST-'][0])
        except Exception as E:
            print('** Error {} **'.format(E))
            pass        # something weird happened making the full filename
    elif event == '-Convert-' and img is not None:    # There is a file to be converted
        graph = window["-GRAPH-"]  # type: sg.Graph
        graph.set_size(img.size)
        graph.change_coordinates((0,0), (new_size, new_size))
        graph.draw_image(data=convert_to_bytes(img), location=(0,new_size))
    elif event == "-Feature-" and feature_name is not None:
        new_size = 100
        img = image_formating(feature_name, resize=(new_size, new_size))
        graph = window["-GRAPH-"]  # type: sg.Graph
        graph.draw_image(data=convert_to_bytes(img), location=(300,300))
    elif event == "-GRAPH-":  # if there's a "Graph" event, then it's a mouse
        x, y = values["-GRAPH-"]
        if not dragging:
            start_point = (x, y)
            drag_figures = graph.get_figures_at_location((x,y))
            dragging = True
            lastxy = x, y
        else:
            end_point = (x, y)
        delta_x, delta_y = x - lastxy[0], y - lastxy[1]
        lastxy = x,y
        select_fig = drag_figures[-1] # This will always be the figure on top
        if select_fig == drag_figures[0]: # The bottom figure will always be the initial blueprint
            select_fig = None
        if select_fig is not None:
            graph.move_figure(select_fig, delta_x, delta_y)
            graph.update()
    elif event.endswith('+UP'):  # The dragging has ended because mouse up
        x, y = values["-GRAPH-"]
        end_point = (x, y)
        start_x, start_y = start_point
        info = 'start X: {} start Y: {}\nend X: {}  end Y: {}'.format(start_x, start_y, x, y)
        # sg.popup('Dragging Done!\n{}'.format(info)) # This line can be used for trouble shooting mouse positions
        dragging = False
    elif event.endswith('+RIGHT+'): # Right click on graph
        x, y = values["-GRAPH-"]
        fig = graph.get_figures_at_location((x,y))
        select_fig = fig[-1]
        if select_fig == fig[0]: # The bottom figure will always be the initial blueprint
            select_fig = None
        else:
            bounds = graph.get_bounding_box(select_fig)
    elif  event == 'Delete':
        if select_fig is not None:
            graph.delete_figure(select_fig)
            select_fig = None
    elif event == 'Insert' and feature_name is not None:
        new_size = 100
        img = image_formating(feature_name, resize=(new_size, new_size))
        graph = window["-GRAPH-"]  # type: sg.Graph
        graph.draw_image(data=convert_to_bytes(img), location=(x, y))
# --------------------------------- Close & Exit ---------------------------------
window.close()
