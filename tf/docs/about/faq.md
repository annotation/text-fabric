# FAQ

**It does not work. Why?**

## Stay up to date!

Always use the latest version of Text-Fabric, because there is still
a lot of development going on.

A working installation contains three parts that are updated occasionally,
sometinmes slowly, other times rapidly:

* text-fabric itself, the Python library that you obtained by `pip3 install text-fabric`;
* TF apps, the apps that are specialized in a specific corpus; you obtained it when you said
  `text-fabric appName` or `A = use(appName)`;
* TF data, which was downloaded by that same statement that downloaded the app.

See `tf.about.install` for instructions how to upgrade these things.


## Latest Text-Fabric

### Text-Fabric cannot be found!

Most likely, you installed Text-Fabric into another Python than you use when you run your
Python programs. See Python Setup below.

### Failed to upgrade Text-Fabric!

When you get errors doing `pip3 install text-fabric`, there is probably an older version around.
You have to say

```sh
pip3 install --upgrade text-fabric
```

If this still does not download the most recent version of `text-fabric`,
it may have been caused by caching. Then say:

```sh
pip3 install --upgrade --no-cache-dir text-fabric
```

You can check what the newest distributed version of Text-Fabric is on
[PyPi](https://pypi.org/project/text-fabric/).

### Failed to upgrade Text-Fabric (still)!

Old versions on your system might get in the way.

Sometimes `pip3 uninstall text-fabric` fails to remove all traces of Text-Fabric.
Here is how you can remove them manually:

* locate the `bin` directory of the current Python, it is something like

  * (Macos regular Python) `/Library/Frameworks/Python.framework/Versions/3.7/bin`
  * (Windows Anaconda) `C:\Users\You\Anaconda3\Scripts`

  Remove the file `text-fabric` from this directory if it exists.

* locate the `site-packages` directory of the current Python, it is something like

  * (Macos regular Python)
    `/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages`

    Remove the subdirectory `tf` from this location, plus all files with
    `text-fabric` in the name.

* After this, you can make a fresh install of `text-fabric`:

```sh
pip3 install text-fabric
```

## Python setup

If you are new to Python, it might be tricky to set up Python the right way.
If you make unlucky choices, and work with trial and error, things might get messed up.
Most of the times when `text-fabric` does not appear to work, it is because of this.
Here are some hints to recover from that.

### Upgrade of Text-Fabric does not have any effect!

Most likely, you have multiple Pythons on your system.
You installed Text-Fabric in one Python, but you are using it in another Python.

This can happen if you installed Python from [python.org](https://www.python.org)
and then later installed Jupyter from Anaconda, which brings its own Python.

You can check whether you are in this situation.

First, on the command line, do 

```sh
text-fabric
```

You will see the version of Text-Fabric that is used when you call the Text-Fabric browser.

Then, in a Jupyter notebook, say

```python
from tf.parameters import VERSION
print(VERSION)
```

You will see the version of Text-Fabric that you use in a Jupyter notebook.

If they are equal, you might use the same Python in both cases.

If they are different, you have to clean up your Python installation.
Ask a local guru, or google your way out. Or read on.

### Other Python versions

The following hygeneic measures are known to be beneficial 
when you have multiple versions of Python on your system.

When you have upgraded Python, remove PATH statements for older versions
from your system startup files.

* For the Macos: look at `.zshrc`, `.bashrc`, and `.bash_profile` in your home directory.
* For Windows: on the command prompt, say `echo %path%` to see what the content
  of your PATH variable is. If you see references to older versions of python
  than you actually work with, they need to be removed.
  [Here is how](https://www.computerhope.com/issues/ch000549.htm)

Do not remove references to Python `2.*`, but only outdated Python `3.*` versions. 

## Text-Fabric browser

### Internal Server Error!

When the TF browser opens with an Internal Server error, the most likely reason is that
the TF kernel has not started up without errors.

Look back at the terminal or command prompt where you started `text-fabric`.

If somewhere down the road you see `Error`, I offer you my apologies!

Copy and paste that error and send it to [me](mailto:text.annotation@icloud.com),
and I'll fix it as soon as I can, and I let you know on the
[issue list](https://github.com/annotation/text-fabric/issues).

### Out of memory!

If TF has run out of memory, you might be able to do something about it.

In this case, during loading TF did not have access too enough RAM memory.
Maybe you had too many programs (or browser tabs) open at that time.

Close as many programs as possible (even better, restart your machine) and try again.
TF is know to work on Windows 10 machines with only 3GB RAM on board,
but only in the best of circumstances.

If your machine has 4GB of RAM, it should be possible to run TF, with care.

## GitHub

Text-Fabric uses the GitHub API to get its apps and data on the fly.

### Github Rate Limit Exceeded!

Two solutions:

1. increase your rate limit by making yourself known to GitHub (**recommended**)
2. use previously downloaded data or get data manually from GitHub

An increased rate limit is more than enough for normal use of using Text-Fabric
with default settings. In this scenario, you always work with the latest
release of Text-Fabric data and apps.

The work needed to increase the rate is fairly simple, but it assumes a bit more
knowledge about how your terminal or your command line prompt operates.

If you work very intensely with data, repeatedly accessing many corpora, it
is a waste to access GitHub for every single load action.
In those cases you can pass extra parameters to the commands by which you load
the data.

This does not require any extra knowledge, except a section of the Text-Fabric API
docs. But you must remember that in order to get the data the first time, you
need to pass different parameters than the subsequent times.

All in all, the second solution requires confidence with cloning and pulling
from GitHub and familiarity with all the ways that Text-Fabric can obtain its data.

See `tf.advanced.repo` for instructions to follow both solutions.
