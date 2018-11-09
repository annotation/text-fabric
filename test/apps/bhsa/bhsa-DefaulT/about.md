

<div class="hdlinks">
  <a target="_blank" href="https://etcbc.github.io/bhsa" title="provenance of this corpus">BHSA</a>
  <a target="_blank" href="https://dans-labs.github.io/text-fabric/Writing/Hebrew/" title="Hebrew characters and transcriptions">Character table</a>
  <a target="_blank" href="https://etcbc.github.io/bhsa/features/hebrew/c/0_home.html" title="BHSA feature documentation">Feature docs</a>
  <a target="_blank" href="https://dans-labs.github.io/text-fabric/Api/General/#search-templates" title="Search Templates Introduction and Reference">Search Reference</a>
  <a target="_blank" href="https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/search.ipynb" title="Search tutorial in Jupyter Notebook">Search tutorial</a>
</div>



meta | data
--- | ---
Job | DefaulT
Author | Dirk Roorda
Created | 2018-11-09T13:22:04+01:00
Data source | BHSA = Biblia Hebraica Stuttgartensia Amstelodamensis
version | c
release | 1.4
download   | [etcbc/bhsa v:c (r1.4)](https://github.com/etcbc/bhsa/releases/download/1.4/c.zip)
DOI | [10.5281/zenodo.1007624](https://doi.org/10.5281/zenodo.1007624)Data source | Phonetic Transcriptions
version | c
release | 1.1
download   | [etcbc/phono v:c (r1.1)](https://github.com/etcbc/phono/releases/download/1.1/c.zip)
DOI | [10.5281/zenodo.1007636](https://doi.org/10.5281/zenodo.1007636)Data source | Parallel Passages
version | c
release | 1.1
download   | [etcbc/parallels v:c (r1.1)](https://github.com/etcbc/parallels/releases/download/1.1/c.zip)
DOI | [10.5281/zenodo.1007642](https://doi.org/10.5281/zenodo.1007642)
Tool | Text-Fabric 6.4.6 [10.5281/zenodo.592193](https://doi.org/10.5281/zenodo.592193)
See also | [Compose results example](https://nbviewer.jupyter.org/github/dans-labs/text-fabric/blob/master/examples/compose.ipynb)


# Relativeless, unparticipled clauses

## Dirk Roorda

# Attributive clauses

*Are there attributive clauses that lack a relativum and are not constructed with a participle?*

As an extra constraint, we do want the clause to contain a verb.

There turn out to be **229** results.

We show the first and last result on the verse pad, and we store two examples in between on the *notepad*.

For the sake of export, we mention the features `typ` and `vs` (verbal stem) in our query. The `*` means that these features do not pose extra restrictions. But mentioning them will include them in the exported CSV.

## Information requests:

### Sections

```
Psalms 119:100
Exodus 9:18
1_Samuel 27:3
Isaiah 42:19
```

### Nodes

```
1420119,448401,111521
```

### Search

```
clause rela=Attr typ*
/without/
  phrase function=Rela
/-/
/without/
  word vt=ptca|ptcp
/-/
  word pdp=verb vs* gn*
```
