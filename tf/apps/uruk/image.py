import os
import re
from glob import glob
from shutil import copyfile

from tf.core.helpers import console
from tf.applib.helpers import dh
from tf.applib.links import outLink
from tf.applib.data import getData
from tf.apps.uruk.atf import OUTER_QUAD_TYPES

LOCAL_IMAGE_DIR = 'cdli-imagery'

PHOTO_TO = '{}/tablets/photos'
PHOTO_EXT = 'jpg'

TABLET_TO = '{}/tablets/lineart'
IDEO_TO = '{}/ideographs/lineart'
LINEART_EXT = 'jpg'


SIZING = {'height', 'width'}

ITEM_STYLE = ('padding: 0.5rem;')

FLEX_STYLE = (
    'display: flex;'
    'flex-flow: row nowrap;'
    'justify-content: flex-start;'
    'align-items: center;'
    'align-content: flex-start;'
)

URL_FORMAT = dict(
    tablet=dict(
        photo=f'https://cdli.ucla.edu/dl/photo/{{}}_d.{PHOTO_EXT}',
        lineart=f'https://cdli.ucla.edu/dl/lineart/{{}}_l.{LINEART_EXT}',
        main='https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&ObjectID={}',
    ),
    ideograph=dict(
        lineart=(
            f'https://cdli.ucla.edu/tools/SignLists/protocuneiform/archsigns/{{}}.{LINEART_EXT}'
        ),
        main='https://cdli.ucla.edu/tools/SignLists/protocuneiform/archsigns.html',
    ),
)


CAPTION_STYLE = dict(
    top=(
        'display: flex;'
        'flex-flow: column-reverse nowrap;'
        'justify-content: space-between;'
        'align-items: center;'
        'align-content: space-between;'
    ),
    bottom=(
        'display: flex;'
        'flex-flow: column nowrap;'
        'justify-content: space-between;'
        'align-items: center;'
        'align-content: space-between;'
    ),
    left=(
        'display: flex;'
        'flex-flow: row-reverse nowrap;'
        'justify-content: space-between;'
        'align-items: center;'
        'align-content: space-between;'
    ),
    right=(
        'display: flex;'
        'flex-flow: row nowrap;'
        'justify-content: space-between;'
        'align-items: center;'
        'align-content: space-between;'
    ),
)


def imageClass(app, n):
  api = app.api
  F = api.F
  if type(n) is str:
    identifier = n
    if n == '':
      identifier = None
      objectType = None
      nType = None
    elif len(n) == 1:
      objectType = 'ideograph'
      nType = 'sign/quad'
    else:
      if n[0] == 'P' and n[1:].isdigit():
        objectType = 'tablet'
        nType = 'tablet'
      else:
        objectType = 'ideograph'
        nType = 'sign/quad'
  else:
    nType = F.otype.v(n)
    if nType in OUTER_QUAD_TYPES:
      identifier = app.atfFromOuterQuad(n)
      objectType = 'ideograph'
    elif nType == 'tablet':
      identifier = F.catalogId.v(n)
      objectType = 'tablet'
    else:
      identifier = None
      objectType = None
  return (nType, objectType, identifier)


def getImages(
    app, ns, kind=None, key=None, asLink=False, withCaption=None, warning=True, _asString=False,
    **options
):
  if type(ns) is int or type(ns) is str:
    ns = [ns]
  result = []
  attStr = ' '.join(f'{opt}="{value}"' for (opt, value) in options.items() if opt not in SIZING)
  cssProps = {}
  for (opt, value) in options.items():
    if opt in SIZING:
      if type(value) is int:
        force = False
        realValue = f'{value}px'
      else:
        if value.startswith('!'):
          force = True
          realValue = value[1:]
        else:
          force = False
          realValue = value
        if realValue.isdecimal():
          realValue += 'px'
      cssProps[f'max-{opt}'] = realValue
      if force:
        cssProps[f'min-{opt}'] = realValue
  cssStr = ' '.join(f'{opt}: {value};' for (opt, value) in cssProps.items())
  if withCaption is None:
    withCaption = None if asLink else 'bottom'
  for n in ns:
    caption = None
    (nType, objectType, identifier) = imageClass(app, n)
    if objectType:
      imageBase = app._imagery.get(objectType, {}).get(kind, {})
      images = imageBase.get(identifier, None)
      if withCaption:
        caption = wrapLink(identifier, objectType, 'main', identifier)
      if images is None:
        thisImage = (
            f'<span><b>no {kind}</b> for {objectType} <code>{identifier}</code></span>'
        ) if warning else ''
      else:
        image = images.get(key or '', None)
        if image is None:
          imgs = "</code> <code>".join(sorted(images.keys()))
          thisImage = f'<span><b>try</b> key=<code>{imgs}</code></span>' if warning else ''
        else:
          if asLink:
            thisImage = identifier
          else:
            theImage = _useImage(app, image, kind, key or '', n)
            thisImage = (f'<img src="{theImage}" style="display: inline;{cssStr}" {attStr} />')
      thisResult = wrapLink(
          thisImage, objectType, kind, identifier, pos=withCaption, caption=caption
      ) if thisImage else None
    else:
      thisResult = (f'<span><b>no {kind}</b> for <code>{nType}</code>s</span>') if warning else ''
    result.append(thisResult)
  if not warning:
    result = [image for image in result if image]
  if not result:
    return ''
  if _asString:
    return ''.join(result)
  resultStr = f'</div><div style="{ITEM_STYLE}">'.join(result)
  html = (f'<div style="{FLEX_STYLE}">'
          f'<div style="{ITEM_STYLE}">'
          f'{resultStr}</div></div>').replace('\n', '')
  dh(html)
  if not warning:
    return True


def _useImage(app, image, kind, key, node):
  _asApp = app._asApp
  api = app.api
  F = api.F
  (imageDir, imageName) = os.path.split(image)
  (base, ext) = os.path.splitext(imageName)
  localBase = app.localDir if _asApp else app.curDir
  localDir = f'{localBase}/{LOCAL_IMAGE_DIR}'
  if not os.path.exists(localDir):
    os.makedirs(localDir, exist_ok=True)
  if type(node) is int:
    nType = F.otype.v(node)
    if nType == 'tablet':
      nodeRep = F.catalogId.v(node)
    elif nType in OUTER_QUAD_TYPES:
      nodeRep = app.atfFromOuterQuad(node)
    else:
      nodeRep = str(node)
  else:
    nodeRep = node
  nodeRep = (
      nodeRep.lower().replace('|', 'q').replace('~', '-').replace('@', '(a)').replace('&', '(e)')
      .replace('+', '(p)').replace('.', '(d)')
  )
  keyRep = '' if key == '' else f'-{key}'
  localImageName = f'{kind}-{nodeRep}{keyRep}{ext}'
  localImagePath = f'{localDir}/{localImageName}'
  # yapf: disable
  if (
      not os.path.exists(localImagePath)
      or os.path.getmtime(image) > os.path.getmtime(localImagePath)
  ):
    copyfile(image, localImagePath)
  base = '/local/' if _asApp else ''
  return f'{base}{LOCAL_IMAGE_DIR}/{localImageName}'


def getImagery(app, lgc, check, silent):
  (imageRelease, imageBase) = getData(
      app.org,
      app.repo,
      app.relativeImages,
      '',
      lgc,
      check,
      withPaths=True,
      keep=True,
      silent=silent,
  )
  if not imageBase:
    app.api = None
    return
  app.imageDir = f'{imageBase}/{app.org}/{app.repo}/{app.relativeImages}'

  app._imagery = {}
  for (dirFmt, ext, kind, objectType) in (
      (IDEO_TO, LINEART_EXT, 'lineart', 'ideograph'),
      (TABLET_TO, LINEART_EXT, 'lineart', 'tablet'),
      (PHOTO_TO, PHOTO_EXT, 'photo', 'tablet'),
  ):
    srcDir = dirFmt.format(app.imageDir)
    filePaths = glob(f'{srcDir}/*.{ext}')
    images = {}
    idPat = re.compile('P[0-9]+')
    for filePath in filePaths:
      (fileDir, fileName) = os.path.split(filePath)
      (base, thisExt) = os.path.splitext(fileName)
      if kind == 'lineart' and objectType == 'tablet':
        ids = idPat.findall(base)
        if not ids:
          console(f'skipped non-{objectType} "{fileName}"')
          continue
        identifier = ids[0]
        key = base.replace('_l', '').replace(identifier, '')
      else:
        identifier = base
        if identifier.startswith('['):
          identifier = '|' + identifier[1:]
        if identifier.endswith(']'):
          identifier = identifier[0:-1] + '|'
        key = ''
      images.setdefault(identifier, {})[key] = filePath
    app._imagery.setdefault(objectType, {})[kind] = images
    if not app.silent:
      console(f'Found {len(images)} {objectType} {kind}s')


def wrapLink(piece, objectType, kind, identifier, pos='bottom', caption=None):
  title = (
      'to CDLI main page for this item'
      if kind == 'main' else f'to higher resolution {kind} on CDLI'
  )
  url = URL_FORMAT.get(objectType, {}).get(kind, '').format(identifier)

  result = outLink(piece, url, title=title) if url else piece
  if caption:
    result = (
        f'<div style="{CAPTION_STYLE[pos]}">'
        f'<div>{result}</div>'
        f'<div>{caption}</div>'
        '</div>'
    )
  return result
