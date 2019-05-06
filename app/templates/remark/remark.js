$(document).ready(function(){
    var select = document.getElementById("slct-hour");
    for (i = 1; i < 10; i++) {
        var option = document.createElement("option");
        if (i == 1) {
            option.text = i + "ste uur";
        } else {
            option.text = i + "de uur";
        }
        option.value = i;
        select.add(option);
    }
    select.value ="{{hour}}";

    $('input[name="txt-date"]').datepicker(datepicker_options);

});
