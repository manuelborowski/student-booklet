//Before removing an entry, a confirm-box is shown.
function confirm_before_delete(url) {
    var message = "Bent u zeker dat u dit wilt wissen?"
    bootbox.confirm(message, function(result) {
        if (result) {
            window.location.href = Flask.url_for(url)
        }
    });
}
