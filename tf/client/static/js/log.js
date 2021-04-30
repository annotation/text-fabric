/*eslint-env jquery*/

import { DEBUG } from "./defs.js"

export class LogProvider {
  /* Issues messages to the interface and/or console
   * Not used for debug messages
   */

  deps({ Log }) {
    this.tell = Log.tell
  }

  init() {
    /* warn the developer that DEBU is still true
     */
    this.tell("!!! IS ON !!!")

    this.place = $("#progress")
    this.clearProgress()
    this.placeProgress("Javascript has kicked in.")
  }
  async later() {
    this.placeProgress("Done ...")
    await new Promise(r => setTimeout(r, 1000))
    this.clearProgress()
  }

  clearProgress() {
    /* Clear progress messages in specified location
     * See placeProgress
     */
    this.place.html("")
  }
  placeProgress(msg) {
    /* Draw a progress message on the interface
     * The message is drawn in element box
     */
    this.place.append(`${msg}<br>`)
  }

  progress(msg) {
    /* issue a message to the console
     */
    console.log(msg)
  }

  clearError(ebox, box) {
    /* Clear error formatting in specified locations
     * See placeError
     */
    ebox.html("")
    ebox.hide()
    if (box != null) {
      box.removeClass("error")
    }
  }

  placeError(ebox, msg, box) {
    /* Draw an error on the interface
     * The error is drawn in element ebox,
     * and the element box receives error formatting
     */
    console.error(msg)
    ebox.show()
    ebox.html(msg)
    if (box != null) {
      box.addClass("error")
    }
  }

  error(msg) {
    /* issue a error message to the console
     * Use it for errors that we can recover from
     */
    console.error(msg)
  }

  tell(msg) {
    /* issue a debug message to the console
     * Only if the DEBUG flag is true
     */
    if (DEBUG) {
      console.log("DEBUG", msg)
    }
  }
}

/* INFORMATIONAL MESSAGES
 *
 * Progress and debug messages
 */

