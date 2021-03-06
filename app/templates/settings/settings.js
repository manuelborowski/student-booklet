var action_id;
var topic_subject;

$(document).ready(function(){
    $('#mdl_add_topic').on('hide.bs.modal', function (e) {
        if (document.activeElement.id == 'close_topic_modal') {
            window.location.href = Flask.url_for('settings.add_topic',
            {'subject': topic_subject, 'topic' : $("#mdl_topic_text").val()})
        }
    });

    $('#mdl_add_topic').on('shown.bs.modal', function() {
        $('#mdl_topic_text').focus();
    })


    $('#modal_import').on('hide.bs.modal', function (e) {
        if (document.activeElement.id == 'close_modal') {
            $('#' + action_id).click();
        }
    });

    $(".measure_topics").change(function(event) {
        data = {
            'id' : $(this).attr('id'),
            'status' : $(this).is(":checked")
        }
        $.getJSON(Flask.url_for('settings.set_topic_status', {'data' : JSON.stringify(data)}),
            function(data) {
                if(data.status) {
                } else {
                    bootbox.alert('Fout: kan instellingen niet bewaren');
                }
            }
        );
    });

    $('[data-toggle="tooltip"]').tooltip();

    $('input[name="txt-sim-day"]').datepicker(datepicker_options);
    $('input[name="select-date-from"]').datepicker(datepicker_options);
    $('input[name="txt-sim-hour"]').clockpicker({autoclose: true});
    var now = new Date();
    $("#select-date-from").val(now.getDate() + "-" + (now.getMonth() + 1) + "-" + now.getFullYear());

});


function confirm_before_delete(url) {
    var message = "Bent u zeker dat u dit van {{academic_year}} wilt wissen?"
    bootbox.confirm(message, function(result) {
        if (result) {
            window.location.href = Flask.url_for(url)
        }
    });
}


function select_academic_year(id) {
    action_id = id;
    $('#modal_import').modal();
}

function select_academic_year_and_valid_from(id) {
    action_id = id;
    $("#div-select-date-from").removeClass("default-hidden");
    $('#modal_import').modal();
}

function add_topic(subject) {
    topic_subject = subject;
    $('#mdl_add_topic').modal();
}

function submit_subject(subject, id){
    $('#save_subject').val(subject);
    select_academic_year(id);
}

function truncate_database_confirm(subject, id){
    bootbox.confirm("Bent u heel zeker dat u de database wil wissen?", function(result) {
        if (result) {
            $('#save_subject').val(subject);
            $('#' + id).click();
        }
    });
}