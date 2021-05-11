HELP = """
text-fabric-make {dataset} serve {page}
text-fabric-make {dataset} ship
text-fabric-make {dataset} {client} ship
text-fabric-make {dataset} {client} {command} [parameters]

dataset: a Text-Fabric dataset such as "nena", "bhsa"
client: the name of a layered-search client as defined in the config.yaml
        in annotation/app-«dataset»

command:

-h
--help
help  : print help and exit

serve [page] : serve search page locally, default index.html
v            : show current version of search-client code
i            : increase version
config       : build corpus config file
corpus       : build corpus data file
client       : build the layered-search client in the destination repo app-«dataset»
clientdebug  : same as taks client but put it in debug mode
debug on|off : set debug flag of the client on or off
publish      : publish the layered search client on the Github Pages of app-«dataset»
ship         : performs all build steps: i, config, corpus, client, debug off, publish
               if {client} is given, ships this client,
               otherwise ships all clients for the dataset
"""
