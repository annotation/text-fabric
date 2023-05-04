# Install

## If you have already Python on your machine

Make sure you have at least Python 3.7.0

Recommended: install JupyterLab:
fire up a terminal (= command prompt) and say

``` sh
pip install jupyterlab
```

To get text-fabric, you can either fire up a terminal and say:

``` sh
pip install 'text-fabric[all]'
```

or fire up a Jupyter Notebook (`jupyter lab`)

and in a cell say

``` sh
!pip install 'text-fabric[all]'
```

If you are in a notebook on an iPad, you can not install the full text-fabric.
The iPad cannot install the libraries needed for the Text-Fabric browser.
To install a reduced text-fabric, say

``` sh
!pip install text-fabric
```

Now restart this notebook by clicking the circular arrow in the toolbar:

![restart](../images/restartkernel.png).

## If you do not have Python

The fastest way to set up everything you need to use Text-Fabric is by installing the
JupyterLab Desktop application.

This installs both JupyterLab and Python in one go,
as a desktop application running under  Macos, Linux or Windows.

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

In a terminal, say

``` sh
text-fabric annotation/banks
```

Or, in a notebook cell, say

```
!text-fabric annotation/banks
```

Wait a few seconds and you see a new window in your browser
with an interface to submit queries to the corpus.

#### Note for Linux users

* On Ubuntu the `text-fabric` script ends up in your `~/.local/bin` directory,
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
    
#### Note on `[all]`

Text-Fabric has some special capabilities:

* `browser`: the Text-Fabric browser, which runs a local webserver which lets you
  have a browse and search experience in a local web environment;
* `github` and `gitlab`: repository backends from which Text-Fabric can load
  corpus data on-demand.
* `pandas`: for exporting a dataset to Pandas.

You can install Text-Fabric with a selection of capabilities:

* `pip install 'text-fabric'` *without additional capabilities*
* `pip install 'text-fabric[all]'` *with all additional capabilities*
* `pip install 'text-fabric[github]'` *with a github backend*
* `pip install 'text-fabric[gitlab]'` *with a gitlab backend*
* `pip install 'text-fabric[browser]'` *with the text-fabric browser enabled*
* `pip install 'text-fabric[pandas]'` *with pandas export enabled*
* `pip install 'text-fabric[github,browser]'` *with the selected extras*
* `pip install 'text-fabric[github,gitlab]'` *with the selected extras*

Even if Text-Fabric is not installed with certain capabilities,
it will have those capabilities if the required modules are installed.
To see which modules are required for which extras, consult
[setup.cfg](https://github.com/annotation/text-fabric/blob/master/setup.cfg).
