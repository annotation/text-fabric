/*eslint-env jquery*/

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

const initForm = () => {
    storeForm()
}

/* main
 *
 */

$(window).on("load", () => {
  initForm()
})
