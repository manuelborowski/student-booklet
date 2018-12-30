//Before removing an entry, a confirm-box is shown.
function confirm_before_delete(url) {
    var message = "Bent u zeker dat u dit van {{schoolyear}} wilt wissen?"
    bootbox.confirm(message, function(result) {
        if (result) {
            window.location.href = Flask.url_for(url)
        }
    });
}


function import_students() {
    if ({{ students_already_in_database|lower }}) {
        bootbox.confirm("Er zijn al leerlingen van {{schoolyear}} in de database, wilt u verder gaan?", function(result) {
            if (result) {
                $('#import_fileid').click();
            }
        });
    } else {
        $('#import_fileid').click();
    }
}

function import_timetable() {
    if ({{ timetable_already_in_database|lower }}) {
        bootbox.confirm("Er is al een lesrooster van {{schoolyear}} in de database, wilt u verder gaan?", function(result) {
            if (result) {
                $('#import_fileid3').click();
            }
        });
    } else {
        $('#import_fileid3').click();
    }
}
