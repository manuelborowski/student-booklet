var match_id;

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


    $('#myModal').on('hide.bs.modal', function (e) {
        if (document.activeElement.id == 'close_modal') {
            $('#btn_delete_extra_measure_' + match_id).css('visibility', 'visible');
            $('#txt_extra_measure_' + match_id).css('visibility', 'visible');
            $('#txt_extra_measure_' + match_id).html($('#modal_extra_measure').val());

            var oids = [];
            $("form#form_" + match_id + " :input").each(function() {
                console.log($(this).attr('name'), $(this).attr('value'));
                if ($(this).attr('name')=='offence_id') {
                    oids.push($(this).attr('value'));
                }
            });
            var data = {};
            data.oid_list = oids;
            data.extra_measure = $('#modal_extra_measure').val();

            $.getJSON(Flask.url_for('review.add_measure', {'data': JSON.stringify(data)}), function(data) {
            if(data.status) {
            } else {
                alert('Fout: kan schakelaar niet aanpassen');
            }
        });


            //$('#extra_measure').val($('#modal_extra_measure').val());
            //document.getElementById(form_id).action = Flask.url_for("review.extra_measure");
            //document.getElementById(form_id).submit();
        }
    });


    //Standard value
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

function extra_measure(mid) {
    match_id = mid;
    $('#myModal').modal();
}