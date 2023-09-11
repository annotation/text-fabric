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
  const go = document.querySelector("form")
  const formData = new FormData(go)
  const formObj = {}
  for (const [key, value] of formData) {
    formObj[key] = value
  }
  const formStr = JSON.stringify(formObj)
  const appName = formData.get("appName")
  const formKey = `tfner/${appName}`
  localStorage.setItem(formKey, formStr)
}

const annoSetControls = () => {
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
    form.submit()
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

const entityControls = () => {
  const form = $("form")
  const findBox = $("#eFind")
  const eStat = $("#nEntityEntries")
  const findClear = $("#entityClear")
  const entities = $("p.e")
  const tSelectStart = $("#tSelectStart")
  const tSelectEnd = $("#tSelectEnd")
  const activeEntity = $("#activeEntity")
  const activeKind = $("#activeKind")
  const selectAll = $("#selectall")
  const selectNone = $("#selectnone")

  const showAll = () => {
    entities.each((i, elem) => {
      const el = $(elem)
      el.show()
    })
    eStat.html(entities.length)
  }

  const showSelected = ss => {
    let n = 0
    entities.each((i, elem) => {
      const el = $(elem)
      const et = el.find("span.et")
      const text = et.html()
      if (text.toLowerCase().includes(ss)) {
        el.show()
        n += 1
      } else {
        el.hide()
      }
    })
    eStat.html(n)
  }

  const show = () => {
    const ss = findBox.val().trim().toLowerCase()
    if (ss.length == 0) {
      findClear.hide()
      showAll()
    } else {
      findClear.show()
      showSelected(ss)
    }
  }

  show()

  findBox.off("keyup").keyup(() => {
    const pat = findBox.val()
    if (pat.length) {
      findClear.show()
    } else {
      findClear.hide()
    }
    show()
  })

  findClear.off("click").click(() => {
    findBox.val("")
    show()
  })

  selectAll.off("click").click(() => {
    const endTokens = $("span[te]")
    endTokens.attr("st", "v")
  })

  selectNone.off("click").click(() => {
    const endTokens = $("span[te]")
    endTokens.attr("st", "x")
  })

  const options = {
    root: null,
    rootMargin: "0px",
    threshold: 0.1,
  }

  const entityListening = entries => {
    //let appeared = 0
    //let disappeared = 0
    entries.forEach(entry => {
      const ratio = entry.intersectionRatio
      const entryE = entry.target
      const elem = $(entryE)
      if (ratio > 0) {
        //appeared += 1
        elem.off("click").click(() => {
          const tStart = elem.attr("tstart")
          const tEnd = elem.attr("tend")
          const kind = elem.attr("kind")
          const enm = elem.attr("enm")
          tSelectStart.val(tStart)
          tSelectEnd.val(tEnd)
          activeEntity.val(enm)
          activeKind.val(kind)
          form.submit()
        })
      } else {
        //disappeared += 1
        elem.off("click")
      }
    })
    //console.warn(`Entities: ${appeared} appeared; ${disappeared} disappeared`)
  }

  const observer = new IntersectionObserver(entityListening, options)
  entities.each((i, elem) => {
    observer.observe(elem)
  })
}

const tokenControls = () => {
  const form = $("form")
  const sentences = $("div.s")
  const findBox = $("#sFind")
  const findClear = $("#findClear")
  const findError = $("#sFindError")
  const tSelectStart = $("#tSelectStart")
  const tSelectEnd = $("#tSelectEnd")
  const qWordShow = $("#qWordShow")
  const lookupf = $("#lookupf")
  const lookupq = $("#lookupq")
  const queryClear = $("#queryClear")
  const scope = $("#scope")
  const scopeFiltered = $("#scopeFiltered")
  const scopeAll = $("#scopeAll")
  const tSelectStartVal = tSelectStart.val()
  const tSelectEndVal = tSelectEnd.val()
  const activeEntity = $("#activeEntity")
  const activeKind = $("#activeKind")
  const eKindSelect = $("#eKindSelect")
  const eKindSel = $("button.ekindsel")

  let upToDate = true
  let tSelectRange = []

  const tSelectInit = () => {
    tSelectRange =
      tSelectStartVal && tSelectEndVal
        ? [parseInt(tSelectStartVal), parseInt(tSelectEndVal)]
        : []
    if (tSelectRange.length) {
      if (tSelectRange[0] > tSelectRange[1]) {
        tSelectRange = [tSelectRange[1], tSelectRange[0]]
      }
    }
  }

  const presentQueryControls = update => {
    if (update) {
      qWordShow.html("")
    }
    const hasQuery = tSelectRange.length
    const hasFind = findBox.val().length
    const findErrorStr = findError.html().length

    if (findErrorStr) {
      findError.show()
    } else {
      findError.hide()
    }

    const setQueryControls = onoff => {
      if (onoff) {
        queryClear.show()
      } else {
        queryClear.hide()
      }
    }

    if (hasFind || hasQuery) {
      if (!upToDate) {
        if (hasFind) {
          lookupf.show()
        }
        if (hasQuery) {
          lookupq.show()
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
          for (let t = tSelectRange[0]; t <= tSelectRange[1]; t++) {
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
      setQueryControls(false)
    }
  }

  tSelectInit()
  presentQueryControls(false)

  findBox.off("keyup").keyup(() => {
    const pat = findBox.val()
    upToDate = false
    if (pat.length) {
      findClear.show()
      lookupf.show()
    } else {
      findClear.hide()
      if (tSelectRange.length == 0) {
        lookupf.hide()
      }
    }
  })

  findClear.off("click").click(() => {
    findBox.val("")
  })

  const setScope = val => {
    scope.val(val)
    if (val == "a") {
      scopeAll.addClass("active")
      scopeFiltered.removeClass("active")
    } else {
      scopeFiltered.addClass("active")
      scopeAll.removeClass("active")
    }
  }

  setScope(scope.val())

  scopeFiltered.off("click").click(() => {
    setScope("f")
  })
  scopeAll.off("click").click(() => {
    setScope("a")
  })

  eKindSel.off("click").click(e => {
    const { currentTarget } = e
    const elem = $(currentTarget)
    const currentStatus = elem.attr("st")

    elem.attr("st", currentStatus == "v" ? "x" : "v")
    const ekinds = eKindSel
      .get()
      .filter(x => $(x).attr("st") == "v")
      .map(x => $(x).attr("name"))
      .join(",")
    eKindSelect.val(ekinds)
    form.submit()
  })

  const options = {
    root: null,
    rootMargin: "0px",
    threshold: 0.1,
  }

  const tokenListening = entries => {
    //let appeared = 0
    //let disappeared = 0
    entries.forEach(entry => {
      const ratio = entry.intersectionRatio
      const entryE = entry.target
      const entryElem = $(entryE)
      const tokens = entryElem.find("span[t]")
      const endTokens = entryElem.find("span[te]")

      if (ratio > 0) {
        //appeared += 1
        tokens.off("click").click(e => {
          e.preventDefault()
          const { currentTarget } = e
          const elem = $(currentTarget)
          const tWord = elem.attr("t")
          const tWordInt = parseInt(tWord)
          upToDate = false
          if (tSelectRange.length == 0) {
            tSelectRange = [tWordInt, tWordInt]
          } else if (tSelectRange.length == 2) {
            const start = tSelectRange[0]
            const end = tSelectRange[1]
            if (tWordInt < start - 5 || tWordInt > end + 5) {
              tSelectRange = [tWordInt, tWordInt]
            } else if (tWordInt <= start) {
              tSelectRange = [tWordInt, tSelectRange[1]]
            } else if (tWordInt >= end) {
              tSelectRange = [tSelectRange[0], tWordInt]
            } else if (end - tWordInt <= tWordInt - start) {
              tSelectRange = [tSelectRange[0], tWordInt]
            } else {
              tSelectRange = [tWordInt, tSelectRange[1]]
            }
          }
          tSelectStart.val(`${tSelectRange[0]}`)
          tSelectEnd.val(`${tSelectRange[1]}`)
          activeEntity.val("")

          presentQueryControls(true)
        })
        endTokens.off("click").click(e => {
          e.preventDefault()
          const { currentTarget } = e
          const elem = $(currentTarget)
          const currentValue = elem.attr("st")
          elem.attr("st", currentValue == "v" ? "x" : "v")
        })
      } else {
        //disappeared += 1
        tokens.off("click")
        endTokens.off("click")
      }
    })
    //console.warn(`Sentences: ${appeared} appeared; ${disappeared} disappeared`)
  }

  const observer = new IntersectionObserver(tokenListening, options)
  sentences.each((i, elem) => {
    observer.observe(elem)
  })

  queryClear.off("click").click(() => {
    tSelectRange.length = 0
    tSelectStart.val("")
    tSelectEnd.val("")
    qWordShow.html("")
    activeEntity.val("")
    activeKind.val("")
  })

  const subMitter = $("#submitter")
  form.off("submit").submit(e => {
    const excludedTokens = $("#excludedTokens")
    const endTokens = $(`span[te][st="x"]`)
    const excl = endTokens
      .get()
      .map(elem => $(elem).attr("te"))
      .join(",")
    excludedTokens.val(excl)
    const { originalEvent: { submitter } = {} } = e
    subMitter.val(submitter && submitter.id)
  })
}

const initForm = () => {
  storeForm()
}

/* main
 *
 */

$(window).on("load", () => {
  initForm()
  annoSetControls()
  entityControls()
  tokenControls()
})
