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
                    button_extra_measure_visible(match_id, false);
                    $('#txt_extra_measure_' + match_id).text($('#modal_extra_measure').val());
                    $('#txt_extra_measure_' + match_id).fadeIn('fast');
                } else {
                    bootbox.alert('Fout: kan de extra sanctie niet toevoegen');
                }
            });
        }
    });
});

function button_extra_measure_visible(match_id, status) {
    $('#btn_extra_measure_' + match_id).css('display', (status) ? 'inherit' : 'none');
    $('#btn_delete_extra_measure_' + match_id).css('display', (status) ? 'none' : 'inherit');
    //$('#btn_match_reviewed_' + match_id).css('display', (status) ? 'none' : 'inherit');
    $('#txt_extra_measure_' + match_id).css('display', (status) ? 'none' : 'inherit');
}

function extra_measure(mid) {
    match_id = mid;
    $('#myModal').modal();
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
                    button_extra_measure_visible(mid, true);
                } else {
                    bootbox.alert('Fout: kan de extra sanctie niet verwijderen');
                }
            });
        }
    });
}

function review_done() {
    var all_reviewed = true;
    $("input[id='match_id']").each(function() {
        var id = $(this).attr('value')
        if ($('#txt_extra_measure_' + id).html() == "") {
            all_reviewed = false;
            $('#btn_extra_measure_' + id).css('background-color', '#c94e1e')
        }
    });
    if(all_reviewed) {
        bootbox.confirm("Bent u zeker dat u de controle wil beëindigen?", function (result) {
            if(result) {
                $("#form_review_done").submit();
            }
        });
    } else {
        bootbox.alert("Opgepast, nog niet alle leerlingen zijn gecontroleerd!");
    }
}

function do_at_ready() {
    // iterate over all matches and show extra-measure-controls when the extra_measure-textbox is not empty
    $("input[id='match_id']").each(function() {
        var id = $(this).attr('value')
        button_extra_measure_visible(id, ($('#txt_extra_measure_' + id).html() == ""));
    });
}
