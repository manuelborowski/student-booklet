//row_id is filled in with the database id of the item (asset, purchase,...) at the moment the user rightclicks on a row
var row_id
//The metadata of the floating menu.  See tables_config.py
var floating_menu = JSON.parse('{{config.floating_menu|tojson}}');
//menu_id indicates what entry is clicked in the floating menu (edit, add, ...)
function handle_floating_menu(menu_id) {
    console.log(menu_id + ' : ' + row_id);
    for(var i=0; i < floating_menu.length; i++) {
        if(floating_menu[i].menu_id == menu_id) {
            if(floating_menu[i].flags.includes('confirm_before_delete_single_id')) {
                confirm_before_delete_single_id(row_id);
            } else if(floating_menu[i].flags.includes('id_required')) {
                window.location.href=Flask.url_for('{{config.subject}}.' + floating_menu[i].route, {'id':row_id});
            } else {
                window.location.href=Flask.url_for('{{config.subject}}.' + floating_menu[i].route);
            }
        }
    }
}

//Before removing an entry, a confirm-box is shown.
function confirm_before_delete_single_id(id) {
    var message = "Are you sure want to delete this " + '{{config.subject}}' + "?";
    if ('{{ config.delete_message }}') {message='{{ config.delete_message }}';}
    bootbox.confirm(message, function(result) {
        if (result) {
            window.location.href = Flask.url_for('{{config.subject}}' + ".delete", {'id' : id})
        }
    });
}

//Before removing multiple entries, a confirm-box is shown.
function confirm_before_delete() {
    var message = "Are you sure want to delete this " + '{{config.subject}}' + "?";
    if ('{{ config.delete_message }}') {message='{{ config.delete_message }}';}
    bootbox.confirm(message, function(result) {
        if (result) {
            document.getElementById('delete_form').submit();
            //window.location.href = Flask.url_for('{{config.subject}}' + ".delete")
        }
    });
}


$(document).ready(function() {
    //The clear button of the filter is pushed
    $('#clear').click(function() {
        $('.filter').val('');
        $('#teacher').val('');
        $('#classgroup').val('');
        //emulate click on trigger button
        $('#filter').trigger('click');
    });

    var filter_settings
    //Get content from localstorage and store in fields
    try {
        filter_settings = JSON.parse(localStorage.getItem("Filter"));
        $('#date_before').val(filter_settings['date_before']);
        $('#date_after').val(filter_settings['date_after']);
        $('#teacher').val(filter_settings['teacher']);
        $('#classgroup').val(filter_settings['classgroup']);
    } catch (err) {
    }

    //The filter button of the filter is pushed
    $('#filter').click(function() {
        //Store filter in localstorage
        filter_settings = {"date_before" : $('#date_before').val(),
                   "date_after" : $('#date_after').val(),
                   "teacher" : $('#teacher').val(),
                   "classgroup" : $('#classgroup').val()
                   };
        //alert(JSON.stringify(filter_settings));
        localStorage.setItem("Filter", JSON.stringify(filter_settings));
        table.ajax.reload();
    });

    //Configure datatable.
    var table = $('#datatable').DataTable({
       serverSide: true,
       stateSave: true,
       dom : 'fiptlBp',
       ajax: {
           url: '/{{config.subject}}/data',
           type: 'POST',
           data : function (d) {
               return $.extend( {}, d, filter_settings);
           }
       },
       pagingType: "full_numbers",
       lengthMenu: [20, 50, 100, 200],
       "buttons": [{extend: 'pdfHtml5', text: 'Exporteer naar PDF'}],
       "order" : [[1, 'asc']],
       "columns": [
       {% for h in config.template %}
            {% if h.name=='cb' %}
                {data: "{{h.data}}", width: "{{h.width}}", orderable: false},
            {% else %}
                {data: "{{h.data}}", width: "{{h.width}}"},
            {% endif %}
       {% endfor %}
       ],
       "language" : {
        /*"url" : "static/DataTables/nl_nl.lang"*/
        "url" : "//cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/Dutch.json"
      },
    });

     //flash messages, if required
     table.on( 'draw', function () {
        var j = table.ajax.json();
        $("#flash-list").html('');
        if(j.flash && j.flash.length) {
            var flash_string="";
            for(let s of j.flash) {
                flash_string += "<div class=\"alert alert-info\" role=\"alert\">" + s +"</div>";
            }
                $("#flash-list").html(flash_string);
        }
     });


    //right click on an item in the table.  A menu pops up to execute an action on the selected row/item
    var i = document.getElementById("menu").style;
    document.getElementById("datatable").addEventListener('contextmenu', function(e) {
        var posX = e.clientX;
        var posY = e.clientY;
        menu(posX, posY);
        e.preventDefault();
        row_id = $(e.target).closest('tr').prop('id');
    }, false);
    document.addEventListener('click', function(e) {
        i.opacity = "0";
        setTimeout(function() {i.visibility = "hidden";}, 1);
    }, false);

    // Get column index when right clicking on a cell
    //$('#datatable tbody').on( 'contextmenu', 'td', function () {
    //    column_id = table.cell( this ).index().column;
    //    console.log( 'Clicked on cell in visible column: '+column_id );
    //});


    function menu(x, y) {
      i.top = y + "px";
      i.left = x + "px";
      i.visibility = "visible";
      i.opacity = "1";
    }

    //date picker
    //Big hack to get dutch calendar to work... :-(
    $.fn.datepicker.dates['nl'] = {
        days : 'zondag_maandag_dinsdag_woensdag_donderdag_vrijdag_zaterdag'.split('_'),
        daysShort : 'zo._ma._di._wo._do._vr._za.'.split('_'),
        daysMin : 'zo_ma_di_wo_do_vr_za'.split('_'),
        months : 'januari_februari_maart_april_mei_juni_juli_augustus_september_oktober_november_december'.split('_'),
        monthsShort : 'jan_feb_maa_apr_mei_jun_jul_aug_sep_okt_nov_dec'.split('_'),
        today: "Vandaag",
        clear: "Clear",
        format: "dd-mm-yyyy",
        titleFormat: "MM yyyy", /* Leverages same syntax as 'format' */
        weekStart: 0
    };
    var date_after=$('input[name="date_after"]'); //our date input has the name "date_after"
    var date_before=$('input[name="date_before"]'); //our date input has the name "date_before"
    var container=$('.bootstrap-iso form').length>0 ? $('.bootstrap-iso form').parent() : "body";
    var options={
        language: 'nl',
        container: container,
        todayHighlight: true,
        autoclose: true,
    };
    date_after.datepicker(options);
    date_before.datepicker(options);

    //checkbox in header is clicked
    $("#select_all").change(function() {
        $(".cb_all").prop('checked', this.checked);
    });


});
