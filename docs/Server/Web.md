# Web site

TF contains a web-server (based on [bottle](http://bottlepy.org),
in which you can enter a search template and it will show you the results.

**Disclaimer: this is work in process, and the website is not yet fully functional,
but the plumbing works**.

??? info "Start up"
    In order to run the server, you need to have the `server` directory of the `text-fabric` repo
    cloned somewhere on your system.

    Open a bash shell, go to `text-fabric/server` and run
    
    ```sh
    ./serve.sh bhsa
    ```
    
    or 

    ```sh
    ./serve.sh cunei
    ```

    This will start up the TF service that can respond to queries, and a Bottle web-server.
    The output will show you to which (local) url you have to navigate in your web browser.
    
    Close the webserver with Ctrl-C (twice).
    After that, the TF service will also be closed.

    If you want to check for stray python processes still running on your system, say

    ```sh
    ps
    ```
    
    on your terminal.

    If there are processes you want to kill, say a process with id 50975:

    ```sh
    kill 50975
    ```

    Later I'll make a pure Python command to start up the processes.
