/*eslint-env jquery*/

const sortDirAsc = "a"
const sortDirDesc = "d"
const scAll = "a"
const scFilt = "f"

const suggestName = oldName => {
  let cancelled = false
  let newName = null
  const answer = prompt("Name for annotation task:", oldName || "")
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

const setControls = () => {
  const subMitter = $("#submitter")
  const seth = $("#seth")
  const duseth = $("#duseth")
  const rseth = $("#rseth")
  const dseth = $("#dseth")

  const aNew = $("#anew")
  const aDup = $("#adup")
  const aRename = $("#arename")
  const aDelete = $("#adelete")
  const aChange = $("#achange")

  const sheetCase = $("#sheetcase")
  const sheetCaseButton = $("#sheetcasebutton")

  const form = $("form")

  aChange.change(e => {
    const oldSetName = seth.val()
    const newSetName = e.target.value
    if (oldSetName == newSetName) {
      return
    }
    seth.val(e.target.value)
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
    seth.val(newName)
    storeForm()
  })

  aDup.off("click").click(e => {
    const setName = seth.val()
    const realSetName = setName.startsWith(".") ? setName.substring(1) : setName
    let newName = suggestName(realSetName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    if (newName.startsWith(".")) {
      newName = newName.substring(1)
    }

    duseth.val(newName)
    storeForm()
  })

  aRename.off("click").click(e => {
    const setName = seth.val()
    const newName = suggestName(setName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    rseth.val(newName)
    storeForm()
  })

  aDelete.off("click").click(() => {
    const setName = seth.val()
    if (confirm(`Delete annotation task ${setName}?`)) {
      dseth.val(setName)
    }
    storeForm()
  })

  sheetCaseButton.off("click").click(() => {
    const val = sheetCase.val()
    const newVal = val == "v" ? "x" : "v"
    sheetCase.val(newVal)
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

const updateModControls = () => {
  const delGo = $("#delgo")
  const addGo = $("#addgo")
  const endTokensV = $(`span[te][st="v"]`)
  const nv = endTokensV.length

  if (nv) {
    delGo.removeClass("notapplicable")
    addGo.removeClass("notapplicable")
  } else {
    delGo.addClass("notapplicable")
    addGo.addClass("notapplicable")
  }
  return nv
}

const entityControls = () => {
  const seth = $("#seth")
  const isSheet = seth.val().startsWith(".")
  const form = $("form")
  const subMitter = $("#submitter")
  const { features } = globalThis
  const findBox = $("#efind")
  const subtleFilterButton = $("#subtlefilterbutton")
  const subtleFilterInput = $("#subtlefilter")
  const eStat = $("#nentityentries")
  const findClear = $("#entityclear")
  const sortControls = $(`button[tp="sort"]`)
  const sortKeyInput = $("#sortkey")
  const sortDirInput = $("#sortdir")
  const entities = isSheet ? $("div.e") : $("p.e")
  const entitiesDiv = $("#entities")
  const activeEntity = $("#activeentity")
  const activeTrigger = $("#activetrigger")
  const selectAll = $("#selectall")
  const selectNone = $("#selectnone")
  const tokenStart = $("#tokenstart")
  const tokenEnd = $("#tokenend")

  const setSubtleFilterControl = () => {
    subtleFilterButton.off("click").click(() => {
      const s = subtleFilterInput.val()
      const newS = s == "v" ? "x" : s == "x" ? "" : "v"
      subtleFilterInput.val(newS)
    })
  }

  const gotoFocus = () => {
    const ea = activeEntity.val()
    let rTarget
    if (isSheet) {
      const et = activeTrigger.val()
      rTarget = []
      if (et) {
        rTarget = entitiesDiv.find(`div.et[etr="${et}"]`)
      }
      if (rTarget.length == 0) {
        rTarget = entitiesDiv.find(`div.e[enm="${ea}"]`)
      }
    } else {
      rTarget = entitiesDiv.find(`p.e[enm="${ea}"]`)
    }
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
    let x = 0
    entities.each((i, elem) => {
      const el = $(elem)

      let show = false

      if (always != "") {
        const enm = el.attr("enm")
        if (enm == always) {
          show = true
        }
      }

      if (!show) {
        const text = isSheet
          ? el.find("div.ntx").text() + el.find("code.ttx").text()
          : el.find("span.eid").text()
        if (text.toLowerCase().includes(ss)) {
          show = true
        }

        if (x < 10) {
          console.warn({ text, ss, hit: text.toLowerCase().includes(ss), show })
        }
      }

      if (show) {
        el.show()
        n += 1
      } else {
        el.hide()
      }
      x += 1
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
      const always = (isSheet && activeTrigger.val()) || activeEntity.val()
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

  setSubtleFilterControl()

  sortControls.off("click").click(e => {
    const { currentTarget } = e
    const elem = $(currentTarget)
    const sortKey = elem.attr("sk")
    const sortDir = elem.attr("sd")
    sortKeyInput.val(sortKey)
    sortDirInput.val(sortDir == sortDirAsc ? sortDirDesc : sortDirAsc)
    subMitter.val(`${sortKey}-${sortDir}`)
    form.trigger("submit")
  })

  selectAll.off("click").click(() => {
    const endTokens = $("span[te]")
    endTokens.attr("st", "v")
    updateScope()
    updateModControls()
  })

  selectNone.off("click").click(() => {
    const endTokens = $("span[te]")
    endTokens.attr("st", "x")
    updateScope()
    updateModControls()
  })

  entitiesDiv.off("click").click(e => {
    e.preventDefault()
    const { target } = e
    const elem = $(target)
    const tag = elem[0].localName
    const eEntity = isSheet
      ? tag == "div" && elem.hasClass("e")
        ? elem
        : elem.closest("div.e")
      : tag == "p" && elem.hasClass("e")
      ? elem
      : elem.closest("p.e")
    const eTrigger = isSheet
      ? tag == "div" && elem.hasClass("et")
        ? elem
        : elem.closest("div.et")
      : null
    if (eEntity.length) {
      const enm = eEntity.attr("enm")
      const prevActiveEntity = activeEntity.val()
      const sameEntity = prevActiveEntity == enm
      activeEntity.val(enm)
      tokenStart.val("")
      tokenEnd.val("")

      let myFeatures

      if (isSheet) {
        const [eid, kind] = enm.split("⊙")
        const prevActiveTrigger = activeTrigger.val()
        myFeatures = { eid, kind }
        let sameTrigger
        if (eTrigger.length) {
          const etr = eTrigger.attr("etr")
          sameTrigger = prevActiveTrigger == etr
          activeTrigger.val(etr)
        } else {
          activeTrigger.val("")
          sameTrigger = prevActiveTrigger == ""
        }
        if (sameEntity && sameTrigger) {
          if (prevActiveTrigger) {
            activeTrigger.val("")
          }
          else {
            activeEntity.val("")
          }
        }
      } else {
        myFeatures = {}
        for (const feat of features) {
          const val = eEntity.find(`span.${feat}`).html()
          myFeatures[feat] = val
        }
      }
      for (const [feat, val] of Object.entries(myFeatures)) {
        $(`#${feat}_active`).val(val)
        $(`#${feat}_select`).val(val)
      }
      subMitter.val(`entity-${enm}`)
      form.trigger("submit")
    }
  })
}

const tokenControls = () => {
  const seth = $("#seth")
  const isSheet = seth.val().startsWith(".")
  const form = $("form")
  const subMitter = $("#submitter")
  const { features, toolkey, bucketType } = globalThis
  const buckets = $("#buckets")
  const findBox = $("#bfind")
  const findC = $("#bfindc")
  const findCButton = $("#bfindb")
  const findClear = $("#findclear")
  const findError = $("#bfinderror")
  const anyEntButton = $("#anyentbutton")
  const anyEntInput = $("#anyent")
  const activeEntity = $("#activeentity")
  const activeTrigger = $("#activetrigger")
  const tokenStart = $("#tokenstart")
  const tokenEnd = $("#tokenend")
  const qTextEntShow = $("#qtextentshow")
  const lookupf = $("#lookupf")
  const lookupq = $("#lookupq")
  const lookupn = $("#lookupn")
  const freeState = $("#freestate")
  const freeButton = $("#freebutton")
  const queryClear = $("#queryclear")
  const scope = $("#scope")
  const scopeButton = $("#scopebutton")
  const activeVal = activeEntity.val()
  const tokenStartVal = tokenStart.val()
  const tokenEndVal = tokenEnd.val()
  const filted = $("span.filted")

  let upToDate = true
  let tokenRange = []

  const setTokenRange = () => {
    const tokenStartVal = tokenStart.val()
    const tokenEndVal = tokenEnd.val()
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

  const queryInit = () => {
    if (!activeVal && tokenStartVal && tokenEndVal) {
      setTokenRange()
    }
  }

  const setAnyEntControl = () => {
    anyEntButton.off("click").click(() => {
      const s = anyEntInput.val()
      const newS = s == "v" ? "x" : s == "x" ? "" : "v"
      anyEntInput.val(newS)
    })
  }

  const presentQueryControls = update => {
    if (update) {
      qTextEntShow.html("")
    }
    const activeVal = activeEntity.val()
    const anyEntVal = anyEntInput.val()
    const hasQuery = activeVal || tokenRange.length
    const hasFilter = findBox.val().length || anyEntVal
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
        qTextEntShow.removeClass("inactive")
        //qTextEntShow.show()
        freeButton.show()
      } else {
        queryClear.hide()
        //qTextEntShow.hide()
        qTextEntShow.html("click a word in the text or an entity in the list ...")
        qTextEntShow.addClass("inactive")
        freeButton.hide()
      }
    }

    if (hasFilter || hasQuery) {
      if (!upToDate) {
        lookupf.addClass("active")
        if (hasQuery) {
          lookupq.show()
          lookupn.show()
        }
      }
      if (hasFilter) {
        findClear.show()
      } else {
        findClear.hide()
      }
      if (hasQuery) {
        setQueryControls(true)
        if (update) {
          if (!activeVal) {
            setTokenRange()
            for (let t = tokenRange[0]; t <= tokenRange[1]; t++) {
              const elem = $(`span[t="${t}"]`)
              elem.addClass("queried")
              const qToken = elem.html()
              qTextEntShow.append(`<span>${qToken}</span> `)
            }
          }
        }
      } else {
        setQueryControls(false)
      }
    } else {
      findClear.hide()
      lookupf.removeClass("active")
      lookupq.hide()
      lookupn.hide()
      setQueryControls(false)
    }
  }

  setAnyEntControl()
  queryInit()
  presentQueryControls(false)

  const doAppearance = () => {
    const widget = $("#appearancewidget")
    const decorateWidget = $("#decoratewidget")
    const appearanceControl = widget.find("button[main]")
    const appearanceButtons = widget.find("button[feat]")

    const controlAppearance = toggle => {
      const inputElem = appearanceControl.closest("span").find("input")
      const currentState = inputElem.val()
      const newState = toggle ? (currentState == "v" ? "x" : "v") : currentState

      inputElem.val(newState)
      appearanceControl.html(newState == "v" ? "decorated" : "plain")

      if (newState == "v") {
        decorateWidget.show()
        setAll(true)
      } else {
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
    lookupf.addClass("active")
    if (pat.length) {
      findClear.show()
    } else {
      findClear.hide()
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

  const setScope = () => {
    const val = scope.val()
    if (val == scAll) {
      scopeButton.html("all")
      scopeButton.attr("title", `act on filtered ${bucketType}s only`)
      filted.hide()
    } else {
      scopeButton.html("filtered")
      scopeButton.attr("title", `act on all ${bucketType}s`)
      filted.show()
    }
  }

  setScope(scope.val())

  scopeButton.off("click").click(() => {
    const val = scope.val()
    const newVal = val == scFilt ? scAll : scFilt
    scope.val(newVal)
    setScope()
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

  buckets.off("click").click(e => {
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
      tag == "span" && elem.hasClass("bh") && node != null && node !== false
        ? elem
        : elem.closest("span.bh[node]")

    if (!isSheet && eToken.length) {
      const t = eToken.attr("t")
      const tInt = parseInt(t)
      upToDate = false
      if (tokenRange.length == 0) {
        tokenRange = [tInt, tInt]
      } else if (tokenRange.length == 2) {
        const start = tokenRange[0]
        const end = tokenRange[1]
        if (tInt < start - 5 || tInt > end + 5) {
          tokenRange = [tInt, tInt]
        } else if (tInt <= start) {
          tokenRange = [tInt, tokenRange[1]]
        } else if (tInt >= end) {
          tokenRange = [tokenRange[0], tInt]
        } else if (end - tInt <= tInt - start) {
          tokenRange = [tokenRange[0], tInt]
        } else {
          tokenRange = [tInt, tokenRange[1]]
        }
      }
      tokenStart.val(`${tokenRange[0]}`)
      tokenEnd.val(`${tokenRange[1]}`)
      activeEntity.val("")
      activeTrigger.val("")

      presentQueryControls(true)
    }

    if (!isSheet && eTokenEnd.length) {
      const currentValue = eTokenEnd.attr("st")
      eTokenEnd.attr("st", currentValue == "v" ? "x" : "v")
      updateScope()
      updateModControls()
    }

    if (eMarkedEntity.length) {
      const ea = eMarkedEntity.attr("enm")
      activeEntity.val(ea)

      for (const feat of features) {
        const val = eMarkedEntity.find(`span.${feat}`).html()
        $(`#${feat}_active`).val(val)
        $(`#${feat}_select`).val(val)
      }
      subMitter.val(`entity-in-bucket-${ea}`)
      form.trigger("submit")
    }

    if (eSectionHeading.length) {
      const nd = eSectionHeading.attr("node")
      const bucket = eSectionHeading.closest("div")
      let viewerControls = bucket.prev()

      if (viewerControls.length == 0 || viewerControls.hasClass("b")) {
        eSectionHeading.attr("title", "hide context")
        eSectionHeading.addClass("center")
        bucket.before(`
        <div class="viewercontrol">
          <button
            type="button"
            name="center"
            class="altv"
            title="scroll to center ${bucketType}in context viewer"
          >🔵</button>
        </div>
        `)
        viewerControls = bucket.prev()
        viewerControls.before(`<div class="viewer"></div>`)
        const viewer = viewerControls.prev()
        viewer.after("<hr>")
        viewer.before("<hr>")
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
            const centerViewer = viewer.find(`span.bh[node="${nd}"]`)
            const centerMain = buckets.find(`span.bh[node="${nd}"]`)
            const targets = [centerViewer, centerMain]
            for (const tgt of targets) {
              if (tgt != null && tgt[0] != null) {
                tgt[0].scrollIntoView({ block: "center" })
              }
              const b = tgt.closest("div")
              b.addClass("center")
            }
            viewerControls.find(`button[name="center"]`).click(() => {
              centerViewer[0].scrollIntoView({ block: "center" })
            })
            doAppearance(true)
          },
        })
      } else {
        viewerControls.prev().prev().prev().remove()
        viewerControls.prev().prev().remove()
        viewerControls.prev().remove()
        viewerControls.remove()
        bucket.removeClass("center")
        eSectionHeading.removeClass("center")
      }
    }
  })

  queryClear.off("click").click(() => {
    tokenRange.length = 0
    tokenStart.val("")
    tokenEnd.val("")
    qTextEntShow.html("")
    activeEntity.val("")
    activeTrigger.val("")
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
  /*
  const modWidgetState = $("#modwidgetstate")
  const delWidgetSwitch = $("#delwidgetswitch")
  const addWidgetSwitch = $("#addwidgetswitch")
  */
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

  /*
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
  */

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
        delFeedback.hide()
        good = true
      } else {
        delGo.removeClass("del")
        delGo.addClass("disabled")
        delFeedback.html(
          `provide at least one red value for ${missingDeletions.join(" and ")}`
        )
        delFeedback.show()
      }
    } else {
      delGo.addClass("disabled")
      delGo.removeClass("del")
      delFeedback.html("click values ...")
      delFeedback.show()
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
        addFeedback.hide()
        good = true
      } else {
        addGo.addClass("disabled")
        addGo.removeClass("add")
        addFeedback.html(
          `provide at least one green value for ${missingAdditions.join(" and ")}`
        )
        addFeedback.show()
      }
    } else {
      addGo.addClass("disabled")
      addGo.removeClass("add")
      addFeedback.html("click values ...")
      addFeedback.show()
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
    if (delGo.hasClass("disabled") || delGo.hasClass("notapplicable")) {
      return
    }
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
    if (addGo.hasClass("disabled") || addGo.hasClass("notapplicable")) {
      return
    }
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

  makeDelData()
  makeAddData()
  updateScope()
  updateModControls()
}

const inhibitEnter = () => {
  /* prevent submission of the form if the focus is in a textarea or input
   * element that does not have type=submit
   */
  const go = document.querySelector("form")
  $(go).on("keydown", ":input:not(textarea):not(:submit)", e => {
    if (e.key == "Enter") {
      e.preventDefault()
    }
  })
}

const initForm = () => {
  storeForm()
  inhibitEnter()
  globalThis.toolkey = $("#toolkey").val()
  globalThis.features = $("#featurelist").val().split(",")
  globalThis.slotType = $("#slottype").val()
  globalThis.bucketType = $("#buckettype").val()
}

/* main
 *
 */

$(window).on("load", () => {
  initForm()
  setControls()
  entityControls()
  tokenControls()
  modifyControls()
})
