# Search

## Search API

The Search API is exposed as `S` or `Search`.

It's main method, `search`,
takes a search template (see `tf.about.searchusage`) as argument.
A template consists of elements that specify nodes with conditions and
relations between them.
The results of a search are instantiations of the search template.
More precisely, each instantiation is a tuple of nodes
that instantiate the elements in the template,
in such a way that the relational pattern expressed in the template
holds between the nodes of the result tuple.

## Implementation note on Search and SearchExe

This class acts as a factory that creates `tf.search.searchexe.SearchExe`
instances which run queries.

The user is given the factory class as search api `S`.

The (public) methods of the factory class has methods for searching.
These methods work on a dedicated instance of `tf.search.searchexe.SearchExe`
within the factory class.
The factory class will create this instance when needed.

A reference to the factory class Search is stored in the SearchExe objects.
This gives the SearchExe objects the possibility to create other
SearchExe objects to perform auxiliary queries.
This is needed to run the queries implied by
quantifiers in the search template.

The search processes done by distinct SearchExe objects do not interfere.

Summarizing: the factory class Search looks to the user like the execution
class SearchExe.
But under the hood, different queries are always performed on different
instances of SearchExe.

### More details

In order to search, an instance of the SearchExe class must be created.
This instance contains all parameters and settings relevant to the search.

The factory Search may contain one instance of a SearchExe.

The factory class Search has methods `study` and `search`,
which create a SearchExe instance and store it inside the Search instance.
After that they call methods with the same name on that SearchExe object.

The factory class Search has methods `fetch`, `count`, `showPlan`.
These call mehtods with the same name on the SearchExe instance stored in
the factory class Search, if it has been created earlier
by `search` or `study`.
If not, an error message is displayed.

All the work involved in searching is performed by the SearchExe object.
The data of a SearchExe object are tied to the parameters of a particular search:
`searchTemplate`, `sets`, `shallow`, `silent`.
This also holds for all data that is created during executions of a query:
`qnodes`, `qedges`, `results`, etc.
