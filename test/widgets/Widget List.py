# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + [markdown] nbsphinx="hidden"
# [Index](Index.ipynb) - [Back](Widget Basics.ipynb) - [Next](Output Widget.ipynb)
# -

# # Widget List

import ipywidgets as widgets

# + [markdown] slideshow={"slide_type": "slide"}
# ## Numeric widgets
# -

# There are many widgets distributed with ipywidgets that are designed to display numeric values.  Widgets exist for displaying integers and floats, both bounded and unbounded.  The integer widgets share a similar naming scheme to their floating point counterparts.  By replacing `Float` with `Int` in the widget name, you can find the Integer equivalent.

# ### IntSlider  
# - The slider is displayed with a specified, initial `value`. Lower and upper bounds are defined by `min` and `max`, and the value can be incremented according to the `step` parameter.
# - The slider's label is defined by `description` parameter 
# - The slider's `orientation` is either 'horizontal' (default) or 'vertical'
# - `readout`  displays the current value of the slider next to it. The options are **True** (default) or **False** 
#     - `readout_format` specifies the format function used to represent slider value. The default is '.2f'
#   

widgets.IntSlider(
    value=7,
    min=0,
    max=10,
    step=1,
    description='Test:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d'
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### FloatSlider  
# -

widgets.FloatSlider(
    value=7.5,
    min=0,
    max=10.0,
    step=0.1,
    description='Test:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='.1f',
)

# An example of sliders **displayed vertically**.

widgets.FloatSlider(
    value=7.5,
    min=0,
    max=10.0,
    step=0.1,
    description='Test:',
    disabled=False,
    continuous_update=False,
    orientation='vertical',
    readout=True,
    readout_format='.1f',
)

# ### FloatLogSlider

# The `FloatLogSlider` has a log scale, which makes it easy to have a slider that covers a wide range of positive magnitudes. The `min` and `max` refer to the minimum and maximum exponents of the `base`, and the `value` refers to the actual value of the slider.

widgets.FloatLogSlider(
    value=10,
    base=10,
    min=-10, # max exponent of base
    max=10, # min exponent of base
    step=0.2, # exponent step
    description='Log Slider'
)

# ### IntRangeSlider

widgets.IntRangeSlider(
    value=[5, 7],
    min=0,
    max=10,
    step=1,
    description='Test:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d',
)

# ### FloatRangeSlider

widgets.FloatRangeSlider(
    value=[5, 7.5],
    min=0,
    max=10.0,
    step=0.1,
    description='Test:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='.1f',
)

# ### IntProgress

widgets.IntProgress(
    value=7,
    min=0,
    max=10,
    description='Loading:',
    bar_style='', # 'success', 'info', 'warning', 'danger' or ''
    style={'bar_color': 'maroon'},
    orientation='horizontal'
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### FloatProgress
# -

widgets.FloatProgress(
    value=7.5,
    min=0,
    max=10.0,
    description='Loading:',
    bar_style='info',
    style={'bar_color': '#ffff00'},
    orientation='horizontal'
)

# The numerical text boxes that impose some limit on the data (range, integer-only) impose that restriction when the user presses enter.
#
# ### BoundedIntText

widgets.BoundedIntText(
    value=7,
    min=0,
    max=10,
    step=1,
    description='Text:',
    disabled=False
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### BoundedFloatText
# -

widgets.BoundedFloatText(
    value=7.5,
    min=0,
    max=10.0,
    step=0.1,
    description='Text:',
    disabled=False
)

# ### IntText

widgets.IntText(
    value=7,
    description='Any:',
    disabled=False
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### FloatText
# -

widgets.FloatText(
    value=7.5,
    description='Any:',
    disabled=False
)

# + [markdown] slideshow={"slide_type": "slide"}
# ## Boolean widgets
# -

# There are three widgets that are designed to display a boolean value.

# ### ToggleButton

widgets.ToggleButton(
    value=False,
    description='Click me',
    disabled=False,
    button_style='', # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Description',
    icon='check' # (FontAwesome names without the `fa-` prefix)
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### Checkbox  
# - `value` specifies the value of the checkbox
# - `indent` parameter places an indented checkbox, aligned with other controls. Options are **True** (default) or **False**    
#
# -

widgets.Checkbox(
    value=False,
    description='Check me',
    disabled=False,
    indent=False
)

# ### Valid
#
# The valid widget provides a read-only indicator.

widgets.Valid(
    value=False,
    description='Valid!',
)

# + [markdown] slideshow={"slide_type": "slide"}
# ## Selection widgets
# -

# There are several widgets that can be used to display single selection lists, and two that can be used to select multiple values.  All inherit from the same base class.  You can specify the **enumeration of selectable options by passing a list** (options are either (label, value) pairs, or simply values for which the labels are derived by calling `str`).
#
# <div class="alert alert-info">
# Changes in *ipywidgets 8*:
#     
# Selection widgets no longer accept a dictionary of options. Pass a list of key-value pairs instead.
# </div>

# + [markdown] slideshow={"slide_type": "slide"}
# ### Dropdown
# -

widgets.Dropdown(
    options=['1', '2', '3'],
    value='2',
    description='Number:',
    disabled=False,
)

# The following is also valid, displaying the words `'One', 'Two', 'Three'` as the dropdown choices but returning the values `1, 2, 3`.

widgets.Dropdown(
    options=[('One', 1), ('Two', 2), ('Three', 3)],
    value=2,
    description='Number:',
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### RadioButtons
# -

widgets.RadioButtons(
    options=['pepperoni', 'pineapple', 'anchovies'],
#    value='pineapple', # Defaults to 'pineapple'
#    layout={'width': 'max-content'}, # If the items' names are long
    description='Pizza topping:',
    disabled=False
)

# #### With dynamic layout and very long labels

widgets.Box(
    [
        widgets.Label(value='Pizza topping with a very long label:'), 
        widgets.RadioButtons(
            options=[
                'pepperoni', 
                'pineapple', 
                'anchovies', 
                'and the long name that will fit fine and the long name that will fit fine and the long name that will fit fine '
            ],
            layout={'width': 'max-content'}
        )
    ]
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### Select
# -

widgets.Select(
    options=['Linux', 'Windows', 'macOS'],
    value='macOS',
    # rows=10,
    description='OS:',
    disabled=False
)

# ### SelectionSlider

widgets.SelectionSlider(
    options=['scrambled', 'sunny side up', 'poached', 'over easy'],
    value='sunny side up',
    description='I like my eggs ...',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True
)

# ### SelectionRangeSlider
#
# The value, index, and label keys are 2-tuples of the min and max values selected. The options must be nonempty.

import datetime
dates = [datetime.date(2015, i, 1) for i in range(1, 13)]
options = [(i.strftime('%b'), i) for i in dates]
widgets.SelectionRangeSlider(
    options=options,
    index=(0, 11),
    description='Months (2015)',
    disabled=False
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### ToggleButtons
# -

widgets.ToggleButtons(
    options=['Slow', 'Regular', 'Fast'],
    description='Speed:',
    disabled=False,
    button_style='', # 'success', 'info', 'warning', 'danger' or ''
    tooltips=['Description of slow', 'Description of regular', 'Description of fast'],
#     icons=['check'] * 3
)

# ### SelectMultiple
# Multiple values can be selected with <kbd>shift</kbd> and/or <kbd>ctrl</kbd> (or <kbd>command</kbd>) pressed and mouse clicks or arrow keys.

widgets.SelectMultiple(
    options=['Apples', 'Oranges', 'Pears'],
    value=['Oranges'],
    #rows=10,
    description='Fruits',
    disabled=False
)

# + [markdown] slideshow={"slide_type": "slide"}
# ## String widgets
# -

# There are several widgets that can be used to display a string value.  The `Text`, `Textarea`, and `Combobox` widgets accept input.  The `HTML` and `HTMLMath` widgets display a string as HTML (`HTMLMath` also renders math). The `Label` widget can be used to construct a custom control label.

# + [markdown] slideshow={"slide_type": "slide"}
# ### Text
# -

widgets.Text(
    value='Hello World',
    placeholder='Type something',
    description='String:',
    disabled=False   
)

# ### Textarea

widgets.Textarea(
    value='Hello World',
    placeholder='Type something',
    description='String:',
    disabled=False
)

# ### Combobox

widgets.Combobox(
    # value='John',
    placeholder='Choose Someone',
    options=['Paul', 'John', 'George', 'Ringo'],
    description='Combobox:',
    ensure_option=True,
    disabled=False
)

# ### Password
#
# The `Password` widget hides user input on the screen. **This widget is not a secure way to collect sensitive information because:**
#
# + The contents of the `Password` widget are transmitted unencrypted.
# + If the widget state is saved in the notebook the contents of the `Password` widget is stored as plain text.

widgets.Password(
    value='password',
    placeholder='Enter password',
    description='Password:',
    disabled=False
)

# + [markdown] slideshow={"slide_type": "slide"}
# ### Label
#
# The `Label` widget is useful if you need to build a custom description next to a control using similar styling to the built-in control descriptions.
# -

widgets.HBox([widgets.Label(value="The $m$ in $E=mc^2$:"), widgets.FloatSlider()])

# ### HTML

widgets.HTML(
    value="Hello <b>World</b>",
    placeholder='Some HTML',
    description='Some HTML',
)

# ### HTML Math

widgets.HTMLMath(
    value=r"Some math and <i>HTML</i>: \(x^2\) and $$\frac{x+1}{x-1}$$",
    placeholder='Some HTML',
    description='Some HTML',
)

# ## Image

file = open("images/WidgetArch.png", "rb")
image = file.read()
widgets.Image(
    value=image,
    format='png',
    width=300,
    height=400,
)

# + [markdown] slideshow={"slide_type": "slide"}
# ## Button
# -

button = widgets.Button(
    description='Click me',
    disabled=False,
    button_style='', # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Click me',
    icon='check' # (FontAwesome names without the `fa-` prefix)
)
button

# The `icon` attribute can be used to define an icon; see the [fontawesome](https://fontawesome.com/icons) page for available icons. 
# A callback function `foo` can be registered using `button.on_click(foo)`. The function `foo` will be called when the button is clicked with the button instance as its single argument.

# ## Output
#
# The `Output` widget can capture and display stdout, stderr and [rich output generated by IPython](http://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html#module-IPython.display). For detailed documentation, see the [output widget examples](https://ipywidgets.readthedocs.io/en/latest/examples/Output Widget.html).

# ## Play (Animation) widget

# The `Play` widget is useful to perform animations by iterating on a sequence of integers with a certain speed. The value of the slider below is linked to the player.

play = widgets.Play(
    value=50,
    min=0,
    max=100,
    step=1,
    interval=500,
    description="Press play",
    disabled=False
)
slider = widgets.IntSlider()
widgets.jslink((play, 'value'), (slider, 'value'))
widgets.HBox([play, slider])

# ## Date picker
#
# For a list of browsers that support the date picker widget, see the [MDN article for the HTML date input field](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/date#Browser_compatibility).

widgets.DatePicker(
    description='Pick a Date',
    disabled=False
)

# ## Time picker
#
# For a list of browsers that support the time picker widget, see the [MDN article for the HTML time input field](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/time#Browser_compatibility).

widgets.TimePicker(
    description='Pick a Time',
    disabled=False
)

# ## Datetime picker
#
# For a list of browsers that support the datetime picker widget, see the [MDN article for the HTML datetime-local input field](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/datetime-local#Browser_compatibility). For the browsers that do not support the datetime-local input, we try to fall back on displaying separate date and time inputs.
#
# ### Time zones
#
# There are two points worth to note with regards to timezones for datetimes:
# - The browser always picks datetimes using *its* timezone.
# - The kernel always gets the datetimes in the default system timezone of the kernel (see https://docs.python.org/3/library/datetime.html#datetime.datetime.astimezone with `None` as the argument).
#
# This means that if the kernel and browser have different timezones, the default string serialization of the timezones might differ, but they will still represent the same point in time.

widgets.DatetimePicker(
    description='Pick a Time',
    disabled=False
)

# ## Color picker

widgets.ColorPicker(
    concise=False,
    description='Pick a color',
    value='blue',
    disabled=False
)

# ## File Upload
#
# The `FileUpload` allows to upload any type of file(s) into memory in the kernel.

widgets.FileUpload(
    accept='',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False  # True to accept multiple files upload else False
)

# The upload widget exposes a `value` attribute that contains the files uploaded. The value attribute is a tuple with a dictionary for each uploaded file. For instance:
#
# ```python
# uploader = widgets.FileUpload()
# display(uploader)
#
# # upload something...
#
# # once a file is uploaded, use the `.value` attribute to retrieve the content:
# uploader.value
# #=> (
# #=>   {
# #=>     'name': 'example.txt',
# #=>     'type': 'text/plain',
# #=>     'size': 36,
# #=>     'last_modified': datetime.datetime(2020, 1, 9, 15, 58, 43, 321000, tzinfo=datetime.timezone.utc), 
# #=>     'content': <memory at 0x10c1b37c8>
# #=>   },
# #=> )
# ```
#
# Entries in the dictionary can be accessed either as items, as one would any dictionary, or as attributes:
#
# ```
# uploaded_file = uploader.value[0]
# uploaded_file["size"]
# #=> 36
# uploaded_file.size
# #=> 36
# ```
#
# The contents of the file uploaded are in the value of the `content` key. They are a [memory view](https://docs.python.org/3/library/stdtypes.html#memory-views):
#
# ```python
# uploaded_file.content
# #=> <memory at 0x10c1b37c8>
# ```
#
# You can extract the content to bytes:
#
# ```python
# uploaded_file.content.tobytes()
# #=> b'This is the content of example.txt.\n'
# ```
#
# If the file is a text file, you can get the contents as a string by [decoding it](https://docs.python.org/3/library/codecs.html):
#
# ```python
# import codecs
# codecs.decode(uploaded_file.content, encoding="utf-8")
# #=> 'This is the content of example.txt.\n'
# ```
#
# You can save the uploaded file to the filesystem from the kernel:
#
# ```python
# with open("./saved-output.txt", "wb") as fp:
#     fp.write(uploaded_file.content)
# ```
#
# To convert the uploaded file into a Pandas dataframe, you can use a [BytesIO object](https://docs.python.org/3/library/io.html#binary-i-o):
#
# ```python
# import io
# import pandas as pd
# pd.read_csv(io.BytesIO(uploaded_file.content))
# ```
#
# If the uploaded file is an image, you can visualize it with an [image](#Image) widget:
#
# ```python
# widgets.Image(value=uploaded_file.content.tobytes())
# ```
#
# <div class="alert alert-info">
# Changes in *ipywidgets 8*:
#     
# The `FileUpload` changed significantly in ipywidgets 8:
#     
# - The `.value` traitlet is now a list of dictionaries, rather than a dictionary mapping the uploaded name to the content. To retrieve the original form, use `{f["name"]: f.content.tobytes() for f in uploader.value}`.
# - The `.data` traitlet has been removed. To retrieve it, use `[f.content.tobytes() for f in uploader.value]`.
# - The `.metadata` traitlet has been removed. To retrieve it, use `[{k: v for k, v in f.items() if k != "content"} for f in w.value]`.
# </div>
#
# <div class="alert alert-warning">
# Warning: When using the `FileUpload` Widget, uploaded file content might be saved in the notebook if widget state is saved.
# </div>

# ## Controller
#
# The `Controller` allows a game controller to be used as an input device.

widgets.Controller(
    index=0,
)

# ## Container/Layout widgets
#
# These widgets are used to hold other widgets, called children. Each has a `children` property that may be set either when the widget is created or later.

# ### Box

items = [widgets.Label(str(i)) for i in range(4)]
widgets.Box(items)

# ### HBox

items = [widgets.Label(str(i)) for i in range(4)]
widgets.HBox(items)

# ### VBox

items = [widgets.Label(str(i)) for i in range(4)]
left_box = widgets.VBox([items[0], items[1]])
right_box = widgets.VBox([items[2], items[3]])
widgets.HBox([left_box, right_box])

# ### GridBox
#
# This box uses the HTML Grid specification to lay out its children in two dimensional grid. The example below lays out the 8 items inside in 3 columns and as many rows as needed to accommodate the items.

items = [widgets.Label(str(i)) for i in range(8)]
widgets.GridBox(items, layout=widgets.Layout(grid_template_columns="repeat(3, 100px)"))

# ### Accordion

accordion = widgets.Accordion(children=[widgets.IntSlider(), widgets.Text()], titles=('Slider', 'Text'))
accordion

# ### Tabs
#
# In this example the children are set after the tab is created. Titles for the tabs are set in the same way they are for `Accordion`.

tab_contents = ['P0', 'P1', 'P2', 'P3', 'P4']
children = [widgets.Text(description=name) for name in tab_contents]
tab = widgets.Tab()
tab.children = children
tab.titles = [str(i) for i in range(len(children))]
tab

# ### Stacked
#
# The `Stacked` widget can have multiple children widgets as for `Tab` and `Accordion`, but only shows one at a time depending on the value of ``selected_index``:

button = widgets.Button(description='Click here')
slider = widgets.IntSlider()
stacked = widgets.Stacked([button, slider])
stacked  # will show only the button

# This can be used in combination with another selection-based widget to show different widgets depending on the selection:

dropdown = widgets.Dropdown(options=['button', 'slider'])
widgets.jslink((dropdown, 'index'), (stacked, 'selected_index'))
widgets.VBox([dropdown, stacked])

# ### Accordion,  Tab, and Stacked use `selected_index`, not value
#
# Unlike the rest of the widgets discussed earlier, the container widgets `Accordion` and `Tab` update their `selected_index` attribute when the user changes which accordion or tab is selected. That means that you can both see what the user is doing *and* programmatically set what the user sees by setting the value of `selected_index`.
#
# Setting `selected_index = None` closes all of the accordions or deselects all tabs.

# In the cells below try displaying or setting the `selected_index` of the `tab` and/or `accordion`.

tab.selected_index = 3

accordion.selected_index = None

# ### Nesting tabs and accordions
#
# Tabs and accordions can be nested as deeply as you want. If you have a few minutes, try nesting a few accordions or putting an accordion inside a tab or a tab inside an accordion. 
#
# The example below makes a couple of tabs with an accordion children in one of them

tab_nest = widgets.Tab()
tab_nest.children = [accordion, accordion]
tab_nest.titles = ('An accordion', 'Copy of the accordion')
tab_nest

# + [markdown] nbsphinx="hidden"
# [Index](Index.ipynb) - [Back](Widget Basics.ipynb) - [Next](Output Widget.ipynb)
