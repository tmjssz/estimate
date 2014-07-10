$( document ).ready(function() {

    //var time = getCookie('time');
    //if (time == '') {
        time = 40;
    //}

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
    }

	// Countdown for question
    $("#countdown").countDown({
		startNumber: time,
		callBack: function() {
            if ($('#id_estimate').val() == "") {
                var input = $("<input>")
                    .attr("type", "hidden")
                    .attr("name", "time_out")
                    .attr("id", "time_out").val("true");
                $("form").append($(input));
            }
            
			$("form").submit();
		}
	});

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

});
