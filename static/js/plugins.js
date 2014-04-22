// Avoid `console` errors in browsers that lack a console.
(function() {
    var method;
    var noop = function () {};
    var methods = [
        'assert', 'clear', 'count', 'debug', 'dir', 'dirxml', 'error',
        'exception', 'group', 'groupCollapsed', 'groupEnd', 'info', 'log',
        'markTimeline', 'profile', 'profileEnd', 'table', 'time', 'timeEnd',
        'timeStamp', 'trace', 'warn'
    ];
    var length = methods.length;
    var console = (window.console = window.console || {});

    while (length--) {
        method = methods[length];

        // Only stub undefined methods.
        if (!console[method]) {
            console[method] = noop;
        }
    }
}());


// ==================================================================
// jQuery Countdown Plugin
// ==================================================================
jQuery.fn.countDown = function(settings,to) {
    settings = jQuery.extend({
        startFontSize: "36px",
        endFontSize: "12px",
        duration: 1000,
        startNumber: 10,
        endNumber: 0,
        callBack: function() { }
    }, settings);
    return this.each(function() {
        
        //where do we start?
        if(!to && to != settings.endNumber) { to = settings.startNumber; }
        
        //set the countdown to the starting number
        jQuery(this).text(to).css("fontSize",settings.startFontSize);
        
        //loopage
        jQuery(this).animate({
            fontSize: settings.endFontSize
        }, settings.duration, "", function() {
            if(to > settings.endNumber + 1) {
                jQuery(this).css("fontSize", settings.startFontSize).text(to - 1).countDown(settings, to - 1);
            }
            else {
                settings.callBack(this);
            }
        });
                
    });
};