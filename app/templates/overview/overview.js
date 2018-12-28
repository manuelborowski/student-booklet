$(document).ready(function(){
//    $("#filter_group").change(function(){
//        //alert('test update filter');
//        alert($(this));
//        $("#filter_form").submit();
//    });


    $("#teacher").change(function(){$('#change_id').val('teacher');$("#filter_form").submit();});
    $("#dayhour").change(function(){$('#change_id').val('dayhour');$("#filter_form").submit();});
    $("#classgroup").change(function(){$('#change_id').val('classgroup');$("#filter_form").submit();});
    $("#lesson").change(function(){$('#change_id').val('lesson');$("#filter_form").submit();});


    $('figure').click(function() {
        //New Code replaced here
        //alert('test');
        $(this).toggleClass('selected');
        var name = $(this).find('#id').attr('name');
        if(name == 'student_id') {
            $(this).find('#id').attr('name', '');
        } else {
            $(this).find('#id').attr('name', 'student_id');
        }
    });
});

