/*eslint-env jquery*/

/* mode: results or passage
 *
 */

// character widget


const copyChar = (el, c) => {
  for (const el of document.getElementsByClassName("ccon")) {
    el.className = "ccoff"
  }
  el.className = "ccon"
  navigator.clipboard.writeText(String.fromCharCode(c))
}
globalThis.copyChar = copyChar

const mathTypeset = dest => {
  const showMathOption = $("#math")
  const showMath = showMathOption.prop("checked")

  if (showMath) {
    const { MathJax } = globalThis
    MathJax.typeset(dest)
  }
}

const lastJobKey = "tfLastJob"

const switchMode = m => {
  const mode = $("#mode")
  const pageNav = $("#navigation")
  const pages = $("#pages")
  const nresults = $("#nresults")
  const passagesNav = $("#passagesnav")
  const passages = $("#passages")
  const sectionsTable = $("#sectionsTable")
  const tuplesTable = $("#tuplesTable")
  const queryTable = $("#queryTable")
  const passageTable = $("#passageTable")
  const resultsc = $("#moderesults")
  const passagec = $("#modepassage")

  mode.val(m)
  if (m == "passage") {
    pageNav.hide()
    pages.hide()
    nresults.hide()
    passages.show()
    passagesNav.show()
    sectionsTable.hide()
    tuplesTable.hide()
    queryTable.hide()
    passageTable.show()
    resultsc.show()
    passagec.hide()
  } else if (m == "results") {
    pageNav.show()
    pages.show()
    nresults.show()
    passagesNav.hide()
    passages.hide()
    sectionsTable.show()
    tuplesTable.show()
    queryTable.show()
    passageTable.hide()
    resultsc.hide()
    passagec.show()
  }
}

const modesEvent = kind => e => {
  e.preventDefault()
  storeForm()
  switchMode(kind)
}

const modes = () => {
  const mode = $("#mode")
  const m = mode.val()

  $("#moderesults").off("click").click(modesEvent("results"))
  $("#modepassage").off("click").click(modesEvent("passage"))
  ensureLoaded("passage", "passages", m)
  if (mode.val() == "results") {
    ensureLoaded("sections", null, m)
    ensureLoaded("tuples", null, m)
    ensureLoaded("query", "pages", m)
  }
}

// switch to passage mode after clicking on a result

const switchEvent = e => {
  e.preventDefault()
  const { currentTarget } = e
  const seq = $(currentTarget).closest("details").attr("seq")
  $("#mode").val("passages")
  $("#sec0").val($(currentTarget).attr("sec0"))
  $("#sec1").val($(currentTarget).attr("sec1"))
  $("#sec2").val($(currentTarget).attr("sec2"))
  $("#pos").val(seq)
  storeForm()
  getTable("passage", "passages", "passage")
}

const switchPassage = () => {
  $(".pq").off("click").click(switchEvent)
}

/* tables: getting tabular data from the server
 *
 */

const ensureLoaded = (kind, subkind, m) => {
  const table = $(`#${kind}Table`)
  if (!table.html()) {
    getTable(kind, subkind, m)
  } else {
    switchMode(m)
  }
}

const getTable = (kind, subkind, m, button) => {
  const url = `/${kind}`
  const destTable = $(`#${kind}Table`)
  const destMsg = $(`#${kind}Messages`)
  const destSub = $(`#${subkind}`)
  const nresults = $(".nresults")
  const go = document.querySelector("form")
  const formData = new FormData(go)
  if (button) {
    button.addClass("fa-spin")
  }
  if (kind == "query") {
    nresults.html("...")
  }
  $.ajax({
    type: "POST",
    url,
    data: formData,
    processData: false,
    contentType: false,
    success: data => {
      const { table = "", messages = "", nResults = 0 } = data
      destTable.html(table)
      if (kind == "query") {
        nresults.html(nResults)
      }
      destMsg.html(messages)
      if (subkind != null) {
        const subs = data[subkind]
        if (subs) {
          destSub.html(subs)
          subLinks(kind, subkind)
          if (subkind == "passages") {
            filterS0()
          }
        }
      }
      const { features } = data
      if (features != null) {
        $("#features").val(features)
      }
      if (button) {
        button.removeClass("fa-spin")
      }
      switchPassage()
      details(kind)
      sections()
      tuples()
      nodes()
      switchMode(m)
      storeForm()
      gotoFocus(kind)
      mathTypeset(destTable)
      activateEdges()
    },
  })
}

const gotoFocus = kind => {
  if (kind == "passage" || kind == "query") {
    const rTarget = $(`#${kind}Table details.focus`)
    if (rTarget != null && rTarget[0] != null) {
      rTarget[0].scrollIntoView(false)
    }
  }
}

const activateTables = (kind, subkind) => {
  const button = $(`#${kind}Go`)
  const passButton = button.find("span")
  button.off("click").click(e => {
    e.preventDefault()
    storeForm()
    let m = $("#mode").val()
    if (kind == "passage" && m != "passage") {
      m = "passage"
    } else if (kind != "passage" && m != "results") {
      m = "results"
    }
    getTable(kind, subkind, m, passButton)
  })
  detailc(kind)
  const xpa = adjustOpened(kind)
  detailSet(kind, xpa)
}

// navigation links through passages and results

const subLinks = (kind, subkind) => {
  if (subkind == "pages") {
    $(".pnav")
      .off("click")
      .click(e => {
        e.preventDefault()
        const { currentTarget } = e
        $("#pos").val($(currentTarget).text())
        storeForm()
        getTable(kind, subkind, "results")
      })
  } else if (subkind == "passages") {
    const opKey = `${kind}Op`
    $(".s0nav")
      .off("click")
      .click(e => {
        e.preventDefault()
        const { currentTarget } = e
        $("#sec0").val($(currentTarget).text())
        $("#sec1").val("1")
        $("#sec2").val("")
        $(`#${opKey}`).val("")
        storeForm()
        getTable(kind, subkind, "passages")
      })
    $(".s1nav")
      .off("click")
      .click(e => {
        e.preventDefault()
        const { currentTarget } = e
        $("#sec1").val($(currentTarget).text())
        $("#sec2").val("")
        $(`#${opKey}`).val("")
        storeForm()
        getTable(kind, subkind, "passages")
      })
  }
}

// controlling the "open all" checkbox

const detailc = kind => {
  $(`#${kind}Expac`)
    .off("click")
    .click(e => {
      e.preventDefault()
      const expa = $(`#${kind}Expa`)
      const xpa = expa.val()
      const newXpa = xpa == "1" ? "-1" : xpa == "-1" ? "1" : xpa == "0" ? "-1" : "-1"
      detailSet(kind, newXpa)
      const dPretty = $(`#${kind}Table details.pretty`)
      if (newXpa == "-1") {
        dPretty.each((i, elem) => {
          const el = $(elem)
          if (el.prop("open")) {
            el.prop("open", false)
          }
        })
      } else if (newXpa == "1") {
        dPretty.each((i, elem) => {
          const el = $(elem)
          if (!el.prop("open")) {
            el.prop("open", true)
          }
        })
      }
    })
}

const detailSet = (kind, xpa) => {
  const expac = $(`#${kind}Expac`)
  const expa = $(`#${kind}Expa`)
  const curVal = xpa == null ? expa.val() : xpa
  if (curVal == "-1") {
    expa.val("-1")
    expac.prop("checked", false)
    expac.prop("indeterminate", false)
  } else if (curVal == "1") {
    expa.val("1")
    expac.prop("checked", true)
    expac.prop("indeterminate", false)
  } else if (curVal == "0") {
    expa.val("0")
    expac.prop("checked", false)
    expac.prop("indeterminate", true)
  } else {
    expa.val("-1")
    expac.prop("checked", false)
    expac.prop("indeterminate", false)
  }
  const op = $(`#${kind}Op`)
  if (curVal == "-1") {
    op.val("")
  } else if (curVal == "1") {
    const dPretty = $(`#${kind}Table details.pretty`)
    const allNumbers = dPretty.map((i, elem) => $(elem).attr("seq")).get()
    op.val(allNumbers.join(","))
  }
  storeForm()
}

const adjustOpened = kind => {
  const openedElem = $(`#${kind}Op`)
  const dPretty = $(`#${kind}Table details.pretty`)
  const openedDetails = dPretty.filter((i, elem) => elem.open)
  const closedDetails = dPretty.filter((i, elem) => !elem.open)
  const openedNumbers = openedDetails.map((i, elem) => $(elem).attr("seq")).get()
  const closedNumbers = closedDetails.map((i, elem) => $(elem).attr("seq")).get()

  const currentOpenedStr = openedElem.val()
  const currentOpened = currentOpenedStr == "" ? [] : currentOpenedStr.split(",")
  const reduceOpened = currentOpened.filter(
    n => closedNumbers.indexOf(n) < 0 && openedNumbers.indexOf(n) < 0
  )
  const newOpened = reduceOpened.concat(openedNumbers)
  openedElem.val(newOpened.join(","))
  const nOpen = openedDetails.length
  const nClosed = closedDetails.length
  const xpa = nOpen == 0 ? "-1" : nClosed == 0 ? "1" : "0"
  return xpa
}

// opening and closing details in a table

const details = kind => {
  const details = $(`#${kind}Table details.pretty`)
  details.on("toggle", e => {
    const { currentTarget } = e
    const xpa = adjustOpened(kind)
    detailSet(kind, xpa)
    if ($(currentTarget).prop("open") && !$(currentTarget).find("div.pretty").html()) {
      getOpen(kind, $(currentTarget))
    }
  })
}

const getOpen = (kind, elem) => {
  const seq = elem.attr("seq")
  const url = `/${kind}/${seq}`
  const dest = elem.find("div.pretty")
  const go = document.querySelector("form")
  const formData = new FormData(go)
  $.ajax({
    type: "POST",
    url,
    data: formData,
    processData: false,
    contentType: false,
    success: data => {
      const { table } = data
      dest.html(table)
      mathTypeset(dest)
      activateEdges()
    },
  })
}

/* auto submit data request after interacting with a control
 *
 */

const reactive = () => {
  const form = $("form")
  $(".r").change(() => {
    form.submit()
  })
  $("textarea").change(() => {
    storeForm()
  })
  $("input").change(() => {
    storeForm()
  })
}

const cradios = () => {
  $(".cradio").change(() => {
    $("#cond").prop("checked", true)
  })
}

/* color map handling
 *
 */

const colorMap = () => {
  const form = $("form")
  const colorMapN = $('input[name="colormapn"]')

  $("#colormapplus")
    .off("click")
    .click(e => {
      e.preventDefault()
      const cn = parseInt(colorMapN.val())
      colorMapN.val(cn + 1)
      storeForm()
      form.submit()
    })
  $("#colormapmin")
    .off("click")
    .click(e => {
      e.preventDefault()
      const cn = parseInt(colorMapN.val())
      colorMapN.val(cn > 0 ? cn - 1 : 0)
      storeForm()
      form.submit()
    })
  $(".clmap").change(() => {
      storeForm()
      form.submit()
  })
}

const eColorMap = () => {
  const form = $("form")

  $(".ecolormapmin")
    .off("click")
    .click(e => {
      e.preventDefault()
      const { currentTarget } = e
      const elem = $(currentTarget)
      const pos = elem.attr("pos")
      $(`input[name="edge_name_${pos}"]`).val("")

      storeForm()
      form.submit()
    })
  $(".eclmap").change(() => {
      storeForm()
      form.submit()
  })
}

const activateEdges = () => {
  const form = $("form")

  $('.etf')
    .off("click")
    .click(e => {
      e.preventDefault()
      const { currentTarget } = e
      const elem = $(currentTarget)
      const ef = elem.attr("ef")
      const nd = elem.attr("nd")
      const md = elem.attr("md")
      const arrow = elem.attr("arrow")
      let f
      let t
      if (arrow == "right") {
        f = parseInt(nd)
        t = parseInt(md)
      }
      else {
        t = parseInt(nd)
        f = parseInt(md)
      }
      for (let p = 1; p <= 3; p++) {
        const fRep = p == 1 ? f : p == 2 ? "any" : f
        const tRep = p == 1 ? "any" : p == 2 ? t : t
        $(`input[name="edge_name_new_${p}"]`).val(ef)
        $(`input[name="edge_from_new_${p}"]`).val(fRep)
        $(`input[name="edge_to_new_${p}"]`).val(tRep)
      }
      storeForm()
      form.submit()
    })
}

/* controlling the filtering of the section list
 *
 */

const filterS0 = () => {
  const filterControl = $("#s0filter")
  const filterTotal = $("#s0total")
  const s0items = $(".s0nav")
  const total = s0items.length

  const applyFilter = filterValueRaw => {
    const filterValue = filterValueRaw.toLowerCase()
    let s = 0
    s0items.each((i, elem) => {
      const el = $(elem)
      const s0 = el.text().toLowerCase()
      if (filterValue == "" || s0.indexOf(filterValue) >= 0) {
        el.show()
        s += 1
      } else {
        el.hide()
      }
    })
    const totalRep = total == s ? `${total}` : `${s} of ${total}`
    filterTotal.html(totalRep)
  }

  filterControl.on("input", e => {
    e.preventDefault()
    const filterValue = e.target.value.toLowerCase()
    applyFilter(filterValue)
    storeForm()
  })

  applyFilter(filterControl.val())
}

/* controlling the side bar
 *
 */

const sidebar = () => {
  const side = $("#side")
  const sideStr = side.val()
  const parts = new Set(sideStr ? sideStr.split(",") : [])
  const headers = $("#sidebar div").filter(
    (i, elem) => $(elem).attr("status") != "about"
  )
  const bodies = $("#sidebarcont div").filter(
    (i, elem) => $(elem).attr("status") != "about"
  )
  headers.each((i, elem) => {
    const el = $(elem)
    const part = el.attr("status")
    if (parts.has(part)) {
      el.addClass("active")
    } else {
      el.removeClass("active")
    }
  })
  bodies.each((i, elem) => {
    const el = $(elem)
    const part = el.attr("status")
    if (parts.has(part)) {
      el.addClass("active")
    } else {
      el.removeClass("active")
    }
  })
  $("#sidebar a")
    .off("click")
    .click(e => {
      e.preventDefault()
      const { currentTarget } = e
      const header = $(currentTarget).closest("div")
      const part = header.attr("status")
      const side = $("#side")
      const sideStr = side.val()
      const parts = new Set(sideStr ? sideStr.split(",") : [])
      const body = $(`#sidebarcont div[status="${part}"]`)
      const isActive = header.hasClass("active")
      if (isActive) {
        header.removeClass("active")
        body.removeClass("active")
        parts.delete(part)
        side.val("")
      } else {
        header.addClass("active")
        body.addClass("active")
        parts.add(part)
      }
      side.val(Array.from(parts).join(","))
      storeForm()
    })
}

const doDstate = () => {
  const dstate = $("#dstate")
  const expandedStr = dstate.val()
  const dOpened = expandedStr == "" ? [] : expandedStr.split(",")
  for (const dId of dOpened) {
    const details = $(`#${dId}`)
    details.prop("open", true)
  }
  $("details.dstate").on("toggle", e => {
    const { currentTarget } = e
    const dStates = $("details.dstate")
    const op = $("#dstate")
    const thisState = $(currentTarget)
    const thisId = thisState.attr("id")
    const thisOpen = thisState.prop("open")
    const expandedDetails = dStates
      .filter((i, elem) => $(elem).prop("open") && $(elem).attr("id") != thisId)
      .map((i, elem) => $(elem).attr("id"))
      .get()
    if (thisOpen) {
      expandedDetails.push(thisId)
    }
    op.val(expandedDetails.join(","))
  })
}

/* controlling the textarea pads
 * Clicking on certain elements in the table rows will
 * populate the pads
 */

const sectionsEvent = e => {
  const elems = $("#sections")
  e.preventDefault()
  e.stopPropagation()
  const { currentTarget } = e
  const txt = $(currentTarget).attr("sec")
  const orig = elems.val()
  elems.val(`${orig}\n${txt}`)
}

const sections = () => {
  $(".rwh").off("click").click(sectionsEvent)
}

const tuplesEvent = e => {
  const elems = $("#tuples")
  e.preventDefault()
  e.stopPropagation()
  const { currentTarget } = e
  const txt = $(currentTarget).attr("tup")
  const orig = elems.val()
  elems.val(`${orig}\n${txt}`)
}

const tuples = () => {
  $(".sq").off("click").click(tuplesEvent)
}

const nodesEvent = e => {
  const elems = $("#tuples")
  e.preventDefault()
  e.stopPropagation()
  const { currentTarget } = e
  const txt = $(currentTarget).text()
  const orig = elems.val()
  elems.val(`${orig}\n${txt}`)
}

const nodes = () => {
  $(".nd").off("click").click(nodesEvent)
}

/* job control
 *
 */

const verifyApp = (jobContent, app) => {
  const { appName } = jobContent
  if (appName == app) {
    return true
  }
  if (confirm(`Change app "${appName}" to "${app}" ?`)) {
    jobContent["appName"] = app
    return true
  }
  return false
}

const suggestName = (jobName, other) => {
  const jobs = getJobs()
  let newName = jobName
  const resolved = s => s != "" && (!other || s != jobName) && !jobs.has(s)
  let cancelled = false
  while (!resolved(newName) && !cancelled) {
    while (!resolved(newName)) {
      newName += "N"
    }
    const answer = prompt("New job name:", newName)
    if (answer == null) {
      cancelled = true
    } else {
      newName = answer
    }
  }
  return cancelled ? null : newName
}

const jobOptions = () => {
  const jChange = $("#jchange")
  const jobh = $("#jobh")
  const currentJob = jobh.val()
  let html = ""
  for (const job of getJobs()) {
    const selected = job == currentJob ? " selected" : ""
    html += `<option value="${job}"${selected}>${job}</option>`
    jChange.html(html)
  }
}

const jobControls = () => {
  const jChange = $("#jchange")
  const jClear = $("#jclear")
  const jDelete = $("#jdelete")
  const jRename = $("#jrename")
  const jNew = $("#jnew")
  const jDup = $("#jdup")
  const jOpen = $("#jopen")
  const jFile = $("#jfile")
  const jMeta = $("#jmeta")
  const aName = $("#appName")
  const metaDiv = $("#exportmeta")
  const metaOpen = $("#jmetaopen")

  const form = $("form")
  const jobh = $("#jobh")

  const isOpen = metaOpen.val() == "v"
  if (isOpen) {
    metaDiv.show()
  }
  else {
    metaDiv.hide()
  }

  jChange.change(e => {
    const oldJob = jobh.val()
    const newJob = e.target.value
    if (oldJob == newJob) {
      return
    }
    storeForm()
    setLastJob($("#appName").val(), newJob)
    jobh.val(e.target.value)
    readForm()
    form.submit()
  })

  jClear.off("click").click(() => {
    const jobName = jobh.val()
    if (confirm(`Reset job ${jobName}?`)) {
      clearForm()
      storeForm()
      setLastJob($("#appName").val(), $("#jobh").val())
      form.submit()
    }
  })

  jDelete.off("click").click(() => {
    const jobName = jobh.val()
    if (confirm(`Delete job ${jobName}?`)) {
      setLastJob($("#appName").val(), "")
      deleteForm()
      jobh.val("")
      clearForm()
    }
  })

  jRename.off("click").click(e => {
    const jobName = jobh.val()
    const newName = suggestName(jobName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    deleteForm()
    jobh.val(newName)
    storeForm()
    setLastJob($("#appName").val(), $("#jobh").val())
  })

  jOpen.off("click").click(e => {
    jFile.click()
    e.preventDefault()
  })
  jFile.change(() => {
    const jobFile = jFile.prop("files")[0]
    const reader = new FileReader()
    reader.onload = e => {
      const jobContent = JSON.parse(e.target.result)
      if (!verifyApp(jobContent, aName.val())) {
        e.preventDefault()
        return
      }
      const newName = suggestName(jobContent.jobName, false)
      if (newName == null) {
        e.preventDefault()
        return
      }
      storeForm()
      jobContent["jobName"] = newName
      readForm(jobContent)
      setLastJob($("#appName").val(), $("#jobh").val())
      form.submit()
    }
    reader.readAsText(jobFile)
  })

  jNew.off("click").click(e => {
    const jobName = jobh.val()
    const newName = suggestName(jobName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    storeForm()
    clearForm()
    jobh.val(newName)
    setLastJob($("#appName").val(), $("#jobh").val())
    storeForm()
  })

  jDup.off("click").click(e => {
    const jobName = jobh.val()
    const newName = suggestName(jobName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    storeForm()
    jobh.val(newName)
    setLastJob($("#appName").val(), $("#jobh").val())
    storeForm()
  })

  jMeta.off("click").click(e => {
    e.preventDefault()
    metaDiv.toggle()
    const isOpen = metaOpen.val() == "v"
    metaOpen.val(isOpen ? "x" : "v")
  })
}

const readForm = jobContent => {
  let formObj
  const go = document.querySelector("form")
  if (jobContent == null) {
    const formData = new FormData(go)
    const appName = formData.get("appName")
    const jobName = formData.get("jobName")
    const formKey = `tf/${appName}/${jobName}`
    const formStr = localStorage.getItem(formKey)
    formObj = JSON.parse(formStr)
  } else {
    formObj = jobContent
  }
  const form = $("#go")
  for (const [key, value] of Object.entries(formObj)) {
    let iElem = $(`[name="${key}"]`)
    if (iElem.length == 0) {
      form.prepend(`<input type="hidden" name="${key}" value="${value}">`)
      iElem = $(`[name="${key}"]`)
    }
    iElem.val(value)
  }
}

const clearForm = () => {
  $("#resetf").val("1")
}

const deleteForm = () => {
  const go = document.querySelector("form")
  const formData = new FormData(go)
  const appName = formData.get("appName")
  const jobName = formData.get("jobName")
  const formKey = `tf/${appName}/${jobName}`
  localStorage.removeItem(formKey)
}

const storeForm = () => {
  const go = document.querySelector("form")
  const formData = new FormData(go)
  const formObj = {}
  for (const [key, value] of formData) {
    formObj[key] = value
  }
  const formStr = JSON.stringify(formObj)
  const appName = formData.get("appName")
  const jobName = formData.get("jobName")
  const formKey = `tf/${appName}/${jobName}`
  localStorage.setItem(formKey, formStr)
}

const getJobs = () => {
  const go = document.querySelector("form")
  const formData = new FormData(go)
  const appName = formData.get("appName")
  const tfPrefix = `tf/${appName}/`
  const tfLength = tfPrefix.length
  return new Set(
    Object.keys(localStorage)
      .filter(key => key.startsWith(tfPrefix))
      .map(key => key.substring(tfLength))
  )
}

const setLastJob = (appName, jobName) => {
  const lastJob = localStorage.getItem(lastJobKey)
  const lastJobData = lastJob ? JSON.parse(lastJob) : {}
  lastJobData[appName] = jobName
  localStorage.setItem(lastJobKey, JSON.stringify(lastJobData))
}

const getLastJob = appName => {
  const lastJob = localStorage.getItem(lastJobKey)
  const lastJobData = lastJob ? JSON.parse(lastJob) : {}
  const { [appName]: lastJobName } = lastJobData
  return lastJobName == null ? "default" : lastJobName
}

const initForm = () => {
  const loadJob = $("#jobl")
  if (loadJob.val() == "1") {
    loadJob.val("")
    const appName = $("#appName").val()
    const lastJobName = getLastJob(appName)
    const jobContent = localStorage.getItem(`tf/${appName}/${lastJobName}`)
    if (jobContent) {
      readForm(JSON.parse(jobContent))
      $("form").submit()
    }
  } else {
    storeForm()
  }
}

/* main
 *
 */

$(window).on("load", () => {
  initForm()
  sidebar()
  modes()
  activateTables("sections", null)
  activateTables("tuples", null)
  activateTables("query", "pages")
  cradios()
  colorMap()
  eColorMap()
  doDstate()
  reactive()
  jobOptions()
  jobControls()
})
