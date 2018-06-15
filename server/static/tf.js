function pageLinks() {
  $('.pnav').click(function(e) {e.preventDefault();$('#pos').val($(this).html());$('#go').submit()})
}

$(function(){
    pageLinks()
})
