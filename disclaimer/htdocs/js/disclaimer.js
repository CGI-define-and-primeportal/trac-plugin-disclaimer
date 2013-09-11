(function($){
  $(document).ready(function(e){
	$("#disclaimer-form #save-spinner").hide();
    var disclaimer = $('#disclaimer-dialog'),
    form = $('#disclaimer-form')
    disclaimer.ready(function(){
      disclaimer.dialog({modal:true, title: 'Disclaimer', width:600, maxHeight:400, closeOnEscape: false})
      $('.ui-dialog-titlebar-close').remove();
      form.show();
      $("#disclaimer-form input[name='send']").attr('disabled', true);
      $("#disclaimer-form input[name='accept']").click(function(){
      	  $("#disclaimer-form input[name='send']").attr('disabled',!$("#disclaimer-form input[name='accept']").attr('checked'))
      });
    })
    form.submit(function(){
    	$("#disclaimer-form #save-spinner").show();
    	$.ajax({
	        url: form.attr('action'),
	        type: 'POST',
	        data: form.serializeArray(),
	        dataType: 'json',
        	success: function(data){
        		setTimeout(function(){
        			form.fadeOut();
        			disclaimer.dialog('close')}, 3000);
        		
        	},
        	error: function(){
        		alert("Error occured. Please contact Service desk: servicedesk@cgi.com");
        		$("#disclaimer-form #save-spinner").hide();
        	}
        })
    	return false;
    })
  })
})(jQuery)
