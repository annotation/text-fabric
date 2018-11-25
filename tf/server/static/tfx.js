function switchMode(m) {
  var mode = $('#mode')
  var pageNav = $('#navigation')
  var pages = $('#pages')
  var passages = $('#passages')
  var sectionsTable = $('#sectionsTable')
  var tuplesTable = $('#tuplesTable')
  var queryTable = $('#queryTable')
  var passageTable = $('#passageTable')

  mode.val(m)
  if (m == 'passage') {
    pageNav.hide()
    pages.hide()
    passages.show()
    sectionsTable.hide()
    tuplesTable.hide()
    queryTable.hide()
    passageTable.show()
  }
  else if (m == 'results') {
    pageNav.show()
    pages.show()
    passages.hide()
    sectionsTable.show()
    tuplesTable.show()
    queryTable.show()
    passageTable.hide()
  }
}

function modes() {
  var mode = $('#mode')
  var m = mode.val()
  var passageTable = $('#passageTable')

  $('#moderesults').click(function(e) {
    e.preventDefault()
    storeForm()
    switchMode('results')

  })
  $('#modepassage').click(function(e) {
    e.preventDefault()
    storeForm()
    switchMode('passage')
  })
  if (mode.val() == 'passage') {
    ensureLoaded('passage', 'passages', m)
  }
  else if (mode.val() == 'results') {
    ensureLoaded('sections', null, m)
    ensureLoaded('tuples', null, m)
    ensureLoaded('query', 'pages', m)
  }
}

function ensureLoaded(kind, subkind, m) {
  var table = $('#'+kind+'Table')
  if (!table.html()) {
    getTable(kind, subkind, m)
  }
  else {
    switchMode(m)
  }
}

function getTable(kind, subkind, m) {
  var url = '/'+kind;
  var dest = $('#'+kind+'Table');
  var destSub = $('#'+subkind)
  var go = document.querySelector("form");
  var formData = new FormData(go);
  var mode = $('#mode').val()
  $.ajax({
    type: 'POST',
    url: url,
    data: formData,
    processData: false,
    contentType: false,
    success: function(data) {
      var table = data.table || ''
      var messages = data.messages || ''
      dest.html(table + messages)
      if (subkind != null) {
        var subs = data[subkind]
        if (subs) {
          destSub.html(subs)
          subLinks(kind, subkind, m)
        }
      }
      var features = data.features;
      if (features != null) {
        $('#features').val(features)
      }
      switchPassage()
      details(kind)
      sections()
      tuples()
      nodes()
      switchMode(m)
      storeForm()
    },
  })
}

function activateTables(kind, subkind, m) {
  var button = $('#'+kind+'Go');
  button.click(function(e) {
    e.preventDefault()
    storeForm()
    var m = $('#mode').val()
    if (kind == 'passage' && m != 'passage') {
      m = 'passage'
    }
    else if (kind != 'passage' && m != 'results') {
      m = 'results'
    }
    getTable(kind, subkind, m)
  })
  detailc(kind, subkind)
  xpa = adjustOpened(kind)
  detailSet(kind, xpa)
}

function switchPassage() {
  $('.pq').click(function(e) {
    e.preventDefault()
    var seq = $(this).closest('details').attr('seq')
    $('#mode').val('passages')
    $('#sec0').val($(this).attr('sec0'))
    $('#sec1').val($(this).attr('sec1'))
    $('#sec2').val($(this).attr('sec2'))
    $('#pos').val(seq)
    storeForm()
    getTable('passage', 'passages', 'passage')
  })
}

function subLinks(kind, subkind, m) {
  if (subkind == 'pages') {
    $('.pnav').click(function(e) {
      e.preventDefault()
      $('#pos').val($(this).html())
      storeForm()
      getTable(kind, subkind, m)
    })
  }
  else if (subkind == 'passages') {
    opKey = kind+'Op'
    $('.s0nav').click(function(e) {
      e.preventDefault()
      $('#sec0').val($(this).html())
      $('#sec1').val('1')
      $('#sec2').val('')
      $('#'+opKey).val('')
      storeForm()
      getTable(kind, subkind, m)
    })
    $('.s1nav').click(function(e) {
      e.preventDefault()
      $('#sec1').val($(this).html())
      $('#sec2').val('')
      $('#'+opKey).val('')
      storeForm()
      getTable(kind, subkind, m)
    })
  }
}

function detailc(kind, subkind) {
  $('#'+kind+'Expac').click(function(e) {
    e.preventDefault()
    var expa = $('#'+kind+'Expa')
    var xpa = expa.val()
    var newXpa;
    if (xpa == "1") {newXpa = "-1"}
    else if (xpa == "-1") {newXpa = "1"}
    else if (xpa == "0") {newXpa = "-1"}
    else {newXpa = "-1"}
    detailSet(kind, newXpa)
    var m = $('#mode').val()
    var dPretty = $('#'+kind+'Table details.pretty')
    if (newXpa == "-1") {
      dPretty.each(function() {
        if ($(this).prop('open')) {
          $(this).prop('open', false)
        }
      })
    }
    else if (newXpa == "1") {
      dPretty.each(function() {
        if (!$(this).prop('open')) {
          $(this).prop('open', true)
        }
      })
    }
  })
}

function detailSet(kind, xpa) {
  var expac = $('#'+kind+'Expac')
  var expa = $('#'+kind+'Expa')
  var curVal = (xpa == null) ? expa.val() : xpa;
  if (curVal == "-1") {
    expa.val("-1")
    expac.prop('checked', false)
    expac.prop('indeterminate', false)
  }
  else if (curVal == "1") {
    expa.val("1")
    expac.prop('checked', true)
    expac.prop('indeterminate', false)
  }
  else if (curVal == "0") {
    expa.val("0")
    expac.prop('checked', false)
    expac.prop('indeterminate', true)
  }
  else {
    expa.val("-1")
    expac.prop('checked', false)
    expac.prop('indeterminate', false)
  }
  var op = $('#'+kind+'Op')
  if (curVal == "-1") {
    op.val('')
  }
  else if (curVal == "1") {
    var dPretty = $('#'+kind+'Table details.pretty')
    var allNumbers = dPretty.map(
      function() {return $(this).attr('seq')}
    ).get()
    op.val(allNumbers.join(','))
  }
  storeForm()
}

function adjustOpened(kind) {
  var openedElem = $('#'+kind+'Op')
  var dPretty = $('#'+kind+'Table details.pretty')
  var openedDetails = dPretty.filter(
    function(index) {return this.open}
  )
  var closedDetails = dPretty.filter(
    function(index) {return !this.open}
  )
  var openedNumbers = openedDetails.map(
    function() {return $(this).attr('seq')}
  ).get()
  var closedNumbers = closedDetails.map(
    function() {return $(this).attr('seq')}
  ).get() 
  
  currentOpenedStr = openedElem.val()
  currentOpened = (currentOpenedStr == '')?[]:currentOpenedStr.split(',');
  reduceOpened = currentOpened.filter(function(n) {
    return ((closedNumbers.indexOf(n) < 0) && (openedNumbers.indexOf(n) < 0))
  })
  newOpened = reduceOpened.concat(openedNumbers)
  openedElem.val(newOpened.join(','))
  var nOpen = openedDetails.length
  var nClosed = closedDetails.length
  var xpa = (nOpen == 0) ? "-1" : (nClosed == 0) ? "1" : "0";
  return xpa
}

function details(kind) {
  var details = $('#'+kind+'Table details.pretty')
  details.on('toggle', function() {
    xpa = adjustOpened(kind)
    detailSet(kind, xpa)
    if ($(this).prop('open') && !$(this).find('div.pretty').html()) {
      getOpen(kind, $(this))
    }
  })
}

function getOpen(kind, elem) {
  var seq = elem.attr('seq')
  var url = '/'+kind+'/'+seq;
  var dest = elem.find('div.pretty')
  var go = document.querySelector("form");
  var formData = new FormData(go);
  $.ajax({
    type: 'POST',
    url: url,
    data: formData,
    processData: false,
    contentType: false,
    success: function(data) {
      var table = data.table
      dest.html(table)
    },
  })
}

function reactive() {
  $('.r').change(function(e) {
    storeForm()
    var mode = $('#mode')
    var m = mode.val()
    getTable('sections', null, m)
    getTable('tuples', null, m)
    getTable('query', 'pages', m)
    getTable('passage', 'passages', m)
  })
  $('.sectionsR').change(function(e) {
    var mode = $('#mode')
    var m = mode.val()
    getTable('sections', null, m)
  })
  $('.tuplesR').change(function(e) {
    var mode = $('#mode')
    var m = mode.val()
    getTable('tuples', null, m)
  })
  $('.queryR').change(function(e) {
    var mode = $('#mode')
    var m = mode.val()
    getTable('query', 'pages', m)
  })
  $('.passageR').change(function(e) {
    var mode = $('#mode')
    var m = mode.val()
    getTable('passage', 'passages', m)
  })
}

function cradios() {
  $('.cradio').change(function(e) {
    $('#cond').prop('checked', true)
    storeForm()
  })
}

function sidebar() {
  var side = $('#side')
  var part = side.val()
  var headers = $('#sidebar div').filter(function() {
    var stat = $(this).attr('status')
    return (stat != 'help' && stat != 'about')
  })
  var bodies = $('#sidebarcont div').filter(function() {
    var stat = $(this).attr('status')
    return (stat != 'help' && stat != 'about')
  })
  if (part) {
    var header = $('#sidebar div[status="'+part+'"]')
    var body = $('#sidebarcont div[status="'+part+'"]')
    headers.removeClass('active')
    bodies.removeClass('active')
    header.addClass('active')
    body.addClass('active')
  }
  $('#sidebar a').click(function(e) {
    e.preventDefault()
    var header = $(this).closest('div')
    var part = header.attr('status')
    var side = $('#side')
    var body = $('#sidebarcont div[status="'+part+'"]')
    var isActive = header.hasClass('active')
    if (part != 'help') {
      headers.removeClass('active')
      bodies.removeClass('active')
    }
    if (isActive) {
      header.removeClass('active')
      body.removeClass('active')
      side.val('')
    }
    else {
      header.addClass('active')
      body.addClass('active')
      side.val(part)
    }
  })
}

function help() {
  var help = $('#help')
  var expandedStr = help.val()
  var helpOpened = (expandedStr == '')?[]:expandedStr.split(',');
  helpOpened.forEach(function(helpId) {
    helpDetails = $('#'+helpId)
    helpDetails.prop('open', true)
  })
  $('details.help').on('toggle', function(e) {
    var dHelp = $('details.help')
    var op = $('#help')
    var go = $('#go')
    var thisHelp = $(this)
    var thisId = thisHelp.attr('id')
    var thisOpen = thisHelp.prop('open')
    var expandedDetails = dHelp.filter(
      function() {return ($(this).prop('open') && $(this).attr('id') != thisId)}
    ).map(function() {return $(this).attr('id')}).get()
    if (thisOpen) {
      expandedDetails.push(thisId)
    }
    op.val(expandedDetails.join(','))
  })
}

function sections() {
  var secs = $('#sections') 
  $('.rwh').click(function(e) {
    e.preventDefault()
    e.stopPropagation()
    var sec = $(this).attr('sec')
    var orig = secs.val()
    secs.val(orig + '\n' + sec)
  })
}
function tuples() {
  var tups = $('#tuples') 
  $('.sq').click(function(e) {
    e.preventDefault()
    e.stopPropagation()
    var tup = $(this).attr('tup')
    var orig = tups.val()
    tups.val(orig + '\n' + tup)
  })
}
function nodes() {
  var tups = $('#tuples') 
  $('.nd').click(function(e) {
    e.preventDefault()
    e.stopPropagation()
    var nd = $(this).html()
    var orig = tups.val()
    tups.val(orig + '\n' + nd)
  })
}

function jobs() {
  var jobh = $('#jobh')
  $('#job').change(function(e) {
    jobh.val(e.target.value)
  })
}

function storeForm() {
  var go = document.querySelector("form");
  var formData = new FormData(go);
  var formObj = {};
  formData.forEach(function(value, key){
      formObj[key] = value
  })
  var formStr = JSON.stringify(formObj)
  var appName = formData.get('appName')
  var jobName = formData.get('jobName')
  var formKey = 'tf/'+appName+'/'+jobName
  localStorage.setItem(formKey, formStr)
}


$(function(){
  sidebar()
  jobs()
  modes()
  var m = $('#mode').val()
  activateTables('sections', null, m)
  activateTables('tuples', null, m)
  activateTables('query', 'pages', m)
  cradios()
  help()
  reactive()
  var rTarget = $('details.focus')
  if (rTarget != null && rTarget[0] != null) {
    rTarget[0].scrollIntoView(false)
  }
  storeForm()
})

