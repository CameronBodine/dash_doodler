# Written by Dr Daniel Buscombe, Marda Science LLC
# for the USGS Coastal Change Hazards Program
#
# MIT License
#
# Copyright (c) 2020, Marda Science LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


########################################################
############ IMPORTS ############################################
########################################################

# ##========================================================
# allows loading of functions from the src directory
import sys
sys.path.insert(1, 'src')

##========================================================
import plotly.express as px
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc

# pip install dash-auth
# import dash_auth

from annotations_to_segmentations import *
from plot_utils import *
import fsspec
import io, base64, PIL.Image, json, shutil, os, time
from glob import glob
from datetime import datetime
from urllib.parse import quote as urlquote
from flask import Flask, send_from_directory

##========================================================
import logging
logging.basicConfig(filename=os.getcwd()+os.sep+'logs/'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'.log',  level=logging.INFO) #DEBUG) #encoding='utf-8',
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


########################################################
############ SETTINGS / FILES ############################################
########################################################

#========================================================
fs = fsspec.filesystem('s3', profile='default')
s3files = fs.ls('s3://cmgp-upload-download-bucket/watermasker1/')
s3files = [f for f in s3files if 'jpg' in f]
Ns3files = len(s3files)

##========================================================
DEFAULT_IMAGE_PATH = "assets/logos/dash-default.jpg"

# from defaults import *
# print('Default hyperparameters imported from src/defaults.py')

DEFAULT_PEN_WIDTH = 3
DEFAULT_CRF_DOWNSAMPLE = 4
DEFAULT_RF_DOWNSAMPLE = 8
DEFAULT_CRF_THETA = 1
DEFAULT_CRF_MU = 1
DEFAULT_RF_NESTIMATORS = 3
DEFAULT_CRF_GTPROB = 0.9

# the number of different classes for labels
DEFAULT_LABEL_CLASS = 0

UPLOAD_DIRECTORY = os.getcwd()+os.sep+"assets"
LABELED_DIRECTORY = os.getcwd()+os.sep+"labeled"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

##========================================================

try:
    with open('classes.txt') as f:
        classes = f.readlines()
except: #in case classes.txt does not exist
    print("classes.txt not found or badly formatted. Exit the program and fix the classes.txt file ... otherwie, will continue using default classes. ")
    classes = ['water', 'land']

class_label_names = [c.strip() for c in classes]

NUM_LABEL_CLASSES = len(class_label_names)

if NUM_LABEL_CLASSES<=10:
    class_label_colormap = px.colors.qualitative.G10
else:
    class_label_colormap = px.colors.qualitative.Light24


# we can't have fewer colors than classes
assert NUM_LABEL_CLASSES <= len(class_label_colormap)

class_labels = list(range(NUM_LABEL_CLASSES))

logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
logging.info('loaded class labels:')
for f in class_label_names:
    logging.info(f)

rf_file = 'RandomForestClassifier_'+'_'.join(class_label_names)+'.pkl.z'    #class_label_names
data_file = 'data_'+'_'.join(class_label_names)+'.pkl.z'    #class_label_names

try:
    shutil.move(rf_file, rf_file.replace('.pkl.z','_'+datetime.now().strftime("%d-%m-%Y-%H-%M-%S")+'.pkl.z'))
except:
    pass


try:
    shutil.move(data_file, data_file.replace('.pkl.z','_'+datetime.now().strftime("%d-%m-%Y-%H-%M-%S")+'.pkl.z'))
except:
    pass


##========================================================

results_folder = 'results/results'+datetime.now().strftime("%Y-%m-%d-%H-%M")

try:
    os.mkdir(results_folder)
    logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
    logging.info("Folder created: %s" % (results_folder))
except:
    pass

logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
logging.info("Results will be written to %s" % (results_folder))


## while file not in assets/ ...
usefile = np.random.randint(Ns3files)
file = s3files[usefile]
# print(file.split(os.sep)[-1])
fp = 's3://'+file
with fs.open(fp, 'rb') as f:
    img = np.array(PIL.Image.open(f))[:,:,:3]
    f.close()
    imsave('assets/'+file.split(os.sep)[-1], img)

# downloads 1 image

files = sorted(glob('assets/*.jpg')) + sorted(glob('assets/*.JPG')) + sorted(glob('assets/*.jpeg'))

files = [f for f in files if 'dash' not in f]

logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
logging.info('loaded files:')
for f in files:
    logging.info(f)


########################################################
############ FUNCTIONS ############################################
########################################################

##========================================================
def convert_integer_class_to_color(n):
    return class_label_colormap[n]

def convert_color_class(c):
    return class_label_colormap.index(c)


##========================================================
def make_and_return_default_figure(
    images=[DEFAULT_IMAGE_PATH],
    stroke_color=convert_integer_class_to_color(DEFAULT_LABEL_CLASS),
    pen_width=DEFAULT_PEN_WIDTH,
    shapes=[],
):

    fig = dummy_fig() #plot_utils.

    add_layout_images_to_fig(fig, images) #plot_utils.

    fig.update_layout(
        {
            "dragmode": "drawopenpath",
            "shapes": shapes,
            "newshape.line.color": stroke_color,
            "newshape.line.width": pen_width,
            "margin": dict(l=0, r=0, b=0, t=0, pad=4),
            "height": 650
        }
    )

    return fig

##========================================================
def shapes_to_key(shapes):
    return json.dumps(shapes)

##========================================================
def shapes_seg_pair_as_dict(d, key, seg, remove_old=True):
    """
    Stores shapes and segmentation pair in dict d
    seg is a PIL.Image object
    if remove_old True, deletes all the old keys and values.
    """
    bytes_to_encode = io.BytesIO()
    seg.save(bytes_to_encode, format="png")
    bytes_to_encode.seek(0)

    data = base64.b64encode(bytes_to_encode.read()).decode()

    if remove_old:
        return {key: data}
    d[key] = data

    return d

##===============================================================

UPLOAD_DIRECTORY = os.getcwd()+os.sep+"assets"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
    logging.info('Made the directory '+UPLOAD_DIRECTORY)


##========================================================

# @server.route("/download/<path:path>")
# def download(path):
#     """Serve a file from the upload directory."""
#     return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)

server = Flask(__name__)
app = dash.Dash(server=server)


# # Keep this out of source code repository - save in a file or a database
# VALID_USERNAME_PASSWORD_PAIRS = {
#     'doodler': 'doodler'
# }
#
# #!pip install dash-auth
# auth = dash_auth.BasicAuth(
#     app,
#     VALID_USERNAME_PASSWORD_PAIRS
# )

##========================================================

app.layout = html.Div(
    id="app-container",
    children=[
        html.Div(
            id="banner",
            children=[
                html.H2(
            "Doodler: Fast Interactive Segmentation of Imagery",
            id="title",
            className="seven columns",
        ),
        html.Img(id="logo", src=app.get_asset_url("logos/dash-logo-new.png")),
        # html.Div(html.Img(src=app.get_asset_url('logos/dash-logo-new.png'), style={'height':'10%', 'width':'10%'})), #id="logo",

        html.H2(""),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                ["                                 Label all classes that are present, in all regions of the image those classes occur."]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=True,
        ),
        html.H2(""),
        html.Ul(id="file-list"),

    ], #children
    ), #div banner id

    dcc.Tabs([
        dcc.Tab(label='Imagery and Controls', children=[

        html.Div(
            id="main-content",
            children=[

                html.Div(
                    id="left-column",
                    children=[
                        dcc.Loading(
                            id="segmentations-loading",
                            type="cube",
                            children=[
                                # Graph
                                dcc.Graph(
                                    id="graph",
                                    figure=make_and_return_default_figure(),
                                    config={
                                        'displayModeBar': 'hover',
                                        "displaylogo": False,
                                        # 'modeBarOrientation': 'h',
                                        "modeBarButtonsToAdd": [
                                            "drawrect",
                                            "drawopenpath",
                                            "eraseshape",
                                        ]
                                    },
                                ),
                            ],
                        ),

                    ],
                    className="ten columns app-background",
                ),

                html.Div(
                       id="right-column",
                       children=[

                dcc.Input(id='my-id', value='Enter-user-ID', type="text"),
                html.Button('Submit', id='button'),
                html.Div(id='my-div'),

                # html.H3("Select Image"),
                dcc.Dropdown(
                    id="select-image",
                    optionHeight=15,
                    style={'display': 'none'},#{'fontSize': 13},
                    options = [
                        {'label': image.split('assets/')[-1], 'value': image } \
                        for image in files
                    ],

                    value='assets/logos/dash-default.jpg', #
                    multi=False,
                ),
                # html.Div([html.Div(id='live-update-text'),
                #           dcc.Interval(id='interval-component', interval=2000, n_intervals=0)]),


                # html.P(children="This image/Copy"),
                dcc.Textarea(id="thisimage_output", cols=80, style={'display': 'none'}),
                # html.Br(),

                        html.H6("Label class"),
                        # Label class chosen with buttons
                        html.Div(
                            id="label-class-buttons",
                            children=[
                                html.Button(
                                    #"%2d" % (n,),
                                    "%s" % (class_label_names[n],),
                                    id={"type": "label-class-button", "index": n},
                                    style={"background-color": convert_integer_class_to_color(c)},
                                )
                                for n, c in enumerate(class_labels)
                            ],
                        ),

                        html.H6(id="pen-width-display"),
                        # Slider for specifying pen width
                        dcc.Slider(
                            id="pen-width",
                            min=0,
                            max=5,
                            step=1,
                            value=DEFAULT_PEN_WIDTH,
                        ),


                        # html.Button('Submit', id='submitbutton'),

                        # Indicate showing most recently computed segmentation
                        dcc.Checklist(
                            id="crf-show-segmentation",
                            options=[
                                {
                                    "label": "SEGMENT IMAGE",
                                    "value": "Show segmentation",
                                }
                            ],
                            value=[],
                        ),

                        # html.Br(),
                        # html.P(['------------------------']),
                        dcc.Markdown(
                            ">CRF settings"
                        ),

                        html.H6(id="theta-display"),
                        # Slider for specifying pen width
                        dcc.Slider(
                            id="crf-theta-slider",
                            min=1,
                            max=100,
                            step=1,
                            value=DEFAULT_CRF_THETA,
                        ),

                        html.H6(id="mu-display"),
                        # Slider for specifying pen width
                        dcc.Slider(
                            id="crf-mu-slider",
                            min=1,
                            max=100,
                            step=1,
                            value=DEFAULT_CRF_MU,
                        ),


                        html.H6(id="crf-downsample-display"),
                        # Slider for specifying pen width
                        dcc.Slider(
                            id="crf-downsample-slider",
                            min=2,
                            max=6,
                            step=1,
                            value=DEFAULT_CRF_DOWNSAMPLE,
                        ),

                        # html.H6(id="crf-gtprob-display"),
                        # # Slider for specifying pen width
                        # dcc.Slider(
                        #     id="crf-gtprob-slider",
                        #     min=0.5,
                        #     max=0.95,
                        #     step=0.05,
                        #     value=DEFAULT_CRF_GTPROB,
                        # ),

                        dcc.Markdown(
                            ">Random Forest settings"
                        ),


                        html.H6(id="rf-downsample-display"),
                        # Slider for specifying pen width
                        dcc.Slider(
                            id="rf-downsample-slider",
                            min=2,
                            max=20,
                            step=1,
                            value=DEFAULT_RF_DOWNSAMPLE,
                        ),

                        # html.H6(id="rf-nestimators-display"),
                        # # Slider for specifying pen width
                        # dcc.Slider(
                        #     id="rf-nestimators-slider",
                        #     min=1,
                        #     max=5,
                        #     step=1,
                        #     value=DEFAULT_RF_NESTIMATORS,
                        # ),

                        # dcc.Markdown(
                        #     ">Note that all segmentations are saved automatically. This download button is for quick checks only e.g. when dense annotations obscure the segmentation view"
                        # ),
                        #
                        # html.A(
                        #     id="download-image",
                        #     download="classified-image-"+datetime.now().strftime("%d-%m-%Y-%H-%M")+".png",
                        #     children=[
                        #         html.Button(
                        #             "Download Label Image (optional)",
                        #             id="download-image-button",
                        #         )
                        #     ],
                        # ),

                    ],
                    className="three columns app-background",
                ),
            ],
            className="ten columns",
        ), #main content Div
        ]),


    #     dcc.Tab(label='File List and Instructions', children=[
    #
    #     html.H4(children="Doodler"),
    #     dcc.Markdown(
    #         "> A user-interactive tool for fast segmentation of imagery (designed for natural environments), using a combined Random Forest (RF) - Conditional Random Field (CRF) method. \
    #         Doodles are used to make a RF model, which maps image features to classes to create an initial image segmentation. The segmentation is then refined using a CRF model. \
    #         The RF model is updated each time a new image is doodled in a session, building a more generic model cumulatively for a collection of similar images/classes. CRF post-processing is image-specific"
    #     ),
    #
    #         dcc.Input(id='my-id', value='Enter-user-ID', type="text"),
    #         html.Button('Submit', id='button'),
    #         html.Div(id='my-div'),
    #
    #         html.H3("Select Image"),
    #         dcc.Dropdown(
    #             id="select-image",
    #             optionHeight=15,
    #             style={'fontSize': 13},
    #             options = [
    #                 {'label': image.split('assets/')[-1], 'value': image } \
    #                 for image in files
    #             ],
    #
    #             value='assets/logos/dash-default.jpg', #
    #             multi=False,
    #         ),
    #         html.Div([html.Div(id='live-update-text'),
    #                   dcc.Interval(id='interval-component', interval=2000, n_intervals=0)]),
    #
    #
    #     html.P(children="This image/Copy"),
    #     dcc.Textarea(id="thisimage_output", cols=80),
    #     html.Br(),
    #
    #     dcc.Markdown(
    #         """
    # **Instructions:**
    # * Before you begin, make a new 'classes.txt' file that contains a list of the classes you'd like to label
    # * Optionally, you can copy the images you wish to label into the 'assets' folder (just jpg, JPG or jpeg extension, or mixtures of those, for now)
    # * Enter a user ID (initials or similar). This will get appended to your results to identify you. Results are also timestamped. You may enter a user ID at any time (or not at all)
    # * Select an image from the list (often you need to select the image twice: make sure the image selected matches the image name shown in the box)
    # * Make some brief annotations ('doodles') of every class present in the image, in every region of the image that class is present
    # * Check 'Show/compute segmentation'. The computation time depends on image size, and the number of classes and doodles. Larger image or more doodles/classes = greater time and memory required
    # * If you're not happy, uncheck 'Show/compute segmentation' and play with the parameters. However, it is often better to leave the parameters and correct mistakes by adding or removing doodles, or using a different pen width.
    # * Once you're happy, you can download the label image, but it is already saved in the 'results' folder.
    # * Before you move onto the next image from the list, uncheck 'Show/compute segmentation'.
    # * Repeat. Happy doodling! Press Ctrl+C to end the program. Results are in the 'results' folder, timestamped. Session logs are also timestamped and found in the 'logs' directory.
    # * As you go, the program only lists files that are yet to be labeled. It does this irrespective of your opinion of the segmentation, so you get 'one shot' before you select another image (i.e. you cant go back to redo)
    # * [Code on GitHub](https://github.com/dbuscombe-usgs/dash_doodler).
    # """
    #     ),
    #     dcc.Markdown(
    #         """
    # **Tips:** 1) Works best for small imagery, typically much smaller than 3000 x 3000 px images. This prevents out-of-memory errors, and also helps you identify small features\
    # 2) Less is usually more! It is often best to use small pen width and relatively few annotations. Don't be tempted to spend too long doodling; extra doodles can be strategically added to correct segmentations \
    # 3) Make doodles of every class present in the image, and also every region of the image (i.e. avoid label clusters) \
    # 4) If things get weird, hit the refresh button on your browser and it should reset the application. Don't worry, all your previous work is saved!\
    # 5) Remember to uncheck 'Show/compute segmentation' before you change parameter values or change image\
    # """
    #     ),
    #
    #
    #     ]), #tab 2

        ]),

        html.Div(
            id="no-display",
            children=[
                dcc.Store(id="image-list-store", data=[]),
                # Store for user created masks
                # data is a list of dicts describing shapes
                dcc.Store(id="masks", data={"shapes": []}),
                # Store for storing segmentations from shapes
                # the keys are hashes of shape lists and the data are pngdata
                # representing the corresponding segmentation
                # this is so we can download annotations and also not recompute
                # needlessly old segmentations
                dcc.Store(id="segmentation", data={}),
                dcc.Store(id="classified-image-store", data=""),
            ],
        ), #nos-display div

    ], #children
) #app layout

##============================================================
def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            if 'jpg' in filename:
                files.append(filename)
            if 'JPG' in filename:
                files.append(filename)
            if 'jpeg' in filename:
                files.append(filename)

    labeled_files = []
    for filename in os.listdir(LABELED_DIRECTORY):
        path = os.path.join(LABELED_DIRECTORY, filename)
        if os.path.isfile(path):
            if 'jpg' in filename:
                labeled_files.append(filename)
            if 'JPG' in filename:
                labeled_files.append(filename)
            if 'jpeg' in filename:
                labeled_files.append(filename)

    filelist = 'files_done.txt'

    with open(filelist, 'w') as filehandle:
        for listitem in labeled_files:
            filehandle.write('%s\n' % listitem)
    logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
    logging.info('File list written to %s' % (filelist))

    return sorted(files), sorted(labeled_files)


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/download/{}".format(urlquote(filename))
    return html.A(filename, href=location)


##========================================================
def show_segmentation(image_path,
    mask_shapes,
    callback_context,
    crf_theta_slider_value,
    crf_mu_slider_value,
    results_folder,
    rf_downsample_value,
    crf_downsample_factor,
    # gt_prob,
    my_id_value,
    rf_file,
    data_file,
    multichannel,
    intensity,
    edges,
    texture,
    # sigma_min,
    # sigma_max,
    # n_estimators,
    ):

    gt_prob = .9
    n_estimators = 3

    """ adds an image showing segmentations to a figure's layout """

    # add 1 because classifier takes 0 to mean no mask
    shape_layers = [convert_color_class(shape["line"]["color"]) + 1 for shape in mask_shapes]

    label_to_colors_args = {
        "colormap": class_label_colormap,
        "color_class_offset": -1,
    }

    sigma_min=1; sigma_max=16

    segimg, seg, img, color_doodles, doodles = compute_segmentations(
        mask_shapes, crf_theta_slider_value,crf_mu_slider_value,
        results_folder, rf_downsample_value, # median_filter_value,
        crf_downsample_factor, gt_prob, my_id_value, callback_context, rf_file, data_file,
        multichannel, intensity, edges, texture, 1, 16, n_estimators,
        img_path=image_path,
        shape_layers=shape_layers,
        label_to_colors_args=label_to_colors_args,
    )

    # get the classifier that we can later store in the Store
    segimgpng = img_array_2_pil(segimg) #plot_utils.

    return (segimgpng, seg, img, color_doodles, doodles )


def parse_contents(contents, filename, date):
    return html.Div([
        html.H5(filename),
        html.H6(datetime.fromtimestamp(date)),

        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src=contents),
        html.Hr(),
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

def look_up_seg(d, key):
    """ Returns a PIL.Image object """
    data = d[key]
    img_bytes = base64.b64decode(data)
    img = PIL.Image.open(io.BytesIO(img_bytes))
    return img

def listToString(s):
    # initialize an empty string
    str1 = " "
    # return string
    return (str1.join(s))

# ##========================================================

@app.callback(
    [
    Output("select-image","options"),
    Output("graph", "figure"),
    Output("image-list-store", "data"),
    Output("masks", "data"),
    Output('my-div', 'children'),
    Output("segmentation", "data"),
    Output('thisimage_output', 'value'),
    Output("pen-width-display", "children"),
    Output("theta-display", "children"),
    Output("mu-display", "children"),
    Output("crf-downsample-display", "children"),
    # Output("crf-gtprob-display", "children"),
    Output("rf-downsample-display", "children"),
    # Output("rf-nestimators-display", "children"),
    Output("classified-image-store", "data"),
    ],
    [
    Input("upload-data", "filename"),
    Input("upload-data", "contents"),
    Input("graph", "relayoutData"),
    Input(
        {"type": "label-class-button", "index": dash.dependencies.ALL},
        "n_clicks_timestamp",
    ),
    Input("crf-theta-slider", "value"),
    Input('crf-mu-slider', "value"),
    Input("pen-width", "value"),
    Input("crf-show-segmentation", "value"),
    Input("crf-downsample-slider", "value"),
    # Input("crf-gtprob-slider", "value"),
    Input("rf-downsample-slider", "value"),
    # Input("rf-nestimators-slider", "value"),
    # Input("select-image", "value"),
    ],
    [
    State("image-list-store", "data"),
    State('my-id', 'value'),
    State("masks", "data"),
    State("segmentation", "data"),
    State("classified-image-store", "data"),
    ],
)

# ##========================================================

def update_output(
    uploaded_filenames,
    uploaded_file_contents,
    graph_relayoutData,
    any_label_class_button_value,
    crf_theta_slider_value,
    crf_mu_slider_value,
    pen_width_value,
    show_segmentation_value,
    crf_downsample_value,
    # gt_prob,
    rf_downsample_value,
    # n_estimators,
    # select_image_value,
    image_list_data,
    my_id_value,
    masks_data,
    segmentation_data,
    segmentation_store_data,
    ):
    """Save uploaded files and regenerate the file list."""

    #select_image_value = 'D800_20160308_222135lr03-1.jpg'

    callback_context = [p["prop_id"] for p in dash.callback_context.triggered][0]
    print(callback_context)

    multichannel = True
    intensity = True
    edges = True
    texture = True

    # if uploaded_filenames is not None and uploaded_file_contents is not None:
    #     for name, data in zip(uploaded_filenames, uploaded_file_contents):
    #         save_file(name, data)
    #     image_list_data = []
    #     all_image_value = ''
    #     files = ''
    #     options = []
    # else:
    image_list_data = []
    all_image_value = ''
    files = ''
    options = []

    # if callback_context=='interval-component.n_intervals':
    files, labeled_files = uploaded_files()

    files = [f.split('assets/')[-1] for f in files]
    labeled_files = [f.split('labeled/')[-1] for f in labeled_files]

    files = list(set(files) - set(labeled_files))
    files = sorted(files)

    options = [{'label': image, 'value': image } for image in files]

    print(files)

    if len(files)>0:
        select_image_value = files[0]
    else:
        print("No more files")


    if 'assets' not in select_image_value:
        select_image_value = 'assets'+os.sep+select_image_value

    if callback_context == "graph.relayoutData":
        try:
            if "shapes" in graph_relayoutData.keys():
                masks_data["shapes"] = graph_relayoutData["shapes"]
            else:
                return dash.no_update
        except:
            return dash.no_update

    # elif callback_context == "select-image.value":
    #
    #    masks_data={"shapes": []}
    #    segmentation_data={}

    pen_width = pen_width_value #int(round(2 ** (pen_width_value)))

    # find label class value by finding button with the greatest n_clicks
    if any_label_class_button_value is None:
        label_class_value = DEFAULT_LABEL_CLASS
    else:
        label_class_value = max(
            enumerate(any_label_class_button_value),
            key=lambda t: 0 if t[1] is None else t[1],
        )[0]

    fig = make_and_return_default_figure(
        images = [select_image_value],
        stroke_color=convert_integer_class_to_color(label_class_value),
        pen_width=pen_width,
        shapes=masks_data["shapes"],
    )

    if ("Show segmentation" in show_segmentation_value) and (
        len(masks_data["shapes"]) > 0):
    # if ('submitbutton' in callback_context) and (
    #     len(masks_data["shapes"]) > 0):
        # to store segmentation data in the store, we need to base64 encode the
        # PIL.Image and hash the set of shapes to use this as the key
        # to retrieve the segmentation data, we need to base64 decode to a PIL.Image
        # because this will give the dimensions of the image
        sh = shapes_to_key(
            [
                masks_data["shapes"],
                '', #segmentation_features_value,
                '', #sigma_range_slider_value,
            ]
        )

        rf_file = 'RandomForestClassifier_'+'_'.join(class_label_names)+'.pkl.z'    #class_label_names
        data_file = 'data_'+'_'.join(class_label_names)+'.pkl.z'    #class_label_names

        logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
        logging.info('Saving RF model to %s' % (rf_file))

        logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
        logging.info('Saving data features to %s' % (rf_file))

        segimgpng = None
        if 'median' not  in callback_context:

            # start timer
            if os.name=='posix': # true if linux/mac or cygwin on windows
               start = time.time()
            else: # windows
               start = time.clock()

            segimgpng, seg, img, color_doodles, doodles  = show_segmentation(
                [select_image_value], masks_data["shapes"], callback_context,#median_filter_value,
                 crf_theta_slider_value, crf_mu_slider_value, results_folder, rf_downsample_value, crf_downsample_value, my_id_value, rf_file, data_file, #gt_prob,
                 multichannel, intensity, edges, texture,#n_estimators, # sigma_range_slider_value[0], sigma_range_slider_value[1],
            )

            if os.name=='posix': # true if linux/mac
               elapsed = (time.time() - start)/60
            else: # windows
               elapsed = (time.clock() - start)/60
            print("Processing took "+ str(elapsed) + " minutes")

            lstack = (np.arange(seg.max()) == seg[...,None]-1).astype(int) #one-hot encode

            #np.savez('test', img.astype(np.uint8), lstack.astype(np.uint8), color_doodles.astype(np.uint8), doodles.astype(np.uint8) )

            if type(select_image_value) is list:
                if 'jpg' in select_image_value[0]:
                    colfile = select_image_value[0].replace('assets',results_folder).replace('.jpg','_label'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
                if 'JPG' in select_image_value[0]:
                    colfile = select_image_value[0].replace('assets',results_folder).replace('.JPG','_label'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
                if 'jpeg' in select_image_value[0]:
                    colfile = select_image_value[0].replace('assets',results_folder).replace('.jpeg','_label'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')

                if np.ndim(img)==3:
                    imsave(colfile,label_to_colors(seg-1, img[:,:,0]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False))
                else:
                    imsave(colfile,label_to_colors(seg-1, img==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False))

            else:
                #colfile = select_image_value.replace('assets',results_folder).replace('.jpg','_label'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
                if 'jpg' in select_image_value:
                    colfile = select_image_value.replace('assets',results_folder).replace('.jpg','_label'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
                if 'JPG' in select_image_value:
                    colfile = select_image_value.replace('assets',results_folder).replace('.JPG','_label'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
                if 'jpeg' in select_image_value:
                    colfile = select_image_value.replace('assets',results_folder).replace('.jpeg','_label'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')

                if np.ndim(img)==3:
                    imsave(colfile,label_to_colors(seg-1, img[:,:,0]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False))
                else:
                    imsave(colfile,label_to_colors(seg-1, img==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False))

            logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
            logging.info('RGB label image saved to %s' % (colfile))

            gt_prob = .9
            n_estimators = 3
            settings_dict = np.array([pen_width, crf_downsample_value, rf_downsample_value, crf_theta_slider_value, crf_mu_slider_value,  n_estimators, gt_prob])#median_filter_value,sigma_range_slider_value[0], sigma_range_slider_value[1]

            if type(select_image_value) is list:
                if 'jpg' in select_image_value[0]:
                    numpyfile = select_image_value[0].replace('assets',results_folder).replace('.jpg','_'+my_id_value+'.npz') #datetime.now().strftime("%Y-%m-%d-%H-%M")+
                if 'JPG' in select_image_value[0]:
                    numpyfile = select_image_value[0].replace('assets',results_folder).replace('.JPG','_'+my_id_value+'.npz') #datetime.now().strftime("%Y-%m-%d-%H-%M")+
                if 'jpeg' in select_image_value[0]:
                    numpyfile = select_image_value[0].replace('assets',results_folder).replace('.jpeg','_'+my_id_value+'.npz') #datetime.now().strftime("%Y-%m-%d-%H-%M")+


                if os.path.exists(numpyfile):
                    saved_data = np.load(numpyfile)
                    savez_dict = dict()
                    for k in saved_data.keys():
                        tmp = saved_data[k]
                        name = str(k)
                        savez_dict['0'+name] = tmp
                        del tmp

                    savez_dict['image'] = img.astype(np.uint8)
                    savez_dict['label'] = lstack.astype(np.uint8)
                    savez_dict['color_doodles'] = color_doodles.astype(np.uint8)
                    savez_dict['doodles'] = doodles.astype(np.uint8)
                    savez_dict['settings'] = settings_dict
                    np.savez(numpyfile, **savez_dict )

                    #np.savez(numpyfile, img.astype(np.uint8), lstack.astype(np.uint8), color_doodles.astype(np.uint8), doodles.astype(np.uint8), saved_img, saved_label, )
                else:
                    savez_dict = dict()
                    savez_dict['image'] = img.astype(np.uint8)
                    savez_dict['label'] = lstack.astype(np.uint8)
                    savez_dict['color_doodles'] = color_doodles.astype(np.uint8)
                    savez_dict['doodles'] = doodles.astype(np.uint8)
                    savez_dict['settings'] = settings_dict

                    np.savez(numpyfile, **savez_dict ) #save settings too

            else:
                if 'jpg' in select_image_value:
                    numpyfile = select_image_value.replace('assets',results_folder).replace('.jpg','_'+my_id_value+'.npz') #datetime.now().strftime("%Y-%m-%d-%H-%M")+
                if 'JPG' in select_image_value:
                    numpyfile = select_image_value.replace('assets',results_folder).replace('.JPG','_'+my_id_value+'.npz') #datetime.now().strftime("%Y-%m-%d-%H-%M")+
                if 'jpeg' in select_image_value:
                    numpyfile = select_image_value.replace('assets',results_folder).replace('.jpeg','_'+my_id_value+'.npz') #datetime.now().strftime("%Y-%m-%d-%H-%M")+

                if os.path.exists(numpyfile):
                    saved_data = np.load(numpyfile)
                    savez_dict = dict()
                    for k in saved_data.keys():
                        tmp = saved_data[k]
                        name = str(k)
                        savez_dict['0'+name] = tmp
                        del tmp

                    savez_dict['image'] = img.astype(np.uint8)
                    savez_dict['label'] = lstack.astype(np.uint8)
                    savez_dict['color_doodles'] = color_doodles.astype(np.uint8)
                    savez_dict['doodles'] = doodles.astype(np.uint8)
                    savez_dict['settings'] = settings_dict

                    np.savez(numpyfile, **savez_dict )#save settings too

                    #np.savez(numpyfile, img.astype(np.uint8), lstack.astype(np.uint8), color_doodles.astype(np.uint8), doodles.astype(np.uint8), saved_img, saved_label, )
                else:
                    savez_dict = dict()
                    savez_dict['image'] = img.astype(np.uint8)
                    savez_dict['label'] = lstack.astype(np.uint8)
                    savez_dict['color_doodles'] = color_doodles.astype(np.uint8)
                    savez_dict['doodles'] = doodles.astype(np.uint8)
                    savez_dict['settings'] = settings_dict

                    np.savez(numpyfile, **savez_dict )#save settings too

            del img, seg, lstack, doodles, color_doodles
            logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
            logging.info('Numpy arrays saved to %s' % (numpyfile))

            segmentation_data = shapes_seg_pair_as_dict(
                segmentation_data, sh, segimgpng
            )
            try:
                segmentation_store_data = pil2uri(
                    seg_pil(
                        select_image_value, segimgpng, do_alpha=True
                    ) #plot_utils.
                )
                shutil.copyfile(select_image_value, select_image_value.replace('assets', 'labeled')) #move
            except:
                segmentation_store_data = pil2uri(
                    seg_pil(
                        PIL.Image.open(select_image_value), segimgpng, do_alpha=True
                    ) #plot_utils.
                )
                shutil.copyfile(select_image_value, select_image_value.replace('assets', 'labeled')) #move

        images_to_draw = []
        if segimgpng is not None:
            images_to_draw = [segimgpng]

        fig = add_layout_images_to_fig(fig, images_to_draw) #plot_utils.

        # show_segmentation_value = []

        image_list_data.append(select_image_value)

        masks_data={"shapes": []}
        segmentation_data={}


        ## while file not in assets/ ...
        usefile = np.random.randint(Ns3files)
        file = s3files[usefile]
        #print(file.split(os.sep)[-1])
        fp = 's3://'+file
        with fs.open(fp, 'rb') as f:
            img = np.array(PIL.Image.open(f))[:,:,:3]
            f.close()
            imsave('assets/'+file.split(os.sep)[-1], img)


    if len(files) == 0:
        return [
        options,
        fig,
        image_list_data,
        masks_data,
        segmentation_data,
        'User ID: "{}"'.format(my_id_value) ,
        select_image_value,
        "Pen width (default: %d): %d" % (DEFAULT_PEN_WIDTH,pen_width),
        "Blur factor (default: %d): %d" % (DEFAULT_CRF_THETA, crf_theta_slider_value), #"Blurring parameter for CRF image feature extraction (default: %d): %d"
        "Model independence factor (default: %d): %d" % (DEFAULT_CRF_MU,crf_mu_slider_value), #CRF color class difference tolerance parameter (default: %d)
        "CRF downsample factor (default: %d): %d" % (DEFAULT_CRF_DOWNSAMPLE,crf_downsample_value),
        # "Probability of doodle (default: %f): %f" % (DEFAULT_CRF_GTPROB,gt_prob),
        "RF downsample factor (default: %d): %d" % (DEFAULT_RF_DOWNSAMPLE,rf_downsample_value),
        # "RF estimators per image (default: %d): %d" % (DEFAULT_RF_NESTIMATORS,n_estimators),
        segmentation_store_data,
        ]
    else:
        return [
        options,
        fig,
        image_list_data,
        masks_data,
        segmentation_data,
        'User ID: "{}"'.format(my_id_value) ,
        select_image_value,
        "Pen width (default: %d): %d" % (DEFAULT_PEN_WIDTH,pen_width),
        "Blur factor (default: %d): %d" % (DEFAULT_CRF_THETA, crf_theta_slider_value),
        "Model independence factor  (default: %d): %d" % (DEFAULT_CRF_MU,crf_mu_slider_value),
        "CRF downsample factor (default: %d): %d" % (DEFAULT_CRF_DOWNSAMPLE,crf_downsample_value),
        # "Probability of doodle (default: %f): %f" % (DEFAULT_CRF_GTPROB,gt_prob),
        "RF downsample factor (default: %d): %d" % (DEFAULT_RF_DOWNSAMPLE,rf_downsample_value),
        # "RF estimators per image (default: %d): %d" % (DEFAULT_RF_NESTIMATORS,n_estimators),
        segmentation_store_data,
        ]


##========================================================
# set the download url to the contents of the classified-image-store (so they can be
# downloaded from the browser's memory)
# app.clientside_callback(
#     """
# function(the_image_store_data) {
#     return the_image_store_data;
# }
# """,
#     Output("download-image", "href"),
#     [Input("classified-image-store", "data")],
# )

##========================================================

if __name__ == "__main__":
    print('Go to http://127.0.0.1:8050/ in your web browser to use Doodler')
    app.run_server()
    #app.run(host='0.0.0.0', port=8050) #()
    #debug=True) #debug=True, port=8888)


            # settings_dict = dict()
            # settings_dict['pen_width'] = pen_width
            # settings_dict['crf_downsample_value'] = crf_downsample_value
            # settings_dict['rf_downsample_value'] = rf_downsample_value
            # settings_dict['crf_theta_slider_value'] = crf_theta_slider_value
            # settings_dict['crf_mu_slider_value'] = crf_mu_slider_value
            # settings_dict['median_filter_value'] = median_filter_value
            # settings_dict['n_estimators'] = n_estimators
            # settings_dict['gt_prob'] = gt_prob
            # settings_dict['sigma_range_slider_value'] = sigma_range_slider_value

            # if type(select_image_value) is list:
            #     if 'jpg' in select_image_value[0]:
            #         grayfile = select_image_value[0].replace('assets',results_folder).replace('.jpg','_label_greyscale'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
            #     if 'JPG' in select_image_value[0]:
            #         grayfile = select_image_value[0].replace('assets',results_folder).replace('.JPG','_label_greyscale'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
            #     if 'jpeg' in select_image_value[0]:
            #         grayfile = select_image_value[0].replace('assets',results_folder).replace('.jpeg','_label_greyscale'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
            #
            #     #grayfile = select_image_value[0].replace('assets',results_folder).replace('.jpg','_label_greyscale'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
            #     imsave(grayfile, seg)
            # else:
            #     if 'jpg' in select_image_value:
            #         grayfile = select_image_value.replace('assets',results_folder).replace('.jpg','_label_greyscale'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
            #     if 'JPG' in select_image_value:
            #         grayfile = select_image_value.replace('assets',results_folder).replace('.JPG','_label_greyscale'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
            #     if 'jpeg' in select_image_value:
            #         grayfile = select_image_value.replace('assets',results_folder).replace('.jpeg','_label_greyscale'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
            #
            #     #grayfile = select_image_value.replace('assets',results_folder).replace('.jpg','_label_greyscale'+datetime.now().strftime("%Y-%m-%d-%H-%M")+'_'+my_id_value+'.png')
            #     imsave(grayfile, seg)
            # del img, seg
            # logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
            # logging.info('Greyscale label image saved to %s' % (grayfile))

                # savez_dict = dict()
                # savez_dict['image'] = img.astype(np.uint8)
                # savez_dict['label'] = lstack.astype(np.uint8)
                # savez_dict['color_doodles'] = color_doodles.astype(np.uint8)
                # savez_dict['doodles'] = doodles.astype(np.uint8)
                # np.savez(numpyfile, savez_dict )

        # segmentation_features_value=[
        #     {"label": l.capitalize(), "value": l}
        #     for l in SEG_FEATURE_TYPES
        # ]
        # logging.info(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
        # for l in SEG_FEATURE_TYPES:
        #     logging.info('Using %s for RF feature extraction' % (l))

            # dict_feature_opts = {
            #     key: (key in segmentation_features_value)
            #     for key in SEG_FEATURE_TYPES
            # }

            # dict_feature_opts["sigma_min"] = sigma_range_slider_value[0]
            # dict_feature_opts["sigma_max"] = sigma_range_slider_value[1]
            # dict_feature_opts["n_estimators"] = n_estimators
                        # html.H6("Image Feature Extraction:"),
                        # dcc.Checklist(
                        #     id="rf-segmentation-features",
                        #     options=[
                        #         {"label": l.capitalize(), "value": l}
                        #         for l in SEG_FEATURE_TYPES
                        #     ],
                        #     value=["intensity", "edges", "texture"],
                        #     labelStyle={'display': 'inline-block'}
                        # ),