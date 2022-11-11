# Install

## Quick, fresh start

### Python and JupyterLab

JupyterLab is a convenient interface to run Python programs, and Text-Fabric has
been developed with this environment in mind.
If you have not seen Jupyter notebooks before, look
[here](https://jupyterlab.readthedocs.io/en/latest/getting_started/overview.html)
or watch this
[video](https://www.youtube.com/watch?v=DKiI6NfSIe8).

Install both Jupyter and Python in one go, as a desktop application running under.
Macos, Linux or Windows.

The Jupyter Desktop App can be downloaded from
[jupyterlab-desktop](https://github.com/jupyterlab/jupyterlab-desktop),
choose the one that fits your system.

After downloading, go to your downloads folder and install the application in the way
you are used to, but notice the following:

**on macos**: right-click the `.pkg` file, answer the dialogbox with `OK`. 

**on all platforms**: install for the current user, not for all users, otherwise
you run into problems later on.

*macos*: click "Change install location" and set it to "Install for me only"

*linux*: after installation, run the following command from a terminal
where `username` should be changed
to your username on the system:

``` sh
sudo chown -R username:username /opt/JupyterLab
```

*windows*: no extra instructions.
Two installers will be launched, let them work with the same default
location for installation.

### Install Text-Fabric

Open the JupyterLab desktop application that you just have installed.
You have a fresh, empty notebook in front of you.

In the first cell, type

``` sh
%pip install text-fabric[all]
```

Text-Fabric is then downloaded and installed,
together with the modules it depends on.

Now restart this notebook by clicking the circular arrow in the toolbar:

![restart](../images/restartkernel.png).

This finishes the installation.
You can wipe out this cell, or start a new notebook.

#### Capabilities

Text-Fabric has some powerful capabilities:

* `browser`: the Text-Fabric browser, which runs a local webserver which lets you
  have a browse and search experience in a local web environment
* `github` and `gitlab`: repository backends from which Text-Fabric can load
  corpus data on-demand.

You can install Text-Fabric with a selection of capabilities:

* `pip install text-fabric` *without additional capabilities*
* `pip install text-fabric[all]` *with all additional capabilities*
* `pip install text-fabric[github]` *with a github backend*
* `pip install text-fabric[gitlab]` *with a gitlab backend*
* `pip install text-fabric[browser]` *with the text-fabric browser enabled*
* `pip install text-fabric[github,browser]` *with the selected extras*
* `pip install text-fabric[github,gitlab]` *with the selected extras*

On some shells you may have to put single quotes around the last argument:

* `pip install 'text-fabric[browser]'`

Even if Text-Fabric is not installed with certain capabilities,
it will have those capabilities if the required modules are installed.

### Work with Text-Fabric

In a notebook, put this *incantation* in a cell and run it:

```
from tf.app import use
```

And in a next cell, load the data of some corpus, e.g. `annotation/banks`.


```
A = use("annotation/banks")
```

The first time you do this you will see that the data is being downloaded and prepared for its first use.
If you do this a second time, the data is already on your computer in preprocessed form, and Text-Fabric
will see that data and load it quickly.

From here you can use a
[tutorial](https://nbviewer.org/github/annotation/banks/blob/master/tutorial/use.ipynb).

More extensive tutorials are available for other corpora, see `tf.about.corpora`.

### Text-Fabric browser

You can also work with Text-Fabric outside any programming context, just in the browser.
A bit like SHEBANQ, the difference is that now your own computer is the one
that serves the website, not something on the internet.

Open a new notebook, and in its first cell type

```
%%sh
text-fabric annotation/banks
```

Wait a few seconds and you see a new window in your browser
with an interface to submit queries to the corpus.

When you are done, go back to the notebook, and close it.

## The long story ...

### Computer

Your computer should be a 64-bit machine and it needs at least 3 GB RAM memory.
It should run Linux, Macos, or Windows.

!!! caution "close other programs"
    When you run the Text-Fabric browser for the first time,
    make sure that most of that minimum of 3GB RAM is actually available,
    and not in use by other programs.

### Python

Install Python on your system (minimum version is 3.6.3).
Make sure to install the 64-bit version.

The leanest install is the standard Python distribution by [python.org](https://www.python.org/downloads/).

You can also install it from [anaconda.com](https://www.anaconda.com/download).

#### On Windows?

Here Anaconda is more convenient than standard Python. 

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

### Text-Fabric

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

### TF data

In order to work with a corpus you need its data.

`tf.about.corpora` tells you how to get the corpus data.

## Jupyter notebook/lab

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
```
