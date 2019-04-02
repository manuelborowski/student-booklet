function flash_messages(list) {
    for (var i=0; i<list.length; i++){
        var message = list[i];
        bootbox.alert(message);
    }
}

function busy_indication_on() {
  document.getElementsByClassName("busy-indicator")[0].style.display = "block";
}

function busy_indication_off() {
  document.getElementsByClassName("busy-indicator")[0].style.display = "none";
}

//date picker
//Big hack to get dutch calendar to work... :-(
$.fn.datepicker.dates['nl'] = {
    days : 'zondag_maandag_dinsdag_woensdag_donderdag_vrijdag_zaterdag'.split('_'),
    daysShort : 'zo._ma._di._wo._do._vr._za.'.split('_'),
    daysMin : 'zo_ma_di_wo_do_vr_za'.split('_'),
    months : 'januari_februari_maart_april_mei_juni_juli_augustus_september_oktober_november_december'.split('_'),
    monthsShort : 'jan_feb_maa_apr_mei_jun_jul_aug_sep_okt_nov_dec'.split('_'),
    today: "Vandaag",
    clear: "Clear",
    format: "dd-mm-yyyy",
    titleFormat: "MM yyyy", /* Leverages same syntax as 'format' */
    weekStart: 0
};
var container=$('.bootstrap-iso form').length>0 ? $('.bootstrap-iso form').parent() : "body";
var datepicker_options={
    language: 'nl',
    container: container,
    todayHighlight: true,
    autoclose: true,
    orientation: "auto"
};



$(document).ready(function(){

    var max_idle_time = 15;
    {% if current_user.is_strict_user %} //ordinary users log out after 2 minutes
    max_idle_time = 2;
    {% endif %}
    var idle_time = 0;
    setInterval(function(){
        idle_time = idle_time + 1;
        if (idle_time > max_idle_time) {
            window.location.href=Flask.url_for('auth.logout');
        }
    }, 60000); // 1 minute
    $(this).mousemove(function (e) {idle_time = 0;});
    $(this).keypress(function (e) {idle_time = 0;});

    $("body").css("padding-top", $("#nav-menu").height());
});
