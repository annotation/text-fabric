# Highlight

??? abstract "hlText()"
    ```python
    A.hlText(nodes, highlights, **options)
    ```

		???+ info "Description"
				Outputs highlighted text.
				The function works much the same as 
				['T.text()'](Text.md#text-representation)
				except that you can pass an extra `highlights` parameter
				to direct the highlighting of portions of the output.

		??? info "nodes"
				The sequence of nodes whose text you want to represent.

		??? info "highlights"
				If `None`, no highlighting will occur.

				Otherwise, it should be a dict, mapping nodes to strings or a set of nodes.
				Such strings should be either the empty string, or a color name.
				The empty string leads to a default highlight color (yellow),
				color names lead to highlighting by that color.

				If the highlights are a set, then the nodes in it will be highlighted
				with the default colour.

				If a node maps to a color, then the portion of text that corresponds
				to that node will be highlighted.
