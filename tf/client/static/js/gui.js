/*eslint-env jquery*/

import {
  SEARCH,
  TIP,
  MAXINPUT,
  DEFAULTJOB,
  QUWINDOW,
  FLAGSDEFAULT,
  BUTTON,
  FOCUSTEXT,
  BOOL,
  htmlEsc,
} from "./defs.js"

export class GuiProvider {
  /* INITIALIZE DYNAMIC PARTS OF THE INTERFACE
   *
   * Almost everything on the interface is depending on the data
   * that is encountered in Config
   * Here we generate HTML and place it in the DOM
   */

  deps({ Log, Features, State, Job, Config, Corpus, Search }) {
    this.Features = Features
    this.State = State
    this.Job = Job
    this.Config = Config
    this.Corpus = Corpus
    this.Search = Search
    this.tell = Log.tell
  }

  init() {
    this.build()
    this.activate()
  }

  /* BUILDING the HTML
   */

  build() {
    /* fill in title and description and colofon
     */
    const {
      Config: {
        mainConfig: {
          description: { simple: simpleDesc, full: fullDesc } = {},
          jobs: { simple: simpleJobs, full: fullJobs } = {},
          provenance: { simple: simpleProv, full: fullProv } = {},
        } = {},
        ntypesR,
        lsVersion,
        description,
        urls,
        layers,
        levels,
      },
      State,
    } = this
    const {
      settings: { simple },
    } = State.getj()

    $("#titleplace").html(simple ? simpleDesc : fullDesc)
    if (!simple) {
      $("#description").html(description)
    }
    $("#provenance").html(simple ? simpleProv : fullProv)
    $("#appversion").html(
      simple ? lsVersion.replace(/^.*?@\s*/, "") : lsVersion.replace(/@/, " @ ")
    )
    $("#jobsplace").html(simple ? simpleJobs : fullJobs)

    $("go").html(SEARCH.dirty)

    /* Generate all search controls
     * and put them on the interface
     */

    const querybody = $("#querybody")
    const html = []

    for (const nType of ntypesR) {
      const tpInfo = layers[nType] || {}
      const tpDesc = levels[nType] || {}
      html.push(this.genTypeWidgets(nType, tpDesc, tpInfo))
    }
    querybody.html(html.join(""))

    this.placeStatTotals()
    this.buildSettings()
    this.buildKeyboard()

    for (const [kind, [linkText, linkHref, linkTitle]] of Object.entries(urls)) {
      const elem = $(`#${kind}link`)
      elem.attr("target", "_blank")
      elem.attr("title", linkTitle)
      elem.attr("href", linkHref)
      if (linkText != null) {
        elem.html(linkText)
      }
    }
  }

  buildKeyboard() {
    const {
      Config: { keyboard },
      State,
    } = this
    const {
      settings: { simple },
    } = State.getj()
    if (!simple && keyboard) {
      const place = $("#keyboardplace")
      const html = []
      html.push(`<details><summary
        class="setting">Special characters</summary><table><tbody>`)
      for (const [k, explain] of Object.entries(keyboard)) {
        const kEsc = htmlEsc(k)
        const kCode = k.charCodeAt(0)
        html.push(`
        <tr>
          <td class="kchar"><a
            class="kchar" kcode="${kCode}" href="#"
            title="copy this character to the clipboard"
            >${kEsc}</a></td>
          <td class="kexplain">${htmlEsc(explain)}</td>
        </tr>
        `)
      }
      html.push(`</tbody></table></details>`)
      place.html(html.join(""))
    }
  }

  buildSettings() {
    const {
      State,
      Features: {
        features: {
          indices: { can, support },
        },
      },
    } = this
    const {
      settings,
      settings: { simple },
    } = State.getj()

    $("#ifsetting").html(`
      <div id="settings">
        <button
          type="button" name="simple"
          class="setting on"
          title="${TIP.simple}"
        ></button>
      </div>
    `)
    if (simple) {
      $("#settingsplace").html("")
      return
    }

    const html = []
    for (const [name, value] of Object.entries(settings)) {
      if (name == "simple") {
        continue
      }
      let useValue = value
      if (name == "multihl") {
        if (value == null && can) {
          useValue = false
          State.setj({ settings: { [name]: useValue } })
        }
      }
      const bState = useValue === null ? "no" : value ? "on" : "off"
      const buttonHtml = `
      <button
        type="button" name="${name}"
        class="setting ${bState}"
        title="${TIP[name]}"
      ></button>
    `
      if (name == "multihl") {
        const canRep = can ? "✅ in this browser" : "❌ in this browser"
        html.push(`
        <div class="setting">
          ${buttonHtml}
          <details><summary>${canRep}</summary><p>${support}</p></details>
        </details>
        `)
      } else {
        html.push(`<p>${buttonHtml}</p>`)
      }
    }
    $("#settingsplace").html(`
      <details><summary class="setting">options</summary>
        <div id="settings">${html.join("")}</div>
      </details>
    `)
  }

  placeStatTotals() {
    /* stats
     */
    const {
      Config: { ntypesR, ntypessize },
    } = this

    const html = []

    for (const nType of ntypesR) {
      const total = ntypessize[nType]
      html.push(`
  <tr class="stat" ntype="${nType}">
    <td><span class="statlabel">${nType}</span></td>
    <td class="stat"><span class="stattotal">${total}</span></td>
    <td class="stat"><span class="statresult" ntype="${nType}"></span></td>
  </tr>
  `)
    }
    const statsbody = $("#statsbody")
    statsbody.html(html.join(""))
  }

  placeStatResults(stats) {
    /* draw statistics found by weed() on the interface
     */
    const {
      Config: { ntypes },
    } = this

    for (const nType of ntypes) {
      const dest = $(`.statresult[ntype="${nType}"]`)
      const stat = stats[nType]
      const useStat = stat == null ? " " : stat
      dest.html(`${useStat}`)
    }
  }

  genTypeWidgets(nType, tpDesc, tpInfo) {
    /* Generate html for the search controls for a node type
     */
    const { State } = this
    const {
      settings: { simple },
    } = State.getj()

    const nTypeRep = `<span class="lv" title="${tpDesc}">${nType}</span>`

    const html = []
    const expandButton = simple
      ? ""
      : `<button type="button" name="expand" class="expand"
          ntype="${nType}"
          title="${TIP.expand}"
         ></button>`

    const execButton = simple ? "" : "<td></td>"
    const visibleButton = simple
      ? ""
      : `<td><button type="button" name="visible" class="visible"
          ntype="${nType}" layer="_"
          title="${TIP.visibletp}"
         ></button></td>`

    html.push(`
  <tr class="qtype" ntype="${nType}">
    <td colspan="2" class="lvcell">${expandButton} ${nTypeRep}</td>
    <td><button type="button" name="ctype" class="focus"
      ntype="${nType}"
      title="${TIP.focus}"
    ></button></td>
    ${execButton}
    ${visibleButton}
  </tr>
  `)

    for (const [layer, lrInfo] of Object.entries(tpInfo)) {
      html.push(this.genWidget(nType, layer, lrInfo))
    }
    return html.join("")
  }

  genWidget(nType, layer, lrInfo) {
    /* Generate html for the search controls for a single layer
     */
    const { State } = this
    const {
      settings: { simple },
    } = State.getj()

    const slash = simple ? "" : "/"
    const flagsButton = simple
      ? ""
      : `<button type="button" name="i" class="flags"
          ntype="${nType}" layer="${layer}"
          title="${TIP.flagi}"
        >i</button><button type="button" name="m" class="flags"
          ntype="${nType}" layer="${layer}"
          title="${TIP.flagm}"
        >m</button><button type="button" name="s" class="flags"
          ntype="${nType}" layer="${layer}"
          title="${TIP.flags}"
        >s</button>`

    const execButton = simple
      ? ""
      : `<td><button type="button" name="exec" class="exec"
          ntype="${nType}" layer="${layer}"
          title="${TIP.exec}"
        ></button></td>`

    const visibleButton = simple
      ? ""
      : `<td><button type="button" name="visible" class="visible"
          ntype="${nType}" layer="${layer}"
          title="${TIP.visible}"
        ></button></td>`

    const xray = `
      <tr ntype="${nType}" layer="${layer}" class="xray"><td colspan="5">
      <div><input type="range" class="xray" ntype="${nType}" layer="${layer}"
      min="1" max="1" step="1"></div>
      <pre ntype="${nType}" layer="${layer}" class="xray"></pre>
      </td></tr>
    `

    return `
  <tr class="ltype" ntype="${nType}" layer="${layer}">
    <td>${this.genLegend(nType, layer, lrInfo)}</td>
    <td>
      ${slash}<input type="text" kind="pattern" class="pattern"
        ntype="${nType}" layer="${layer}"
        maxlength="${MAXINPUT}"
        value=""
      ><span kind="error" class="error"
        ntype="${nType}" layer="${layer}"
      ></span>${slash}</td>
    <td>${flagsButton}</td>
    ${execButton}
    ${visibleButton}
  </tr>
  ${xray}
  `
  }

  genLegend(nType, layer, lrInfo) {
    /* Generate html for the description / legend of a single layer
     */
    const { State } = this
    const {
      settings: { simple },
    } = State.getj()
    const { valueMap, description } = lrInfo
    const html = []

    const header = `<button type="button" ntype="${nType}" layer="${layer}"
        class="lyr" title="${description}"
      >${layer}</button>`

    if (!simple) {
      if (valueMap) {
        html.push(`
    <details>
      <summary>${header}</summary>
    `)
        if (valueMap) {
          const valueItems = Array.isArray(valueMap)
            ? valueMap
            : Object.entries(valueMap)
          for (const [acro, full] of valueItems) {
            html.push(`
    <div class="legend">
      <b><code>${acro}</code></b> =
      <i><code>${full}</code></i>
    </div>`)
          }
        }
        html.push(`
    </details>
      `)
      } else {
        html.push(header)
      }
    } else {
      html.push(header)
    }
    return html.join("")
  }

  /* MAKE THE INTERFACE ACTIVE
   *
   * Add actions to the controls of the search interface,
   * including those for navigating the results
   */

  /* ADDING ACTIONS TO THE DOM
   */

  activate() {
    this.activateJobs()
    this.activateSearch()
  }

  activateJobs() {
    /* make all job controls active
     */
    const { State, Job } = this

    const jobnew = $("#newj")
    const jobdup = $("#dupj")
    const jobrename = $("#renamej")
    const jobkill = $("#deletej")
    const jobchange = $("#jchange")

    jobnew.off("click").click(() => {
      /* make brand new job with no data, ask for new name
       */
      const newJob = this.suggestName(null)
      if (newJob == null) {
        return
      }
      Job.make(newJob)
      this.applyJobOptions(true)
    })
    jobdup.off("click").click(() => {
      /* duplicate current job, ask for related new name
       */
      const { jobName } = State.gets()
      const newJob = this.suggestName(jobName)
      if (newJob == null) {
        return
      }
      Job.copy(newJob)
      this.applyJobOptions(true)
    })
    jobrename.off("click").click(() => {
      /* rename current job, ask for related new name
       */
      const { jobName } = State.gets()
      const newJob = this.suggestName(jobName)
      if (newJob == null) {
        return
      }
      Job.rename(newJob)
      this.applyJobOptions(true)
    })
    jobkill.off("click").click(() => {
      /* kill current job
       */
      Job.kill()
      this.applyJobOptions(true)
    })
    jobchange.change(e => {
      /* switch to another job
       */
      const { jobName } = State.gets()
      const newJob = e.target.value
      if (jobName == newJob) {
        return
      }
      Job.change(newJob)
      this.clearBrowserState()
    })

    /* import job button
     */

    const fileSelect = $("#importj")
    const fileElem = $("#imjname")

    fileSelect.off("click").click(e => {
      fileElem.click()
      e.preventDefault()
    })

    fileElem.off("change").change(e => Job.read(e.target))

    /* export job button
     */

    const expjButton = $("#exportj")
    expjButton.off("click").click(() => {
      Job.write()
    })
  }

  suggestName(jobName) {
    /* ask for a new name for a job
     * Given jobName, we append an `N` until the name is not one of the known jobs.
     * This is only a suggestion, the user may override it.
     * But if jobName is null, the first new name will be taken straightaway
     * without user interaction.
     */
    const { Job } = this

    const jobNames = new Set(Job.list())
    let newName = jobName
    const resolved = s => s && s != jobName && !jobNames.has(s)
    let cancelled = false
    while (!resolved(newName) && !cancelled) {
      while (!resolved(newName)) {
        if (newName == null) {
          newName = DEFAULTJOB
        } else {
          newName += "N"
        }
      }
      if (jobName != null) {
        const answer = prompt("New job name:", newName)
        if (answer == null) {
          cancelled = true
        } else {
          newName = answer
        }
      }
    }
    return cancelled ? null : newName
  }

  activateKeyboard() {
    const copyctls = $("a[kcode]")
    copyctls.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const kCode = elem.attr("kcode")
      console.log(`k=${String.fromCharCode(kCode)}`)
      navigator.clipboard.writeText(String.fromCharCode(kCode))
    })
  }

  activateSettings() {
    const { State, Search } = this

    const settingctls = $("#settings button")
    settingctls.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const name = elem.attr("name")
      const isNo = elem.hasClass("no")
      if (!isNo) {
        const isOn = elem.hasClass("on")
        State.setj({ settings: { [name]: !isOn } })
        this.applySettings(name)
        if (name == "nodeseq") {
          Search.runQuery({ display: [] })
        }
        if (name == "multihl") {
          Search.runQuery({ allSteps: true })
        }
      }
      this.clearBrowserState()
    })
  }

  activateSearch() {
    /* make the search button active
     */
    const { State, Search } = this

    const go = $(`#go`)

    const handleQuery = e => {
      e.preventDefault()
      go.off("click")
      Search.runQuery({ allSteps: true })
      State.setj({ dirty: false })
      this.clearBrowserState()
      go.click(handleQuery)
    }

    go.off("click").click(handleQuery)

    /* handle changes in the expansion of layers
     */

    this.activateKeyboard()
    this.activateSettings()

    const expands = $(`button[name="expand"]`)
    expands.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const nType = elem.attr("ntype")
      const isNo = elem.hasClass("no")
      if (!isNo) {
        const isOn = elem.hasClass("on")
        State.setj({ expandTypes: { [nType]: !isOn } })
        this.applyLayers(nType)
      }
      this.clearBrowserState()
    })

    /* handle changes in the focus type
     */
    const focuses = $(`button[name="ctype"]`)
    focuses.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const nType = elem.attr("ntype")
      const { focusType } = State.getj()
      if (nType == focusType) {
        return
      }
      State.setj({ focusType: nType })
      Search.runQuery({ compose: [true] })
      Search.runQuery({ display: [] })
      this.applyContainer(nType)
      this.clearBrowserState()
    })
    /* handle changes in the search patterns
     */
    const patterns = $(`input[kind="pattern"]`)
    patterns.off("change").change(e => {
      const elem = $(e.target)
      const nType = elem.attr("ntype")
      const layer = elem.attr("layer")
      const {
        target: { value: pattern },
      } = e
      this.makeDirty(elem)
      State.setj({ query: { [nType]: { [layer]: { pattern } } } })

      const {
        settings: { autoexec },
      } = State.getj()
      if (autoexec) {
        Search.runQuery({ allSteps: true })
      }
      this.applyExec(nType, layer)
      this.clearBrowserState()
    })
    const errors = $(`[kind="error"]`)
    errors.hide()

    /* handle changes in the regexp flags
     */
    const flags = $(`button.flags`)
    flags.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const name = elem.attr("name")
      const nType = elem.attr("ntype")
      const layer = elem.attr("layer")
      const isOn = elem.hasClass("on")
      this.makeDirty(elem)
      State.setj({ query: { [nType]: { [layer]: { flags: { [name]: !isOn } } } } })

      const {
        settings: { autoexec },
      } = State.getj()
      if (autoexec) {
        Search.runQuery({ allSteps: true })
      }
      this.setButton(name, `[ntype="${nType}"][layer="${layer}"]`, !isOn)
      this.clearBrowserState()
    })

    /* handles changes in the "exec" controls
     */
    const execs = $(`button.exec`)
    execs.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const nType = elem.attr("ntype")
      const layer = elem.attr("layer")
      const isNo = elem.hasClass("no")
      if (!isNo) {
        const isOn = elem.hasClass("on")
        this.makeDirty(elem)
        State.setj({ query: { [nType]: { [layer]: { exec: !isOn } } } })

        const {
          settings: { autoexec },
        } = State.getj()
        if (autoexec) {
          Search.runQuery({ allSteps: true })
        }
        this.setButton("exec", `[ntype="${nType}"][layer="${layer}"]`, !isOn, true)
      }
      this.clearBrowserState()
    })

    /* handles changes in the "visible" controls
     */
    const visibles = $(`button.visible`)
    visibles.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const nType = elem.attr("ntype")
      const layer = elem.attr("layer")
      const isOn = elem.hasClass("on")
      State.setj({ visibleLayers: { [nType]: { [layer]: !isOn } } })
      this.setButton("visible", `[ntype="${nType}"][layer="${layer}"]`, !isOn, true)
      Search.runQuery({ display: [] })
      this.clearBrowserState()
    })

    /* handles display of search results
     */
    this.activateResults()

    /* handles export of search results
     */
    const exprButton = $("#exportr")
    exprButton.off("click").click(() => {
      const { tpResults } = State.gets()
      if (tpResults == null) {
        alert("Query has not been executed yet")
        return
      }

      Search.saveResults()
    })
  }

  makeDirty(elem) {
    const { State } = this

    const go = $("#go")
    const expr = $("#exportr")
    elem.addClass("dirty")
    go.addClass("dirty")
    go.html(SEARCH.dirty)
    expr.removeClass("active")
    State.setj({ dirty: true })
  }

  activateResults() {
    /* make the number controls active
     *   the result slider
     *   the input box for the focus position
     * Keep the various ways of changing the focus position synchronized
     */
    const { State, Search } = this

    const slider = $("#slider")
    const setter = $("#setter")
    const minp = $("#minp")
    const min2p = $("#min2p")
    const mina = $("#mina")
    const maxp = $("#maxp")
    const max2p = $("#max2p")
    const maxa = $("#maxa")

    slider.off("change").change(() => {
      const { focusPos } = State.getj()
      State.setj({
        prevFocusPos: focusPos,
        focusPos: this.checkFocus(slider.val() - 1),
      })
      Search.runQuery({ display: [] })
    })
    setter.off("change").change(() => {
      const { focusPos } = State.getj()
      State.setj({
        prevFocusPos: focusPos,
        focusPos: this.checkFocus(setter.val() - 1),
      })
      Search.runQuery({ display: [] })
    })
    minp.off("click").click(() => {
      const { focusPos } = State.getj()
      if (focusPos == -2) {
        return
      }
      State.setj({
        prevFocusPos: focusPos,
        focusPos: this.checkFocus(focusPos - 1),
      })
      Search.runQuery({ display: [] })
    })
    min2p.off("click").click(() => {
      const { focusPos } = State.getj()
      if (focusPos == -2) {
        return
      }
      State.setj({
        prevFocusPos: focusPos,
        focusPos: this.checkFocus(focusPos - QUWINDOW),
      })
      Search.runQuery({ display: [] })
    })
    mina.off("click").click(() => {
      const { focusPos } = State.getj()
      if (focusPos == -2) {
        return
      }
      State.setj({ prevFocusPos: focusPos, focusPos: 0 })
      Search.runQuery({ display: [] })
    })
    maxp.off("click").click(() => {
      const { focusPos } = State.getj()
      if (focusPos == -2) {
        return
      }
      State.setj({
        prevFocusPos: focusPos,
        focusPos: this.checkFocus(focusPos + 1),
      })
      Search.runQuery({ display: [] })
    })
    max2p.off("click").click(() => {
      const { focusPos } = State.getj()
      if (focusPos == -2) {
        return
      }
      State.setj({
        prevFocusPos: focusPos,
        focusPos: this.checkFocus(focusPos + QUWINDOW),
      })
      Search.runQuery({ display: [] })
    })
    maxa.off("click").click(() => {
      const { focusPos } = State.getj()
      if (focusPos == -2) {
        return
      }
      State.setj({
        prevFocusPos: focusPos,
        focusPos: this.checkFocus(-1),
      })
      Search.runQuery({ display: [] })
    })
  }

  activateLayers() {
    /* do the xray of layers
     */

    const maxShowSize = 5000
    const minChunkSize = 10000
    const maxSteps = 1000

    const getStepSize = size => {
      if (size <= minChunkSize) {
        return 0
      }
      if (size <= minChunkSize * maxSteps) {
        return minChunkSize
      }
      return Math.round(1 + size / maxSteps)
    }

    const getMaterial = (text, start, stepSize) => {
      const chunkSize = Math.max(maxShowSize, stepSize == 0 ? text.length : stepSize)
      return htmlEsc(text.slice(start - 1, start + chunkSize - 1))
    }

    const {
      Corpus: { texts },
    } = this

    const activateLayer = slider => {
      const elem = $(slider)
      const nType = elem.attr("ntype")
      const layer = elem.attr("layer")
      const {
        [nType]: { [layer]: text },
      } = texts
      const content = $(`pre.xray[ntype="${nType}"][layer="${layer}"]`)
      const stepSize = getStepSize(text.length)

      if (stepSize == 0) {
        elem.hide()
      } else {
        elem.show()
        elem.attr("max", text.length)
        elem.attr("step", stepSize)
        elem.val(1)
        elem.off("change").change(() => {
          const xpos = elem.val() >> 0
          const material = getMaterial(text, xpos, stepSize)
          content.html(material)
        })
      }
    }

    const sliders = $("input.xray")
    for (const slider of sliders.get()) {
      activateLayer(slider)
    }

    const controls = $("button.lyr")
    controls.off("click").click(e => {
      e.preventDefault()
      const elem = $(e.target)
      const nType = elem.attr("ntype")
      const layer = elem.attr("layer")
      const row = $(`tr.xray[ntype="${nType}"][layer="${layer}"]`)
      const slider = $(`input.xray[ntype="${nType}"][layer="${layer}"]`)
      const content = $(`pre.xray[ntype="${nType}"][layer="${layer}"]`)
      const isHidden = row.is(":hidden")
      if (isHidden) {
        row.show()
        const {
          [nType]: { [layer]: text },
        } = texts
        const xpos = slider.val() >> 0
        const stepSize = getStepSize(text.length)
        const material = getMaterial(text, xpos, stepSize)
        content.html(material)
      } else {
        row.hide()
      }
    })
  }

  /* APPLYING STATE CHANGES to the DOM
   */

  apply(run) {
    /* apply jobState to the interface
     *
     * try to run the query if parameter run is true
     */

    this.applyJobOptions()
    this.applySettings()
    this.applyQuery()
    this.applyResults(run)
    this.clearBrowserState()
  }

  applyQuery() {
    const { Config, State } = this
    const { ntypes, layers } = Config
    const { query, focusType, visibleLayers } = State.getj()

    for (const nType of ntypes) {
      const { [nType]: tpInfo = {} } = layers
      const { [nType]: tpQuery } = query
      const { [nType]: tpVisible } = visibleLayers

      this.applyLayers(nType)

      const { _: visibleNodes } = tpVisible
      this.setButton("visible", `[ntype="${nType}"][layer="_"]`, visibleNodes, true)

      for (const layer of Object.keys(tpInfo)) {
        const {
          [layer]: { pattern, flags },
        } = tpQuery
        const box = $(`[kind="pattern"][ntype="${nType}"][layer="${layer}"]`)
        box.val(pattern)

        const useFlags = { ...FLAGSDEFAULT, ...flags }
        for (const [flag, isOn] of Object.entries(useFlags)) {
          this.setButton(flag, `[ntype="${nType}"][layer="${layer}"]`, isOn)
        }

        this.applyExec(nType, layer)

        const { [layer]: visible } = tpVisible
        this.setButton("visible", `[ntype="${nType}"][layer="${layer}"]`, visible, true)
      }
    }
    this.applyContainer(focusType)
  }
  applyExec(nType, layer) {
    const { State } = this

    const {
      query: {
        [nType]: {
          [layer]: { pattern, exec },
        },
      },
    } = State.getj()
    const useExec = pattern.length == 0 ? null : exec
    this.setButton("exec", `[ntype="${nType}"][layer="${layer}"]`, useExec, true)
  }

  applyJobOptions(clear) {
    /* populate the options of the select box with the remembered jobs in localStorage
     */
    const { Job, State } = this
    const { jobName } = State.gets()
    const jobchange = $("#jchange")
    const jobname = $("#jobname")

    let html = ""
    for (const otherJobName of Job.list()) {
      const selected = otherJobName == jobName ? " selected" : ""
      html += `<option value="${otherJobName}"${selected}>${otherJobName}</option>`
      jobchange.html(html)
    }
    jobchange.val(jobName)
    jobname.val(jobName)

    if (clear) {
      this.clearBrowserState()
    }
  }

  applySettings(name) {
    const { State } = this

    const { settings } = State.getj()

    const allTasks = Object.entries(settings)
    const tasks = name == null ? allTasks : [[name, settings[name]]]

    if (name == "simple") {
      this.init()
      this.activateLayers()
      this.apply(false)
    } else {
      for (const [aname, setting] of tasks) {
        this.setButton(aname, "", setting, true)
      }
    }
  }

  applyLayers(nType) {
    const {
      Config: { layers: { [nType]: tpLayers = {} } = {} },
      State,
    } = this
    const {
      expandTypes: { [nType]: expand },
      visibleLayers: { [nType]: tpVisible },
      query: { [nType]: tpQuery },
    } = State.getj()

    const totalLayers = Object.keys(tpLayers).length
    const useExpand = totalLayers == 0 ? null : expand

    for (const layer of Object.keys(tpLayers)) {
      const row = $(`.ltype[ntype="${nType}"][layer="${layer}"]`)
      const {
        [layer]: { pattern },
      } = tpQuery
      const { [layer]: visible } = tpVisible
      const isActive = visible || pattern.length > 0

      if (expand || isActive) {
        row.show()
      } else {
        row.hide()
      }
    }
    const {
      expand: { no, on, off },
    } = BUTTON
    const expandText = {
      no,
      on: `${on}`,
      off: `${off}`,
    }
    this.setButton("expand", `[ntype="${nType}"]`, useExpand, expandText)
  }

  applyContainer(focusType) {
    /* update the tags on the buttons for the focusType selection
     * Only one of them can be on, they are function-wise radio buttons
     */
    const {
      Config: { ntypes, ntypesI },
    } = this

    const focusIndex = ntypesI.get(focusType)
    for (const nType of ntypes) {
      const nTypeIndex = ntypesI.get(nType)
      const k = focusIndex == nTypeIndex ? "r" : focusIndex < nTypeIndex ? "a" : "d"
      const elem = $(`button[name="ctype"][ntype="${nType}"]`)
      elem.html(FOCUSTEXT[k])
    }
    this.setButton("ctype", ``, false)
    this.setButton("ctype", `[ntype="${focusType}"]`, true)

    /* also mark the corresponding row in the statistics table
     */

    const statRows = $(`tr.stat`)
    const statContainer = $(`tr.stat[ntype="${focusType}"]`)
    statRows.removeClass("focus")
    statContainer.addClass("focus")
  }

  applyResults(run) {
    /* fill in the results of a job
     * We will run the query first if all of the following conditions are met:
     * - parameter run = true.
     * - the query is not empty
     * Otherwise, we clear all result components in the state.
     */
    // const { State, Search } = this
    const { Search } = this

    if (run) {
      Search.runQuery({ allSteps: true })
    } else {
      this.applyPosition()
    }
  }

  applyPosition() {
    /* adjust the interface to the current focus
     * Especially the result navigation controls and the slider
     */
    const { State } = this

    const { resultsComposed } = State.gets()
    const { focusPos } = State.getj()
    const setter = $("#setter")
    const setterw = $("#setterw")
    const slider = $("#slider")
    const sliderw = $("#sliderw")
    const total = $("#total")
    const totalw = $("#totalw")
    const minp = $("#minp")
    const min2p = $("#min2p")
    const mina = $("#mina")
    const maxp = $("#maxp")
    const max2p = $("#max2p")
    const maxa = $("#maxa")
    const nResults = resultsComposed == null ? 0 : resultsComposed.length
    const nResultsP = Math.max(nResults, 1)
    const stepSize = Math.max(Math.round(nResults / 100), 1)
    const focusVal = focusPos == -2 ? 0 : focusPos + 1
    const totalVal = focusPos == -2 ? 0 : nResults
    setter.attr("max", nResultsP)
    setter.attr("step", stepSize)
    slider.attr("max", nResultsP)
    slider.attr("step", stepSize)
    setter.val(focusVal)
    slider.val(focusVal)
    total.html(totalVal)

    sliderw.hide()
    setterw.hide()
    totalw.hide()
    minp.removeClass("active")
    min2p.removeClass("active")
    mina.removeClass("active")
    maxp.removeClass("active")
    max2p.removeClass("active")
    maxa.removeClass("active")

    if (focusPos != -2) {
      setterw.show()
      totalw.show()
      if (nResults > 2 * QUWINDOW) {
        sliderw.show()
      }
      if (focusPos < nResults - 1) {
        maxa.addClass("active")
        maxp.addClass("active")
      }
      if (focusPos + QUWINDOW < nResults - 1) {
        max2p.addClass("active")
      }
      if (focusPos > 0) {
        mina.addClass("active")
        minp.addClass("active")
      }
      if (focusPos - QUWINDOW > 0) {
        min2p.addClass("active")
      }
    }

    /* scrolls the interface to the result that is in focus
     */
    const rTarget = $(`#resultsbody>tr.focus`)
    if (rTarget != null && rTarget[0] != null) {
      rTarget[0].scrollIntoView({ block: "center", behavior: "smooth" })
    }
  }

  /* auxiliary methods
   */

  setButton(name, spec, onoff, changeTag) {
    /* Put a button in an on or off state
     * name is what is in their "name" attribute,
     * with spec you can pass additional selection criteria,
     * as a jQuery selector
     * onoff is true or false: true will add the class on, false will remove that class
     * changeTag: modify the tags on the button
     * - if true: pick up the tags from the constant BUTTON, indexed by name
     * - if an object: pick up the texts directly from this object
     * in both cases we expect texts for keys "no", "on", "off"
     * Which one is chosen, depends on onoff: null, true, false
     */
    const elem = $(`button[name="${name}"]${spec}`)
    if (onoff == null) {
      elem.removeClass("on")
      elem.addClass("no")
    } else {
      if (onoff) {
        elem.addClass("on")
        elem.removeClass("no")
      } else {
        elem.removeClass("on")
        elem.removeClass("no")
      }
    }
    if (changeTag) {
      const texts = typeof changeTag == BOOL ? BUTTON[name] : changeTag
      elem.html(texts[onoff == null ? "no" : onoff ? "on" : "off"])
    }
  }

  checkFocus(focusPos) {
    /* take care that the focus position is always within
     * the correct range with respect to the number of results
     *
     * We implement here that going past the end of the results
     * will cycle back to the beginning and vice versa,
     * but only in step-by-step mode, not in screenful mode
     */
    const { State } = this

    const { resultsComposed } = State.gets()

    if (resultsComposed == null) {
      return -2
    }

    const nResults = resultsComposed.length
    if (focusPos == nResults) {
      return 0
    }
    if (focusPos == -1 || focusPos > nResults) {
      return nResults - 1
    }
    if (focusPos < 0) {
      return 0
    }
    return focusPos
  }

  clearBrowserState() {
    /* clears the browser state after a change in the form fields.
     * this prevents an "are you sure" - popup before reloading the page
     */
    if (window.history.replaceState) {
      window.history.replaceState(null, null, window.location.href)
    }
  }
}
