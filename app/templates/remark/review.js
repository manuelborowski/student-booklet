var match_id;

$(document).ready(function(){
    $('#myModal').on('hide.bs.modal', function (e) {
        if (document.activeElement.id == 'close_modal') {
            var remark_ids = [];
            $("form#form_" + match_id + " :input").each(function() {
                if ($(this).attr('name')=='remark_id') {
                    remark_ids.push($(this).attr('value'));
                }
            });
            var data = {};
            data.remark_id_list = remark_ids;
            message = encodeURIComponent($('#modal_extra_measure').val().replace(/\//g, '&47;'));
            $.getJSON(Flask.url_for('remarks.add_extra_measure', {'remark_ids': JSON.stringify(remark_ids), 'em' : message }), function(data) {
                if(data.status) {
                    review_hide_elements(match_id, 'reviewed');
                    $('#txt_extra_measure_' + match_id).text($('#modal_extra_measure').val());
                    $('#txt_extra_measure_' + match_id).fadeIn('fast');
                } else {
                    bootbox.alert('Fout: kan de extra sanctie niet toevoegen');
                }
            });
        }
    });
});

function review_hide_elements(mid, status) {
    if (status == 'default') {
        $('#btn_extra_measure_' + mid).css('display', 'inherit');
        $('#postpone-review-' + mid).css('display', 'inherit');
        $('#postpone-label-' + mid).css('display', 'none');
        $('#btn_delete_extra_measure_' + mid).css('display', 'none');
        $('#txt_extra_measure_' + mid).css('display', 'none');
        $('#review-status-' + mid).val("default");
    } else if (status == 'reviewed') {
        $('#btn_extra_measure_' + mid).css('display', 'none');
        $('#postpone-review-' + mid).css('display', 'none');
        $('#postpone-label-' + mid).css('display', 'none');
        $('#btn_delete_extra_measure_' + mid).css('display', 'inherit');
        $('#txt_extra_measure_' + mid).css('display', 'inherit');
        $('#review-status-' + mid).val("reviewed");
    }
    else if (status == 'postponed') {
        $('#btn_extra_measure_' + mid).css('display', 'none');
        $('#postpone-review-' + mid).css('display', 'none');
        $('#postpone-label-' + mid).css('display', 'inherit');
        $('#btn_delete_extra_measure_' + mid).css('display', 'none');
        $('#txt_extra_measure_' + mid).css('display', 'none');
        $("#form_" + mid +  " table").css('display', "none");
        $('#review-status-' + mid).val("postponed");
    }
}

function extra_measure(mid) {
    match_id = mid;
    $('#myModal').modal();
}

function postpone_review(mid) {
    review_hide_elements(mid, "postponed");
}

$('#myModal').on('shown.bs.modal', function() {
  $('#modal_extra_measure').focus();
})
function delete_extra_measure(mid) {
    bootbox.confirm("Bent u zeker dat u deze maatregel wilt verwijderen?", function (result) {
        if (result) {
            //Find the first remark and use that id
            var remark_id = -1;
            $("form#form_" + mid + " :input").each(function() {
                if ($(this).attr('name')=='remark_id') {
                    remark_id = ($(this).attr('value'));
                    return false;
                }
            });
            $.getJSON(Flask.url_for('remarks.delete_extra_measure', {'remark_id': remark_id}), function(data) {
                if(data.status) {
                    review_hide_elements(mid, 'default');
                } else {
                    bootbox.alert('Fout: kan de extra sanctie niet verwijderen');
                }
            });
        }
    });
}

function review_done() {
    var all_reviewed = true;
    var reviewed_counter = 0;
    var postponed_counter = 0;
    var default_counter = 0;
    $("input[id='match_id']").each(function() {
        var id = $(this).attr('value')

        if($('#review-status-' + id).val() == "default") {
            default_counter++;
            $('#btn_extra_measure_' + id).css('background-color', "#ffdd00");
            $('#postpone-review-' + id).css('background-color', "#ffdd00");
        } else if($('#review-status-' + id).val() == "reviewed") {
            reviewed_counter++;
        } else if($('#review-status-' + id).val() == "postponed") {
            postponed_counter++;
        }
    });
    if(default_counter == 0) {
        bootbox.confirm(reviewed_counter + " leerling(en) gecontroleerd<br>" +
                        postponed_counter + " leerling(en) met uitgestelde controle<br>" +
                        "Bent u zeker dat u de controle wil beëindigen?", function (result) {
            if(result) {
                $("#form_review_done").submit();
            }
        });
    } else {
        bootbox.alert("Opgepast, nog niet alle leerlingen zijn gecontroleerd!");
    }
}