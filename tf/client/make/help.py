HELP = """
text-fabric-make {org}/{repo} serve {folder}
text-fabric-make {org}/{repo} ship
text-fabric-make {org}/{repo} {client} ship
text-fabric-make {org}/{repo} make [config] output
text-fabric-make {org}/{repo} {client} make [config] output
text-fabric-make {org}/{repo} {client} {command} [parameters]

org/repo: a Text-Fabric dataset in a GitHub repo under org,
          such as "etcbc/bhsa" and "CambridgeSemiticsLab/nena_tf"
client: the name of a layered-search client as defined in the config.yaml
        in «org»/«repo»-search

command:

-h
--help
help  : print help and exit

serve [folder] : serve index search page locally, if folder: serves from that folder
v              : show current version of search-client code
i              : increase version
config         : build corpus config file
corpus         : build corpus data file
client         : build the layered-search client in the destination «org»/«repo»-search
clientdebug    : same as above but put it in debug mode
debug on|off   : set debug flag of the client on or off
publish        : publish the layered search client on the Github Pages of
                 «org»/«repo»-«search»
ship           : performs all build steps:
                 i, config, corpus, client, debug off, publish;
                 if {client} is given, ships this client,
                 otherwise ships all clients for the dataset
make folder    : performs build steps, but does not increase the version.
                 Does not publish, but delivers the app in folder.
                 If folder does not exist, it will be created.
                 If it exists, it will NOT be emptied first.
"""
