/*eslint-env jquery*/

import { SEARCH, MAXINPUT, NUMBER, QUWINDOW, RESULTCOL, TIP, htmlEsc } from "./defs.js"


const getTextRange = (memSavingMethod, iPos, node) => {
  if (memSavingMethod == 1) {
    const offset = iPos[0]
    const start = iPos[node - offset]
    const end = iPos[node - offset + 1] - 1
    const textRange = new Array(end - start + 1)
    for (let i = start; i <= end; i++) {
      textRange[i - start] = i
    }
    return textRange
  }
  return iPos.get(node)
}

export class SearchProvider {
  /* SEARCH EXECUTION
   *
   * The implementation of layered search:
   *
   * 1. gather:
   *    - match the regular expressions against the texts of the layers
   *    - for each node type, take the intersection of the resulting
   *      nodesets in the layers
   * 2. weed (the heart of the layered search algorithm):
   *    - intersect across node types (using projection to upward and downward levels)
   * 3. compose:
   *    - organize the result nodes around the nodes in a focus type
   * 4. display:
   *    - draw the table of results on the interface by screenfuls
   *    - make navigation controls for moving the focus through the table
   */

  constructor() {
    this.getAcro = /[^0-9]/g
    this.tabNl = /[\n\t]/g
  }

  deps({ Log, Features, Disk, State, Gui, Config, Corpus }) {
    this.Log = Log
    this.Features = Features
    this.Disk = Disk
    this.State = State
    this.Gui = Gui
    this.Config = Config
    this.Corpus = Corpus
    this.tell = Log.tell
  }

  async runQuery({ allSteps, gather, weed, compose: composeArg, display } = {}) {
    /* Performs a complete query
     * The individual substeps each check whether there is something to do
     */

    /* LONG RUNNING FUNCTIONS
     *
     * We apply a device to make behaviour more conspicuous on the interface.
     *
     * There are two problems
     *
     * 1. some actions go so fast, that the user does not see them happening
     * 2. some actions take a lot of time, without the user knowing that he must wait
     *
     * To solve that, we apply some CSS formatting to background and border colors.
     * In order to trigger them, we wrap some functions into this sequence:
     *
     * a. add the CSS class "waiting" to some elements
     * b. run the function in question
     * c. remove the CSS class "waiting" from thiose elements
     *
     * However, when we implement this straightforwardly and synchronously,
     * we do not see any effect, because the browser does not take the trouble
     * to re-render during this sequence.
     *
     * So we need an asynchronous wrapper, and here is what happens:
     *
     * a. add the CSS class "waiting"
     * b. sleep for a fraction of a second
     * c. - now the browser renders the interface and you see the effect of "waiting"
     * d. run the function in question
     * e. remove the CSS class "waiting"
     * f. - when the sequence is done, the browser renders again, and you see the
     *       effect of "waiting" gone
     */

    const { Log, Gui } = this

    const output = $(`#resultsbody,#resultshead`)
    const go = $("#go")
    const expr = $("#exportr")
    const runerror = $("#runerror")

    Log.progress(`executing query`)
    go.html(SEARCH.exe)
    go.removeClass("dirty")
    go.addClass("waiting")
    output.addClass("waiting")
    /* sleep a number of milliseconds to trigger a rendering of the browser
     */
    await new Promise(r => setTimeout(r, 50))

    const errors = []

    if (allSteps || gather) {
      try {
        this.gather()
      } catch (error) {
        errors.push({ where: "gather", error })
        Log.error(error)
      }
    }

    if (errors.length == 0) {
      if (allSteps || weed) {
        try {
          const stats = this.weed()
          Gui.placeStatResults(stats)
        } catch (error) {
          errors.push({ where: "weed", error })
          Log.error(error)
        }
      }
    }
    if (errors.length == 0) {
      if (allSteps || composeArg !== undefined) {
        try {
          this.composeResults(allSteps ? false : composeArg)
        } catch (error) {
          errors.push({ where: "compose", error })
          Log.error(error)
        }
      }
    }
    if (errors.length == 0) {
      if (allSteps || display) {
        try {
          this.displayResults()
        } catch (error) {
          errors.push({ where: "display", error })
          Log.error(error)
        }
      }
    }

    if (errors.length > 0) {
      Log.placeError(
        runerror,
        errors.map(({ where, error }) => `${where}: ${error}`).join("<br>"),
        go
      )
    } else {
      Log.clearError(runerror, go)
    }
    go.html(SEARCH[errors.length == 0 ? "done" : "failed"])
    expr.addClass("active")
    output.removeClass("waiting")
    go.removeClass("waiting")
    $(".dirty").removeClass("dirty")
    Log.progress(`done query`)
  }

  doSearch(nType, layer, lrInfo, regex, multiHl) {
    /* perform regular expression search for a single layer
     * return character positions and nodes that hold those positions
     */
    const {
      Corpus: {
        texts: {
          [nType]: { [layer]: text },
        },
        positions,
      },
    } = this
    const { pos: posKey } = lrInfo
    const {
      [nType]: { [posKey]: pos },
    } = positions
    const matches = new Map()
    const nodeSet = new Set()
    if (multiHl) {
      let result
      while ((result = regex.exec(text)) !== null) {
        const { indices } = result
        for (let g = 0; g < result.length; g++) {
          const b = indices[g][0]
          const e = indices[g][1]
          for (let h = b; h < e; h++) {
            const node = pos[h]
            if (node != null) {
              if (!matches.has(node)) {
                matches.set(node, new Map())
              }
              matches.get(node).set(h, g)
              nodeSet.add(node)
            }
          }
        }
      }
    } else {
      const results = text.matchAll(regex)
      for (const result of results) {
        const hit = result[0]
        const start = result.index
        const end = start + hit.length
        for (let i = start; i < end; i++) {
          const node = pos[i]
          if (node != null) {
            if (!matches.has(node)) {
              matches.set(node, new Map())
            }
            matches.get(node).set(i, 0)
            nodeSet.add(node)
          }
        }
      }
    }
    return { matches, nodeSet }
  }

  gather() {
    /* perform regular expression search for all layers
     * return for each node type
     *     the intersection of the nodesets found for each layer
     *     for each layer, a mapping of nodes to matched positions
     */
    const {
      Log,
      Features: {
        features: {
          indices: { can },
        },
      },
      Config: { ntypesR, layers },
      State,
    } = this

    const {
      query,
      settings: { multihl },
    } = State.getj()

    State.sets({ resultsComposed: [], resultTypeMap: new Map() })
    const { tpResults } = State.sets({ tpResults: {} })

    for (const nType of ntypesR) {
      const { [nType]: tpInfo = {} } = layers
      const { [nType]: tpQuery } = query
      let intersection = null
      const matchesByLayer = {}

      for (const [layer, lrInfo] of Object.entries(tpInfo)) {
        const box = $(`[kind="pattern"][ntype="${nType}"][layer="${layer}"]`)
        const ebox = $(`[kind="error"][ntype="${nType}"][layer="${layer}"]`)
        Log.clearError(ebox, box)
        const {
          [layer]: { pattern, flags, exec },
        } = tpQuery
        if (!exec || pattern.length == 0) {
          continue
        }
        if (pattern.length > MAXINPUT) {
          Log.placeError(
            ebox,
            `pattern must be less than ${MAXINPUT} characters long`,
            box
          )
          continue
        }
        const mhl = can && multihl
        const flagString = Object.entries(flags)
          .filter(x => x[1])
          .map(x => x[0])
          .join("")
        let regex
        try {
          const dFlag = mhl ? "d" : ""
          regex = new RegExp(pattern, `g${dFlag}${flagString}`)
        } catch (error) {
          Log.placeError(ebox, `"${pattern}": ${error}`, box)
          continue
        }
        const { matches, nodeSet } = this.doSearch(nType, layer, lrInfo, regex, mhl)
        matchesByLayer[layer] = matches
        if (intersection == null) {
          intersection = nodeSet
        } else {
          for (const node of intersection) {
            if (!nodeSet.has(node)) {
              intersection.delete(node)
            }
          }
        }
      }
      tpResults[nType] = { matches: matchesByLayer, nodes: intersection }
    }
  }

  weed() {
    /* combine the search results across node types
     * the current search results will be weeded in place:
     *   the nodesets found per node type will be projected onto other types
     *   and then the intersection with those projected sets will be taken.
     *   This leads to the situation where for each node type there is a nodeset
     *   that maps 1-1 to the nodeset of any other type modulo projection.
     *  returns statistics: how many nodes there are for each type.
     */
    const {
      Config: { ntypes },
      Corpus: { up, down },
      State,
    } = this
    const { tpResults } = State.gets()
    const stats = {}

    /* determine highest and lowest types in which a search has been performed
     */
    let hi = null
    let lo = null

    for (let i = 0; i < ntypes.length; i++) {
      const nType = ntypes[i]
      const {
        [nType]: { nodes },
      } = tpResults

      if (nodes != null) {
        if (lo == null) {
          lo = i
        }
        hi = i
      }
    }

    /* we are done if no search has been performed
     */
    if (hi == null) {
      return stats
    }

    /*
     * Suppose we have types 0 .. 7 with hi and lo as follows.
     *
     *  0
     *  1
     *  2=hi
     *  3
     *  4
     *  5=lo
     *  6
     *  7
     *
     *  Then we walk through the layers as follows
     *
     *  2 dn 3 dn 4 dn 5
     *  5 up 4 up 3 up 2 up 1 up 0
     *  5 dn 6 dn 7
     */

    /* intersect downwards
     */

    for (let i = hi; i > lo; i--) {
      const upType = ntypes[i]
      const dnType = ntypes[i - 1]
      const {
        [upType]: { nodes: upNodes },
        [dnType]: resultsDn = {},
      } = tpResults
      let { nodes: dnNodes } = resultsDn
      const dnFree = dnNodes == null

      /* project upnodes downward if there was no search in the down type
       *
       * if there was a search in the down type, weed out the down nodes that
       * have no upward partner in the up nodes
       */
      if (dnFree) {
        dnNodes = new Set()
        for (const un of upNodes) {
          if (down.has(un)) {
            for (const dn of down.get(un)) {
              dnNodes.add(dn)
            }
          }
        }
        resultsDn.nodes = dnNodes
      } else {
        for (const dn of dnNodes) {
          if (!up.has(dn) || !upNodes.has(up.get(dn))) {
            dnNodes.delete(dn)
          }
        }
      }
    }

    /* intersect upwards (all the way to the top)
     */
    for (let i = lo; i < ntypes.length - 1; i++) {
      const dnType = ntypes[i]
      const upType = ntypes[i + 1]
      const {
        [upType]: resultsUp = {},
        [dnType]: { nodes: dnNodes },
      } = tpResults

      const upNodes = new Set()
      for (const dn of dnNodes) {
        if (up.has(dn)) {
          upNodes.add(up.get(dn))
        }
      }
      resultsUp.nodes = upNodes
    }

    /* project downwards from the lowest level to the bottom type
     */
    for (let i = lo; i > 0; i--) {
      const upType = ntypes[i]
      const dnType = ntypes[i - 1]
      const {
        [upType]: { nodes: upNodes },
        [dnType]: resultsDn = {},
      } = tpResults
      const dnNodes = new Set()
      for (const un of upNodes) {
        if (down.has(un)) {
          for (const dn of down.get(un)) {
            dnNodes.add(dn)
          }
        }
      }
      resultsDn.nodes = dnNodes
    }

    /* collect statistics
     */
    for (const [nType, { nodes }] of Object.entries(tpResults)) {
      stats[nType] = nodes.size
    }
    return stats
  }

  composeResults(recomputeFocus) {
    /* divided search results into chunks by focusType
     * The results are organized by the nodes that have focusType as node type.
     * Each result is an object with as keys a nodetype and as values some
     * results in that node type.
     * If the node type is higher than or equal than the focus type, the
     * results are just nodes.
     * If the node type is one lower than the focus type, the results are
     * pairs [d, descendants], where d is the node, and descendants is a nested array
     * of the descendants of d.
     * Nodes lower than this will not make it into the levels, because they are
     * subsumed in the descendants of the children of the focus node.
     *
     * The result at the position that has currently focus on the interface,
     * is marked by means of a class.
     *
     * recomputeFocus = true:
     * If we do a new compose because the user has changed the focus type
     * we estimate the focus position in the new focus type based on the
     * focus position in the old focus type
     * We adjust the interface to the new focus pos (slider and number controls)
     */
    const {
      Config: { ntypesI, utypeOf },
      Corpus: { up },
      State,
    } = this
    const { tpResults, resultsComposed: oldResultsComposed } = State.gets()

    if (tpResults == null) {
      State.sets({ resultsComposed: null })
      return
    }

    const {
      focusPos: oldFocusPos,
      prevFocusPos: oldPrevFocusPos,
      dirty: oldDirty,
      focusType,
    } = State.getj()

    const { [focusType]: { nodes: focusNodes } = {} } = tpResults

    const oldNResults = oldResultsComposed == null ? 1 : oldResultsComposed.length
    const oldNResultsP = Math.max(oldNResults, 1)
    const oldRelative = oldFocusPos / oldNResultsP
    const oldPrevRelative = oldPrevFocusPos / oldNResultsP

    const { resultsComposed, resultTypeMap } = State.sets({
      resultsComposed: [],
      resultTypeMap: new Map(),
    })

    if (focusNodes) {
      for (const cn of focusNodes) {
        /* collect the upnodes
         */
        resultTypeMap.set(cn, focusType)

        const levels = { [focusType]: [cn] }

        let un = cn
        let uType = focusType

        while (up.has(un)) {
          un = up.get(un)
          uType = utypeOf[uType]
          resultTypeMap.set(un, uType)
          if (levels[uType] === undefined) {
            levels[uType] = []
          }
          levels[uType].push(un)
        }

        /* collect the down nodes
         */
        const descendants = this.getDescendants(cn, ntypesI.get(focusType))
        for (const desc of descendants) {
          const d = typeof desc === NUMBER ? desc : desc[0]
          const dType = resultTypeMap.get(d)
          if (levels[dType] === undefined) {
            levels[dType] = []
          }
          levels[dType].push(desc)
        }

        resultsComposed.push(levels)
      }
    }
    const nResults = resultsComposed == null ? 0 : resultsComposed.length
    let focusPos = oldDirty ? -2 : oldFocusPos,
      prevFocusPos = oldDirty ? -2 : oldPrevFocusPos
    if (recomputeFocus) {
      focusPos = Math.min(nResults, Math.round(nResults * oldRelative))
      prevFocusPos = Math.min(nResults, Math.round(nResults * oldPrevRelative))
    } else {
      if (focusPos == -2) {
        focusPos = nResults == 0 ? -1 : 0
        prevFocusPos = -2
      } else if (focusPos > nResults) {
        focusPos = 0
        prevFocusPos = -2
      }
    }

    State.setj({ focusPos, prevFocusPos })
  }

  getDescendants(u, uTypeIndex) {
    /* get all descendents of a node, organized by node type
     * This is an auxiliary function for composeResults()
     * The function calls itself recursively for all the children of
     * the node in a lower level
     * returns an array of subarrays, where each subarray corresponds to a child node
     * and has the form [node, [...descendants of node]]
     */
    if (uTypeIndex == 0) {
      return []
    }

    const {
      Config: { dtypeOf, ntypes },
      Corpus: { down },
      State,
    } = this
    const { resultTypeMap } = State.gets()

    const uType = ntypes[uTypeIndex]
    const dType = dtypeOf[uType]
    const dTypeIndex = uTypeIndex - 1

    const dest = []

    if (down.has(u)) {
      for (const d of down.get(u)) {
        resultTypeMap.set(d, dType)
        if (dTypeIndex == 0) {
          dest.push(d)
        } else {
          dest.push([d, this.getDescendants(d, dTypeIndex, resultTypeMap)])
        }
      }
    }
    return dest
  }

  getHlText(textRange, matches, text, valueMap, tip) {
    /* get highlighted text for a node
     * The results of matching a pattern against a text are highlighted within that text
     * returns a sequence of spans, where a span is an array of postions plus a boolean
     * that indicated whether the span is highlighted or not.
     * Used by display() and tabular() below
     */
    const { getAcro } = this

    const hasMap = valueMap != null
    const doMap = hasMap && !Array.isArray(valueMap)

    const spans = []
    let str = ""
    let curHl = -2

    for (const i of textRange ?? []) {
      const ch = text[i]
      if (doMap) {
        str += ch
      }
      const hl = matches.get(i) ?? -1
      if (curHl != hl) {
        const newSpan = [hl, ch]
        spans.push(newSpan)
        curHl = hl
      } else {
        spans[spans.length - 1][1] += ch
      }
    }
    /* the str that we get back from the node, may contain after-node material
     * and hence is not necessarily a value that we can feed to the valueMap.
     * However, the values that we need for this purpose are purely numeric
     * or the empty string
     */

    const tipStr = doMap && tip ? valueMap[str.replaceAll(getAcro, "")] : null
    return { spans, tipStr }
  }

  getLayersPerType(colPerLayer) {
    const {
      Config: { ntypesR, ntypesI, layers },
      State,
    } = this
    const {
      focusType,
      visibleLayers,
      settings: { nodeseq },
    } = State.getj()
    const focusIndex = ntypesI.get(focusType)

    const layersPerType = new Map()

    for (const nType of ntypesR) {
      const { [nType]: definedLayers = {} } = layers
      const { [nType]: tpVisible = {} } = visibleLayers
      const nodeLayer = ["_"]
      const tpLayers = nodeLayer
        .concat(Object.keys(definedLayers))
        .filter(x => tpVisible[x])

      layersPerType.set(nType, tpLayers)
    }

    const visibleTypes = ntypesR.filter(x => layersPerType.get(x).length > 0)

    const contextTypes = visibleTypes.filter(x => ntypesI.get(x) > focusIndex)
    const focusTypes = visibleTypes.filter(x => ntypesI.get(x) == focusIndex)
    const contentTypes = ntypesR.filter(x => ntypesI.get(x) < focusIndex)
    const upperTypes = contextTypes.concat(focusTypes)
    let cols
    if (colPerLayer) {
      cols = []
      for (const nType of visibleTypes) {
        const nIndex = ntypesI.get(nType)
        const typeRep =
          nIndex < focusIndex
            ? `${focusType}-content:${nType}`
            : nIndex === focusIndex && focusIndex > 0
            ? `${nType}-content:`
            : nType

        for (const layer of layersPerType.get(nType)) {
          const layerRep = layer === "_" ? (nodeseq ? "seqno" : "node") : layer
          cols.push(`${typeRep}:${layerRep}`)
        }
      }
    } else {
      cols = contextTypes.concat(focusTypes)
      if (focusIndex > 0) {
        cols = cols.concat(`${focusType}-content`)
      }
    }

    const layersContent = []
    for (const cnType of contentTypes) {
      layersContent.push(...layersPerType.get(cnType))
    }

    return {
      contextTypes,
      focusTypes,
      contentTypes,
      upperTypes,
      cols,
      layersPerType,
      layersContent,
    }
  }

  displayResults() {
    /* Displays composed results on the interface.
     * Results are displayed in a table, around a focus position
     * We only display a limited amount of results around the focus position,
     * but the user can move the focus position in various ways.
     * Per result this is visible:
     *   Context nodes are rendered highlighted
     *   The focus nodes themselves are rendered as single nodes
     *     if they have content, otherwise they are left out
     *   The children of the focus node are rendered with
     *   all of descendants (recursively),
     *     where the descendants that have results are highlighted.
     */
    const {
      Features: {
        features: {
          indices: { can },
        },
      },
      Config: { memSavingMethod, simpleBase, layers, ntypesI, ntypesinit },
      Corpus: { links, texts, iPositions },
      State,
      Gui,
    } = this

    const { resultTypeMap, tpResults, resultsComposed } = State.gets()
    const {
      settings: { nodeseq, multihl },
      focusPos,
      prevFocusPos,
    } = State.getj()

    if (tpResults == null) {
      State.sets({ resultsComposed: null })
      return
    }

    const mhl = can && multihl

    const {
      upperTypes,
      contentTypes,
      cols,
      layersPerType,
      layersContent,
    } = this.getLayersPerType(false)

    const colsRep = cols.map(x => `<th>${x}</th>`)
    const header = `<tr><th>${RESULTCOL}</th>${colsRep.join("")}</tr>`
    const resultshead = $("#resultshead")
    resultshead.html(header)

    const genValueHtml = (nType, layer, node, linkUrl) => {
      /* generates the html for a layer of node, including the result highlighting
       */

      if (layer == "_") {
        const num = nodeseq ? node - ntypesinit[nType] + 1 : node
        return linkUrl
          ? `<a class="n corpus"
              href="${linkUrl}"
              title="${TIP.corpus}"
             >${num}</a>`
          : `<span class="n">${num}</span>`
      }
      const {
        [nType]: {
          [layer]: { pos: posKey, valueMap, tip },
        },
      } = layers
      const {
        [nType]: { [layer]: text },
      } = texts
      const {
        [nType]: { [posKey]: iPos },
      } = iPositions

      const textRange = getTextRange(memSavingMethod, iPos, node)
      const { [nType]: { matches: { [layer]: matches } = {} } = {} } = tpResults
      const nodeMatches =
        matches == null || !matches.has(node) ? new Map() : matches.get(node)

      const { spans, tipStr } = this.getHlText(
        textRange,
        nodeMatches,
        text,
        valueMap,
        tip
      )
      const hasTip = tipStr != null
      const tipRep = hasTip ? ` title="${tipStr}"` : ""

      const html = []
      const multiple = spans.length > 1 || hasTip
      if (multiple) {
        html.push(`<span${tipRep}>`)
      }
      for (const [hl, val] of spans) {
        const theHl = hl == 0 && !mhl ? "hl" : `hl${hl}`
        const hlRep = hl >= 0 ? ` class="${theHl}"` : ""
        const hlTitle = hl >= 0 ? ` title="group ${hl}"` : ""
        html.push(`<span${hlRep}${hlTitle}>${htmlEsc(val)}</span>`)
      }
      if (multiple) {
        html.push(`</span>`)
      }
      const bare = html.join("")
      return linkUrl
        ? `<a class="corpus"
            href="${linkUrl}"
            title="${TIP.corpus}"
           >${bare}</a>`
        : bare
    }

    const genNodeHtml = node => {
      /* generates the html for a node, including all layers and highlighting
       */
      const [n, children] = typeof node === NUMBER ? [node, []] : node
      const nType = resultTypeMap.get(n)
      const { [nType]: { nodes } = {} } = tpResults
      const { [nType]: { [n]: linkUrl } = {} } = links
      const tpLayers = layersPerType.get(nType)
      const nLayers = tpLayers.length
      const hasLayers = nLayers > 0
      const hasSingleLayer = nLayers == 1
      const hasChildren = children.length > 0
      if (!hasLayers && !hasChildren) {
        return ""
      }

      const hlClass =
        simpleBase && ntypesI.get(nType) == 0 ? "" : nodes.has(n) ? " hlh" : "o"

      const hlRep = hlClass == "" ? "" : ` class="${hlClass}"`
      const lrRep = hasSingleLayer ? "" : ` m`
      const hdRep = hasChildren ? "h" : ""

      const html = []
      html.push(`<span${hlRep}>`)

      if (hasLayers) {
        html.push(`<span class="${hdRep}${lrRep}">`)
        let first = true
        for (const layer of tpLayers) {
          const link = first ? linkUrl : null
          html.push(`${genValueHtml(nType, layer, n, link)}`)
          first = false
        }
        html.push(`</span>`)
      }

      if (hasChildren) {
        html.push(`<span>`)
        for (const ch of children) {
          html.push(genNodeHtml(ch))
        }
        html.push(`</span>`)
      }

      html.push(`</span>`)

      return html.join("")
    }

    const genResultHtml = (i, result) => {
      /* generates the html for a single result
       */
      const isFocus = i == focusPos
      const isPrevFocus = i == prevFocusPos
      const typeNodes = []
      for (const nType of upperTypes) {
        typeNodes.push(
          `<td>${(result[nType] ?? []).map(x => genNodeHtml(x)).join(" ")}</td>`
        )
      }
      if (contentTypes.length > 0) {
        if (layersContent.length > 0) {
          const nType = contentTypes[0]
          typeNodes.push(
            `<td>${(result[nType] ?? []).map(x => genNodeHtml(x)).join(" ")}</td>`
          )
        }
      }
      const typeRep = typeNodes.join("\n")
      const focusCls = isFocus ? ` class="focus"` : isPrevFocus ? ` class="pfocus"` : ""

      return `
  <tr${focusCls}>
    <th>${i + 1}</th>
    ${typeRep}
  </tr>
    `
    }

    const genResultsHtml = () => {
      /* generates the html for all relevant results around a focus position in the
       * table of results
       */
      if (resultsComposed == null) {
        return ""
      }

      const startPos = Math.max((focusPos || 0) - 2 * QUWINDOW, 0)
      const endPos = Math.min(startPos + 4 * QUWINDOW + 1, resultsComposed.length - 1)
      const html = []
      for (let i = startPos; i <= endPos; i++) {
        html.push(genResultHtml(i, resultsComposed[i]))
      }
      return html.join("")
    }

    const html = genResultsHtml()
    const resultsbody = $("#resultsbody")
    resultsbody.html(html)
    Gui.applyPosition()
  }

  /* RESULTS EXPORT
   * Exports the current results to a tsv file
   * All results will be exported, not only the ones that are displayed
   * on the screen.
   * One result per row, with the same information per result that is currently active:
   * the same focus, the same visibility of layers and node numbers.
   *
   * The resulting tsv is written in UTF-16-LE encoding for optimal interoperability
   * with Excel
   */

  tabular() {
    /* tsv export, closely analogous to how the results are displayed on screen
     */

    const {
      Config: { memSavingMethod, layers, ntypesinit },
      Corpus: { texts, iPositions },
      State,
      tabNl,
    } = this

    const { resultTypeMap, tpResults, resultsComposed } = State.gets()
    const {
      settings: { nodeseq, exporthl, exportsr },
    } = State.getj()

    if (tpResults == null) {
      State.sets({ resultsComposed: null })
      return
    }

    const { upperTypes, contentTypes, cols, layersPerType } = this.getLayersPerType(
      exportsr
    )

    const header = `${RESULTCOL}\t${cols.join("\t")}\n`

    const genValueTsv = (nType, layer, node) => {
      /* generates the value for a layer of node, including the result highlighting
       */

      if (layer == "_") {
        return `${nodeseq ? node - ntypesinit[nType] + 1 : node} `
      }
      const {
        [nType]: {
          [layer]: { pos: posKey, valueMap, tip },
        },
      } = layers
      const {
        [nType]: { [layer]: text },
      } = texts
      const {
        [nType]: { [posKey]: iPos },
      } = iPositions

      const textRange = getTextRange(memSavingMethod, iPos, node)
      const { [nType]: { matches: { [layer]: matches } = {} } = {} } = tpResults
      const nodeMatches =
        matches == null || !matches.has(node) ? new Map() : matches.get(node)

      const { spans, tipStr } = this.getHlText(
        textRange,
        nodeMatches,
        text,
        valueMap,
        tip
      )
      const tipRep = tipStr == null ? "" : `(=${tipStr})`

      let piece = ""

      for (const [hl, val] of spans) {
        if (exporthl && hl >= 0) {
          const hlRep = hl == 0 ? "" : `${hl}=`
          piece += `«${hlRep}${val}»`
        } else {
          piece += val
        }
        piece += tipRep
      }
      piece = piece.replaceAll(tabNl, " ")
      return piece
    }

    const genNodeTsv = (node, stack) => {
      /* generates the html for a node, including all layers and highlighting
       */
      const [n, children] = typeof node === NUMBER ? [node, []] : node
      const nType = resultTypeMap.get(n)
      const tpLayers = layersPerType.get(nType)

      const newStack = [
        ...(stack ?? []),
        ...tpLayers.map(lr => genValueTsv(nType, lr, n)),
      ]

      let tsv
      if (children.length == 0) {
        tsv = newStack
      } else {
        const tsvs = []
        let first = true

        for (const ch of children) {
          tsvs.push(genNodeTsv(ch, newStack))
          if (first) {
            first = false
            newStack.fill("")
          }
        }
        tsv = zip(tsvs)
      }
      return tsv
    }

    const zip = tsvs => {
      const maxLen = Math.max(...tsvs.map(x => x.length))
      const stack = []
      for (let i = 0; i < maxLen; i++) {
        stack[i] = tsvs.map(x => (i < x.length ? x[i] : "")).join("")
      }
      return stack
    }

    const genResultTsv = (s, result) => {
      /* generates the tsv for a single result
       */
      const typeNodes = []
      for (const nType of upperTypes) {
        typeNodes.push((result[nType] ?? []).map(x => genNodeTsv(x)))
      }
      for (const nType of contentTypes) {
        typeNodes.push((result[nType] ?? []).map(x => genNodeTsv(x)))
      }

      const tsv = []

      if (exportsr) {
        const line = [`${s + 1}`]
        for (const chunks of typeNodes) {
          const fields = []
          let first = true
          for (const chunk of chunks) {
            for (let i = 0; i < chunk.length; i++) {
              if (first) {
                fields[i] = ""
              }
              const piece = chunk[i]
              fields[i] += piece
            }
            first = false
          }
          line.push(fields.join("\t"))
        }
        tsv.push(`${line.join("\t")}\n`)
      } else {
        const maxLayers = Math.max(
          ...typeNodes.map(x => Math.max(...x.map(y => y.length)))
        )

        for (let i = 0; i < maxLayers; i++) {
          const line = [`${s + 1}`]
          for (const chunks of typeNodes) {
            line.push("\t")
            for (const chunk of chunks) {
              line.push(i < chunk.length ? chunk[i] : "")
            }
          }
          tsv.push(`${line.join("")}\n`)
        }
      }
      return tsv
    }

    /* generates the tsv for all relevant results around a focus position in the
     * table of results
     */
    if (resultsComposed == null) {
      return ""
    }
    const tsv = []
    for (let i = 0; i < resultsComposed.length; i++) {
      const rows = genResultTsv(i, resultsComposed[i])
      for (let j = 0; j < rows.length; j++) {
        tsv.push(rows[j])
      }
    }
    return header + tsv.join("")
  }

  async saveResults() {
    /* save job results to file
     * The file will be offered to the user as a download
     */
    const { Log, Disk, State } = this

    const { jobName } = State.gets()
    const {
      focusType,
      settings: { exporthl, exportsr },
    } = State.getj()
    const jobExtraSR = exportsr ? "-xc" : "-xr"
    const jobExtraHL = exporthl ? "-hl" : ""

    const expr = $("#exportr")
    const runerror = $("#runerror")

    Log.progress(`exporting results`)
    expr.addClass("waiting")

    await new Promise(r => setTimeout(r, 50))

    const errors = []

    let text

    try {
      text = this.tabular()
    } catch (error) {
      errors.push({ where: "tabular", error })
      Log.error(error)
    }
    if (errors.length == 0) {
      try {
        Disk.download(
          text,
          `${jobName}-${focusType}${jobExtraSR}${jobExtraHL}`,
          "tsv",
          true
        )
      } catch (error) {
        errors.push({ where: "download", error })
        Log.error(error)
      }
    }

    if (errors.length > 0) {
      Log.placeError(
        runerror,
        errors.map(({ where, error }) => `${where}: ${error}`).join("<br>"),
        expr
      )
    } else {
      Log.clearError(runerror, expr)
    }
    expr.addClass("active")
    expr.removeClass("waiting")
    Log.progress(`done export`)
  }
}
