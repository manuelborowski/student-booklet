//Before removing an entry, a confirm-box is shown.
function confirm_before_delete(url) {
    var message = "Bent u zeker dat u dit van {{schoolyear}} wilt wissen?"
    bootbox.confirm(message, function(result) {
        if (result) {
            window.location.href = Flask.url_for(url)
        }
    });
}

var upload_type;
$('#mdl_select_schoolyear').on('hide.bs.modal', function (e) {
    if (document.activeElement.id == 'close_modal') {
        $('#' + upload_type).click();
    }
});

function upload_file(type) {
    upload_type = type;
    $('#mdl_select_schoolyear').modal();
}


