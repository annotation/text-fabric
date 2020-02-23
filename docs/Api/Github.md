The [`checkRepo()`](Repo.md) function uses the GitHub API.
GitHub has a rate limiting policy for its API of max 60 calls per hour.
This can be too restrictive, and here are two ways to keep working nevertheless.

??? hint "How to increase the rate limit?"
    If you use this function in an application of yours that uses it very often,
    you can increase the limit to 5000 calls per hour by making yourself known.

    * [create a personal access token]({{ghapppers}})
    * Copy your token and put it in an environment variable named `GHPERS`
      on the system where your app runs.
      See below how to do that.
    * If `checkRepo()` finds this variable, it will add the
      token to every GitHub API call it makes, and that will
      increase the rate.
    * Never pass your personal credentials on to others, let them obtain their own!

    You might want to read this:

    * [Read more about rate limiting on Github]({{ghrate}})

    How to put your personal access token into an environment variable?

    ??? note "What is an environment variable?"
        It is a setting on your system that various programs/processes can read.
        On Windows it is part of the `Registry`.

        In this particular case, you put a personal token that you obtain from GitHub
        in such an environment variable.
        When Text-Fabric accesses GitHub, it will look up this token
        first, and pass it to the GitHub API. GitHub then knows who you are and
        will give you more privileges.

    ??? hint "On Mac and Linux"
        Find the file that contains your terminal settings. In many cases that is
        `.bash_profile` in your home directory.

        Some people put commands like these in their `~/.bashrc` file, which is also fine.
        If you do not see a `.bashrc` file, put it into your `.bash_profile` file.

        A slightly more advanced shell than `bash` is `zsh` and it is the default on newer
        Macs. If that is your case, look for a file `.zshrc` in your home directory or
        create one.

        Whatever is your case, pick the file indicated above and edit it.

        ??? hint "How to edit a file in your terminal?"
            If you are already familiar with `vi`, `vim`, `emacs`, or `nano`
            you already know how to do it.

            If not, `nano` is simple editor that is useful for tasks like this.
            Assuming that you want to edit the `.zshrc` in your home directory,
            go to your terminal and say this:

            ```
            nano ~/.zshrc
            ```

            Then you get a view on your file. Then 

            *   press `Ctrl V` a number of times till you are at the end of the file,
            *   type the two lines lines of text (specified in the next step), or
                copy them from the clipboard
            *   type `Ctrl X` to exit; nano will ask you to save changes, type `Y`,
                it will then verify the file name, type `Enter` and you're done

        Put the following lines in this file:

        ``` sh
        GHPERS="xxx"
        export GHPERS
        ```

        where the `xxx` are replaced by your actual token.

        Then restart your terminal or say in an existing terminal

        ```  sh
        source ~/.zshrc
        ```

    ??? hint "On Windows"
        Click on the Start button and type in `environment variable` into the search box.

        Click on `Edit the system environment variables`.

        This will  open up the System Properties dialog to the Advanced tab.

        Click on the `Environment Variables button` at the bottom.

        Click on `New ...` under `User environment variables`.

        Then fill in `GHPERS` under *name* and the token string under *value*.

        Then quit the command prompt and start a new one.

    With this done, you will automatically get the good rate limit,
    whenever you fire up Text-Fabric in the future.

??? hint "How to avoid accessing Github?"
    Another way te avoid being bitten by the rate limit is to reduce the number
    of your access actions to GitHub.

    There are two instances where Text-Fabric wants to access GitHub:

    1. when you start the Text-Fabric browser from the command line
    2. when you give the `use()` command in your Python program (or in a Jupyter Notebook).

    ??? note "Using a corpus for the first time, within the rate limit"
        If you are still within the rate limit, just give the usual commands, such as

        ``` sh
        text-fabric corpus
        ```

        or

        ``` python
        use('corpus', hoist=globals())
        ```

        where `corpus` should be replaced with the real name of your corpus.

        The data will be downloaded to your computer and stored in your
        `~/text-fabric-data` directory tree.

    ??? note "Using a corpus for the first time, after hitting the rate limit"
        If you want to load a new corpus after having passed the rate limit, and not
        wanting to wait an hour, you could directly clone the repos from GitHub:

        Open your terminal, and go to (or create) directory `~/github` (in your
        home directory).

        Inside that directory, go to or create directory `annotation`.
        Go to that directory.

        Then do

        ``` sh
        git clone https://github.com/annotation/app-corpus
        ```

        (replacing `corpus` with the name of your corpus).

        This will fetch the Text-Fabric *app* for that corpus.

        Now the corpus data itself:

        Find out where on GitHub it is (organization/corpus), e.g.
        `Nino-cunei/oldbabylonian` or `etcbc/bhsa`.

        Under your local `~/github`, find or create directory `organization`.
        Then go to that directory and say:

        ``` sh
        git clone https://github.com/organization/corpus
        ```

        (replacing `organization` with the name of the organization where the corpus resides
        and `corpus` with the name of your corpus).
        Now you have all data you need on your system.

        If you want to see by example how to use this data, have a look at
        [repo]({{tutnb}}/banks/repo.ipynb), especially when it discusses `clone`.

        In order to run Text-Fabric without further access to GitHub, say

        ``` sh
        text-fabric corpus:clone checkout=clone
        ```

        or, in a program,

        ``` python
        A = use('corpus:clone', checkData='clone', hoist=globals())
        ```

        This will instruct Text-Fabric to use the app and data from within your `~/github`
        directory tree.

    ??? note "Using a corpus that you already have"
        Depending on how you got the corpus, it is in your
        `~/github` or in your `~/text-fabric-data` directory tree.

        If you cloned it from GitHub or created it yourself, it is in your `~/github` tree;
        if you used the autoload of Text-Fabric it is in your `~/text-fabric-data`.

        In the first case, do this:

        ``` sh
        text-fabric corpus:clone checkout=clone
        ```

        or, in a program,

        ``` python
        A = use('corpus:clone', checkData='clone', hoist=globals())
        ```

        In the second case, do this:

        ``` sh
        text-fabric corpus:local checkout=local
        ```

        or, in a program,

        ``` python
        A = use('corpus:local', checkData='local', hoist=globals())
        ```

        See also [A.use()](../Api/App.md).

    ??? note "Updating a corpus that you already have"
        This can only be done conveniently for corpora that you have cloned
        from GitHub before.

        Suppose you have cloned organization/repo.

        Then, in your terminal:

        ``` sh
        cd ~/github/organization/repo
        git pull origin master
        ```

        (replacing `organization` with the name of the organization where the corpus resides
        and `corpus` with the name of your corpus).

        Now you have the newest corpus data on your system.
