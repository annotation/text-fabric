/* global configData */

export class ConfigProvider {
/* CONFIG
 *
 * Readonly data: defaults, settings, descriptions.
 */

  deps({ Log }) {
    this.tell = Log.tell
  }

  init() {
    /* try to encapsulate all access to the data inside this class
     */

    const {
      mainConfig,
      defs: { lsVersion, org, repo, dataset, client, description, urls },
      levels,
      focusType, simpleBase,
      ntypes, ntypesinit, ntypessize,
      utypeOf, dtypeOf,
      layers, visible,
      defaultSettings,
      defaultFlags,
      keyboard,
      memSavingMethod,
    } = configData

    /* the version stamp of this app
     */
    this.lsVersion = lsVersion

    /* how big data is handled in memory
     */
    this.memSavingMethod = memSavingMethod

    /* the Github organization of the app
     */
    this.org = org

    /* the Github repo of the app
     */
    this.repo = repo

    /* the dataset name of the app
     */
    this.dataset = dataset

    /* the client name of the app
     */
    this.client = client

    /* main config settings of the app
     */
    this.mainConfig = mainConfig

    /* default settings of the app
     */
    this.defaultSettings = defaultSettings

    /* default flags of the query patterns
     */
    this.defaultFlags = defaultFlags

    /* keyboard symbols
    */
    this.keyboard = keyboard

    /* the description of the configData
     */
    this.description = description

    /* per node type (level): the description of that level
     */
    this.levels = levels

    /* several kinds of urls: for corpus, maker, tf, source, package
     * For each kind, there is a pair consisting of the href and the title of the url
     */
    this.urls = urls

    /* the base type of the configData, e.g. word or letter
     */
    this.simpleBase = simpleBase

    /* info about layers:
     * per node type and then per layer:
     * - valueMap: mapping from acronyms to full values: => legend (optional)
     * - pos: the name of the key where the positions for this layer can be found
     *   in the corpusData (some layers share positions for efficiency)
     * - pattern: an example pattern (only used in debug mode)
     * - description: a description of the layer
     */
    this.layers = layers

    /* visibility of layers, per node type and then per layer
     */
    this.visible = visible

    /* ordered list of types in the data, from lowest to highest
     */
    this.ntypes = ntypes

    /* where each node types start: the first Text-Fabric node number of that type
     */
    this.ntypesinit = ntypesinit

    /* the amount of nodes in each node type
     */
    this.ntypessize = ntypessize

    /* mapping from type to one-higher type
     */
    this.utypeOf = utypeOf

    /* mapping from type to one-lower type
     */
    this.dtypeOf = dtypeOf

    /* computed attributes for convenience
     */

    /* the default focus type
     * if it is missing, we fill in a middle type
     */
    const pos = Math.round(ntypes.length / 2)
    this.focusType = focusType || ntypes[pos]

    /* array of types in reversed order
     */
    this.ntypesR = [...ntypes]
    this.ntypesR.reverse()

    /* mapping of types to their index in the array of types
     */
    const ntypesI = new Map()
    for (let i = 0; i < ntypes.length; i++) {
      ntypesI.set(ntypes[i], i)
    }
    this.ntypesI = ntypesI
  }
}
