# When you want to contribute

## Structure

Text-Fabric is a core engine with an app infrastructure.
Here is a quick overview of the
[main parts of the code](https://annotation.github.io/text-fabric/tf/about/code.html).

## Paradigm

Text-Fabric has parts that deal with long tables of data, especially the core part.
Here we adopt a plain, iterative style for performance reasons.

Parts that face the user directly, e.g. the top-level parts of an API are suitable for
Object Oriented programming.
We refrain from adding an object-oriented flavour all the way down to the
smallest particles of data.

However, in many cases we prefer Functional techniques to organise functionality:
taking functions as arguments and delivering functions as results of other functions.

In the Javascript parts we particularly are function-oriented.

## Style

Programming the core requires ordinary Python programming and a bit of HTML +
JQUERY + Javascript for the web interface parts.

We use Python (at least 3.9) and ES6 Javascript.

In this project we use linters and formatters for both Python and ES6.

The linter and formatting options are in this directory:

*   Python:
    [`flake8`](https://github.com/annotation/text-fabric/blob/master/codestyle/flake8.txt)
    and
    [`black`](https://github.com/psf/black)

*   ES6:
    [`eslint`](https://github.com/annotation/text-fabric/blob/master/codestyle/eslintrc.txt)
    and
    [`prettier`](https://github.com/annotation/text-fabric/blob/master/codestyle/prettierrc.txt)

Note that in
*   Javascript we use an indent of 2 characters;
*   in Python we use 4 chars, both for control of flow indenting and for
    sub-expression indenting;

Note that in both languages
*   we prefer camelCase names;
    we use underscores only in ALL_CAPS names, mostly constants,
    and private methods may start with an underscore. 

## Releases

We still do not have a formal release procedure with evaluation of intermediate
releases.  The user base is still small, and we react fast to upcoming requirements.

Once we have more diverse users and more developers, we will consider a more
thoughtful release procedure.
