function flash_messages(list) {
    for (var i=0; i<list.length; i++){
        var message = list[i];
        bootbox.alert(message);
    }
}

function loader_on() {
  document.getElementsByClassName("loader")[0].style.display = "block";
}

function loader_off() {
  document.getElementsByClassName("loader")[0].style.display = "none";
}