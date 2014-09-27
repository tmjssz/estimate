/* //////////////////////////////////////////////////////////////////////////////////////////////
CONTENTS
========
 1. LANDING PAGES
 2. NAVIGATION
 3. SHOW QUESTION
 4. QUESTION SCORE
 5. HIGHSCORES
 6. STATISTICS
 7. ACCOUNT SETTINGS
 8. AJAX FORMS: FEEDBACK & FRIEND INVITE
 9. MODAL OVERLAYS
////////////////////////////////////////////////////////////////////////////////////////////// */



$( document ).ready(function() {


    // ========================================================================================
    // 1. LANDING PAGES
    // ========================================================================================
    

    // Set focus on first input of Modal Overlay when page is loaded
    // ........................................................................................

    function setModalFocusOnChecked(checkbox, input) {
        if ( checkbox.is(':checked') ) {
            input.focus();
        }
        else {
            // else the register form input is focused
            $('#estimate_form input#id_estimate').focus();
            $('#register-form input#id_username').focus();
        }
    }

    function focusInputOnModalOpen(modal) {
        $(modal).each(function(){
            var checkbox = $(this).find('input.modal-state');
            var input = $(this).find('.modal-inner form').find('input[type="text"], input[type="email"], textarea').first();
            checkbox.change(function() {
                setModalFocusOnChecked(checkbox, input);
            });
            setModalFocusOnChecked(checkbox, input);
        });
    }

    focusInputOnModalOpen('.modal');




    // ========================================================================================
    // 2. NAVIGATION
    // ========================================================================================


    // Click handler for mobile navigation
    // ........................................................................................

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
    
    



    // ========================================================================================
    // 3. SHOW QUESTION
    // ========================================================================================


    // Question Countdown 
    // ........................................................................................

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


    // Format estimate input content, that all 3 digits are separated
    // ........................................................................................

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
    });

    function isNumber(n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
    }


    // Check if estimate is given, when submit button is clicked
    // ........................................................................................

    $('#question-show form input[type=submit]').click(function(e) {
        if ($('#id_estimate').val() == "") {
            e.preventDefault();
            $('#question-show form .errorlist').hide();
            $('#question-show form .errorlist.empty').show().fadeOut(4000, 'swing');
            $('#id_estimate').focus();
        }
    });





    // ========================================================================================
    // 4. QUESTION SCORE
    // ========================================================================================


    // Click handler for 'Show resolution' Button
    // ........................................................................................

	$('#show_btn').click(function() {
		$(this).hide();
        $('.timed_out').fadeIn();
	});





    // ========================================================================================
    // 5. HIGHSCORES
    // ========================================================================================


    // Click handler for Highscore change Button
    // ........................................................................................

    $('.highscore-change').click(function() {
        if (!$(this).hasClass('selected')) {
            $('.highscore-change.selected').toggleClass('selected');
            $(this).toggleClass('selected');
            var rel = $(this).attr('rel');
            $('.score-list table').hide();
            $('.score-list table.'+rel).fadeIn();
        }
    });





    // ========================================================================================
    // 6. STATISTICS
    // ========================================================================================


    // Click Listener on question statistics checkboxes next to estimates (only for admin)
    // ........................................................................................

    $("form.activate-stats, form.deactivate-stats").on("change", "input:checkbox", function(){
        var id = $(this).val();
        $(this).parent().submit();
    });





    // ========================================================================================
    // 7. ACCOUNT SETTINGS
    // ========================================================================================


    // Click handler for 'Password change' Button
    // ........................................................................................

    $('span.pw-change').click(function() {
        $(this).hide();
        $('div.pw-change').fadeIn();
    });





    // ========================================================================================
    // 8. AJAX FORMS: FEEDBACK & FRIEND INVITE
    // ========================================================================================


    // Spinner Options
    // ........................................................................................

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
    

    // Function to set Click handler for Modal Form Submit Buttons
    // ........................................................................................

    function setModalSubmitHandler(modal_elem, url) {
        var submit_elem = modal_elem.find('.modal-content input[type="submit"]').first();
        
        submit_elem.click(function(e) {
            e.preventDefault();
            var form_elem = modal_elem.find('.modal-inner .modal-content form').first();
            var answer_elem = modal_elem.find('.modal-inner .modal-answer').first();
            var content_elem = modal_elem.find('.modal-inner .modal-content').first();
            var spinner = new Spinner(opts).spin();

            content_elem[0].appendChild(spinner.el);
            ajaxFormPost(url, form_elem, answer_elem, content_elem, spinner);

            content_elem.find('form input, form textarea').attr('disabled', 'disabled');
        });
    }

    function ajaxFormPost(url, form_elem, answer_elem, content_elem, spinner) {
        $.ajax({
            url : url,
            type: "POST",
            data: form_elem.serialize(),
            success: function( response ){
                answer_elem.html( $(response).find('#main >') );
                content_elem.hide();
                spinner.stop();
                content_elem.find('form input, form textarea').removeAttr('disabled');
                content_elem.find('form input[type="text"], form input[type="email"], form textarea').val('');
                
                answer_elem.find('.close-modal-btn').click(function() {
                    answer_elem.html('');
                    content_elem.fadeIn();
                });
            }
        });
    }


    setModalSubmitHandler($('#modal-feedback'), "/feedback/");
    setModalSubmitHandler($('#modal-invite-friend'), "/freund-einladen/");
    setModalSubmitHandler($('#modal-question-feedback'), "/feedback/");   





    // ========================================================================================
    // 9. MODAL OVERLAYS
    // ========================================================================================


    // Function to set click handlers for clicks outside a modal window to close it
    // ........................................................................................

    function closeModalOnClickOutside(modal_elem) {
        var modalWindow = modal_elem.find('.modal-window').first();
        var modalInner = modal_elem.find('.modal-inner').first();
        var closeLabel = modal_elem.find('.modal-label').first();

        modalWindow.click(function() {
            closeLabel.click();
        });
        modalInner.click(function(event){
            event.stopPropagation();
        });
    }

    closeModalOnClickOutside($('#modal-login'));
    closeModalOnClickOutside($('#modal-invite-friend'));
    closeModalOnClickOutside($('#modal-feedback'));
    closeModalOnClickOutside($('#modal-question-feedback'));
    closeModalOnClickOutside($('#modal-play'));
    closeModalOnClickOutside($('#modal-group-create'));
    closeModalOnClickOutside($('#modal-group-invite'));
    closeModalOnClickOutside($('#modal-welcome'));
    closeModalOnClickOutside($('#modal-message'));

});
