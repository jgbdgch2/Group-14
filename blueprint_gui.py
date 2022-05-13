import PySimpleGUI as sg
import os.path
import PIL.Image
import io
import base64

# Image handling
def convert_to_bytes(file_or_bytes, resize=None):
    '''
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :return: (bytes) a byte-string object
    :rtype: (bytes)
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
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()



# --------------------------------- Define Layout ---------------------------------
# First is the top menu
menu_def = [['&File', ['&Open     Ctrl-O', '&Save      Ctrl-S', 'E&xit']],
            ['&Edit', ['Thing1', 'Thing2']]]

# Second the window layout...2 columns
# sg.FolderBrowse() allows for simple file selection
left_col = [[sg.Text('', size=(30, 1), key='-FOLDER-')],
            [sg.Listbox(values=[], enable_events=True, size=(30,20),key='-FILE LIST-')],
            [sg.Button('Convert', key='-Convert-')]] # This creates a listbox that shows the images in the folder

# Creates the column for the image
images_col = [[sg.Push(), sg.Text('Open a new project', key='-TOUT-'), sg.Push()],
              [sg.Image(key='-IMAGE1-')],
              [sg.Text('_'*60, key='-Hdivider-')],
              [sg.Image(key='-IMAGE2-')]]


# ----- Full layout -----
layout = [[sg.Menu(menu_def, tearoff=False, key='-MENU BAR-')],
          [sg.vtop(sg.Column(left_col, element_justification='c')), sg.VSeperator(),sg.Column(images_col, element_justification='c')]]

# --------------------------------- Create Window ---------------------------------
window = sg.Window('Blueprint Conversion', layout, resizable=True)

# ----- Run the Event Loop -----
# --------------------------------- Event Loop ---------------------------------
while True:
    event, values = window.read()
    #if event in (sg.WIN_CLOSED, 'Exit'): # Both of these exit lines do the same thing
        #break
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Open     Ctrl-O':
        folder = sg.popup_get_folder('Will not see this message', no_window=True)
        window['-FOLDER-'].update(folder)
        try:
            file_list = os.listdir(folder)         # get list of files in folder
        except:
            file_list = []
        fnames = [f for f in file_list if os.path.isfile(
            os.path.join(folder, f)) and f.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".bmp"))]
        window['-FILE LIST-'].update(fnames)
    elif event == '-FILE LIST-':    # A file was chosen from the listbox
        try:
            filename = os.path.join(folder, values['-FILE LIST-'][0])
            window['-TOUT-'].update('')
            new_size = 400
            window['-IMAGE1-'].update(data=convert_to_bytes(filename, resize=(new_size, new_size)))
            window['-Hdivider-'].update('_'*int(new_size/7))

        except Exception as E:
            print('** Error {} **'.format(E))
            pass        # something weird happened making the full filename
    elif event == '-Convert-' and len(values['-FILE LIST-']) > 0:    # There is a file to be converted
        try:
            filename = os.path.join(folder, values['-FILE LIST-'][0])
            new_size = 400
            window['-IMAGE2-'].update(data=convert_to_bytes(filename, resize=(new_size, new_size)))
        except Exception as E:
            print('** Error {} **'.format(E))
            pass        # something weird happened making the full filename
# --------------------------------- Close & Exit ---------------------------------
window.close()
