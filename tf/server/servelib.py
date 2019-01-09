import json
from io import BytesIO
from zipfile import ZipFile

from flask import request

from ..parameters import ZIP_OPTIONS
from .wrap import setValues


DEFAULT_NAME = 'default'

BATCH = 20


def getInt(x, default=1):
  if len(x) > 15:
    return default
  if not x.isdecimal():
    return default
  return int(x)


def getFormData(config):
  form = {}
  jobName = request.form.get('jobName', '').strip()
  emptyRequest = False
  if jobName:
    form['jobName'] = jobName
    form['loadJob'] = ''
  else:
    emptyRequest = True
    form['jobName'] = DEFAULT_NAME
    form['loadJob'] = '1'
  form['query'] = request.form.get('query', '').replace('\r', '')
  form['messages'] = request.form.get('messages', '') or ''
  form['features'] = request.form.get('features', '') or ''
  form['tuples'] = request.form.get('tuples', '').replace('\r', '')
  form['sections'] = request.form.get('sections', '').replace('\r', '')
  form['appName'] = request.form.get('appName', '')
  form['jobName'] = request.form.get('jobName', '').strip() or DEFAULT_NAME
  form['side'] = request.form.get('side', '')
  form['help'] = request.form.get('help', '')
  form['author'] = request.form.get('author', '').strip()
  form['title'] = request.form.get('title', '').strip()
  form['description'] = request.form.get('description', '').replace('\r', '')
  form['withNodes'] = request.form.get('withNodes', '')
  form['condensed'] = request.form.get('condensed', '')
  form['condenseTp'] = request.form.get('condenseTp', '')
  form['textformat'] = request.form.get('textformat', '')
  form['sectionsExpandAll'] = request.form.get('sectionsExpandAll', '')
  form['tuplesExpandAll'] = request.form.get('tuplesExpandAll', '')
  form['queryExpandAll'] = request.form.get('queryExpandAll', '')
  form['linked'] = getInt(request.form.get('linked', ''), default=1)
  form['passageOpened'] = request.form.get('passageOpened', '')
  form['sectionsOpened'] = request.form.get('sectionsOpened', '')
  form['tuplesOpened'] = request.form.get('tuplesOpened', '')
  form['queryOpened'] = request.form.get('queryOpened', '')
  form['mode'] = request.form.get('mode', '') or 'passage'
  form['position'] = getInt(request.form.get('position', ''), default=1)
  form['batch'] = getInt(request.form.get('batch', ''), default=BATCH)
  form['sec0'] = request.form.get('sec0', '')
  form['sec1'] = request.form.get('sec1', '')
  form['sec2'] = request.form.get('sec2', '')
  form['s0filter'] = request.form.get('s0filter', '')
  setValues(config.OPTIONS, request.form, form, emptyRequest)
  return form


def getAbout(header, provenance, form):
  return f'''
{header}

{provenance}

Job: {form['jobName']}

# {form['title']}

## {form['author']}

{form['description']}

## Information requests:

### Sections

```
{form['sections']}
```

### Nodes

```
{form['tuples']}
```

### Search

```
{form['query']}
```
'''


def zipData(csvs, resultsX, about, form):
  appName = form['appName']
  jobName = form['jobName']

  zipBuffer = BytesIO()
  with ZipFile(
      zipBuffer,
      "w",
      **ZIP_OPTIONS,
  ) as zipFile:

    zipFile.writestr('job.json', json.dumps(form).encode('utf8'))
    zipFile.writestr('about.md', about)
    if csvs is not None:
      for (csv, data) in csvs:
        contents = ''.join(
            ('\t'.join(str(t) for t in tup) + '\n')
            for tup in data
        )
        zipFile.writestr(f'{csv}.tsv', contents.encode('utf8'))
      for (name, data) in (
          ('resultsx', resultsX),
      ):
        if data is not None:
            contents = '\ufeff' + ''.join(
                ('\t'.join('' if t is None else str(t) for t in tup) + '\n')
                for tup in data
            )
            zipFile.writestr(f'resultsx.tsv', contents.encode('utf_16_le'))
  return (f'{appName}-{jobName}.zip', zipBuffer.getvalue())
