$( document ).ready(function() {

	// Countdown for question
    $("#countdown").countDown({
		startNumber: 30,
		callBack: function() {
			$("form").submit();
		}
	});

    // Click handler for 'Show resolution' Button
	$('#show_btn').click(function() {
		$(this).hide();
		$('#show_resolution').fadeIn();
        $('table.timed_out').fadeIn();
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

    // Click handler for Register/Login Accordion on Landing Page
    var accItem = $('#register-login .accordion li');
    $(accItem).click(function(e) {
        e.preventDefault();
        if ( $(this).hasClass('not-selected') ) {
            var rel = $(this).attr('rel');
            $(accItem).removeClass('selected').addClass('not-selected');
            $(this).removeClass('not-selected').addClass('selected');

            $('#register-login .form').hide();
            $('#'+rel).fadeIn();
        }
    });

    // Click handler for 'Password change' Button
    $('span.pw-change').click(function() {
        $(this).hide();
        $('div.pw-change').fadeIn();
    });

});
