$(document).ready(function(){
    $("#teacher").change(function(){$('#change_id').val('teacher');$("#form_filter").submit();});
    $("#dayhour").change(function(){$('#change_id').val('dayhour');$("#form_filter").submit();});
    $("#grade").change(function(){$('#change_id').val('grade');$("#form_filter").submit();});
    $("#lesson").change(function(){$('#change_id').val('lesson');$("#form_filter").submit();});


    $('figure').click(function() {
        $(this).toggleClass('selected');
        var name = $(this).find('#id').attr('name');
        if(name == 'student_id') {
            $(this).find('#id').attr('name', '');
        } else {
            $(this).find('#id').attr('name', 'student_id');
        }
    });
    $("#select_all").html("Iedereen");

});

function select_all_students() {
    if ($("#select_all").html() == "Iedereen") {
        $('figure').addClass('selected');
        $('#students input').each(function(i){
            $(this).attr('name', 'student_id');
        });
        $("#select_all").html("Niemand");
    } else {
        $('figure').removeClass('selected');
        $('#students input').each(function(i){
            $(this).attr('name', '');
        });
        $("#select_all").html("Iedereen");
    }
}
