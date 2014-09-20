$( document ).ready(function() {

    /*var time = getCookie('time');
    if (time == '') {
        time = 40;
    }

    function getCookie(cname) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for(var i=0; i<ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1);
            if (c.indexOf(name) != -1) return c.substring(name.length,c.length);
        }
        return "";
    }

    var setCookie = function(name, value, days) {
        var expires;
        if (days) {
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toGMTString();
        }
        else {
            expires = "";
        }
        document.cookie = name + "=" + value + expires + "; path=/";
    }*/

    //time = 40;
    
    
    // COUNTDOWN FOR QUESTIONS -----------------------------------------------
    var countdown = $("#countdown");

    if (countdown.length > 0) {
        time = $('#time_left').val();

        $("#countdown").countDown({
            startNumber: time,
            callBack: function() {
                if ($('#id_estimate').val() == "") {
                    var input = $("<input>")
                        .attr("type", "hidden")
                        .attr("name", "time_out")
                        .attr("id", "time_out").val("true");
                    $("form#estimate_form").append($(input));
                }
                
                $("form#estimate_form").submit();
            }
        });
    }

    // Format the input content, that all 3 digits are separated
    $('#id_estimate').focus();
    $('#id_estimate').keyup(function() {
        var num = $(this).val().replace(/(\s)/g, '');
        $(this).val(num.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1 "));
    });
    // reformat input value before submitting
    $('#estimate_form').submit(function() { 
        var value = $('#id_estimate').val().replace(/ /g, '');
        value = value.replace(/,/g, '.');

        var time_out = $('#question-show form #time_out').val();

        if (!isNumber(value) && !time_out) {
            $('#question-show form .errorlist').hide();
            $('#question-show form .errorlist.not-number').show().fadeOut(4000, 'swing');
            return false;
        }

        $('#id_estimate').val(value);

        // reset cookie
        setCookie('time', 40, 0);
    });

    function isNumber(n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
    }


    // Check if estimate is given, when submit button is clicked
    $('#question-show form input[type=submit]').click(function(e) {
        if ($('#id_estimate').val() == "") {
            e.preventDefault();
            $('#question-show form .errorlist').hide();
            $('#question-show form .errorlist.empty').show().fadeOut(4000, 'swing');
            $('#id_estimate').focus();
        }
    });

    // Click handler for 'Show resolution' Button
	$('#show_btn').click(function() {
		$(this).hide();
        $('.timed_out').fadeIn();
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

    // Click handler for Highscore change Button
    $('.highscore-change').click(function() {
        if (!$(this).hasClass('selected')) {
            $('.highscore-change.selected').toggleClass('selected');
            $(this).toggleClass('selected');
            var rel = $(this).attr('rel');
            $('.score-list table').hide();
            $('.score-list table.'+rel).fadeIn();
            //window.history.pushState("", rel, "#"+rel);
        }
    });

    // SPINNER OPTIONS
    var opts = {
      lines: 13, // The number of lines to draw
      length: 7, // The length of each line
      width: 3, // The line thickness
      radius: 10, // The radius of the inner circle
      corners: 0.5, // Corner roundness (0..1)
      rotate: 0, // The rotation offset
      direction: 1, // 1: clockwise, -1: counterclockwise
      color: '#000', // #rgb or #rrggbb or array of colors
      speed: 1, // Rounds per second
      trail: 54, // Afterglow percentage
      shadow: false, // Whether to render a shadow
      hwaccel: false, // Whether to use hardware acceleration
      className: 'spinner', // The CSS class to assign to the spinner
      zIndex: 2e9, // The z-index (defaults to 2000000000)
      top: '50%', // Top position relative to parent
      left: '50%' // Left position relative to parent
    };
    

    // Click handler for Feedback Form Submit Buttons
    $('#feedback-content input[type="submit"]').click(function(e) {
        var content_id = 'feedback-content';
        var answer_id = 'feedback-answer';
        e.preventDefault();

        var target = document.getElementById(content_id);
        var spinner = new Spinner(opts).spin(target);

        $.ajax({
            url : "/feedback/",
            type: "POST",
            data: $('#' + content_id + ' form').serialize(),
            success: function( response ){
                $('#' + answer_id).html( $(response).find('#main >') );
                $('#' + content_id).hide();
                spinner.stop();
            }
        });

        $('#' + content_id + ' form input, #' + content_id + ' form textarea').attr('disabled', 'disabled');
    });

    // Click handler for Question-Feedback Form Submit Buttons
    $('#feedback-question-content input[type="submit"]').click(function(e) {
        var content_id = 'feedback-question-content';
        var answer_id = 'feedback-question-answer';
        e.preventDefault();

        var target = document.getElementById(content_id);
        var spinner = new Spinner(opts).spin(target);

        $.ajax({
            url : "/feedback/",
            type: "POST",
            data: $('#' + content_id + ' form').serialize(),
            success: function( response ){
                $('#' + answer_id).html( $(response).find('#main >') );
                $('#' + content_id).hide();
                spinner.stop();
            }
        });

        $('#' + content_id + ' form input, #' + content_id + ' form textarea').attr('disabled', 'disabled');
    });

    // Click handler for Friend Invitation Form Submit Buttons
    $('#invite-friend-content input[type="submit"]').click(function(e) {
        var content_id = 'invite-friend-content';
        var answer_id = 'invite-friend-answer';
        e.preventDefault();

        var target = document.getElementById(content_id);
        var spinner = new Spinner(opts).spin(target);

        $.ajax({
            url : "/freund-einladen/",
            type: "POST",
            data: $('#' + content_id + ' form').serialize(),
            success: function( response ){
                $('#' + answer_id).html( $(response).find('#main >') );
                $('#' + content_id).hide();
                spinner.stop();
                $('#' + content_id + ' form input, #' + content_id + ' form textarea').removeAttr('disabled');
                $('#' + content_id + ' form #id_mail, #' + content_id + ' form #id_message').val('');
                
                $('#' + answer_id + ' .close-modal-btn').click(function() {
                    $('#' + answer_id).html('');
                    $('#' + content_id).fadeIn();
                });
            }
        });

        $('#' + content_id + ' form input, #' + content_id + ' form textarea').attr('disabled', 'disabled');
    });
    

    // Function to set click handlers for clicks outside a modal window to close it
    function closeModalOnClickOutside(modalWindow, modalInner, closeLabel) {
        $(modalWindow).click(function() {
            $(closeLabel).click();
        });
        $(modalInner).click(function(event){
            event.stopPropagation();
        });
    }

    closeModalOnClickOutside('.modal-window.login', '.modal-inner.login', 'label.login-btn');
    closeModalOnClickOutside('.modal-window.feedback', '.modal-inner.feedback', 'label.modal-close.feedback');
    closeModalOnClickOutside('.modal-window.friend-invite', '.modal-inner.friend-invite', 'label.modal-close.friend-invite');
    closeModalOnClickOutside('.modal-window.question-feedback', '.modal-inner.question-feedback', 'label.modal-close.question-feedback');
    closeModalOnClickOutside('.modal-window.group', '.modal-inner.group', 'label.modal-close.group');
    closeModalOnClickOutside('.modal-window.group-invite', '.modal-inner.group-invite', 'label.modal-close.group-invite');


    // Click Listener on question statistics checkboxes next to estimates
    $("form.activate-stats, form.deactivate-stats").on("change", "input:checkbox", function(){
        var id = $(this).val();
        $(this).parent().submit();
    });

});
