//Convert python True/False to js true/false
var False = false;
var True = true;

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
    var message = "Are you sure want to delete this?";
    if ('{{ config.delete_message }}') {message='{{ config.delete_message }}';}
    bootbox.confirm(message, function(result) {
        if (result) {
            window.location.href = Flask.url_for('{{config.subject}}' + ".delete", {'id' : id})
        }
    });
}

//If one or more checkboxes are checked, return true.  Else display warning and return false
function is_checkbox_selected() {
    var nbr_checked = 0;
    $(".cb_all").each(function(i){if(this.checked) {nbr_checked++;}});
    if (nbr_checked==0) {
        bootbox.alert("U hebt niets geselecteerd, probeer nogmaals");
        return false;
    } else {
        return true;
    }
}

//Before removing multiple entries, a confirm-box is shown.
function confirm_before_delete() {
    if (is_checkbox_selected()) {
        var message = "Bent u zeker dat u dit wilt verwijderen?";
        if ('{{ config.delete_message }}') {message='{{ config.delete_message }}';}
        bootbox.confirm(message, function(result) {
            if (result) {
                document.getElementById('button_form').action = Flask.url_for('{{config.subject}}' + ".delete");
                document.getElementById('button_form').submit();
            }
        });
    }
}

//An remark is about to be edited
function edit_remarks() {
    if (is_checkbox_selected()) {
        document.getElementById('button_form').action = Flask.url_for('{{config.subject}}' + ".edit");
        document.getElementById('button_form').submit();
    }
}

//Review starts
function start_review() {
    //window.location.href = Flask.url_for("remarks.start_review");
    document.getElementById('filter_form').action = Flask.url_for("remarks.start_review");
    document.getElementById('filter_form').submit();
}



$(document).ready(function() {
    //The clear button of the filter is pushed
    $('#clear').click(function() {
        $('.filter').val('');
        {% if 'schoolyear' in filter %}
        $('#schoolyear').val('{{filter_form.schoolyear.default_schoolyear}}');
        {% endif %}
        {% if 'teacher' in filter %}
        $('#teacher').val('');
        {% endif %}
        {% if 'grade' in filter %}
        $('#grade').val('');
        {% endif %}
        {% if 'reviewed' in filter %}
        $('#rbn_reviewed_false').prop("checked", true);
        {% endif %}
        //emulate click on trigger button
        $('#filter').trigger('click');
    });

     var filter_settings
    //Get content from localstorage and store in fields
    try {
        filter_settings = JSON.parse(localStorage.getItem("Filter"));
        {% if 'schoolyear' in filter %}
        $('#schoolyear').val(filter_settings['schoolyear']);
        {% endif %}
        {% if 'teacher' in filter %}
        $('#teacher').val(filter_settings['teacher']);
        {% endif %}
        {% if 'grade' in filter %}
        $('#grade').val(filter_settings['grade']);
        {% endif %}
        {% if 'reviewed' in filter %}
        $('#rbn_reviewed_' + filter_settings['reviewed']).prop("checked", true);
        {% endif %}


    } catch (err) {
    }

    //The filter button of the filter is pushed
    $('#filter').click(function() {
        //Store filter in localstorage
        filter_settings = {
            {% if 'schoolyear' in filter %}
            "schoolyear" : $('#schoolyear').val(),
            {% endif %}
            {% if 'teacher' in filter %}
            "teacher" : $('#teacher').val(),
            {% endif %}
            {% if 'grade' in filter %}
            "grade" : $('#grade').val(),
            {% endif %}
            {% if 'reviewed' in filter %}
            "reviewed" : $('input[name=rbn_reviewed]:checked').val()
            {% endif %}
        };
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
       lengthMenu: [50, 100, 200],
       "buttons": [{extend: 'pdfHtml5', text: 'Exporteer naar PDF'}],
       "order" : [[1, 'desc']],
       "columns": [
       {% if 'row_detail' in config %}
        {
            "class":          "details-control",
            "orderable":      false,
            "data":           null,
            "defaultContent": "",
            "width": "1%"
        },
        {% endif %}
       {% for h in config.template %}
            {data: "{{h.data}}", width: "{{h.width}}", orderable: {{h.orderable}} },
       {% endfor %}
       ],
       "language" : {
        /*"url" : "static/DataTables/nl_nl.lang"*/
        "url" : "//cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/Dutch.json"
        },
        "initComplete": function(settings, json) { //intercept flash messages when the table is loaded
            if ('flash' in json) {
                bootbox.alert(json['flash'].toString());
            }
        },

    });
    //$('#datatable').attr('data-page-length',50);

    {% if 'row_detail' in config %}

    //For an extra-measure, show the associated remarks as a sub-table
    var d_table_start = '<table cellpadding="5" cellspacing="0" border="2" style="padding-left:50px;">'
    var d_table_stop = '</table>'
    var d_header = '<tr><td>Datum</td><td>Leerling</td><td>LKR</td><td>KL</td><td>Les</td><td>Opmerking</td><td>Maatregel</td></tr>'
    var d_row    = '<tr><td>%s</td><td>{}</td><td>LKR</td><td>KL</td><td>Les</td><td>Opmerking</td><td>Maatregel</td></tr>'

    function format ( d ) {
        s = d_table_start;
        s += d_header;
        for (i=0; i < d.remarks.length; i++) {
            s += '<tr>'
            s = s + '<td>' + d.remarks[i].date + '</td>';
            s = s + '<td>' + d.remarks[i].student.full_name + '</td>';
            s = s + '<td>' + d.remarks[i].teacher.code + '</td>';
            s = s + '<td>' + d.remarks[i].grade.code + '</td>';
            s = s + '<td>' + d.remarks[i].lesson.code + '</td>';
            s = s + '<td>' + d.remarks[i].subjects + '</td>';
            s = s + '<td>' + d.remarks[i].measures + '</td>';
            s += '</tr>'
        }
        s += d_table_stop;
        return s;
    }

    // Array to track the ids of the details displayed rows
    var detailRows = [];

    $('#datatable tbody').on( 'click', 'tr td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = table.row( tr );
        var idx = $.inArray( tr.attr('DT_RowId'), detailRows );

        if ( row.child.isShown() ) {
            tr.removeClass( 'details' );
            row.child.hide();

            // Remove from the 'open' array
            detailRows.splice( idx, 1 );
        }
        else {
            tr.addClass( 'details' );
            row.child( format( row.data() ) ).show();

            // Add to the 'open' array
            if ( idx === -1 ) {
                detailRows.push( tr.attr('DT_RowId') );
            }
        }
    } );

    {% endif %}

    table.on( 'draw', function () {
    {% if 'row_detail' in config %}
        //Row details
        $.each( detailRows, function ( i, id ) {
            $('#'+id+' td.details-control').trigger( 'click' );
        } );
    {% endif %}
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
