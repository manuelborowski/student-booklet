//Convert python True/False to js true/false
var False = false;
var True = true;

//row_id is filled in with the database id of the item at the moment the user rightclicks on a row
var row_id
//The metadata of the floating menu.  See tables_config.py
var floating_menu = JSON.parse('{{config.floating_menu|tojson}}');
//menu_id indicates what entry is clicked in the floating menu (edit, add, ...)
function handle_floating_menu(menu_id) {
    console.log(menu_id + ' : ' + row_id);
    for(var i=0; i < floating_menu.length; i++) {
        if (floating_menu[i].menu_id == menu_id) {
            if (floating_menu[i].flags.includes('confirm_before_delete_single_id')) {
                confirm_before_delete_single_id(row_id);
            } else if (floating_menu[i].flags.includes('id_required')) {
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
    $(".cb_all").each(function(i){if (this.checked) {nbr_checked++;}});
    if (nbr_checked==0) {
        bootbox.alert("U hebt niets geselecteerd, probeer nogmaals");
        return false;
    } else {
        return true;
    }
}

{% if 'delete' in config.buttons %}
//Before removing multiple entries, a confirm-box is shown.
function confirm_before_delete() {
    if (is_checkbox_selected()) {
        var message = "Bent u zeker dat u dit wilt verwijderen?";
        if ('{{ config.delete_message }}') {message='{{ config.delete_message }}';}
        bootbox.confirm(message, function(result) {
            if (result) {
                busy_indication_on();
                document.getElementById('button_form').action = Flask.url_for("{{config.subject}}.{{config.delete_endpoint}}");
                document.getElementById('button_form').submit();
            }
        });
    }
}
{% endif %}

{% if 'add' in config.buttons %}
function add_item() {
    document.getElementById('button_form').action = Flask.url_for("{{config.subject}}.{{config.add_endpoint}}");
    document.getElementById('button_form').submit();
}
{% endif %}

{% if 'edit' in config.buttons %}
function edit_item() {
    if (is_checkbox_selected()) {
        document.getElementById('button_form').action = Flask.url_for("{{config.subject}}.{{config.edit_endpoint}}");
        document.getElementById('button_form').submit();
    }
}
{% endif %}

{% if 'start_check' in config.buttons %}
//Review starts
function start_review() {
    //window.location.href = Flask.url_for("remarks.start_review");
    document.getElementById('filter_form').action = Flask.url_for("{{config.subject}}.{{config.start_check_endpoint}}");
    document.getElementById('filter_form').submit();
}
{% endif %}



$(document).ready(function() {
        {% if 'academic_year' in filter %}
        $('#academic_year').change(function(){$('#filter').click();});
        {% endif %}
        {% if 'teacher' in filter %}
        $('#teacher').change(function(){$('#filter').click();});
        {% endif %}
        {% if 'grade' in filter %}
        $('#grade').change(function(){$('#filter').click();});
        {% endif %}
        {% if 'reviewed' in filter %}
        $('input[name=rbn_reviewed]:radio').change(function(){$('#filter').click();});
        {% endif %}


    //The clear button of the filter is pushed
    $('#clear').click(function() {
        $('.filter').val('');
        {% if 'academic_year' in filter %}
        $('#academic_year').val('{{filter_form.academic_year.default_academic_year}}');
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

    //The filter button of the filter is pushed
    $('#filter').click(function() {
        //Store filter in localstorage
        filter_settings = {
            {% if 'academic_year' in filter %}
            "academic_year" : $('#academic_year').val(),
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
           url: Flask.url_for("{{config.subject}}.{{config.data_endpoint}}"),
           type: 'POST',
           data : function (d) {
               return $.extend({}, d, filter_settings);
           }
       },
       pagingType: "full_numbers",
       {% if current_user.is_at_least_admin %}
       lengthMenu: [50, 100, 200, 500, 1000],
       {% else %}
       lengthMenu: [50, 100, 200],
       {% endif %}
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

        "createdRow": function(row, data, dataIndex) {
            if (data.overwrite_row_color != "") {
                $(row).attr("style", "background-color: " + data.overwrite_row_color + ";");
            }
        },

        "preDrawCallback": function(settings) {
            busy_indication_on();
        },
        "drawCallback": function(settings) {
            busy_indication_off();
        }

    });
    //$('#datatable').attr('data-page-length',50);

    {% if 'row_detail' in config %}

    //For an extra-measure, show the associated remarks as a sub-table
    var d_table_start = '<table cellpadding="5" cellspacing="0" border="2" style="padding-left:50px;">'
    var d_table_stop = '</table>'
    var d_header = '<tr><td>Datum</td><td>Leerling</td><td>LKR</td><td>KL</td><td>Les</td><td>Opmerking</td><td>Maatregel</td></tr>'
    var d_row    = '<tr><td>%s</td><td>{}</td><td>LKR</td><td>KL</td><td>Les</td><td>Opmerking</td><td>Maatregel</td></tr>'

    function format_row_detail(data) {
        s = d_table_start;
        s += d_header;
        if (data) {
            for (i=0; i < data.length; i++) {
                if (data[i].overwrite_row_color != "") {
                    s += '<tr style="background-color: ' + data[i].overwrite_row_color + '">';
                } else {
                    s += '<tr>'
                }
                s = s + '<td>' + data[i].date + '</td>';
                s = s + '<td>' + data[i].student.full_name + '</td>';
                s = s + '<td>' + data[i].teacher.code + '</td>';
                s = s + '<td>' + data[i].grade.code + '</td>';
                s = s + '<td>' + data[i].lesson.code + '</td>';
                s = s + '<td>' + data[i].subjects + '</td>';
                s = s + '<td>' + data[i].measures + '</td>';
                s += '</tr>'
            }
            s += d_table_stop;
            return s;
        }
       return 'Geen gegevens';
    }

    // Array to track the ids of the details displayed rows
    var detail_rows_cache = [];

    $('#datatable tbody').on('click', 'tr td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var idx = $.inArray(tr.attr('DT_RowId'), detail_rows_cache);

        if (row.child.isShown()) {
            tr.removeClass('details');
            row.child.hide();
            detail_rows_cache.splice(idx, 1);
        }
        else {
            var tx_data = {"id" : row.data().DT_RowId};
            $.getJSON(Flask.url_for('reviewed.get_row_detail', {'data' : JSON.stringify(tx_data)}),
                function(rx_data) {
                if (rx_data.status) {
                    row.child(format_row_detail(rx_data.details)).show();
                    tr.addClass('details');
                    if (idx === -1) {
                        detail_rows_cache.push(tr.attr('DT_RowId'));
                    }
                } else {
                    bootbox.alert('Fout: kan details niet ophalen');
                }
            });
        }
    });

    {% endif %}

    table.on('draw', function () {
    {% if 'row_detail' in config %}
        //Row details
        $.each(detail_rows_cache, function (i, id) {
            $('#'+id+' td.details-control').trigger('click');
        });
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
    //$('#datatable tbody').on('contextmenu', 'td', function () {
    //    column_id = table.cell(this).index().column;
    //    console.log('Clicked on cell in visible column: '+column_id);
    //});


    function menu(x, y) {
      i.top = y + "px";
      i.left = x + "px";
      i.visibility = "visible";
      i.opacity = "1";
    }

    //checkbox in header is clicked
    $("#select_all").change(function() {
        $(".cb_all").prop('checked', this.checked);
    });
    //busy_indication_on();
});
