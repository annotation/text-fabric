# Display

??? abstract "Generic/specific"
    Displaying nodes is an intricate mix of functionality that is shared by all apps
    and that is specific to some app.
    Here is our logistics of pretty displays.

    Like a number of other methods `pretty()` is defined as a generic function and
    added as a method to each *app*:

    ```python
    app.pretty = types.MethodType(pretty, app)
    ```

    So although we define `pretty(app, ...)` as a generic function,
    through its argument `app` we can call app specific functionality.

    We follow this pattern for quite a bit of functions.
    They all have `app` as first argument.

    The case of `pretty()` is the most intricate one, since there is a *lot* of generic
    functionality and a lot of corpus specific functionality, as is evident from examples of the 
    BHSA corpus and one from the Uruk corpus below.

    Here is the flow of information for `pretty()`:

    1. definition as a generic function
       [`pretty()`]({{tfghb}}/{{c_appdisplay}});
    2. this function fetches the relevant display parameters and gathers information
       about the node to display, e.g. its boundary slots;
    3. armed with this information, it calls the app-dependent `_pretty()` function,
       e.g. from
       [uruk]({{tfghb}}/{{c_uruk_app}})
       or
       [bhsa]({{tfghb}}/{{c_bhsa_app}});
    4. `_pretty()` is a function that calls itself recursively for all other nodes that
       are involved in the display;
    5. for each node that `_pretty()` is going to display,
		   it first computes a few standard
       things for that node by means of a generic function   
       [`prettyPre()`]({{tfghb}}/{{c_appdisplay}});
			 in particular, it will be computed whether
       the display of the node in question fits in the display of the node
			 where it all began with, or whether parts of the display should be clipped;
			 also, a header label for the
       current node will be comnposed, including relevant hyperlinks and optional extra
       information reuqired by the display options;
    6. finally, it is the turn of the app-dependent `_pretty()`
		   to combine the header label
       with the displays it gets after recursively calling itself for subordinate nodes.

    ![bhsa](../images/bhsa-example.png)

    Above: BHSA pretty display

    Below: Uruk pretty display

    ![uruk](../images/uruk-example.png)

