# Helpers

Various functions that have a function that is not directly tied to a class.
These functions are available in `tf.core.helpers`,
so in order to use function `fff`, say

```python
from tf.core.helpers import fff
```

## Messages

??? abstract "shapeMessages"
    Wraps error messages into HTML. The messages come from the TF API,
    through the TF kernel, in response to wrong search templates
    and other mistaken user input.

## HTML and Markdown

??? abstract "\_outLink(text, href, title=None, ...)"
    Produce a formatted HTML link.

??? abstract "mathEsc(val)"
    Produce a representation of *val* where $ signs are escaped to `<span>$</span>`
    so that they are not interpreted as math in a Jupyter notebook.

??? abstract "htmlEsc(val)"
    Produce a representation of *val* that is safe for usage in a Markdown and HTML context.

??? abstract "htmlEsc(val)"
    Produce a representation of *val* that is safe for usage in a HTML context.

??? abstract "mdEsc(val)"
    Produce a representation of *val* that is safe for usage in a Markdown context.

