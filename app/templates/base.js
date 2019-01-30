function flash_messages(list) {
    for (var i=0; i<list.length; i++){
        bootbox.alert(list[i]);
    }
}
