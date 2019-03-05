# When you want to contribute

## Structure

Text-Fabric is a core engine with an app infrastructure.
Here is a quick overview of the
[main parts of the code](https://annotation.github.io/text-fabric/Code/Overview/):

* The [core API](https://annotation.github.io/text-fabric/Api/Fabric/)
  of TF:
  [TF core code](https://github.com/annotation/text-fabric/tree/master/tf/core)
* The [search API](https://annotation.github.io/text-fabric/Use/Search/)
  of TF:
  [TF search code](https://github.com/annotation/text-fabric/tree/master/tf/search)
* [Writing system functions](https://annotation.github.io/text-fabric/Writing/Transcription/)
  to deal with complext writing systems and transcriptions:
  [TF writing code](https://github.com/annotation/text-fabric/tree/master/tf/writing)
* [Conversion functions](https://annotation.github.io/text-fabric/Create/Convert/)
  to convert to and from the Text-Fabric format:
  [TF conversion code](https://github.com/annotation/text-fabric/tree/master/tf/convert)
* An app-API offered by TF that TF-apps can use:
  [TF applib code](https://github.com/annotation/text-fabric/tree/master/tf/applib)
* A
  [web interface](https://annotation.github.io/text-fabric/Server/Web/)
  and
  [data kernel](https://annotation.github.io/text-fabric/Server/Kernel/):
  [TF server code](https://github.com/annotation/text-fabric/tree/master/tf/server)
* The TF-apps themselves. They are outside the this text-fabric repo, you find them under the same
  [organization](https://github.com/ammotation) as the repos whose names start with `-app`.

## Paradigm

Text-Fabric has parts that deal with long tables of data, especially the core part.
Here we adopt a plain, iterative style for performance reasons.

Parts that face the user directly, e.g. the top-level parts of an API are suitable for
Object Oriented programming.
We refrain from adding an OOP flavour all the way down to the smallest particles of data.

However, in many cases we prefer Functional techniques to organise functionality:
taking functions as arguments and delivering functions as results of other functions.

In the Javascript parts we particularly are function-oriented.

## Style

Programming the core requires ordinary Python programming and a bit of HTML + JQUERY + Javascript for the
web interface parts.

We use Python3 (currently 3.6.3) and ES6 Javascript.

In this project we use linters and formatters for both Python3 and ES6.

The linter and formatting options are in this directory:

* Python 3:
  [flake8](https://github.com/annotation/text-fabric/blob/master/codestyle/flake8.txt)
  and
  [yapf](https://github.com/annotation/text-fabric/blob/master/codestyle/style.yapf.txt)

* ES6:
  [eslint](https://github.com/annotation/text-fabric/blob/master/codestyle/eslintrc.txt)
  and
  [prettier](https://github.com/annotation/text-fabric/blob/master/codestyle/prettierrc.txt)

Note that in both languages
* we use an indent of 2 characters;
  in Python we use 2 chars for control of flow indenting and 4 chars for sub-expression indenting;
* we prefer camelCase names;
  in Python we use underscores only in ALL_CAPS names, mostly constants,
  and private methods may start with an underscore. 

## Releases

We still do not have a formal release procedure with evaluation of intermediate releases.
The user base is still small, and we react fast to upcoming requirements.

Once we have more diverse users and more developers, we will consider a more
thoughtful release procedure.
