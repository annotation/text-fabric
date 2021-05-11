export class JobProvider {
/* JOB CONTROL
 *
 * Jobs correspond to search sessions. The current job lives in the state,
 * as a member called "jobState".
 *
 * The user can make new jobs, duplicate them, rename them, kill them, switch
 * between them, save them as file, load them from file.
 *
 * All jobs that the apps loads, will be saved in localStorage.
 * Each action that changes the jobState, triggers a save action into
 * localStorage.
 */

/* Starting
 *
 * When we start up we look in localStorage for the last job.
 * If we find that, we load its data into the jobState part of the state.
 *
 * If not, we derive an initial jobState from State, and load that
 * into the state
 */

  deps({ Log, Disk, Mem, State, Gui }) {
    this.Disk = Disk
    this.Mem = Mem
    this.State = State
    this.Gui = Gui
    this.tell = Log.tell
  }

  init() {
    /* Lookup last job from local storage, if any,
     * or else use init settings from State
     */
    const { Mem, State } = this

    const [jobName, jobContent] = Mem.getkl()
    State.startj(jobName, jobContent)
  }

  async later() {
    const { Gui } = this
    Gui.apply(true)
    Gui.activateLayers()
  }

  /* job actions as defined by controls on the interface
   *
   * All these actions have to take care of
   *
   * - updating the state
   * - applying the new state to the interface
   * - storing the new state in local storage
   */

  list() {
    /* list of all remembered jobs
     */
    const { Mem } = this
    return Mem.keys()
  }

  make(newJob) {
    /* make a fresh job
     */
    const { State, Gui } = this
    const { jobName } = State.gets()

    if (jobName == newJob) {
      return
    }
    State.startj(newJob, {})
    Gui.apply(true)
  }

  copy(newJob) {
    /* copy current job to a new name
     */
    const { State, Gui } = this
    const { jobName } = State.gets()

    if (jobName == newJob) {
      return
    }
    State.sets({ jobName: newJob })
    Gui.apply(false)
  }

  rename(newJob) {
    /* rename current job
     */
    const { Mem, State, Gui } = this
    const { jobName } = State.gets()

    if (jobName == newJob) {
      return
    }
    Mem.remk(jobName)
    State.sets({ jobName: newJob })
    Gui.apply(false)
  }

  kill() {
    /* kill (=delete) current job
     * But only if there is still a job left,
     * otherwise rename to the default name
     */
    const { Mem, State } = this
    const { jobName } = State.gets()

    const newJob = Mem.remk(jobName)
    this.change(newJob)
  }

  change(jobName) {
    /* switch to selected job
     */
    const { Mem, State, Gui } = this

    const jobContent = Mem.getk(jobName)
    State.startj(jobName, jobContent)
    Gui.apply(true)
  }

  read(elem) {
    /* produce a handler for reading an uploaded file
     */
    const { Disk, State, Gui } = this

    const handler = (fileName, ext, content) => {
      if (ext != ".json") {
        alert(`${fileName}${ext} is not a JSON file`)
        return
      }
      const jobContent = JSON.parse(content)
      State.startj(fileName, jobContent)
      Gui.apply(true)
      Gui.applyJobOptions()
    }
    Disk.upload(elem, handler)
  }

  write() {
    /* save current job state to file
     * The file will be offered to the user as a download
     */
    const { State, Disk } = this

    const { jobName } = State.gets()
    const jobState = State.getj()

    const text = JSON.stringify(jobState)
    Disk.download(text, jobName, "json", false)
  }
}

