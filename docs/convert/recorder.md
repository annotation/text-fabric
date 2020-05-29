# Recorder

Support for round trips of TF data to annotation tools and back.

The scenario is:

*   Prepare a piece of corpus material for plain text use in an annotation tool,
    in this case BRAT.
*   Alongside the plain text, generate a mapping file that maps nodes to 
    character positions in the plain text
*   Use BRAT to annotate the plain text
*   Read the resulting BRAT annotation files and convert them into TF features.
