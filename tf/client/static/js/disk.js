export class DiskProvider {
  /* FILE MANAGEMENT
   *
   * We cannot read from files and write to files directly from a browser script.
   *
   * When we want to read, we ask the user to point to a file,
   * and we "upload" that file
   * When we want to write, we offer a download to the user.
   */

  deps({ Log }) {
    this.tell = Log.tell
  }


  upload(elem, handler) {
    /* Reads the content of a file
     * Elem should be an <input type="file"> element
     * for which the user has selected a file already
     * After reading, handler is called
     * It should take fileName, extension and content as arguments
     * and so something business-logical with it
     */
    const { files } = elem
    if (files.length == 0) {
      alert("No file selected")
    } else {
      for (const file of files) {
        const reader = new FileReader()
        const [fileName, ext] = file.name.match(/([^/]+)(\.[^.]*$)/).slice(1)
        reader.onload = e => {
          handler(fileName, ext, e.target.result)
        }
        reader.readAsText(file)
      }
    }
  }

  download(text, fileName, ext, asUtf16) {
    /* collect data into a file for download
     * A downlaod will be prepared, with a given file name and extension.
     * The data is encoded as text in UTF-8 or in UTF-16
     */
    let blob

    if (asUtf16) {
      /* it turns out we need this clumsy detour via byte arrays
       * because otherwise the BOM mark will not be written correctly
       */
      const byteArray = []

      /* BOM Mark
       */
      byteArray.push(255, 254)

      /* Low level way to translate each uniocode character into 16 bits
       */
      for (let i = 0; i < text.length; ++i) {
        const charCode = text.charCodeAt(i)
        byteArray.push(charCode & 0xff)
        byteArray.push((charCode / 256) >>> 0)
      }

      blob = new Blob(
        [new Uint8Array(byteArray)], { type: "text/plain;charset=UTF-16LE;" }
      )
    } else {
      blob = new Blob([text], { type: "text/plain;charset=UTF-8;" })
    }
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.setAttribute("href", url)
    link.setAttribute("download", `${fileName}.${ext}`)
    link.style.visibility = "hidden"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

