(function($){
  $(document).ready(function(e){
    var disclaimer = $('#disclaimer-dialog'),
        form = $('#disclaimer-form')
    disclaimer.ready(function(){
      
      disclaimer.dialog({modal:true, title: 'Disclaimer', width:500, height:400})
      $('.ui-dialog-titlebar-close').remove();
      form.show();
    })
    form.submit(function() {
      $.ajax({
        url: form.attr('action'),
        type: 'POST',
        data: form.serializeArray(),
        dataType: 'json',
        success: function(data) {
          form.fadeOut()
          setTimeout(function(){
            disclaimer.dialog('close')
          }, 3000)
        },
      })
      return false
    })
  })
})(jQuery)
