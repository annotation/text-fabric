function pageLinks() {
  $('.pnav').click(function(e) {
    e.preventDefault()
    $('#pos').val($(this).html())
    $('#go').submit()
  })
}

function reactive() {
  $('input.r').change(function(e) {
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
    currentOpened = (currentOpenedStr == '')?[]:op.val().split(',');
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
  pageLinks()
  tuples()
  detailSet()
  details()
  detailc()
  radios()
  reactive()
})
