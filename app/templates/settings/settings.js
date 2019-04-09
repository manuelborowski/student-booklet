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


    $('#mdl_select_schoolyear').on('hide.bs.modal', function (e) {
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

});


//Before removing an entry, a confirm-box is shown.
function confirm_before_delete(url) {
    var message = "Bent u zeker dat u dit van {{schoolyear}} wilt wissen?"
    bootbox.confirm(message, function(result) {
        if (result) {
            window.location.href = Flask.url_for(url)
        }
    });
}


function select_schoolyear(id) {
    action_id = id;
    $('#mdl_select_schoolyear').modal();
}


function add_topic(subject) {
    topic_subject = subject;
    $('#mdl_add_topic').modal();
}

function submit_subject(subject, id){
    $('#save_subject').val(subject);
    select_schoolyear(id);
}
