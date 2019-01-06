$(document).ready(function(){
    $("#teacher").change(function(){$('#change_id').val('teacher');$("#filter_form").submit();});
    $("#dayhour").change(function(){$('#change_id').val('dayhour');$("#filter_form").submit();});
    $("#classgroup").change(function(){$('#change_id').val('classgroup');$("#filter_form").submit();});
    $("#lesson").change(function(){$('#change_id').val('lesson');$("#filter_form").submit();});


    $('figure').click(function() {
        $(this).toggleClass('selected');
        var name = $(this).find('#id').attr('name');
        if(name == 'student_id') {
            $(this).find('#id').attr('name', '');
        } else {
            $(this).find('#id').attr('name', 'student_id');
        }
    });
    $("#select_all").val("Iedereen");

});

function select_all_students() {
    if ($("#select_all").val() == "Iedereen") {
        $('figure').addClass('selected');
        $('#students input').each(function(i){
            console.log(i + ' ' + $(this).val());
            $(this).attr('name', 'student_id');
        });
        $("#select_all").val("Niemand");
    } else {
        $('figure').removeClass('selected');
        $('#students input').each(function(i){
            $(this).attr('name', '');
        });
        $("#select_all").val("Iedereen");
    }
}
