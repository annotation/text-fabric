/*eslint-env jquery*/

const suggestName = oldName => {
  let cancelled = false
  let newName = null
  const answer = prompt("Name for annotation set:", oldName || "")
  if (answer == null) {
    cancelled = true
  } else {
    newName = answer
  }
  return cancelled ? null : newName
}

const storeForm = () => {
  const { toolkey } = globalThis
  const go = document.querySelector("form")
  const formData = new FormData(go)
  const formObj = {}
  for (const [key, value] of formData) {
    formObj[key] = value
  }
  const formStr = JSON.stringify(formObj)
  const appName = formData.get("appname")
  const formKey = `tf${toolkey}/${appName}`
  localStorage.setItem(formKey, formStr)
}

const annoSetControls = () => {
  const subMitter = $("#submitter")
  const annoseth = $("#annoseth")
  const duannoseth = $("#duannoseth")
  const rannoseth = $("#rannoseth")
  const dannoseth = $("#dannoseth")

  const aNew = $("#anew")
  const aDup = $("#adup")
  const aRename = $("#arename")
  const aDelete = $("#adelete")
  const aChange = $("#achange")

  const form = $("form")

  aChange.change(e => {
    const oldAnnoSet = annoseth.val()
    const newAnnoSet = e.target.value
    if (oldAnnoSet == newAnnoSet) {
      return
    }
    annoseth.val(e.target.value)
    storeForm()
    subMitter.val("achange")
    form.trigger("submit")
  })

  aNew.off("click").click(e => {
    const newName = suggestName(null)
    if (newName == null) {
      e.preventDefault()
      return
    }
    annoseth.val(newName)
    storeForm()
  })

  aDup.off("click").click(e => {
    const annoSetName = annoseth.val()
    const newName = suggestName(annoSetName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    duannoseth.val(newName)
    storeForm()
  })

  aRename.off("click").click(e => {
    const annoSetName = annoseth.val()
    const newName = suggestName(annoSetName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    rannoseth.val(newName)
    storeForm()
  })

  aDelete.off("click").click(() => {
    const annoSetName = annoseth.val()
    if (confirm(`Delete annotation set ${annoSetName}?`)) {
      dannoseth.val(annoSetName)
    }
    storeForm()
  })
}

const updateScope = () => {
  const selectAll = $("#selectall")
  const selectNone = $("#selectnone")
  const endTokensX = $(`span[te][st="x"],span[te][st=""]`)
  const endTokensV = $(`span[te][st="v"]`)
  const nx = endTokensX.length
  const nv = endTokensV.length
  const nt = nx + nv
  const labx = nx && !nv ? " (all)" : ` of ${nt}`
  const labv = nv && !nx ? " (all)" : ` of ${nt}`

  if (nx && !nv) {
    selectNone.addClass("active")
  } else {
    selectNone.removeClass("active")
  }
  if (nv && !nx) {
    selectAll.addClass("active")
  } else {
    selectAll.removeClass("active")
  }
  selectNone.html(`❌ ${nx}${labx}`)
  selectAll.html(`✅ ${nv}${labv}`)
}

const entityControls = () => {
  const form = $("form")
  const subMitter = $("#submitter")
  const { features } = globalThis
  const findBox = $("#efind")
  const eStat = $("#nentityentries")
  const findClear = $("#entityclear")
  const sortControls = $(`button[tp="sort"]`)
  const sortKeyInput = $("#sortkey")
  const sortDirInput = $("#sortdir")
  const entities = $("p.e")
  const entitiesDiv = $("#entities")
  const tokenStart = $("#tokenstart")
  const tokenEnd = $("#tokenend")
  const activeEntity = $("#activeentity")
  const selectAll = $("#selectall")
  const selectNone = $("#selectnone")

  const gotoFocus = () => {
    const ea = activeEntity.val()
    const rTarget = entitiesDiv.find(`p.e[enm="${ea}"]`)
    if (rTarget != null && rTarget[0] != null) {
      rTarget[0].scrollIntoView({ block: "center" })
    }
  }

  const showAll = () => {
    entities.each((i, elem) => {
      const el = $(elem)
      el.show()
    })
    eStat.html(entities.length)
    gotoFocus()
  }

  const showSelected = (ss, always) => {
    let n = 0
    entities.each((i, elem) => {
      const el = $(elem)

      let show = false

      if (always) {
        const enm = el.attr("enm")
        if (enm == always) {
          show = true
        }
      }

      if (!show) {
        const et = el.find("span")
        const text = et.html()
        if (text.toLowerCase().includes(ss)) {
          show = true
        }
      }

      if (show) {
        el.show()
        n += 1
      } else {
        el.hide()
      }
    })
    eStat.html(n)
    gotoFocus()
  }

  const showIt = () => {
    const ss = findBox.val().trim().toLowerCase()
    if (ss.length == 0) {
      findClear.hide()
      showAll()
    } else {
      findClear.show()
      const always = activeEntity.val()
      showSelected(ss, always)
    }
  }

  showIt()

  findBox.off("keyup").keyup(() => {
    const pat = findBox.val()
    if (pat.length) {
      findClear.show()
    } else {
      findClear.hide()
    }
    showIt()
  })

  findClear.off("click").click(() => {
    findBox.val("")
    showIt()
  })

  sortControls.off("click").click(e => {
    const { currentTarget } = e
    const elem = $(currentTarget)
    const sortKey = elem.attr("sk")
    const sortDir = elem.attr("sd")
    sortKeyInput.val(sortKey)
    sortDirInput.val(sortDir == "u" ? "d" : "u")
    subMitter.val(`${sortKey}-${sortDir}`)
    form.trigger("submit")
  })

  selectAll.off("click").click(() => {
    const endTokens = $("span[te]")
    endTokens.attr("st", "v")
    updateScope()
  })

  selectNone.off("click").click(() => {
    const endTokens = $("span[te]")
    endTokens.attr("st", "x")
    updateScope()
  })

  entitiesDiv.off("click").click(e => {
    e.preventDefault()
    const { target } = e
    const elem = $(target)
    const tag = elem[0].localName
    const eEntity = tag == "p" && elem.hasClass("e") ? elem : elem.closest("p.e")
    if (eEntity.length) {
      const tStart = eEntity.attr("tstart")
      const tEnd = eEntity.attr("tend")
      const enm = eEntity.attr("enm")
      tokenStart.val(tStart)
      tokenEnd.val(tEnd)
      activeEntity.val(enm)

      for (const feat of features) {
        const val = eEntity.find(`span.${feat}`).html()
        $(`#${feat}_active`).val(val)
        $(`#${feat}_select`).val(val)
      }
      subMitter.val(`entity-${enm}`)
      form.trigger("submit")
    }
  })
}

const tokenControls = () => {
  const form = $("form")
  const subMitter = $("#submitter")
  const { features, toolkey } = globalThis
  const sentences = $("#sentences")
  const findBox = $("#sfind")
  const findC = $("#sfindc")
  const findCButton = $("#sfindb")
  const findClear = $("#findclear")
  const findError = $("#sfinderror")
  const tokenStart = $("#tokenstart")
  const tokenEnd = $("#tokenend")
  const qWordShow = $("#qwordshow")
  const lookupf = $("#lookupf")
  const lookupq = $("#lookupq")
  const lookupn = $("#lookupn")
  const freeState = $("#freestate")
  const freeButton = $("#freebutton")
  const queryClear = $("#queryclear")
  const scope = $("#scope")
  const scopeFiltered = $("#scopefiltered")
  const scopeAll = $("#scopeall")
  const tokenStartVal = tokenStart.val()
  const tokenEndVal = tokenEnd.val()
  const activeEntity = $("#activeentity")
  const entitiesDiv = $("#entities")
  const filted = $("span.filted")

  let upToDate = true
  let tokenRange = []

  const tokenInit = () => {
    tokenRange =
      tokenStartVal && tokenEndVal
        ? [parseInt(tokenStartVal), parseInt(tokenEndVal)]
        : []
    if (tokenRange.length) {
      if (tokenRange[0] > tokenRange[1]) {
        tokenRange = [tokenRange[1], tokenRange[0]]
      }
    }
  }

  const presentQueryControls = update => {
    if (update) {
      qWordShow.html("")
    }
    const hasQuery = tokenRange.length
    const hasFind = findBox.val().length
    const findErrorStr = findError.html().length

    if (findErrorStr) {
      findError.show()
    } else {
      findError.hide()
    }

    const setQueryControls = onoff => {
      if (onoff) {
        lookupq.show()
        queryClear.show()
        qWordShow.show()
        freeButton.show()
      } else {
        queryClear.hide()
        qWordShow.hide()
        freeButton.hide()
      }
    }

    if (hasFind || hasQuery) {
      if (!upToDate) {
        if (hasFind) {
          lookupf.show()
        }
        if (hasQuery) {
          lookupq.show()
          lookupn.show()
        }
      }
      if (hasFind) {
        findClear.show()
      } else {
        findClear.hide()
      }
      if (hasQuery) {
        setQueryControls(true)
        if (update) {
          for (let t = tokenRange[0]; t <= tokenRange[1]; t++) {
            const elem = $(`span[t="${t}"]`)
            elem.addClass("queried")
            const qWord = elem.html()
            qWordShow.append(`<span>${qWord}</span> `)
          }
        }
      } else {
        setQueryControls(false)
      }
    } else {
      findClear.hide()
      lookupf.hide()
      lookupq.hide()
      lookupn.hide()
      setQueryControls(false)
    }
  }

  tokenInit()
  presentQueryControls(false)

  const doAppearance = () => {
    const widget = $("#appearancewidget")
    const decorateWidget = $("#decoratewidget")
    const appearanceControl = widget.find("button[main]")
    const appearanceButtons = widget.find("button[feat]")
    console.warn({ appearanceButtons })

    const controlAppearance = toggle => {
      const inputElem = appearanceControl.closest("span").find("input")
      const currentState = inputElem.val()
      const newState = toggle ? (currentState == "v" ? "x" : "v") : currentState

      inputElem.val(newState)
      appearanceControl.html(newState == "v" ? "decorated" : "plain")

      if (newState == "v") {
        decorateWidget.show()
        setAll(true)
      }
      else {
        decorateWidget.hide()
        setAll(false)
      }
    }

    const setAppearance = (elem, toggle, enable) => {
      const inputElem = elem.closest("span").find("input")
      const currentState = inputElem.val()
      const newState = toggle ? (currentState == "v" ? "x" : "v") : currentState
      const feat = elem.attr("feat")
      const eTarget = $("span.es")
      const targetElems =
        feat == "_stat_"
          ? eTarget.find(`.n`)
          : feat == "_entity_"
          ? $("span.ei")
          : eTarget.find(`.${feat}`)
      const lgbElems = $(".lgb")
      const lgeElems = $(".lge")

      inputElem.val(newState)
      if (enable && newState == "v") {
        elem.addClass("active")
        if (feat == "_entity_") {
          targetElems.removeClass("noformat")
          lgbElems.show()
          lgeElems.show()
        } else {
          targetElems.show()
        }
      } else {
        elem.removeClass("active")
        if (feat == "_entity_") {
          targetElems.addClass("noformat")
          lgbElems.hide()
          lgeElems.hide()
        } else {
          targetElems.hide()
        }
      }
    }

    const setAll = enable => {
      appearanceButtons.each((i, e) => {
        const elem = $(e)
        setAppearance(elem, false, enable)
      })
    }

    appearanceControl.off("click").click(() => {
      controlAppearance(true)
    })

    appearanceButtons.off("click").click(e => {
      const { currentTarget } = e
      const elem = $(currentTarget)
      setAppearance(elem, true, true)
    })

    controlAppearance(false)
  }

  doAppearance(false)

  findBox.off("keyup").keyup(() => {
    const pat = findBox.val()
    upToDate = false
    if (pat.length) {
      findClear.show()
      lookupf.show()
    } else {
      findClear.hide()
      if (tokenRange.length == 0) {
        lookupf.hide()
      }
    }
  })

  findCButton.off("click").click(() => {
    const val = findC.val()
    const newVal = val == "v" ? "x" : "v"
    findC.val(newVal)
  })

  findClear.off("click").click(() => {
    findBox.val("")
  })

  freeButton.off("click").click(() => {
    const free = freeState.val()
    const newFree = free == "bound" ? "all" : free == "free" ? "bound" : "free"
    freeState.val(newFree)
  })

  const setScope = val => {
    scope.val(val)
    if (val == "a") {
      scopeAll.addClass("active")
      scopeFiltered.removeClass("active")
      filted.hide()
    } else {
      scopeFiltered.addClass("active")
      scopeAll.removeClass("active")
      filted.show()
    }
  }

  setScope(scope.val())

  scopeFiltered.off("click").click(() => {
    setScope("f")
  })
  scopeAll.off("click").click(() => {
    setScope("a")
  })

  const selectWidget = $("#selectwidget")

  for (const feat of features) {
    const sel = selectWidget.find(`button.${feat}_sel`)
    const select = selectWidget.find(`#${feat}_select`)

    sel.off("click").click(e => {
      const { currentTarget } = e
      const elem = $(currentTarget)
      const currentStatus = elem.attr("st")

      elem.attr("st", currentStatus == "v" ? "x" : "v")
      const vals = sel
        .get()
        .filter(x => $(x).attr("st") == "v")
        .map(x => $(x).attr("name"))
        .join(",")
      select.val(vals)
      subMitter.val(`${feat}_sel`)
      form.trigger("submit")
    })
  }

  sentences.off("click").click(e => {
    e.preventDefault()
    const { target } = e
    const elem = $(target)
    const viewer = elem.closest("div.viewer")
    if (viewer.length) {
      return
    }
    const tag = elem[0].localName
    const t = elem.attr("t")
    const te = elem.attr("te")
    const enm = elem.attr("enm")
    const node = elem.attr("node")
    const eToken =
      tag == "span" && t != null && t !== false ? elem : elem.closest("span[t]")
    const eTokenEnd =
      tag == "span" && te != null && te !== false ? elem : elem.closest("span[te]")
    const eMarkedEntity =
      tag == "span" && elem.hasClass("es") && enm != null && enm !== false
        ? elem
        : elem.closest("span.es[enm]")
    const eSectionHeading =
      tag == "span" && elem.hasClass("sh") && node != null && node !== false
        ? elem
        : elem.closest("span.sh[node]")

    if (eToken.length) {
      const tWord = eToken.attr("t")
      const tWordInt = parseInt(tWord)
      upToDate = false
      if (tokenRange.length == 0) {
        tokenRange = [tWordInt, tWordInt]
      } else if (tokenRange.length == 2) {
        const start = tokenRange[0]
        const end = tokenRange[1]
        if (tWordInt < start - 5 || tWordInt > end + 5) {
          tokenRange = [tWordInt, tWordInt]
        } else if (tWordInt <= start) {
          tokenRange = [tWordInt, tokenRange[1]]
        } else if (tWordInt >= end) {
          tokenRange = [tokenRange[0], tWordInt]
        } else if (end - tWordInt <= tWordInt - start) {
          tokenRange = [tokenRange[0], tWordInt]
        } else {
          tokenRange = [tWordInt, tokenRange[1]]
        }
      }
      tokenStart.val(`${tokenRange[0]}`)
      tokenEnd.val(`${tokenRange[1]}`)
      activeEntity.val("")

      presentQueryControls(true)
    }

    if (eTokenEnd.length) {
      const currentValue = eTokenEnd.attr("st")
      eTokenEnd.attr("st", currentValue == "v" ? "x" : "v")
      updateScope()
    }

    if (eMarkedEntity.length) {
      const ea = eMarkedEntity.attr("enm")
      activeEntity.val(ea)

      const eEntry = entitiesDiv.find(`p.e[enm="${ea}"]`)
      tokenStart.val(eEntry.attr("tstart"))
      tokenEnd.val(eEntry.attr("tend"))

      for (const feat of features) {
        const val = eMarkedEntity.find(`span.${feat}`).html()
        $(`#${feat}_active`).val(val)
        $(`#${feat}_select`).val(val)
      }
      subMitter.val(`entity-in-sentence-${ea}`)
      form.trigger("submit")
    }

    if (eSectionHeading.length) {
      const nd = eSectionHeading.attr("node")
      const sent = eSectionHeading.closest("div")
      let viewerControls = sent.next()

      if (viewerControls.length == 0 || viewerControls.hasClass("s")) {
        eSectionHeading.attr("title", "hide context")
        eSectionHeading.addClass("center")
        sent.after(`
        <div class="viewercontrol">
          <button
            type="button"
            name="center"
            class="altv"
            title="scroll to center sentence in context viewer"
          >🔵</button>
        </div>
        `)
        viewerControls = sent.next()
        viewerControls.after(`<div class="viewer"></div>`)
        const viewer = viewerControls.next()
        viewer.before("<hr>")
        viewer.after("<hr>")
        const go = document.querySelector("form")
        const formData = new FormData(go)
        const url = `/${toolkey}/context/${nd}`
        $.ajax({
          type: "POST",
          url,
          data: formData,
          processData: false,
          contentType: false,
          success: data => {
            viewer.html(data)
            const centerViewer = viewer.find(`span.sh[node="${nd}"]`)
            const centerMain = sentences.find(`span.sh[node="${nd}"]`)
            const targets = [centerViewer, centerMain]
            for (const tgt of targets) {
              if (tgt != null && tgt[0] != null) {
                tgt[0].scrollIntoView({ block: "center" })
              }
              const s = tgt.closest("div")
              s.addClass("center")
            }
            viewerControls.find(`button[name="center"]`).click(() => {
              centerViewer[0].scrollIntoView({ block: "center" })
            })
            doAppearance(true)
          },
        })
      } else {
        viewerControls.next().next().next().remove()
        viewerControls.next().next().remove()
        viewerControls.next().remove()
        viewerControls.remove()
        sent.removeClass("center")
        eSectionHeading.removeClass("center")
      }
    }
  })

  queryClear.off("click").click(() => {
    tokenRange.length = 0
    tokenStart.val("")
    tokenEnd.val("")
    qWordShow.html("")
    activeEntity.val("")
    for (const feat of features) {
      $(`#${feat}_active`).val("")
    }
  })

  form.on("submit", e => {
    const excludedTokens = $("#excludedtokens")
    const endTokens = $(`span[te][st="x"]`)
    const excl = endTokens
      .get()
      .map(elem => $(elem).attr("te"))
      .join(",")
    excludedTokens.val(excl)
    const { originalEvent: { submitter } = {} } = e
    if (submitter) {
      subMitter.val(submitter.id)
    }
  })
}

const modifyControls = () => {
  const { features } = globalThis
  const form = $("form")
  const subMitter = $("#submitter")
  const modWidgetState = $("#modwidgetstate")
  const delWidgetSwitch = $("#delwidgetswitch")
  const addWidgetSwitch = $("#addwidgetswitch")
  const delWidget = $("#delwidget")
  const delAssign = delWidget.find(".assignwidget")
  const addWidget = $("#addwidget")
  const addAssign = addWidget.find(".assignwidget")
  const delControl = delAssign.find(`span`)
  const addControl = addAssign.find(`span`)
  const input = addAssign.find(`input[type="text"]`)
  const delResetButton = $(`#delresetbutton`)
  const addResetButton = $(`#addresetbutton`)
  const delGo = $("#delgo")
  const addGo = $("#addgo")
  const delFeedback = $("#delfeedback")
  const addFeedback = $("#addfeedback")
  const delReport = $("#delreport")
  const addReport = $("#addreport")
  const delData = $("#deldata")
  const addData = $("#adddata")

  const switchToAddDel = toggle => {
    let val = modWidgetState.val() || "add"
    if (toggle) {
      const newVal = val == "add" ? "del" : "add"
      modWidgetState.val(newVal)
      val = newVal
    }
    if (val == "add") {
      delWidget.hide()
      addWidget.show()
    } else {
      delWidget.show()
      addWidget.hide()
    }
  }

  switchToAddDel()

  delWidgetSwitch.off("click").click(() => {
    switchToAddDel(true)
  })

  addWidgetSwitch.off("click").click(() => {
    switchToAddDel(true)
  })

  const makeDelData = () => {
    const deletions = []
    const missingDeletions = []

    for (const feat of features) {
      const widget = $(`div.delfeat[feat="${feat}"]`)
      const span = widget.find("span[st]")

      const theseDels = []

      for (const elem of span.get()) {
        const el = $(elem)
        const st = el.attr("st")
        const val = el.attr("val")
        if (st == "minus") {
          theseDels.push(val)
        }
      }
      deletions.push(theseDels)
      if (theseDels.length == 0) {
        missingDeletions.push(feat)
      }
    }
    const anyHasDeletions = deletions.some(x => x.length > 0)
    const allHaveDeletions = deletions.every(x => x.length > 0)
    const allOrNothingDeletions = !anyHasDeletions || allHaveDeletions

    let good = false

    if (anyHasDeletions) {
      if (allOrNothingDeletions) {
        delGo.removeClass("disabled")
        delGo.addClass("del")
        delFeedback.html("")
        good = true
      } else {
        delGo.removeClass("del")
        delGo.addClass("disabled")
        delFeedback.html(
          `provide at least one red value for ${missingDeletions.join(" and ")}`
        )
      }
    } else {
      delGo.addClass("disabled")
      delGo.removeClass("del")
      delFeedback.html("click values ...")
    }
    delData.val(encodeURIComponent(JSON.stringify({ deletions })))
    return { good, data: { deletions } }
  }
  const makeAddData = () => {
    const missingAdditions = []
    const additions = []
    const freeVals = []

    for (const feat of features) {
      const widget = $(`div.addfeat[feat="${feat}"]`)
      const span = widget.find("span[st]")
      const inp = widget.find("input[st]")

      const theseAdds = []

      for (const elem of span.get()) {
        const el = $(elem)
        const st = el.attr("st")
        const val = el.attr("val")
        if (st == "plus") {
          theseAdds.push(val)
        }
      }
      for (const elem of inp.get()) {
        const el = $(elem)
        const st = el.attr("st")
        const val = el.val()
        if (st == "plus") {
          theseAdds.push(val)
          freeVals.push(val)
        } else {
          freeVals.push(null)
        }
      }
      additions.push(theseAdds)
      if (theseAdds.length == 0) {
        missingAdditions.push(feat)
      }
    }
    const anyHasAdditions = additions.some(x => x.length > 0)
    const allHaveAdditions = additions.every(x => x.length > 0)
    const allOrNothingAdditions = !anyHasAdditions || allHaveAdditions

    let good = false

    if (anyHasAdditions) {
      if (allOrNothingAdditions) {
        addGo.removeClass("disabled")
        addGo.addClass("add")
        addFeedback.html("")
        good = true
      } else {
        addGo.addClass("disabled")
        addGo.removeClass("add")
        addFeedback.html(
          `provide at least one green value for ${missingAdditions.join(" and ")}`
        )
      }
    } else {
      addGo.addClass("disabled")
      addGo.removeClass("add")
      addFeedback.html("click values ...")
    }
    addData.val(encodeURIComponent(JSON.stringify({ additions, freeVals })))
    return { good, data: { additions, freeVals } }
  }

  delControl.off("click").click(e => {
    const { currentTarget } = e
    const elem = $(currentTarget)
    const currentStatus = elem.attr("st")

    const newStatus = currentStatus == "minus" ? "x" : "minus"
    elem.attr("st", newStatus)
    makeDelData()
  })

  addControl.off("click").click(e => {
    const { currentTarget } = e
    const elem = $(currentTarget)
    const currentStatus = elem.attr("st")

    const newStatus = currentStatus == "plus" ? "x" : "plus"

    elem.attr("st", newStatus)
    makeAddData()
  })
  input.off("keyup").keyup(e => {
    const { currentTarget } = e
    const elem = $(currentTarget)
    const val = elem.val()
    if (val == "") {
      elem.attr("st", "x")
    } else {
      elem.attr("st", "plus")
    }
    makeAddData()
  })
  input.off("click").click(e => {
    const { currentTarget } = e
    const elem = $(currentTarget)
    const val = elem.val()
    if (val == "") {
      elem.attr("st", "x")
    } else {
      const currentStatus = elem.attr("st")
      elem.attr("st", currentStatus == "x" ? "plus" : "x")
    }
    makeAddData()
  })
  delResetButton.off("click").click(() => {
    const span = delWidget.find("span[st]")
    span.each((i, elem) => {
      const el = $(elem)
      el.attr("st", "")
    })
  })
  addResetButton.off("click").click(() => {
    const span = addWidget.find("span[st]")
    const inp = addWidget.find("input[st]")
    span.each((i, elem) => {
      const el = $(elem)
      el.attr("st", "")
    })
    inp.each((i, elem) => {
      const el = $(elem)
      el.attr("st", "")
      el.val("")
    })
  })

  delGo.off("click").click(() => {
    const { good, data } = makeDelData()

    delReport.html("")
    delFeedback.html("")

    if (good) {
      delData.val(encodeURIComponent(JSON.stringify(data)))
      subMitter.val("delgo")
      form.trigger("submit")
    } else {
      delData.val("")
    }
  })

  addGo.off("click").click(() => {
    const { good, data } = makeAddData()

    addReport.html("")
    addFeedback.html("")

    if (good) {
      addData.val(encodeURIComponent(JSON.stringify(data)))
      subMitter.val("addgo")
      form.trigger("submit")
    } else {
      addData.val("")
    }
  })

  updateScope()
  makeDelData()
  makeAddData()
}

const initForm = () => {
  storeForm()
  globalThis.toolkey = $("#toolkey").val()
  globalThis.features = $("#featurelist").val().split(",")
}

/* main
 *
 */

$(window).on("load", () => {
  initForm()
  annoSetControls()
  entityControls()
  tokenControls()
  modifyControls()
})
