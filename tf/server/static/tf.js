function pageLinks() {
  $('.pnav').click(function(e) {
    e.preventDefault()
    $('#pos').val($(this).html())
    $('#go').submit()
  })
}

function reactive() {
  $('input').change(function(e) {
    $('#go').submit()
  })
}

function radios() {
  $('.cradio').change(function(e) {
    $('#cond').prop('checked', true)
  })
}

function details() {
  $('details.pretty').on('toggle', function() {
    var openedDetails = $('details.pretty').filter(
      function(index) {return this.open}
    )
    var closedDetails = $('details.pretty').filter(
      function(index) {return !this.open}
    )
    var openedNumbers = openedDetails.map(
      function() {return $(this).attr('seq')}
    ).get()
    var closedNumbers = closedDetails.map(
      function() {return $(this).attr('seq')}
    ).get() 
    
    currentOpenedStr = $('#op').val()
    currentOpened = (currentOpenedStr == '')?[]:$('#op').val().split(',');
    reduceOpened = currentOpened.filter(function(n) {
      return ((closedNumbers.indexOf(n) < 0) && (openedNumbers.indexOf(n) < 0))
    })
    newOpened = reduceOpened.concat(openedNumbers)
    console.warn({currentOpened, reduceOpened, newOpened})
    $('#op').val(newOpened.join(','))
    $('#go').submit()
  })
}

$(function(){
  pageLinks()
  details()
  radios()
  reactive()
})
