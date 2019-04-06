import re
import types

from ..parameters import (
    URL_GH,
    URL_TFDOC,
    APP_URL,
    APP_NB_URL,
)
from ..core.helpers import htmlEsc
from .repo import Checkout
from .helpers import dh


pathRe = re.compile(r'^(.*/(?:github|text-fabric-data))/([^/]+)/([^/]+)/(.*)$', flags=re.I)


def linksApi(app, appName, silent):
  app.header = types.MethodType(header, app)

  api = app.api
  tutUrl = f'{APP_NB_URL}/{appName}/start.ipynb'
  extraUrl = f'{APP_URL}/app-{appName}'
  dataLink = outLink(
      app.repo.upper(),
      app.docUrl,
      f'provenance of {app.corpus}',
  )
  charLink = (
      outLink(
          'Character table',
          app.charUrl.format(tfDoc=URL_TFDOC),
          app.charText,
      ) if app.charUrl else ''
  )
  featureLink = outLink(
      'Feature docs', app.featureUrl.format(
          version=app.version,
          feature=app.docIntro,
      ), f'{app.repo.upper()} feature documentation'
  )
  appLink = outLink(f'{appName} API', extraUrl, f'{appName} API documentation')
  tfLink = outLink(
      f'Text-Fabric API {api.TF.version}', f'{URL_TFDOC}/Api/Fabric/', 'text-fabric-api'
  )
  tfsLink = outLink(
      'Search Reference', f'{URL_TFDOC}/Use/Search/',
      'Search Templates Introduction and Reference'
  )
  tutLink = outLink('App tutorial', tutUrl, 'App tutorial in Jupyter Notebook')
  if app._asApp:
    app.dataLink = dataLink
    app.charLink = charLink
    app.featureLink = featureLink
    app.tfsLink = tfsLink
    app.tutLink = tutLink
  else:
    if not silent:
      dh(
          '<b>Documentation:</b>'
          f' {dataLink} {charLink} {featureLink} {appLink} {tfLink} {tfsLink}'
          '<details open><summary><b>Loaded features</b>:</summary>\n' + _featuresPerModule(app) +
          '</details>'
      )


def header(app):
  return (
      f'''
<div class="hdlinks">
  {app.dataLink}
  {app.charLink}
  {app.featureLink}
  {app.tfsLink}
  {app.tutLink}
</div>
''',
      f'<img class="hdlogo" src="/data/static/logo.png"/>',
      f'<img class="hdlogo" src="/server/static/icon.png"/>',
  )


def outLink(text, href, title=None, passage=None, className=None, target='_blank'):
  titleAtt = '' if title is None else f' title="{title}"'
  classAtt = f' class="{className.lower()}"' if className else ''
  targetAtt = f' target="{target}"' if target else ''
  passageAtt = f' sec="{passage}"' if passage else ''
  return f'<a{classAtt}{targetAtt} href="{htmlEsc(href)}"{titleAtt}{passageAtt}>{text}</a>'


def _featuresPerModule(app):
  api = app.api
  features = api.Fall() + api.Eall()

  fixedModuleIndex = {}
  for m in app.moduleSpecs:
    fixedModuleIndex[(m['org'], m['repo'], m['relative'])] = (m['corpus'], m['docUrl'])

  moduleIndex = {}
  mLocations = app.mLocations if hasattr(app, 'mLocations') else []
  baseLoc = mLocations[0] if hasattr(app, 'mLocations') else ()

  for mLoc in mLocations:
    match = pathRe.fullmatch(mLoc)
    if not match:
      moduleIndex[mLoc] = ('??', '??', '??', mLoc, '')
    else:
      (base, org, repo, relative) = match.groups()
      mId = (org, repo, relative)
      (corpus,
       docUrl) = ((app.corpus, app.featureUrl.format(version=app.version, feature='{feature}'))
                  if mLoc == baseLoc else fixedModuleIndex[mId] if mId in fixedModuleIndex else
                  (f'{org}/{repo}/{relative}', f'{URL_GH}/{org}/{repo}/tree/master/{relative}'))
      moduleIndex[mId] = (org, repo, relative, corpus, docUrl)

  featureCat = {}

  for feature in features:
    added = False
    featureInfo = app.api.TF.features[feature]
    featurePath = featureInfo.path
    match = pathRe.fullmatch(featurePath)
    if match:
      (base, fOrg, fRepo, relative) = match.groups()
      fRelative = relative.rsplit('/', 1)[0]
      mId = (fOrg, fRepo, fRelative)
    else:
      mId = featurePath.rsplit('/', 1)[0]
    if type(mId) is str:
      for (mIId, mInfo) in moduleIndex.items():
        if type(mIId) is str:
          if featurePath.startswith(mIId):
            featureCat.setdefault(mIId, []).append(feature)
            added = True
    else:
      for (mIId, mInfo) in moduleIndex.items():
        if type(mIId) is not str:
          (mOrg, mRepo, mRelative) = mIId
          if fOrg == mOrg and fRepo == mRepo and fRelative.startswith(mRelative):
            featureCat.setdefault(mIId, []).append(feature)
            added = True
    if not added:
      featureCat.setdefault(mId, []).append(feature)

  baseId = (app.org, app.repo, app.relative)
  baseMods = {mId for mId in featureCat.keys() if type(mId) is tuple and mId == baseId}
  moduleOrder = list(baseMods) + sorted(
      (mId for mId in featureCat.keys() if mId not in baseMods),
      key=lambda mId: (1, mId) if type(mId) is str else (0, mId)
  )

  html = ''
  for mId in moduleOrder:
    catFeats = featureCat[mId]
    if not catFeats:
      continue
    modInfo = moduleIndex.get(mId, None)
    if modInfo:
      (org, repo, relative, corpus, docUrl) = modInfo
    else:
      corpus = mId if type(mId) is str else '/'.join(mId)
      docUrl = '' if type(mId) is str else f'{URL_GH}/{mId[0]}/{mId[1]}/tree/master/{mId[2]}'
    html += f'<p><b>{corpus}</b>:'

    seen = set()

    for feature in catFeats:
      if '@' in feature:
        dlFeature = f'{feature.rsplit("@", 1)[0]}@ll'
        if dlFeature in seen:
          continue
        seen.add(dlFeature)
        featureRep = dlFeature
      else:
        featureRep = feature
      featureInfo = app.api.TF.features[feature]
      featurePath = featureInfo.path
      isEdge = featureInfo.isEdge
      pre = '<b><i>' if isEdge else ''
      post = '</i></b>' if isEdge else ''
      html += f' {pre}'
      html += (
          outLink(featureRep, docUrl.format(feature=featureRep), title=featurePath)
          if docUrl else f'<span title="{featurePath}">{featureRep}</span>'
      )
      html += f'{post} '
    html += '</p>'
  return html


def liveText(org, repo, version, commit, release, local):
  return f'{org}/{repo} v:{version} ({Checkout.toString(commit, release, local)})'


def liveUrl(org, repo, version, commit, release, local, relative):
  relativeFlat = relative.replace('/', '-')
  if local:
    return f'{URL_GH}/{org}/{repo}/tree/master/{relative}'
  return (
      f'{URL_GH}/{org}/{repo}/releases/download/{release}/{relativeFlat}-{version}.zip'
      if release else
      f'{URL_GH}/{org}/{repo}/tree/{commit}/{relative}'
  )
