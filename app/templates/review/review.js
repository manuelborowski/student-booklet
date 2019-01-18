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
            var oids = [];
            $("form#form_" + match_id + " :input").each(function() {
                if ($(this).attr('name')=='offence_id') {
                    oids.push($(this).attr('value'));
                }
            });
            var data = {};
            data.oid_list = oids;
            //replace newline characters with %0a so it can be put inside a GET request
            extra_measure = $('#modal_extra_measure').val().replace(/\n/g, '%0a');
            $.getJSON(Flask.url_for('review.add_measure', {'oids': JSON.stringify(oids), 'em' : extra_measure }), function(data) {
                if(data.status) {
                    button_extra_measure_visible(match_id, false);
                    $('#txt_extra_measure_' + match_id).html($('#modal_extra_measure').val());
                } else {
                    alert('Fout: kan de extra sanctie niet toevoegen');
                }
            });

        }
    });

    //Standard value
    $("#select_all").html("Iedereen");

    do_at_ready();

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

function button_extra_measure_visible(match_id, status) {
    $('#btn_extra_measure_' + match_id).css('display', (status) ? 'inherit' : 'none');
    $('#btn_delete_extra_measure_' + match_id).css('display', (status) ? 'none' : 'inherit');
    $('#btn_match_reviewed_' + match_id).css('display', (status) ? 'none' : 'inherit');
    $('#txt_extra_measure_' + match_id).css('display', (status) ? 'none' : 'inherit');
}

function extra_measure(mid) {
    match_id = mid;
    $('#myModal').modal();
}

function delete_measure(mid) {
    bootbox.confirm("Bent u zeker dat u deze maatregel wilt verwijderen?", function (result) {
        if (result) {
            //Find the first offence and use that id
            var offence_id = -1;
            $("form#form_" + mid + " :input").each(function() {
                if ($(this).attr('name')=='offence_id') {
                    offence_id = ($(this).attr('value'));
                    return false;
                }
            });
            $.getJSON(Flask.url_for('review.delete_measure', {'offence_id': offence_id}), function(data) {
                if(data.status) {
                    button_extra_measure_visible(mid, true);
                } else {
                    alert('Fout: kan de extra sanctie verwijderen');
                }
            });
        }
    });
}
function match_reviewed(mid) {
    bootbox.confirm("De controle is in orde?", function (result) {
        if (result) {
            //Find the first offence and use that id
            var offence_id = -1;
            $("form#form_" + mid + " :input").each(function() {
                if ($(this).attr('name')=='offence_id') {
                    offence_id = ($(this).attr('value'));
                    return false;
                }
            });
            window.location.href = Flask.url_for('review.match_reviewed', {'offence_id': offence_id});
        }
    });
}

function do_at_ready() {
    // iterate over all matches and show extra-measure-controls when the extra_measure-textbox is not empty
    $("input[id='match_id']").each(function() {
        var id = $(this).attr('value')
        button_extra_measure_visible(id, ($('#txt_extra_measure_' + id).val() == ""));
    });
}
