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
                    review_action(match_id, false);
                    $('#txt_extra_measure_' + match_id).text($('#modal_extra_measure').val());
                    $('#txt_extra_measure_' + match_id).fadeIn('fast');
                } else {
                    bootbox.alert('Fout: kan de extra sanctie niet toevoegen');
                }
            });
        }
    });
});

function review_action(mid, status) {
    if (status == 'default') {
        $('#btn_extra_measure_' + mid).css('display', 'inherit');
        $('#btn_delete_extra_measure_' + mid).css('display', 'none');
        $('#txt_extra_measure_' + mid).css('display', 'none');
    } else if (status == 'reviewed') {
        $('#btn_extra_measure_' + mid).css('display', 'none');
        $('#postpone-review-' + mid).css('display', 'none');
        $('#btn_delete_extra_measure_' + mid).css('display', 'inherit');
        $('#txt_extra_measure_' + mid).css('display', 'inherit');
    }
    else if (status == 'postponed') {
    }

}

function extra_measure(mid) {
    match_id = mid;
    $('#myModal').modal();
}

function postpone_review(mid) {
    $("#form_" + mid +  " table").css('display', "none");
    $("#postpone-label-" + mid).css("display", "inherit");
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
                    review_action(mid, true);
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
        review_action(id, ($('#txt_extra_measure_' + id).html() == ""));
    });
}
