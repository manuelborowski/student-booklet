$(document).ready(function() {
    var main_path = window.location.pathname.split("/")[1];
    $('#sb_navbar a').each(function(i){
        $(this).removeAttr("style");
    });

    var s = $("#sb_navbar a[href='" + "{{url_rule}}" + "']");
    s.attr("style", "color:#0088cc");

});
