/*eslint-env jquery*/

/* --- INTRO ----------------------------------------------
 *
 * This is a Web App that implements Layered Search in a Corpus.
 * The app is a single page app (SPA), meant to work with a static HTML file,
 * not served by a web server, not even by localhost,
 * although both should be possible.
 *
 * Author:
 *
 * Dirk Roorda (https://pure.knaw.nl/portal/en/persons/dirk-roorda)
 * Organization: KNAW/HuC - Digital Infrastructure (https://di.huc.knaw.nl)
 * License: MIT (https://mit-license.org)
 *
 * Acknowledgments:
 *
 * The first development of this concept was inspired by
 * Cody Kingham (https://www.linkedin.com/in/cody-kingham-1135018a)
 * and funded by
 * Geoffrey Khan (https://www.ames.cam.ac.uk/people/professor-geoffrey-khan)
 * when we were applying it to the
 * NENA corpus (https://nena.ames.cam.ac.uk/)
 *
 * The data for this interface is generated from the Text-Fabric data version
 * of a corpus.
 *
 */

/* --- OVERVIEW ----------------------------------------------
 *
 * The code consists of 10 classes, divided into 3 groups.
 *
 * N.B: I would have liked to separate the classes into files and then
 * use the import mechanism to include them.
 * However, that will work only when the app is served by a server (web or localhost),
 * but not when it is a local file, opened in the browser.
 * See:
 *
 * The 10 classes define Service Providers.
 * They will each be instantiated by single object the Provider.
 *
 * We list them in the order that they are defined in the code.
 *
 * Functional   Business logic
 * ---------------------------
 * Config       Manages incoming config data of the corpus
 * Corpus       Manages incoming bulk data of the corpus
 * Search       Implements the search algorithm
 *
 * Application  Generic logic of a typical web app
 * ----------------------------------------------
 * State        Single source of truth about computations and user interactions
 * Job          Task units that can be saved and loaded, imported and exported
 * Gui          The graphical user interface
 *
 * Systems      Low level technical provisions
 * -------------------------------------------
 * Disk         Uploading and donwloading files
 * Mem          Storing data in Local Storage
 * Log          Feedback to the user
 *
 * Top-level    Making it work
 * ---------------------------
 * App          Orchestrates the service providers
 */

/* --- PATTERNS ----------------------------------------------
 *
 * The service providers (except top-level App) share a common pattern:
 * they start life like this:
 *
 *    constructor() do nothing
 *    deps()        create a links to all other providers that this provider needs
 *    init()        actions that can be done quickly and immediately
 *    later()       actions that can be done once all data has been loaded
 *
 * The rest is business logic and auxilary functions
 *
 * The GuiProvider has the following pattern
 *
 *    init()        build: generate HTML,
 *                  activate: furnish buttons and text inputs with event listeners
 *    apply()       when the state has changed, update the interface to reflect
 *                  the latest changes
 *
 * Importantly, apply-like functions may not be executed during "init" time,
 * only at "later" time.
 */

/* --- CORPUS DATA ----------------------------------------------
 *
 * The fixed data is in the global vars corpusxxx and configData.
 *
 * Both kinds of data will be wrapped into Provider objects: Config and Corpus
 * after which the global vars should not be accessed, not even for reading.
 * We cannot really enforce this, though.
 *
 * Config is for the small configuration data.
 *
 * Corpus contains the big textual and positional data.
 */

/* --- BUSINESS LOGIC ----------------------------------------------
 *
 * In this app, the logic is: layered search.
 *
 * See:
 * (https://annotation.github.io/text-fabric/tf/about/clientmanual.html)
 *
 */

import { SearchProvider } from "./search.js"
import { ConfigProvider } from "./config.js"
import { CorpusProvider } from "./corpus.js"
import { StateProvider } from "./state.js"
import { JobProvider } from "./job.js"
import { GuiProvider } from "./gui.js"
import { MemProvider } from "./mem.js"
import { DiskProvider } from "./disk.js"
import { LogProvider } from "./log.js"
import { FeatureProvider } from "./feature.js"

class AppProvider {
/* TOP LEVEL ORCHESTRATION
 *
 * We take care to use an async function for the longish
 * initialization, so that we can display progress messages
 * in the mean time
 *
 * Feature testing
 * We test some features for support in the current browser, and register the outcome
 * for further use in the app.
 *
 * Document loading:
 * we take care that the user sees as much of the interface as early as possible.
 * We specify all scripts in the header of the document, but with the defer
 * attribute, so that the scripts load asynchronously
 * and are executed in the given order:
 *
 * configdata.js
 *  - information on the basis of which this app builds the interface
 *  - small file
 * layered.js
 *  - the app itself (this very script that you are reading now)
 * corpusdata.js
 *  - texts and mappings from nodes to textual positions
 *  - a big file, multi-megabyte
 *
 * When the document is ready, and the app has been loaded, the app will execute
 * initInterface() which builds the interface.
 *
 * In the meanwhile, corpusdata is still being fetched, while the interface is
 * probably already rendered.
 * When corpusdata is in, the app will execute initCorpus().
 *
 * Then the app continues by fetching the most recent known job, if any,
 * and executes its query
 *
 * Only then the app is ready to use, and the progress / waiting markers disappear.
 */

  constructor() {
    /* create all Provider objects
     */
    this.providers = {
      Log: new LogProvider(),
      Features: new FeatureProvider(),
      Disk: new DiskProvider(),
      Mem: new MemProvider(),

      State: new StateProvider(),
      Job: new JobProvider(),
      Gui: new GuiProvider(),

      Config: new ConfigProvider(),
      Corpus: new CorpusProvider(),
      Search: new SearchProvider(),
    }

    /* The initialization order
     *
     * We specify the order in which the Providers must execute their
     * init() and later() methods
    */

    this.order = {
      init: ["Log", "Features", "Config", "Mem", "State", "Job", "Gui"],
      later: ["Corpus", "Job", "Log"],
    }
    this.deps()
    this.test()
  }

  deps() {
    /* let Provider objects register their dependencies on other Provider objects
     */

    const { providers, providers: { Log } } = this
    for (const Provider of Object.values(providers)) {
      Provider.deps(providers)
    }
    this.tell = Log.tell
  }
  test() {
    const { providers: { Features } } = this
    Features.init()
    Features.test()
  }

  init() {
    /* make all Provider objects ready,
     * except the ones that take time to load
     * (see later()
     */
    const { providers, order: { init } } = this

    for (const name of init) {
      providers[name].init()
    }
  }

  async later() {
    /* continue work after the corpus data is in
     */
    const { providers, order: { later } } = this

    for (const name of later) {
      await providers[name].later()
    }
  }
}

/* MAIN PROGRAM
 */

const App = new AppProvider()

$(document).on("DOMContentLoaded", () => {
  /* DOM is loaded, not all data has arrived
   */
  App.init()
})

$(window).on("load", () => {
  /* All data has arrived
   */
  App.later()
})
