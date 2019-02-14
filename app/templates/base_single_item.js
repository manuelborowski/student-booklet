function init_up_download(_file_type, _subject) {
    var file_el = _file_type + '_fileid';
    var upload_el = _file_type + '_upload';
    var download_el = _file_type + '_download';
    var fd = document.getElementById(file_el);
    console.log('at document ready : file_el ' + fd.id);

    {% if role == "edit" %}
        //The actual filedialog element is hidden because it does not blend in with the bootstrap css.
        //Pushing the bootstrap-upload button generates a click-event on the filedialog element
        document.getElementById(upload_el).addEventListener('click', function() {fd.click();});
    {% endif %}
    document.getElementById(download_el).addEventListener('click', download);


    //Called when the filedialog closes
    fd.addEventListener('change', function() {
        var _select = document.getElementById(_file_type);
         for(var i=0; i < _select.options.length; i++) {
            if (_select.options[i].value == fd.files[0].name) {
                toastr.error('Bestand "' + fd.files[0].name + '" bestaat reeds, kies een ander');
                fd.value="";
                return;
            }
        }
        var option = document.createElement("option");
        option.text = fd.files[0].name;
        _select.add(option, 0);
        _select.selectedIndex = "0";
     });

    //To download the file, jump to the download url with the filename as parameter
    function download() {
        var _file = document.getElementById(_file_type).value;
        window.location.href = Flask.url_for(_subject + ".download", {'type' : this.id,'file' : _file});
    }
}

$(document).ready(function() {
});