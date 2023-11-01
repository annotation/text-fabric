HELP = """
tf-make [--backend={backend} {org}/{repo} serve {folder}
tf-make [--backend={backend} {org}/{repo} ship
tf-make [--backend={backend} {org}/{repo} {client} ship
tf-make [--backend={backend} {org}/{repo} make [config] output
tf-make [--backend={backend} {org}/{repo} {client} make [config] output
tf-make [--backend={backend} {org}/{repo} {client} {command} [parameters]

backend: `github` or `gitlab` or a GitLab instance such as `gitlab.huc.knaw.nl`.
          If absent, `github` is assumed.
org/repo: a TF dataset in a GitHub / GitLab repo under org,
          such as `ETCBC/bhsa` and `CambridgeSemiticsLab/nena_tf`
client:   the name of a layered-search client as defined in the config.yaml
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
publish        : publish the layered search client on the GitHub Pages of
                 «org»/«repo»-«search»
ship           : performs all build steps:
                 i, config, corpus, client, debug off, publish;
                 if {client} is given, ships this client,
                 otherwise ships all clients for the dataset
make [folder]  : performs build steps, but does not increase the version.
                 Does not publish, but delivers the app in folder.
                 If folder does not exist, it will be created.
                 If it exists, it will NOT be emptied first.
"""
