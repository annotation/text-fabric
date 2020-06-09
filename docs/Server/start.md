# Start kernel and webserver

What the `text-fabric` script does is the same as:

```sh
python3 -m tf.server.start
```
    
During start up the following happens:

Kill previous processes
:   The system is searched for non-terminated incarnations of the processes
    it wants to start up.
    If they are encountered, they will be killed, so that they cannot prevent
    a successful start up.

Start TF kernel
:   A `tf.server.kernel` is started.
    This process loads the bulk of the TF data, so it can take a while.
    When it has loaded the data, it sends out a message that loading is done,
    which is picked up by the script.

Start TF web server
:   A short while after receiving the "data loading done" message,
    the TF web server is started.
    
    !!! hint "Debug mode"
        If you have passed `-d` to the `text-fabric` script,
        the **Flask** web server will be started in debug and reload mode.
        That means that if you modify `web.py` or a module it imports,
        the web server will reload itself automatically.
        When you refresh the browser you see the changes.
        If you have changed templates, the css, or the javascript,
        you should do a "refresh from origin".

Load web page
:   After a short while, the default web browser will be started
    with a url and port at which the
    web server will listen. You see your browser being started up
    and the TF page being loaded.

Wait
:   The script now waits till the web server is finished.
    You finish it by pressing Ctrl-C, and if you have used the `-d` flag,
    you have to press it twice.

Terminate the TF kernel"
:   At this point, the `text-fabric` script will terminate the TF kernel.

Clean up
:   Now all processes that have started up have been killed.
    
    If something went wrong in this sequence, chances are that a process keeps running.
    It will be terminated next time you call the `text-fabric`.
    
!!! hint "You can kill too"
    If you run
    
```sh
text-fabric -k
``` 

all tf-browser-related processes will be killed.

```sh
text-fabric -k ddd
```

will kill all such processes as far as they are for data source `ddd`.

## Implementation notes

Different corpora will use different ports for the kernel and webserver communication.

The ports are computed from the arguments with which text-fabric is called.

That is done by the [crc32](https://docs.python.org/3.7/library/zlib.html#zlib.crc32) function.
There is no guarantee that collisions occur, and that the ports computed this way are free.
So we will look for the first available port after this.

On the whole, the following things are fairly well taken care of:

*   Invocations of text-fabric with different arguments lead to different ports
*   Repeated invocations of text-fabric with the same arguments lead to the same ports.

In particular, the following invocations lead to different ports:

```sh
text-fabric banks
```

and

```
text-fabric banks:clone
```

and likewise for all other arguments.

