/* global corpusData */

export class CorpusProvider {
  /* THE CORPUS
   *
   * Readonly data: texts, iPositions, the parent relation "up".
   */

  deps({ Log, Config }) {
    this.Config = Config
    this.Log = Log
    this.tell = Log.tell
  }

  async later() {
    /* try to encapsulate all access to the data inside this class
     */

    const { links, texts, posinfo } = corpusData

    /* links from section nodes to the inline corpus
     */
    this.links = links

    /* full text for a layer; per type and then per layer
     */
    this.texts = texts

    /* mapping of textual positions to nodes per layer or the inverse
     *
     * It depends on the memSavingMethod:
     *
     * if it is 0, we get positions (mapping of textual positions to nodes)
     * if it is 1, we get iPositions (mapping of nodes to textual positions)
     */
    this.posinfo = posinfo

    await this.warmUpData()

    /* Now we have more data in this object:
     *
     * - up: mapping from a node to its parent one level higher
     * - down: mapping from a node to its children one level lower
     * - positions: mapping from character positions to nodes;
     *   per type and then per layer
     */
  }

  async warmUpData() {
    /* Expand parts of the data that have been optimised before shipping
     */
    const { Log } = this

    Log.progress(`Decompress up-relation and infer down-relation`)
    this.decompress()
    await Log.placeProgress(`Compute positions for all layers`)
    await this.positionMaps()
    Log.progress(`Done`)
  }

  decompress() {
    /* The mapping "up" is expanded. We also compute its converse, "down".
     */
    const { up } = corpusData

    const newUp = new Map()
    const down = new Map()

    for (const line of up) {
      const [spec, uStr] = line.split("\t")
      const u = uStr >> 0
      if (!down.has(u)) {
        down.set(u, new Set())
      }

      const ns = []
      const ranges = spec.split(",")

      for (const range of ranges) {
        const bounds = range.split("-").map(x => x >> 0)
        if (bounds.length == 1) {
          ns.push(bounds[0])
        } else {
          for (let i = bounds[0]; i <= bounds[1]; i++) {
            ns.push(i)
          }
        }
      }
      const downs = down.get(u)
      for (const n of ns) {
        newUp.set(n, u)
        downs.add(n)
      }
    }
    this.up = newUp
    this.down = down
  }

  async positionMaps() {
    /* The data from the corpus contains
     * node-to-position mappings for all relevant nodes.
     * We make the inverses of these mappings here.
     *
     * Assumption:
     * we assume, that, within a layer, every text positions corresponds
     * to at most one node
     * (we do not support overlapping nodes of the same type)
     */

    const {
      Log,
      Config: { memSavingMethod },
      posinfo,
    } = this

    if (memSavingMethod == 0) {
      this.positions = posinfo
      const iPositions = {}

      for (const [nType, tpInfo] of Object.entries(posinfo)) {
        for (const [layer, pos] of Object.entries(tpInfo)) {
          await Log.placeProgress(`mapping ${nType}-${layer}`)

          const iPos = new Map()

          for (let i = 0; i < pos.length; i++) {
            const node = pos[i]
            if (node == null) {
              continue
            }
            if (!iPos.has(node)) {
              iPos.set(node, [])
            }
            iPos.get(node).push(i)
          }

          if (iPositions[nType] == null) {
            iPositions[nType] = {}
          }
          iPositions[nType][layer] = iPos
        }
      }

      this.iPositions = iPositions
    }
    else if (memSavingMethod == 1) {
      this.iPositions = posinfo
      const positions = {}

      for (const [nType, tpInfo] of Object.entries(posinfo)) {
        for (const [layer, iPos] of Object.entries(tpInfo)) {
          await Log.placeProgress(`mapping ${nType}-${layer}`)

          const afterLastPos = iPos[iPos.length - 1]
          /* this is 1 more than the last textual position.
           * Hence it is the length of the text of the layer
           */
          const offset = iPos[0]
          /* this is one less than the first node whose position
           * is recorded in in iPos
           */
          const buffer = new ArrayBuffer(32 * afterLastPos)
          const pos = new Uint32Array(buffer)
          for (let i = 1; i < iPos.length - 1; i++) {
            const node = offset + i
            const start = iPos[i]
            const end = iPos[i + 1]
            for (let t = start; t < end; t++) {
              pos[t] = node
            }
          }
          if (positions[nType] == null) {
            positions[nType] = {}
          }
          positions[nType][layer] = pos
        }
      }
      this.positions = positions
    }
  }
}
