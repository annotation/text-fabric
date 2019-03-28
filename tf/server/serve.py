import pickle
import markdown
from flask import jsonify, redirect, render_template, make_response

from ..core.helpers import console, wrapMessages
from ..applib.helpers import RESULT
from .wrap import (
    pageLinks,
    passageLinks,
    getValues,
    wrapOptions,
    wrapCondense,
    wrapFormats,
    wrapProvenance,
)
from .servelib import getAbout, getFormData, zipData

TIMEOUT = 180


def serveTable(setup, kind, getx=None, asDict=False):
  form = getFormData(setup.config)
  textFormat = form['textformat'] or None
  task = form[kind].strip()
  openedKey = f'{kind}Opened'
  openedSet = {int(n) for n in form[openedKey].split(',')} if form[openedKey] else set()

  optionSpecs = setup.config.OPTIONS
  options = getValues(optionSpecs, form)

  method = dict if asDict else jsonify

  kernelApi = setup.TF.connect()

  messages = ''
  table = None
  if task:
    (
        table,
        messages,
    ) = kernelApi.table(
        kind,
        task,
        form['features'],
        opened=openedSet,
        fmt=textFormat,
        withNodes=form['withNodes'],
        getx=int(getx) if getx else None,
        **options,
    )

    if messages:
      messages = wrapMessages(messages)

  return method(
      table=table,
      messages=messages,
  )


def serveQuery(setup, getx, asDict=False):
  kind = 'query'
  form = getFormData(setup.config)
  task = form[kind]
  condenseType = form['condenseTp'] or None
  resultKind = condenseType if form['condensed'] else RESULT
  textFormat = form['textformat'] or None
  openedKey = f'{kind}Opened'
  openedSet = {int(n) for n in form[openedKey].split(',')} if form[openedKey] else set()

  optionSpecs = setup.config.OPTIONS
  options = getValues(optionSpecs, form)

  pages = ''
  features = ''

  kernelApi = setup.TF.connect()
  method = dict if asDict else jsonify
  total = 0

  if task:
    messages = ''
    table = None
    if task in setup.wildQueries:
      messages = (
          f'Aborted because query is known to take longer than {TIMEOUT} second'
          + ('' if TIMEOUT == 1 else 's')
      )
    else:
      try:
        (
            table,
            messages,
            features,
            start,
            total,
        ) = kernelApi.search(
            task,
            form['batch'],
            position=form['position'],
            opened=openedSet,
            condensed=form['condensed'],
            condenseType=condenseType,
            fmt=textFormat,
            withNodes=form['withNodes'],
            linked=form['linked'],
            getx=int(getx) if getx else None,
            **options,
        )
      except TimeoutError:
        messages = (
            f'Aborted because query takes longer than {TIMEOUT} second'
            + ('' if TIMEOUT == 1 else 's')
        )
        console(f'{task}\n{messages}', error=True)
        setup.wildQueries.add(task)
        total = 0

    if table is not None:
      pages = pageLinks(total, form['position'])
    # messages have already been shaped by search
    # if messages:
    #  messages = wrapMessages(messages)
  else:
    table = f'no {resultKind}s'
    messages = ''

  return method(
      pages=pages,
      table=table,
      nResults=total,
      messages=messages,
      features=features,
  )


def servePassage(setup, getx):
  form = getFormData(setup.config)
  textFormat = form['textformat'] or None

  optionSpecs = setup.config.OPTIONS
  options = getValues(optionSpecs, form)

  passages = ''

  kernelApi = setup.TF.connect()

  openedKey = 'passageOpened'
  openedSet = set(form[openedKey].split(',')) if form[openedKey] else set()

  sec0 = form['sec0']
  sec1 = form['sec1']
  sec2 = form['sec2']
  (
      table,
      sec0Type,
      passages,
      browseNavLevel,
  ) = kernelApi.passage(
      form['features'],
      form['query'],
      sec0,
      sec1=sec1,
      sec2=sec2,
      opened=openedSet,
      fmt=textFormat,
      withNodes=form['withNodes'],
      getx=getx,
      **options,
  )
  passages = pickle.loads(passages)
  passages = passageLinks(passages, sec0Type, sec0, sec1, browseNavLevel)
  return jsonify(
      table=table,
      passages=passages,
  )


def serveExport(setup):
  sectionsData = serveTable(setup, 'sections', None, asDict=True)
  tuplesData = serveTable(setup, 'tuples', None, asDict=True)
  queryData = serveQuery(setup, None, asDict=True)

  form = getFormData(setup.config)

  kernelApi = setup.TF.connect()
  (header, appLogo, tfLogo) = kernelApi.header()
  css = kernelApi.css()
  provenance = kernelApi.provenance()
  setNames = kernelApi.setNames()
  setNamesRep = ', '.join(setNames)
  setNameHtml = f'''
<p class="setnames">Sets:
<span class="setnames">{setNamesRep}</span>
</p>''' if setNames else ''
  (provenanceHtml, provenanceMd) = wrapProvenance(form, provenance, setNames)

  descriptionMd = markdown.markdown(
      form['description'], extensions=[
          'markdown.extensions.tables',
          'markdown.extensions.fenced_code',
      ]
  )

  sectionsMessages = sectionsData['messages']
  sectionsTable = sectionsData['table']
  tuplesMessages = tuplesData['messages']
  tuplesTable = tuplesData['table']
  queryMessages = queryData['messages']
  queryTable = queryData['table']

  return render_template(
      'export.html',
      dataSource=setup.dataSource,
      css=css,
      descriptionMd=descriptionMd,
      sectionsTable=(
          sectionsMessages if sectionsMessages or sectionsTable is None else sectionsTable
      ),
      tuplesTable=(
          tuplesMessages if tuplesMessages or tuplesTable is None else tuplesTable
      ),
      queryTable=(
          queryMessages if queryMessages or queryTable is None else queryTable
      ),
      colofon=f'{appLogo}{header}{tfLogo}',
      provenance=provenanceHtml,
      setNames=setNameHtml,
      **form,
  )


def serveDownload(setup):
  form = getFormData(setup.config)
  kernelApi = setup.TF.connect()

  task = form['query']
  condenseType = form['condenseTp'] or None
  textFormat = form['textformat'] or None
  csvs = None
  resultsX = None
  messages = ''
  if task in setup.wildQueries:
    messages = (
        f'Aborted because query is known to take longer than {TIMEOUT} second'
        + ('' if TIMEOUT == 1 else 's')
    )
  else:
    try:
      (queryMessages, csvs, resultsX) = kernelApi.csvs(
          task,
          form['tuples'],
          form['sections'],
          condensed=form['condensed'],
          condenseType=condenseType,
          fmt=textFormat,
      )
    except TimeoutError:
      messages = (
          f'Aborted because query takes longer than {TIMEOUT} second'
          + ('' if TIMEOUT == 1 else 's')
      )
      console(f'{task}\n{messages}', error=True)
      setup.wildQueries.add(task)
      return jsonify(messages=messages)

  if queryMessages:
    redirect('/')
    return jsonify(messages=queryMessages)

  (header, appLogo, tfLogo) = kernelApi.header()
  provenance = kernelApi.provenance()
  setNames = kernelApi.setNames()
  (provenanceHtml, provenanceMd) = wrapProvenance(form, provenance, setNames)

  csvs = pickle.loads(csvs)
  resultsX = pickle.loads(resultsX)
  about = getAbout(header, provenanceMd, form)
  (fileName, zipBuffer) = zipData(csvs, resultsX, about, form)

  headers = {
      'Expires': '0',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Content-Type': 'application/octet-stream',
      'Content-Disposition': f'attachment; filename="{fileName}"',
      'Content-Encoding': 'identity',
  }
  return make_response(zipBuffer, headers)


def serveAll(setup, anything):
  form = getFormData(setup.config)
  condensedAtt = ' checked ' if form['condensed'] else ''
  withNodesAtt = ' checked ' if form['withNodes'] else ''

  optionSpecs = setup.config.OPTIONS
  options = getValues(optionSpecs, form)

  pages = ''
  passages = ''

  kernelApi = setup.TF.connect()

  (header, appLogo, tfLogo) = kernelApi.header()
  css = kernelApi.css()
  provenance = kernelApi.provenance()
  setNames = kernelApi.setNames()
  setNamesRep = ', '.join(setNames)
  setNameHtml = f'''
<p class="setnames">Sets:
<span class="setnames">{setNamesRep}</span>
</p>''' if setNames else ''
  (provenanceHtml, provenanceMd) = wrapProvenance(form, provenance, setNames)

  (
      defaultCondenseType,
      exampleSection,
      exampleSectionText,
      condenseTypes,
      defaultTextFormat,
      textFormats,
  ) = kernelApi.condenseTypes()
  condenseType = form['condenseTp'] or defaultCondenseType
  condenseOpts = wrapCondense(condenseTypes, condenseType)
  textFormat = form['textformat'] or defaultTextFormat
  textFormatOpts = wrapFormats(textFormats, textFormat)

  return render_template(
      'index.html',
      dataSource=setup.dataSource,
      css=css,
      header=f'{appLogo}{header}{tfLogo}',
      setNames=setNameHtml,
      options=wrapOptions(optionSpecs, options),
      condensedAtt=condensedAtt,
      condenseOpts=condenseOpts,
      defaultCondenseType=defaultCondenseType,
      textFormatOpts=textFormatOpts,
      defaultTextFormat=defaultTextFormat,
      exampleSection=exampleSection,
      exampleSectionText=exampleSectionText,
      withNodesAtt=withNodesAtt,
      pages=pages,
      passages=passages,
      **form,
  )
