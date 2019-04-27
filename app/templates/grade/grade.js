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
    $("#select_all").html("Selecteer iedereen");

    $("#dayhour > option").each(function(){
        if (this.value.includes("disabled")) {
            this.setAttribute('disabled', true);
        }
    });
    $("#grade > option").each(function(){
        if (this.value.includes("disabled")) {
            this.setAttribute('disabled', true);
        }
    });
    $("#lesson > option").each(function(){
        if (this.value.includes("disabled")) {
            this.setAttribute('disabled', true);
        }
    });

});

function select_all_students() {
    if ($("#select_all").html() == "Selecteer iedereen") {
        $('figure').addClass('selected');
        $('#students input').each(function(i){
            $(this).attr('name', 'student_id');
        });
        $("#select_all").html("Selecteer niemand");
    } else {
        $('figure').removeClass('selected');
        $('#students input').each(function(i){
            $(this).attr('name', '');
        });
        $("#select_all").html("Selecteer iedereen");
    }
}

function add_remark() {
    var student_selected = false;
    $('#students input').each(function(i){
        if($(this).attr('name') == 'student_id') {
            student_selected = true;
            return false;
        }
    });
    if (student_selected) {
        $("#form_filter").attr("action", "{{ url_for('grade.action')}}");
        $("#form_filter").submit();
    } else {
        bootbox.alert("U moet minstens 1 leerling selecteren");
    }
}