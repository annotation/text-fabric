import {
  DEBUG,
  FLAGSDEFAULT,
  DEFAULTJOB,
  MAXINPUT,
  OBJECT,
  NUMBER,
  STRING,
  BOOL,
} from "./defs.js"

const isObject = value =>
  value != null && typeof value === OBJECT && !Array.isArray(value)

export class StateProvider {
  /* THE STATE
   *
   * The state contains changeable information needed to present the
   * interface.
   * It contains two kinds of information:
   *   - computed search results
   *   - user interaction state (button clicks, field entries)
   *
   * For a description of the state members, see the class definition below.
   *
   * MUTABLE STATE
   *
   * Contrary React-Redux practice, our state is mutable.
   * We do not work with cycles that re-render the display after state changes,
   * so we do not need to detect state changes efficiently.
   * Instead, at each state change, we also update the interface.
   *
   * STATE PROVIDER OBJECT
   *
   * The state logic is encapsulated in a class which is instantiated
   * with one object, whose data represents the state of the app.
   *
   * INITIAL STATE
   *
   * The jobState part of the data is fixed in shape.
   * The State Provider furnish a jobState that has all members and sub members present,
   * filled with default values, none of which are undefined
   * (null is allowed for leaf members)
   *
   * The jobState can be initialized from external, incoming data,
   * use the startj method for that.
   *
   * SAFE MERGE
   *
   * The jobState may come from untrusted sources, such as an imported file
   * of localStorage. Such a jobState may not conform to the shape of the jobState
   * as prescribed here.
   * So the Provider performs a safe merge of the new jobState into a
   * fresh initial jobState.
   * A safe merge copies leaf members of the incoming state into corresponding places
   * in the initial state, provided the path in the incoming state exists in the initial
   * state, and the type of the value in the incoming state is the same as that of
   * the corresponding value in the initial state,
   * and the incoming value is not undefined.
   * If the type of the value is string, the value should be less than MAXINPUT.
   *
   * If any of these conditions are not met, the update of that value is skipped.
   * An error message will be written to the console .
   *
   * GETTING the state
   *
   * Always by the gets() or getj() methods
   *
   * gets is for top level state slices except jobState
   * sets gets the jobState slice as a deep copy (so you cannot modify the jobState)
   *
   * const { query: { [nType]: { [layer]: pattern } } } = State.getj()
   *
   * N.B. We do not have to take care to use default values ( = {} ) for intermediate
   * subobjects, because the members of the jobState are guaranteed to exist.
   *
   * SETTING the state
   *
   * Always by the sets() or setj() methods
   *
   * We get the members of state object back (except jobState).
   * This enables patterns where we set a state member
   * and then use that value in a local variable:
   *
   * const { tpResults } = State.sets({ tpResults: {} })
   *
   * Note that setj() does not return data!
   *
   * When setting the jobState with setj(),
   * we apply the same checks as when we start a job from external data.
   *
   * INVARIANT:
   *
   * The jobState always has the full prescribed shape, with all members present at any
   * level, and with no undefined leaf values
   */

  /* private members
   */

  deps({ Log, Features, Mem, Config }) {
    this.Log = Log
    this.Features = Features
    this.Mem = Mem
    this.Config = Config
    this.tell = Log.tell
  }

  init() {
    /* Make the contents for an initial, valid state, with defaults filled in
     * It can be called when certain elements of the state change.
     */

    this.data = {
      /* for each node type: { nodes, matches }
       * nodes: the set of nodes that match the query
       * - they match all layers of this node type,
       * - when you project the nodes to other node types,
       *   the projected nodes match all layers of those types as well
       * matches: for each layer of this type:
       * - the mapping from nodes to matched character positions
       */
      tpResults: null,

      /* array of results
       * when a composeType is chosen, we generate a table of results from tpResults
       * A result consists of
       * - a node of the focusType: the result node
       * - its ancestor nodes from higher type
       * - all of its descendent nodes in lower types.
       * A result only contains the nodes, not yet actual matched text.
       * In order to render the results table, we need both
       * tpResults and resultsComposed
       */
      resultsComposed: null,

      /* a mapping of nodes to node types,
       * for all nodes that occur in rendered results
       * including non-matching descendants of matching focus nodes
       */
      resultTypeMap: null,

      /* the name of the current job
       * The current search session is called a "job".
       * When we store a jobState in localStorage, we use its name as key.
       * When we store a jobState on file, we use its name as file name.
       */
      jobName: null,

      /* the current state of all user interactions
       * The jobState is what gets serialized when we store / retrieve jobs,
       * whether in localStorage or in files.
       * See for the members the definition of jobState below.
       */
      jobState: this.initjslice(),
    }
  }

  initjslice() {
    /* Make the contents for an initial, valid jobState, with defaults filled in
     * This is the first step in guaranteeing that the jobState has a fixed shape.
     */
    const {
      Config: {
        defaultSettings: {
          autoexec,
          nodeseq,
          exporthl,
          exportsr,
          multihl,
          simple,
        } = {},
        defaultFlags = FLAGSDEFAULT,
        ntypes,
        focusType,
        layers,
        visible,
      },
      Features: {
        features: {
          indices: { can },
        },
      },
    } = this

    /* First set a dumb, superficial value
     */
    const jobState = {
      /* options that affect general aspects of the interface and its operations
       */
      settings: {
        /* whether to offer a simplified interface
         */
        simple,

        /* whether to run search immediately after change or after button press
         */
        autoexec,

        /* whether displayed node numbers start at 1 per node type
         * or are exactly the TF node numbers
         */
        nodeseq,

        /* whether to mark matches in TSV exports
         */
        exporthl,

        /* whether to keep results in single rows in TSV exports
         * even if there are multiple layers per level
         */
        exportsr,

        /* whether to highlight groups with different colours
         * only if the browser supports it
         */
        multihl: can ? multihl : null,
      },

      /* https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions
       */
      /* { pattern, flags, exec } per node type and then per layer
       * - pattern: a regex (regular expression): defines the search
       * - flags: (i m s)
       * - exec: whether it is will be / is executed
       */
      query: {},

      /* whether the results in the state are out of sync with the pattern
       * This becomes true when a user edits the search patterns
       * but has not yet executed the new query
       */
      dirty: false,

      /* per node type whether its layers are expanded.
       * Not expanded means: only the active layers are visible.
       * A layer is active if
       * - it has a non-empty pattern or
       * - its visible flag is set
       */
      expandTypes: {},

      /* the node type used for composing results
       */
      focusType,

      /* per node type and layer whether the layer is visible in the results
       */
      visibleLayers: {},

      /* the current position in the table of results
       * this result is drawn in the middle of the screen if possible
       * The focused result will be marked strongly on the interface.
       * Special values:
       * * -2: query has not been executed
       * * -1: query has been executed and has 0 results
       * *  0: query has been executed, there are results, focus on first result
       */
      focusPos: -2,

      /* the previous focusPos.
       * The result at this position will be marked lightly.
       */
      prevFocusPos: -2,
    }

    /* Now create deeper values, from Config defaults
     */
    const { query, expandTypes, visibleLayers } = jobState

    for (const nType of ntypes) {
      const { [nType]: tpInfo = {} } = layers
      const { [nType]: tpVisible = {} } = visible

      query[nType] = {}
      expandTypes[nType] = false
      visibleLayers[nType] = { _: false }

      for (const layer of Object.keys(tpInfo)) {
        const { [layer]: { pattern = "" } = {} } = tpInfo
        const { [layer]: lrVisible = false } = tpVisible

        query[nType][layer] = {
          pattern: DEBUG ? pattern : "",
          flags: { ...defaultFlags },
          exec: true,
        }
        visibleLayers[nType][layer] = lrVisible
      }
    }
    return jobState
  }

  startjslice(incoming) {
    /* create a starting jobState out of an incoming jobState,
     * which is safely merged into an initial jobState
     */
    const {
      data,
      Features: {
        features: {
          indices: { can },
        },
      },
    } = this

    const { settings = {}, settings: { multihl } = {} } = incoming
    if (multihl === null && can) {
      settings.multihl = true
    } else if (multihl !== null && !can) {
      settings.multihl = null
    }

    const freshJobState = this.initjslice()
    this.merge(freshJobState, incoming, [])
    data.jobState = freshJobState
  }

  /* public members
   */

  gets() {
    /* GET STATE
     *
     * returns a shallow copy of the state, but only with the non jobState
     * members.
     * Note that the caller cannot use this to change the members
     * that are string or number.
     * But he can change the contents of the members that hold an object as value.
     * This is intentional.
     */
    const {
      data: { jobState, ...rest },
    } = this
    return rest
  }

  getjn() {
    /* GET JOB NAME
     * convenience function
     */
    const {
      data: { jobName },
    } = this
    return jobName
  }

  sets(incoming) {
    /* SET STATE
     *
     * update the state by means of an object data containing the updates
     * The structure of the updates reflects the structure of a (part of) the state,
     * only at top-level.
     *
     * If the part jobName or jobState is affected, the jobState is committed to
     * localStorage
     */
    const { Log, Mem, data } = this

    let commit = false

    for (const [inKey, inValue] of Object.entries(incoming)) {
      const stateVal = data[inKey]
      if (stateVal === undefined) {
        Log.error(`state update: unknown key ${inKey}`)
        continue
      }
      data[inKey] = inValue
      if (inKey == "jobName" || inKey == "jobState") {
        commit = true
      }
    }
    if (commit) {
      const { jobName, jobState } = data
      Mem.setkl(jobName, jobState)
    }
    return this.gets()
  }

  startj(jobIn, jobStateIn) {
    /* INIT JOB STATE
     *
     * updates the state for a new, named job with incoming data
     * The jobState is committed to Mem
     */
    const { Mem, data } = this
    const jobName = jobIn || DEFAULTJOB

    data.jobName = jobName
    this.startjslice(jobStateIn)
    const { jobState } = data
    Mem.setkl(jobName, jobState)
  }

  getj() {
    /* GET JOB STATE
     *
     * returns the jobState
     * The caller should not modify the jobState, so we return a deep copy of it
     */
    const {
      data: { jobState },
    } = this
    return JSON.parse(JSON.stringify(jobState))
  }

  setj(incoming) {
    /* SET JOB STATE
     *
     * Performs a safe update of the jobState by incoming data
     * The jobState is committed to Mem
     */
    const {
      Mem,
      data: { jobName, jobState },
    } = this
    this.merge(jobState, incoming, [])
    Mem.setkl(jobName, jobState)
  }

  /* auxiliary functions for state operations
   */

  merge(orig, incoming, path) {
    /* Merge an incoming object safely into an original object.
     * The shape of orig will not be altered
     *  1. no new keys will be introduced at any level
     *  2. no value becomes undefined
     *  3. no value changes type
     *  4. no value becomes too long
     *
     * For all violations, an error message is sent to the console .
     *
     * Invariant: orig is an object, not a leaf value
     */

    const { Log } = this
    const pRep = `Merge: incoming at path "${path.join(".")}": `

    if (incoming === undefined) {
      Log.error(`${pRep}undefined`)
      return
    }
    if (!isObject(incoming)) {
      Log.error(`${pRep}non-object`)
      return
    }
    for (const [inKey, inVal] of Object.entries(incoming)) {
      const origVal = orig[inKey]
      if (origVal === undefined) {
        Log.error(`${pRep}unknown key ${inKey}`)
        continue
      }
      if (inVal === undefined) {
        Log.error(`${pRep}undefined value for ${inKey}`)
        continue
      }
      const oTp = typeof origVal
      const inTp = typeof inVal
      if (origVal === null || oTp === NUMBER || oTp === STRING || oTp === BOOL) {
        if (isObject(inVal)) {
          const repVal = JSON.stringify(inVal)
          Log.error(`${pRep}object ${repVal} for ${inKey} instead of leaf value`)
          continue
        }
        if (inVal !== null && origVal !== null && inTp != oTp) {
          Log.error(`${pRep}type conflict ${inTp}, expected ${oTp} for ${inKey}`)
          continue
        }
        if (inTp === STRING && inVal.length > MAXINPUT) {
          const eRep = `${inVal.length} (${inVal.substr(0, 20)} ...)`
          Log.error(`${pRep}maximum length exceeded for ${inKey}: ${eRep}`)
          continue
        }

        /* all is well, we replace the value in orig by the incoming value
         */
        orig[inKey] = inVal
        continue
      }
      if (!isObject(inVal)) {
        Log.error(`${pRep}unknown type ${inTp} for ${inKey}=${inVal} instead of object`)
        continue
      }
      if (isObject(origVal)) {
        if (!isObject(inVal)) {
          Log.error(`${pRep}leaf value ${inVal} for ${inKey} instead of object`)
          continue
        }
        this.merge(origVal, inVal, [...path, inKey])
      }
    }
  }
}
