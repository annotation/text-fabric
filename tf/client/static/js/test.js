/*eslint-env jquery*/

import { LogProvider } from "./log.js"

import { FeatureProvider } from "./feature.js"

const Tester = new FeatureProvider(true)

$(document).on("DOMContentLoaded", () => {
  /* DOM is loaded, not all data has arrived
   */
  const Log = new LogProvider()

  Tester.init()
  Tester.deps({ Log })
  Tester.test()
})
