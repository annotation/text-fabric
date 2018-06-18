# Text-Fabric as a service

Text-Fabric can be used as a service.
The full API of Text-Fabric needs a lot of memory, which makes it unusably for
rapid successions of loading and unloading, like when used in a web server context.

However, you can start TF as a server, after which many clients can connect to it,
all looking at the same (read-only) data.

The API that the TF server offers is limited, it is primarily template search that is offered.

See the code in
[tf.server.service](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/service.py)
to get started.
