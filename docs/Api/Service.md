# Text-Fabric as a service

Text-Fabric can be used as a service.
The full API of Text-Fabric needs a lot of memory, which makes it unusably for
rapid successions of loading and unloading, like when used in a web server context.

However, you can start TF as a server, after which many clients can connect to it,
all looking at the same (read-only) data.

The API that the TF server offers is limited, currently only template search is offered.

Here is a quick tutorial.

To create a server:

Write a script like this:

```python
from tf.service import makeTfServer

PORT = 18981

# say where your corpus files are: locations, modules

VERSION = '2017'
DATABASE = '~/github/etcbc'
BHSA = f'bhsa/tf/{VERSION}'
PHONO = f'phono/tf/{VERSION}'
PARALLELS = f'parallels/tf/{VERSION}'
locations = [DATABASE]
modules = [BHSA, PHONO, PARALLELS]

# generate a server and run it

makeTfServer(locations, modules, PORT).start()
```

To make connection to the server in a client:

```python
from tf.service import makeTfConnection

# say where the server is (host, port)

HOST = 'localhost'
PORT = 18981


# create a connector and use it

TF = makeTfConnection(HOST, PORT)
api = TF.connect()
```

To get data from the server:

```python
    (results, context) = api.search(query, True)
    results = tuple(results)
    context = {feature: context[feature] for feature in context}
```

See the
[BHSA test](https://github.com/Dans-labs/text-fabric/tree/master/test/bhsa)
 directory for a concrete example.
