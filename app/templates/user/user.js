$(document).ready(function(){
    var sel_type = $("#type");
    sel_type.change(function(){
        console.log( $(this).val());
        if($(this).val() == "local") {
            $("#passwords").css('display', 'inherit');
        } else {
            $("#password").val('RPISTBR');
            $("#confirm_password").val('RPISTBR');
            $("#passwords").css('display', 'none');
        }
    });
});