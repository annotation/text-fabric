function pageLinks() {
  $('.pnav').click(function(e) {
    e.preventDefault()
    $('#pos').val($(this).html())
    $('#go').submit()
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
  var openedStr = help.val()
  var helpOpened = (openedStr == '')?[]:openedStr.split(',');
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
    var openedDetails = dHelp.filter(
      function() {return ($(this).prop('open') && $(this).attr('id') != thisId)}
    ).map(function() {return $(this).attr('id')}).get()
    if (thisOpen) {
      openedDetails.push(thisId)
    }
    op.val(openedDetails.join(','))
  })
}

function jobs() {
  var jobh = $('#jobh')
  $('#job').change(function(e) {
    jobh.val(e.target.value)
  })
}
function reactive() {
  $('.r').change(function(e) {
    $('#go').submit()
  })
}

function radios() {
  $('.cradio').change(function(e) {
    $('#cond').prop('checked', true)
  })
}

function detailc() {
  $('#expac').click(function(e) {
    e.preventDefault()
    var expa = $('#expa')
    var xpa = expa.val()
    var newXpa;
    if (xpa == "1") {newXpa = "-1"}
    else if (xpa == "-1") {newXpa = "1"}
    else if (xpa == "0") {newXpa = "-1"}
    else {newXpa = "-1"}
    detailSet(newXpa)
    $('#go').submit()
  })
}

function sections() {
  var secs = $('#sections') 
  $('.rwh').click(function(e) {
    e.preventDefault()
    e.stopPropagation()
    var sec = $(this).html()
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


function detailSet(xpa) {
  var expac = $('#expac')
  var expa = $('#expa')
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
  var op = $('#op')
  if (curVal == "-1") {
    op.val('')
  }
  else if (curVal == "1") {
    var dPretty = $('details.pretty')
    var allNumbers = dPretty.map(
      function() {return $(this).attr('seq')}
    ).get()
    op.val(allNumbers.join(','))
  }
}

function details() {
  $('details.pretty').on('toggle', function() {
    var dPretty = $('details.pretty')
    var op = $('#op')
    var go = $('#go')
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
    var nAll = openedNumbers.length + closedNumbers.length
    
    currentOpenedStr = op.val()
    currentOpened = (currentOpenedStr == '')?[]:currentOpenedStr.split(',');
    reduceOpened = currentOpened.filter(function(n) {
      return ((closedNumbers.indexOf(n) < 0) && (openedNumbers.indexOf(n) < 0))
    })
    newOpened = reduceOpened.concat(openedNumbers)
    op.val(newOpened.join(','))
    detailSet("0")
    go.submit()
  })
}

$(function(){
  sidebar()
  jobs()
  pageLinks()
  sections()
  tuples()
  nodes()
  detailSet()
  details()
  detailc()
  radios()
  help()
  reactive()
})
