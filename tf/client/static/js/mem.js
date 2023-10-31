import { DEFAULTJOB } from "./defs.js"

export class MemProvider {
/* LOCAL STORAGE MANAGEMENT
 *
 * When we store / retrieve keys in localStorage,
 * we always prepend a prefix to the key:
 * - a fixed part, marking that it is a layered search app
 * - a Config dependent part: the org and repo of the data
 *
 * We also store the last key used.
 * All content goes through JSON.stringify upon storing
 * and through JSON.parse upon retrieving.
 *
 * When retrieving content for non-existing keys, we silently return the empty object.
 *
 * localStorage for file:// URLs is not clearly defined.
 * If several apps like this are being used in the same browser,
 * this practice will prevent collisions
 */

  /* private members
   */

  deps({ Log, Config }) {
    this.Config = Config
    this.tell = Log.tell
  }

  init() {
    const { Config: { org, repo, client } } = this
    this.appPrefix = `tf.client/${org}/${repo}/${client}/`
    this.keyLast = `${this.appPrefix}LastJob`
    this.keyPrefix = `${this.appPrefix}Keys/`
    this.keyLength = this.keyPrefix.length
  }

  getRawKey(userKey) {return `${this.keyPrefix}${userKey}`}
  getUserKey(rawKey) {return rawKey.substring(this.keyLength)}
  getLastKey() {return localStorage.getItem(this.keyLast)}

  /* public members
   */

  getk(userKey) {
    /* retrieve stored content for a key
     *
     * Also store the key as last used key
     */
    localStorage.setItem(this.keyLast, userKey)
    const rawKey = this.getRawKey(userKey)
    return JSON.parse(localStorage.getItem(rawKey) ?? "{}")
  }

  setk(userKey, content) {
    /* stored content behind a key
     */
    const rawKey = this.getRawKey(userKey)
    localStorage.setItem(rawKey, JSON.stringify(content))
  }

  remk(userKey) {
    /* delete key and its stored content
     * If the key happens to be the last key,
     * remove the last key
     * return the last available key if any, else the default key
     */
    const rawKey = this.getRawKey(userKey)
    localStorage.removeItem(rawKey)
    const lastKey = this.getLastKey()
    if (userKey == lastKey) {
      localStorage.removeItem(this.keyLast)
    }
    const allKeys = this.keys()
    return (allKeys.length == 0) ? DEFAULTJOB : allKeys[allKeys.length - 1]
  }

  getkl() {
    /* retrieve stored content for the last key
     *
     * If there is no last key, take the last key
     * of all available keys, if any
     * and store that key as last key
     *
     * return both the key and the content
     */
    let lastKey = localStorage.getItem(this.keyLast)
    let content

    if (lastKey == null) {
      const allKeys = this.keys()
      if (allKeys.length == 0) {
        lastKey = DEFAULTJOB
        content = {}
        localStorage.setItem(this.keyLast, lastKey)
      }
      else {
        lastKey = allKeys[allKeys.length - 1]
        content = this.getk(lastKey)
      }
    }
    else {
      content = this.getk(lastKey)
    }
    return [lastKey, content]
  }

  setkl(userKey, content) {
    /* store content behind a key and make it the last key
     */
    this.setk(userKey, content)
    localStorage.setItem(this.keyLast, userKey)
  }

  keys() {
    /* get the ordered array of all stored keys
     */
    const rawKeys = Object.keys(localStorage)
      .filter(rawKey => rawKey.startsWith(this.keyPrefix))
      .map(rawKey => this.getUserKey(rawKey))
    rawKeys.sort()
    return rawKeys
  }
}

