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
  const rannoseth = $("#rannoseth")
  const dannoseth = $("#dannoseth")

  const aNew = $("#anew")
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

const tokenControls = () => {
  const tokens = $("span[t]")
  const tSelectStart = $("#tSelectStart")
  const tSelectEnd = $("#tSelectEnd")
  const qWordShow = $("#qWordShow")
  const queryFilter = $("#queryFilter")
  const queryClear = $("#queryClear")
  const tSelectStartVal = tSelectStart.val()
  const tSelectEndVal = tSelectEnd.val()
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
    if (tSelectRange.length) {
      queryFilter.show()
      queryClear.show()
      if (update) {
        for (let t = tSelectRange[0]; t <= tSelectRange[1]; t++) {
          const elem = $(`span[t="${t}"]`)
          elem.addClass("queried")
          const qWord = elem.html()
          qWordShow.append(`<span>${qWord}</span> `)
        }
      }
    } else {
      queryFilter.hide()
      queryClear.hide()
    }
  }

  tSelectInit()
  presentQueryControls(false)

  tokens.off("click").click(e => {
    e.preventDefault()
    const { currentTarget } = e
    const elem = $(currentTarget)
    const tWord = elem.attr("t")
    const tWordInt = parseInt(tWord)
    if (tSelectRange.length == 0) {
      tSelectRange = [tWordInt, tWordInt]
    }
    else if (tSelectRange.length == 2) {
      const start = tSelectRange[0]
      const end = tSelectRange[1]
      if (tWordInt < start - 5 || tWordInt > end + 5) {
        tSelectRange = [tWordInt, tWordInt]
      }
      else if (tWordInt <= start) {
        tSelectRange = [tWordInt, tSelectRange[1]]
      }
      else if (tWordInt >= end) {
        tSelectRange = [tSelectRange[0], tWordInt]
      }
      else if (end - tWordInt <= tWordInt - start) {
        tSelectRange = [tSelectRange[0], tWordInt]
      }
      else {
        tSelectRange = [tWordInt, tSelectRange[1]]
      }
    }
    tSelectStart.val(`${tSelectRange[0]}`)
    tSelectEnd.val(`${tSelectRange[1]}`)

    presentQueryControls(true)
  })

  queryClear.off("click").click(() => {
    tSelectRange.length = 0
    tSelectStart.val("")
    tSelectEnd.val("")
    qWordShow.html("")
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
  tokenControls()
})
