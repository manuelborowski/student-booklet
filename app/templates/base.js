function flash_messages(list) {
    for (var i=0; i<list.length; i++){
        var message = list[i];
        bootbox.alert(message);
    }
}

function busy_indication_on() {
  document.getElementsByClassName("loader")[0].style.display = "block";
}

function busy_indication_off() {
  document.getElementsByClassName("loader")[0].style.display = "none";
}


$(document).ready(function(){
    //log out automatically after 10 minutes
    var idleTime = 0;
    setInterval(function(){
        idleTime = idleTime + 1;
        if (idleTime > 9) { // 10 minutes
            window.location.href=Flask.url_for('auth.logout');
        }
    }, 60000); // 1 minute
    $(this).mousemove(function (e) {idleTime = 0;});
    $(this).keypress(function (e) {idleTime = 0;});
});



