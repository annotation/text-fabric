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
  const appName = formData.get("appname")
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
  const { features } = globalThis
  const findBox = $("#efind")
  const eStat = $("#nentityentries")
  const findClear = $("#entityclear")
  const sortControls = $(`button[tp="sort"]`)
  const sortKeyInput = $("#sortkey")
  const sortDirInput = $("#sortdir")
  const entities = $("p.e")
  const tokenStart = $("#tokenstart")
  const tokenEnd = $("#tokenend")
  const activeEntity = $("#activeentity")
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
      const et = el.find("span")
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

  sortControls.off("click").click(e => {
    const { currentTarget } = e
    const elem = $(currentTarget)
    const sortKey = elem.attr("sk")
    const sortDir = elem.attr("sd")
    sortKeyInput.val(sortKey)
    sortDirInput.val(sortDir == "u" ? "d" : "u")
    form.submit()
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
          const enm = elem.attr("enm")
          tokenStart.val(tStart)
          tokenEnd.val(tEnd)
          activeEntity.val(enm)
          for (const feat of features) {
            const val = elem.find(`span.${feat}`).html()
            $(`#${feat}_active`).val(val)
            $(`#${feat}_select`).val(val)
          }
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
  const { features } = globalThis
  const sentences = $("div.s")
  const findBox = $("#sfind")
  const findClear = $("#findclear")
  const findError = $("#sfinderror")
  const tokenStart = $("#tokenstart")
  const tokenEnd = $("#tokenend")
  const qWordShow = $("#qwordshow")
  const lookupf = $("#lookupf")
  const lookupq = $("#lookupq")
  const queryClear = $("#queryclear")
  const scope = $("#scope")
  const scopeFiltered = $("#scopefiltered")
  const scopeAll = $("#scopeall")
  const tokenStartVal = tokenStart.val()
  const tokenEndVal = tokenEnd.val()
  const activeEntity = $("#activeentity")

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
      setQueryControls(false)
    }
  }

  tokenInit()
  presentQueryControls(false)

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

  for (const feat of features) {
    const sel = $(`button.${feat}_sel`)
    const select = $(`#${feat}_select`)

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
      form.submit()
    })
  }

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
    tokenRange.length = 0
    tokenStart.val("")
    tokenEnd.val("")
    qWordShow.html("")
    activeEntity.val("")
    for (const feat of features) {
      $(`#${feat}_active`).val("")
    }
  })

  const subMitter = $("#submitter")
  form.off("submit").submit(e => {
    const excludedTokens = $("#excludedtokens")
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
})
