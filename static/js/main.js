$( document ).ready(function() {

	// Countdown for question
    $("#countdown").countDown({
		startNumber: 30,
		callBack: function() {
			$("form").submit();
		}
	});

    // Click handler for 'Show resolution' Button
	$('#show_resolution').click(function() {
		$(this).hide();
		$('#resolution').removeClass('hidden');
	});


	// Click handler for mobile navigation
    var navigation = $('.navigation-wrapper nav ul');
    var naviToggle = $('#naviToggle');
    $(naviToggle).click(function(e) {
    	e.preventDefault();
    	navigation.slideToggle(function(){
    		if(navigation.is(':hidden')) {
    			navigation.removeAttr('style');
    		}
    	});
    });

});
