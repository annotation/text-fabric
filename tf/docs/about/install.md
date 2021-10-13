# Install

## As it is now ...

### Python and JupyterLab

Text-Fabric is a Python package, so you absolutely need Python.

JupyterLab is a convenient interface to run Python programs, and Text-Fabric has
been developed with this environment in mind.
If you have not seen Jupyter notebooks before, you can see what it is
[here](https://jupyterlab.readthedocs.io/en/latest/getting_started/overview.html).

!!! hint
    Watch the introductory
    [video](https://www.youtube.com/watch?v=A5YyoCKxEOU&t=4s)
    over there.

If you are new to Python, you can now install both in one go, as a desktop application.
There are apps for Macos, Linux and Windows.

### Download

The apps can be downloaded from
[jupyterlab-desktop](https://github.com/jupyterlab/jupyterlab-desktop),
choose the one that fits your system.

### Install

After downloading, go to your downloads folder and install the application in the way
you are used to, but notice the following:

!!! caution "Macos security warning"
    On the mac, if you just double click the `.pkg` file, you get a security
    warning (unidentified developer) and you are stuck.
    Remedy: right-click the `.pkg` file, answer the dialogbox with `OK`, 
    and your installation will begin.

!!! caution "Installation should be for the current user"
    Normally you install apps for all users on your computer.
    But this app works better if you install it for the current user only.
    Because you'll need to install extra Python modules, and when you do that
    the app needs permission to save those modules.
    When the app is installed for the current user, the app has permission
    to write those files.

How to install for the current user?
It depends on the platform.
See [here](https://github.com/jupyterlab/jupyterlab-desktop/blob/master/user-guide.md#Customizing-the-Bundled-Python-Environment)
if you like. It boils down to the following:

**Macos**

During installation, click "Change install location" and set it to "Install for me only"

**Linux**

After installation, run the following command from a terminal where `username` should be changed
to your username on the system

``` sh
sudo chown -R username:username /opt/JupyterLab
```

**Windows**

No extra instructions. Two installers will be launched, let them work with the same default
location for installation.

Wow, now you have both Python and JupyterLab, you are all set to do Text-Fabric work, including
installing it.

### Install Text-Fabric

Open the JupyterLab desktop application that you just have installed.
You have a fresh, empty notebook in front of you.

In the first cell, type

``` sh
pip install text-fabric
```

You will see that Text-Fabric is downloaded and installed, together with the modules
it depends on.

Now restart the kernel of this notebook by clicking the circular arrow in the toolbar:

![restart](../images/restartkernel.png).

This finishes the installation.
You can wipe out this cell, or start a new notebook.

### Work with Text-Fabric

In a notebook, put this *incantation* in a cell and run it:

```
from tf.app import use
```

And in a next cell, load the corpus data
(here you see the `bhsa` = Hebrew Bible, see `tf.about.corpora` for other options)


```
A = use("bhsa", hoist=globals())
```

If you have worked with the `bhsa` before on the same computer, the data is already there,
and this step will be quick.
Otherwise you will see that the data is being downloaded and prepared for its first use.
That takes a bit of work and produces a long list of all features of the `bhsa` on your screen.

From here you can use the
[start tutorial](https://nbviewer.org/github/annotation/tutorials/blob/master/bhsa/start.ipynb)
to get going, just after **Incantation**.

### Text-Fabric browser

You can also work with Text-Fabric outside any programming context, just in the browser.
A bit like SHEBANQ, the difference is that now your own computer is the one
that serves the website, not something on the internet.

Open a new notebook, and in its first cell type

```
%%sh
text-fabric bhsa
```

Wait a few seconds and you see a new window in your browser
with an interface to submit queries to the corpus.

When you are done, go back to the notebook, and close it.

## As it was before ...

Text Fabric is a Python package on the Python Package Index,
so you can install it directly with `pip3` or `pip` from
the command line.

### Computer

Your computer should be a 64-bit machine and it needs at least 3 GB RAM memory.
It should run Linux, Macos, or Windows.

!!! caution "close other programs"
    When you run the Text-Fabric browser for the first time,
    make sure that most of that minimum of 3GB RAM is actually available,
    and not in use by other programs.

### Python

Install or upgrade Python on your system to at least version 3.6.3.


Go for the 64-bit version. Otherwise Python may not be able to address
all the memory it needs.

The leanest install is provided by [python.org](https://www.python.org/downloads/).

You can also install it from [anaconda.com](https://www.anaconda.com/download).

#### On Windows?

Choose Anaconda over standard Python. The reason is that when you want to add Jupyter
to the mix, you need to have additional developers' tools installed.
The Anaconda distribution has Jupyter out of the box.

When installing Python, make sure that the installer adds the path to Python
to your environment variables.

**Install Chrome or Firefox and set it as your default browser.**
The Text-Fabric browser does not display well in Microsoft Edge,
for Edge does not support the
[details](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
element.

#### On Linux?

On Ubuntu 18.04 Python 3.6 is already installed.
But you have to install pip3 in order to add the Python package text-fabric.

```sh
sudo apt install python3-pip
```

## Text-Fabric

### Installation

(macos or linux (non-anaconda))

```sh
pip3 install text-fabric
```

(windows or linux (anaconda))

```sh
pip install text-fabric
```

#### To 3 or not to 3?

From now on we always use `python3` and `pip3` in instructions.

On Windows you have to say `python` and `pip`.
There are more differences, when you go further with programming.

Also, if you use Anaconda, whether on Windows or Mac or Linux, it is `pip`.

Advice: if you are serious on programming, consider switching to a `Unix`-like
platform, such as Linux or the Mac (macos).

#### On Linux?

* On Ubuntu the text-fabric script ends up in your `~/.local/bin` directory,
  but this is not on your PATH.
* You need to execute your `.profile` file first by:

```sh
source ~/.profile
```

You need to do this every time when you open a new terminal and
want to run Text-Fabric.
If you get tired of this, you can add this to your `.bashrc` file:

```sh
PATH="~/.local/bin:${PATH}"
export PATH
```
    
### Upgrade Text-Fabric

```sh
pip3 install --upgrade text-fabric
```

### TF apps and data

In order to work with a corpus you need its data.

For some corpora there is a TF app, which takes care of downloading and updating that data.

`tf.about.corpora` tells you how to install and update a TF app and get the corpus data.

## Jupyter notebook

Optionally install [Jupyter](https://jupyter.org) as well:

```sh
pip3 install jupyter
```

*Jupyter lab* is a nice context to work with Jupyter notebooks.
Recommended for working with the
the tutorials of Text-Fabric.
Also when you want to copy and paste cells from one notebook
to another.

```sh
pip3 install jupyterlab
jupyter labextension install jupyterlab-toc
```

The toc-extension is handy to get an overview
when working with the lengthy tutorial. It will create an extra
tab in the Jupyter Lab interface with a table of contents of the
current notebook.

Jupyter lab is an interesting off-spring from the marriage between the
Python world and the Javascript world.

In order to install lab extensions you need to have 
[Node](https://nodejs.org/en/) installed.
