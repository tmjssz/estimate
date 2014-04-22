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
});
