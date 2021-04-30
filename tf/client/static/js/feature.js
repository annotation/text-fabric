/*eslint-env jquery*/

/* --- FEATURES ---
 *
 * Here is a list of features to be tested: i.e. does the browser support the feature?
 *
 * Every feature is a separate object with
 *
 * - metadata: description, known support, etc
 * - data: test data
 * - use(): a function that uses the feature on the test data
 * - fallback(): a function that implements a workaround or graceful degradation
 * - can: a boolean that reports whether the use() function ran without issue
 * - error: any error that occurred when running the use function
 *
 * The use() and fallback() functions should return some html that can be used
 * in a report.
 */

const indices = {
  /* whether RegExp supports the "d" flag and match results have the
   * "indices" attribute
   * See
   * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/exec
   */
  capability: `highlight submatches with different colors`,
  missing: `only highlight the complete matches with one color`,
  support: `
✅ Chrome >=90<br>
✅ Firefox >=90<br>
✅ Wondows: Edge >=88<br>
❎ MacOS: Safari >14.2 upcoming <br>
❎ i(Pad)OS: all browsers >14.5 upcoming<br>
`,

  data: {
    text: "abc123-----def456",
    pattern: "[a-z]([a-z])[a-z][0-9]([0-9])[0-9]",
    flag: "d",
  },

  use() {
    const { data: { text, pattern, flag } } = this
    const re = new RegExp(pattern, `g${flag}`)

    const highlights = new Map()
    let result

    while ((result = re.exec(text)) !== null) {
      const { indices } = result
      for (let g = 0; g < result.length; g++) {
        const b = indices[g][0]
        const e = indices[g][1]
        for (let h = b; h < e; h++) {
          highlights.set(h, g)
        }
      }
    }

    return `<p>${this.getHlText(text, highlights)}</p>`
  },

  fallback() {
    const { data: { text, pattern } } = this
    const re = new RegExp(pattern, `g`)

    const highlights = new Map()
    const results = text.matchAll(re)
    const g = 0

    for (const match of results) {
      const hit = match[0]
      const b = match.index
      const e = b + hit.length
      for (let h = b; h < e; h++) {
        highlights.set(h, g)
      }
    }
    return `<p>${this.getHlText(text, highlights)}</p>`
  },

  getHlText(text, highlights) {
    /* auxiliary function to apply highlights to a text
     *
     * The highlights are given as a mapping from character positions to
     * highlight groups.
     *
     * First the text is converted to a series of spans with the same
     * highlight, then the spans are serialized into html.
     */
    const spans = []
    let curG = -2

    for (let i = 0; i < text.length; i++) {
      const ch = text[i]
      const g = highlights.get(i) ?? -1
      if (curG != g) {
        const newSpan = [g, ch]
        spans.push(newSpan)
        curG = g
      } else {
        spans[spans.length - 1][1] += ch
      }
    }
    const html = []
    for (const [g, m] of spans) {
      const gRep = (g >= 0) ? ` class="hl${g}"` : ""
      html.push(`<span${gRep}>${m}</span>`)
    }
    return html.join("")
  },

  can: null,
  error: null,

}

export class FeatureProvider {
/* BROWSER SUPPORT FOR CERTAIN FEATURES
 *
 * Tests for the features specified above.
 */

  constructor(reporting) {
    /* incorporates the features specified above.
     *
     * The reporting parameter indicates whether a report
     * of the test should be generated.
     *
     * If you call this class from a test page, you can set it to true.
     * But if you use it for a quick feature test inside an app,
     * call it with false, or leave it out.
     */
    this.reporting = reporting
    this.features = { indices }
    this.keyDetails = ["capability", "missing", "support", "miss"]
  }

  deps({ Log }) {
    this.tell = Log.tell
  }

  init() {
    /* display characteristics of the current browser
     */
    const { reporting } = this
    if (reporting) {
      const browserDest = $(`#browser`)
      browserDest.html(`
      <dl>
        <dt>Browser</dt><dd>${navigator.userAgent}</dd>
        <dt>Platform</dt><dd>${navigator.platform}</dd>
      </dl>
      `)
    }
  }

  test() {
    /* test all known features in this browser
     * For each feature the use() function is tried.
     * The fallback() function is also carried out (if reporting).
     * The can and error attributes of the feature object will be set.
     *
     * An app can read off the support of this browser for these features
     * from the can attributes.
     */
    const { features, reporting } = this

    let useResult = []
    let fallbackResult = []

    for (const [name, feature] of Object.entries(features)) {
      try {
        useResult = feature.use()
        feature.can = true
      }
      catch (error) {
        feature.error = error
        feature.can = false
      }
      if (reporting) {
        fallbackResult = feature.fallback()
        this.report(name, useResult, fallbackResult)
      }
    }
    if (reporting) {
      $(`#tests`).append("<hr>")
    }
    this.tell(features)
  }

  report(name, useResult, fallbackResult) {
    /* create a report for a feature identified by name
     * The feature must have been tested, and the
     * outputs of its use() and fallback() functions are
     * passed as arguments.
     */

    const { features: { [name]: details }, keyDetails } = this
    const { can, error } = details
    const testDest = $(`#tests`)

    const html = []
    const canRep = can ? "✅" : "❌"
    html.push(`<hr><h2>${canRep} ${name}</h2><dl>`)
    for (const dt of keyDetails) {
      const { [dt]: dd } = details
      html.push(`<dt>${dt}</dt><dd>${dd}</dd>`)
    }
    html.push("</dl>")

    if (can) {
      html.push(`<h4>Desired output:</h4>`)
      html.push(useResult)
    }
    else {
      html.push(`<h4>Error message:</h4>`)
      html.push(`<div class="error">${error}</div>`)
    }
    html.push(`<h4>Fallback output${can ? " (not needed)" : ""}:</h4>`)
    html.push(fallbackResult)
    testDest.append(html.join(""))
  }
}
