

<div class="hdlinks">
  <a target="_blank" href="https://etcbc.github.io/bhsa" title="provenance of this corpus">BHSA</a>
  <a target="_blank" href="https://dans-labs.github.io/text-fabric/Writing/Hebrew/" title="Hebrew characters and transcriptions">Character table</a>
  <a target="_blank" href="https://etcbc.github.io/bhsa/features/hebrew/c/0_home.html" title="BHSA feature documentation">Feature docs</a>
  <a target="_blank" href="https://dans-labs.github.io/text-fabric/Api/General/#search-templates" title="Search Templates Introduction and Reference">Search Reference</a>
  <a target="_blank" href="https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/search.ipynb" title="Search tutorial in Jupyter Notebook">Search tutorial</a>
</div>



meta | data
--- | ---
Job | Medina
Author | Dirk Roorda
Created | 2018-10-25T11:34:36+02:00
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
Tool | Text-Fabric 6.3.1 [10.5281/zenodo.592193](https://doi.org/10.5281/zenodo.592193)
See also | [Compose results example](https://nbviewer.jupyter.org/github/dans-labs/text-fabric/blob/master/examples/compose.ipynb)


# An MQL query by Robert Medina

## Dirk Roorda

Robert Medina and Oliver Glanz developed an MQL query:

```
select all objects where
[clause
    [word FOCUS FIRST lex = ">CR"]
    [UnorderedGroup
      [phrase FOCUS function IN (Adju, Cmpl, Loca, Supp, Time, Modi)]
      [phrase 
        [word FOCUS vt IN (perf, impf)]
      ]
      [phrase FOCUS function = Objc]
    ]
]
```

The translation in TF-search is here.

A little explanation:

The `=:` between the `clause` and the `word` means that they start at the same word.

Embedding is indicated by indentation.

Order is not significant. So the three phrases correspond to an *unordered group* in MQL. 

If you want, you can express order by putting in [relational operators](https://dans-labs.github.io/text-fabric/Api/General/#relational-operators) such as `=:`.

## Information requests:

### Sections

```

```

### Nodes

```

```

### Search

```
clause
  =: word lex=>CR
  phrase function=Adju|Cmpl|Loca|Supp|Time|Modi
  phrase
    word vt=perf|impf
  phrase function=Objc

```
