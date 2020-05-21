# Text-Fabric kernel

Text-Fabric can be used as a service.
The full API of Text-Fabric needs a lot of memory, which makes it unusably for
rapid successions of loading and unloading, like when used in a web server context.

However, you can start TF as a service process, after which many clients can connect to it,
all looking at the same (read-only) data. We call this a **TF kernel**.

The API that the TF kernel offers is limited, it is primarily template search that is offered.
see *Kernel API* below.

## Start

You can run the TF kernel as follows:

```sh
python3 -m tf.server.kernel ddd
```

where `ddd` points to a corpus, see `tf.app.use`.

!!! example
    See the
    [start-up script](https://github.com/annotation/text-fabric/blob/master/tf/server/start.py)
    of the text-fabric browser.

## Connect

The TF kernel can be connected by an other Python program as follows:

```python
from tf.server.kernel import makeTfConnection
TF = makeTfConnection(host, port)
api = TF.connect()
```

After this, `api` can be used to obtain information from the TF kernel.

See the web server of the text-fabric browser, `tf.server.web`.

## Kernel API

The API of the TF kernel is created by the function `makeTfKernel`.

It returns a class `TfKernel` with a number of exposed methods
that can be called by other programs.

For the machinery of interprocess communication we rely on the
[rpyc](https://github.com/tomerfiliba/rpyc) module.
See especially the docs on
[services](https://rpyc.readthedocs.io/en/latest/docs/services.html#services).

!!! explanation "Shadow objects"
    The way rpyc works in the case of data transmission has a pitfall.
    When a service returns a Python object to the client, it
    does not return the object itself, but only a shadow object
    so called *netref* objects. This strategy is called
    [boxing](https://rpyc.readthedocs.io/en/latest/docs/theory.html#boxing).
    To the client the shadow object looks like the real thing,
    but when the client needs to access members, they will be fetched
    on the fly.

    This is a performance problem when the service sends a big list or dict,
    and the client iterates over all its items. Each item will be fetched in
    a separate interprocess call, which causes an enormous overhead.

    Boxing only happens for mutable objects. And here lies the work-around:

    The service must send big chunks of data as immutable objects,
    such as tuples. They are sent within a single interprocess call,
    and fly swiftly through the connecting pipe. 
