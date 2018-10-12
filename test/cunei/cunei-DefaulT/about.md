

<div class="hdlinks">
  <a target="_blank" href="https://github.com/Nino-cunei/uruk/blob/master/docs/about.md" title="provenance of this corpus">Uruk IV-III (v1.0)</a>
  <a target="_blank" href="https://github.com/Nino-cunei/uruk/blob/master/docs/transcription.md" title="feature documentation">Feature docs</a>
  <a target="_blank" href="https://dans-labs.github.io/text-fabric/Api/General/#search-templates" title="Search Templates Introduction and Reference">Search help</a>
  <a target="_blank" href="https://nbviewer.jupyter.org/github/Nino-cunei/tutorials/blob/master/search.ipynb" title="Search tutorial in Jupyter Notebook">Search tutorial</a>
</div>



meta | data
--- | ---
Job | DefaulT
Author | Dirk Roorda
Created | 2018-10-12T16:54:24+02:00
Data source | Uruk IV/III: Proto-cuneiform tablets 
version | 1.0
release | 1.1.0
live   | [Nino-cunei/uruk v1.0 (r1.1.0)](https://github.com/Nino-cunei/uruk/releases/download/1.1.0/1.0.zip)
archived   | [10.5281/zenodo.1193841](https://doi.org/10.5281/zenodo.1193841)

Tool | Text-Fabric 6.0.9 [10.5281/zenodo.592193](https://doi.org/10.5281/zenodo.592193)
See also | [Compose results example](https://nbviewer.jupyter.org/github/dans-labs/text-fabric/blob/master/examples/compose.ipynb)


# Uncased numerals

## Dirk Roorda

# Where are the numerals?

We are interested in tablets that lack numerals in their cases.

But we do want to see numerals at the top level: in lines that are not subdivided into cases.

One more constraint: we also require that the tablet does contains cases.

This query finds all witnesses of the fact that there are tablets with numerals and lines with cases, while none of these cases contains any numerals.

## Information requests:

### Sections

```
P001195
P464179
```

### Nodes

```
151512,18052
154571
```

### Search

```
tablet catalogId~P excavation*
/where/
  case
/have/
  /without/
    sign type=numeral
  /-/
/-/
/with/
  case
/-/
  sign type=numeral repeat*
```
