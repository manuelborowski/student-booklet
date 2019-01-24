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

function edit_offences() {
    if (is_checkbox_selected()) {
        document.getElementById('button_form').action = Flask.url_for('{{config.subject}}' + ".edit");
        document.getElementById('button_form').submit();
    }
}

function start_review() {
    document.getElementById('button_form').action = Flask.url_for("review.start_review");
    document.getElementById('button_form').submit();
}



$(document).ready(function() {
    //The clear button of the filter is pushed
    $('#clear').click(function() {
        $('.filter').val('');
        $('#teacher').val('');
        $('#classgroup').val('');
        $('#rbn_reviewed_false').prop("checked", true);
        //emulate click on trigger button
        $('#filter').trigger('click');
    });

     var filter_settings
//    //Get content from localstorage and store in fields
//    try {
//        filter_settings = JSON.parse(localStorage.getItem("Filter"));
//        $('#date_before').val(filter_settings['date_before']);
//        $('#date_after').val(filter_settings['date_after']);
//        $('#teacher').val(filter_settings['teacher']);
//        $('#classgroup').val(filter_settings['classgroup']);
//        $('#rbn_reviewed_' + filter_settings['reviewed']).prop("checked", true);
//
//
//    } catch (err) {
//    }

    //The filter button of the filter is pushed
    $('#filter').click(function() {
        //Store filter in localstorage
        filter_settings = {"date_before" : $('#date_before').val(),
                   "date_after" : $('#date_after').val(),
                   "teacher" : $('#teacher').val(),
                   "classgroup" : $('#classgroup').val(),
                   "reviewed" : $('input[name=rbn_reviewed]:checked').val()
                   };
//        localStorage.setItem("Filter", JSON.stringify(filter_settings));
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
       "order" : [[1, 'desc']],
       "columns": [
        {
            "class":          "details-control",
            "orderable":      false,
            "data":           null,
            "defaultContent": "",
            "width": "1%"
        },

       {% for h in config.template %}
            {data: "{{h.data}}", width: "{{h.width}}", orderable: {{h.orderable}} },
       {% endfor %}
       ],
       "language" : {
        /*"url" : "static/DataTables/nl_nl.lang"*/
        "url" : "//cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/Dutch.json"
      },
    });

    var d_table_start = '<table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">'
    var d_table_stop = '</table>'
    var d_header = '<tr><td>Datum</td><td>Leerling</td><td>LKR</td><td>KL</td><td>Les</td><td>Opmerking</td><td>Maatregel</td></tr>'
    var d_row    = '<tr><td>%s</td><td>{}</td><td>LKR</td><td>KL</td><td>Les</td><td>Opmerking</td><td>Maatregel</td></tr>'

    function format ( d ) {
        s = d_table_start;
        s += d_header;
        for (i=0; i < d.offences.length; i++) {
            s += '<tr>'
            s = s + '<td>' + d.offences[i].date + '</td>';
            s = s + '<td>' + d.offences[i].student.full_name + '</td>';
            s = s + '<td>' + d.offences[i].teacher.code + '</td>';
            s = s + '<td>' + d.offences[i].classgroup.name + '</td>';
            s = s + '<td>' + d.offences[i].lesson.name + '</td>';
            s = s + '<td>' + d.offences[i].types + '</td>';
            s = s + '<td>' + d.offences[i].measures + '</td>';
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

        //Row details
        $.each( detailRows, function ( i, id ) {
            $('#'+id+' td.details-control').trigger( 'click' );
        } );

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
