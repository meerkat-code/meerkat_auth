function drawUserTable(){
    //Get all users from the database.
    //$.getJSON( '/en/users/get_users', function(data){
       
        //Display the data in a bootstrap table
        var columns = [{
                'field': 'state',
                'checkbox': true,
                'align': 'center',
                'valign': 'middle'
            },{
                'field': "username",
                'title': i18n.gettext('Username'),
                'align': "left",
                'class': "header",
                'sortable': true,
                'width': "25%"
            },{
                'field': "email",
                'title': i18n.gettext('Email'),
                'align': "left",
                'class': "header",
                'sortable': true,
                'width': "25%"
            },{
                'field': "access",
                'title': i18n.gettext('Access'),
                'align': "left",
                'class': "header",
                'sortable': false,
                'width': "25%"
            },{
                'field': "creation",
                'title': i18n.gettext('Account Creation'),
                'align': "left",
                'class': "header",
                'sortable': false,
                'visible': true,
                'width': "25%"
            },{
                'field': "data",
                'title': i18n.gettext('Data'),
                'align': "left",
                'class': "header",
                'sortable': false,
                'visible': false,
                'searchable': true,
                'width': "25%"
            }         
        ];

        function prepData(res){
            for( var a in res.rows ){
                //Format the access to make it more visually appearing
                access = "";
                var row = res.rows[a];
                for( var b in row.countries ){
                    access += caps(row.countries[b]) + "-" + caps(row.roles[b]) + " | ";
                }
                row.access = access.slice(0, -3);

                //Format the data to make it searchable
                data = "";
                if( typeof(row.data) != "object" ){
                    console.error("Bad user data - not an object.");
                    row.data = {};
                } 
                var keys = Object.keys( row.data );
                for(var c in keys){
                    var element = row.data[keys[c]];
                    data += caps(keys[c]) + ": " + caps( element.val ) + " | ";
                }
                row.data = data.slice(0,-3);
            }
            return res.rows;
        }
        
        table = $('#user-table table').bootstrapTable({
            columns: columns,
            classes: 'table table-no-bordered table-hover',
            pagination: true,
            pageSize: 20,
            search: true,
            url:'/en/users/get_users',
            responseHandler: prepData,
            showRefresh: true
        });

        //Insert data into editor when clicking upon a row.
        $('#user-table table').on('click-row.bs.table', function (row, $element, field) {
            drawUserEditor($element.username);
        });

        //Add extra toolbar buttons
        var buttons = "<div class='btn-group  pull-right table-custom-toolbar'>" + 
            "<button class='btn highlight delete-users' type='button'>" +
            "<span class='glyphicon glyphicon-trash'/></button>" +
            "<button class='btn blue new-user' type='button'>" +
            "<span class='glyphicon glyphicon-plus'/></button>" +
            "</div>";

        $('.fixed-table-toolbar').append(buttons);

        $('button.new-user').click( function(){
            drawUserEditor("");
        });

        $('button.delete-users').click( function(){
          
            var selected = $('#user-table table').bootstrapTable('getSelections');
            var usernames = [];
            var confirmString = i18n.gettext("Are you sure you want to delete the following users?") + 
                "\n";
            for( var user in selected ){
                usernames.push( selected[user].username );
                confirmString = confirmString + selected[user].username + ", ";
            }
            if( usernames.length > 0 ){
                if( confirm(confirmString.slice(0, -2)) ){
                    //Post json to server.
                    $.ajax({
                        url: '/en/users/delete_users',
                        type: 'post',
                        success: function (data) {
                            alert(data);
                            $('#user-table table').bootstrapTable('refresh');
                        },
                        error: function (data) {
                            alert( i18n.gettext( "There has been a server error. " +
                                   "Please contact administrator and try again later." ) );
                            $('.user-editor .submit-form').text( buttonText );
                        },
                        contentType: 'application/json;charset=UTF-8',
                        data: JSON.stringify(usernames, null, '\t')
                    });
                    drawUserEditor("");
                }
            }
        });

    //});

}

function drawUserEditor(username){
    
    $.getJSON( '/en/users/get_user/' + username, function(data){

        console.log( data );

        var html = "<form id='user-editor' class='user-editor'>";
        
        html += "<div class='row top-part'><div class='col-xs-12 col-sm-6 col-md-4'>";

        html += "<div class='input-group row'>" + 
                "<label class='username  col-xs-12 col-md-6 col-lg-5'>" + i18n.gettext("Username:") + 
                "</label><input type='text' class='username col-xs-12 col-md-6 col-lg-7' " +
                "name='username' value='" + data.username + "' id='username' " +
                "oninput='checkValidUsername()' /></div>";

        html += "<div class='input-group row'>" +
                "<label class='email  col-xs-12 col-md-6 col-lg-5'>" + 
                i18n.gettext("Email:") + "</label>" + 
                "<input id='email' type='text' class='email col-xs-12 col-md-6 col-lg-7' " +
                "oninput='checkEqual(\"email\", \"email2\")' name='email' value='" + 
                data.email + "'/></div>";

        html += "<div class='input-group row'>" + 
                "<label class='email2 col-xs-12 col-md-6 col-lg-5'>" + 
                i18n.gettext("Retype Email:") + "</label>" + 
                "<input  id='email2' type='text' oninput='checkEqual(\"email\", \"email2\")' " +
                "class='email2 col-xs-12 col-md-6 col-lg-7' value='" + 
                data.email + "'/></div>";

        html += "<div class='input-group row'>" + 
                "<label class='password col-xs-12 col-md-6 col-lg-5'>" + 
                i18n.gettext("Password:") + "</label>" + 
                "<input id='password' oninput='checkEqual(\"password\", \"password2\")' " + 
                "type='password' class='password col-xs-12 col-md-6 col-lg-7' " +
                "name='password' value=''/></div>";

        html += "<div class='input-group row'>" + 
                "<label class='password2 col-xs-12 col-md-6 col-lg-5'>" + 
                i18n.gettext("Retype Password:") + "</label>" + 
                "<input id='password2' oninput='checkEqual(\"password\", \"password2\")' " +
                "type='password' class='password2 col-xs-12 col-md-6 col-lg-7' "+
                "value=''/></div>";

        html += "<div class='input-group row'>" + 
                "<label class='creation col-xs-12 col-md-6 col-lg-5'>" +
                i18n.gettext("Creation time:") + "</label>" + 
                "<input type='text' readonly class='creation col-xs-12 col-md-6 col-lg-7' value='" + 
                data.creation + "' name='creation' /></div>";

        html += "<div class='input-group row'>" + 
                "<label class='updated col-xs-12 col-md-6 col-lg-5'>" + 
                i18n.gettext("Last update:") + "</label>" + 
                "<input type='text' readonly class='updated col-xs-12 col-md-6 col-lg-7' value='" + 
                data.updated + "'/></div>";

        html += "</div>";

        //Now create the access editor.
        html += "<div class='col-xs-12 col-sm-6 col-md-4'>";

        html += "<div class='form-section clearfix'> <div class='section-title'> " + 
                i18n.gettext("Add New Access") + " </div>";

        html += "<div class='input-group row'>" + 
                "<label class='country col-xs-12 col-md-6 col-lg-5'>" +
                i18n.gettext("Country:") + "</label>" + 
                "<select class='country col-xs-12 col-md-6 col-lg-7' >";

        var countries = Object.keys(user.acc);
        for( var i in countries){
            country = countries[i];
            html += "<option value='" + country + "' ";
            if( i === 0 ) html += "selected";
            html += ">" + caps( country ) + "</option>";
        }
                                    
        html += "</select></div>";

        html += "<div class='input-group row'>" + 
                "<label class='role col-xs-12 col-md-6 col-lg-5'>" + 
                i18n.gettext("Access Role:") + "</label>" + 
                "<select class='role col-xs-12 col-md-6 col-lg-7'>";

        function drawAvailableRoles(country){
            console.log(country);
            var roles = user.acc[country];
            console.log( roles );
            var optionsHTML = "";
            for( var j in roles){
                role = roles[j];
                optionsHTML += "<option value='" + role + "' ";
                if( j === 0 ) optionsHTML += "selected";
                optionsHTML += ">" + caps( role ) + "</option>";
            }
            $('select.role').html( optionsHTML );
        }
                                    
        html += "</select></div>";

        html += "<button class='btn btn-sm pull-right add-access' type='button'>" +
                i18n.gettext("Add Access") + "</button>";

        html += "</div>"; //End of form section

        html += "<div class='input-group'><label class='access col-xs-12'>" +
                i18n.gettext("Select Current Access:") + "</label>";

        html += "<select multiple class='access-levels col-xs-12'>";

        //Factorise this bit out so that we can redraw the options once access has been updated.
        function drawAccessOptions(){
            var optionsHTML = "";
            console.log( data.countries );
            for( var k in data.countries ){
                console.log( k );
                country = data.countries[k];
                role = data.roles[k];
                optionsHTML += "<option country='" + country + "' role='" + role + "' value='" + k + "' " ;
                if( countries.indexOf( country ) == -1 ) optionsHTML += "disabled";
                optionsHTML += ">" + caps( country ) + " | " + caps( role ) + "</option>";
            }
            $('select.access-levels').html( optionsHTML );
        }

        html += "</select>";

        html += "<button type='button' class='btn btn-sm pull-right delete-access' >" +
                i18n.gettext("Delete Access") + "</button>";

        html += "</div></div>"; //End of input group and end of middle part.

        //Now create the data editor.
        html += "<div class='col-xs-12 col-sm-6 col-md-4'>";

        html += "<div class='form-section clearfix'> <div class='section-title'>" + 
                i18n.gettext("Edit Data") + "</div>";

        html += "<div class='input-group row'>" +
                "<label class='dataKey col-xs-12 col-md-6 col-lg-5'>Data Key:</label>" + 
                "<input type='text' class='dataKey col-xs-12 col-md-6 col-lg-7'/></div>";

        html += "<div class='input-group row'>" +
                "<label class='dataValue col-xs-12 col-md-6 col-lg-5'>" + 
                i18n.gettext("Data Value:") + "</label>" + 
                "<input type='text' class='dataValue col-xs-12 col-md-6 col-lg-7'/></div>";

        html += "<button class='btn btn-sm pull-right add-data' type='button' >" + 
                i18n.gettext("Add Data") + "</button>";

        html += "</div>"; //End of form section

        html += "<div class='input-group reset-data'><label class='data col-xs-12'>" + 
                i18n.gettext("Select Current Data:") + "</label>";

        html += "<select multiple class='data-elements col-xs-12'>";
        
        //Factorise this bit out so that we can redraw the options once data has been updated.
        function drawDataOptions(){
            var optionsHTML = "";
            var dataKeys = Object.keys(data.data);
            for( var x in dataKeys ){
                var element = data.data[dataKeys[x]];

                if( element.status != "uneditable" ){
                    optionsHTML += "<option dataKey='" + dataKeys[x] + "' dataValue='" + element.val + "' ";
                    if( element.status == "undeletable" ) optionsHTML += "disabled datastatus='undeletable' ";
                    optionsHTML += ">" + dataKeys[x] + " | " + element.val + "</option>";
                }
            }
            $('select.data-elements').html( optionsHTML );
        }

        html += "</select>";

        html += "<button class='btn btn-sm pull-right delete-data' type='button'>" +
                i18n.gettext("Delete Data") + "</button>";

        html += "</div></div></div>"; //End of input group and end of final part and end of row.

        html += "<input type='hidden' class='original_username' name='original_username' value='" +
                data.username + "' />";

        html += "<input type='hidden' class='original_password' name='original_password' value='" + 
                data.password + "' />";

        state = data.state !== "" ? data.state : "new";

        html += "<input type='hidden' class='state' name='state' value='" + state + "' />";

        html += "<div class='form-messages col-xs-12 col-sm-6'> </div>";

        buttonText = username === "" ? i18n.gettext("Create User") : i18n.gettext("Submit Changes");

        html += "<button type='button' class='col-xs-12 col-sm-6 btn btn-large submit-form pull-right'>"+
                buttonText + "</button>";

        html += "</form>";

        //DRAW THE FORM
        $('.user-editor').html( html );

        //Add dynamic links across the form
        //---------------------------------
        
        //HANDLE DATA EDITING.

        drawDataOptions();

        //Update the data elements shown in the multi-select box.
        function updateData(){
            //Re draw the data
            drawDataOptions();

            //Fill in data element values when clicking on a data element in select box.
            $('.data-elements option').click( function(e){

                $('input.dataKey').attr('disabled','disabled');
                $('input.dataKey').val($(this).attr("dataKey"));
                $('input.dataValue').val($(this).attr("dataValue"));
                $('button.add-data').text(i18n.gettext('Edit Data'));
                e.stopPropagation();

            });
        }

        //Refactorisation of the code required to reset the data editor.
        function resetData(){
            $('input.dataKey').removeAttr('disabled');
            $('input.dataKey').val("");
            $('input.dataValue').val("");
            $('button.add-data').text(i18n.gettext('Add Data'));
        }

        updateData();

        //Reset values to empty for adding new data when clicking outside select box.
        $('.reset-data').click( function(){ reset(); });

        //Add the new data element when clicking on the add data value.
        $('button.add-data').click( function(){
            key = $('input.dataKey').val();
            val = $('input.dataValue').val();
            if( key && val ){
                if( data.data.hasOwnProperty( key ) ){
                    data.data[key].val = val;
                }else{
                    data.data[key] = { "val": val };
                }
                resetData();
                updateData();
            }
        });   

        //Delete selected data when clicking the delete button.
        $('button.delete-data').click( function(e){

            //Assemble a list of keys for data tot be deleted.
            var keys = [];
            $('select.data-elements option:selected').each( function(){
                keys.push( $(this).attr('dataKey') );
            });

            //Only delete if some data is actually select.
            if( keys.length > 0 ){

                //Create a confirm dialouge showing the user what data they are about to delete.
                var confirmString = i18n.gettext("Are you sure you want to delete this data?") +
                                    "\n";
                for (var y in keys){
                    var key = keys[y];    
                    confirmString += "     " + key + " | " + data.data[key].val + "\n";
                }

                //If the user confirms, actually do the deletion.
                if( confirm( confirmString ) ){
                    for( var z in keys ) delete data.data[keys[z]];
                    updateData();
                }
                resetData();
            }
            //Stop rest kicking in if no deletion happens.
            e.stopPropagation();
        }); 

        //HANDLE ACCESS LEVELS

        drawAccessOptions();
        drawAvailableRoles($('select.country').val());
        
        $('select.country').change(function(){
            drawAvailableRoles($('select.country').val());
        });
        

        //Add the new access element when clicking on the add access value.
        $('button.add-access').click( function(){
            country = $('select.country').val();
            role = $('select.role').val();
            if( country && role ){
                data.countries.push( country );
                data.roles.push( role );
                drawAccessOptions();
            }
        });   

        //Delete selected access when clicking the delete button.
        $('button.delete-access').click( function(e){

            //Assemble a list of indicies for access to be deleted.
            var indicies = [];
            $('select.access-levels option:selected').each( function(){
                indicies.push( $(this).val() );
            });

            //Only delete if some access is actually select.
            if( indicies.length > 0 ){

                //Create a confirm dialouge showing the user what access they are about to delete.
                var confirmString = i18n.gettext("Are you sure you want to delete this access?") +
                                    "\n";
                for( var y in indicies ){ 
                    country = data.countries[indicies[y]];
                    role = data.roles[indicies[y]]; 
                    confirmString += "     " + country + " | " + role + "\n";
                }

                //If the user confirms, actually do the deletion.
                if( confirm( confirmString ) ){
                    for( var z in indicies ){
                        delete data.countries[ indicies[z] ];  //Will not reindex array.
                        delete data.roles[ indicies[z] ];  //Will not reindex array.
                    }
                    data.countries = cleanArray( data.countries );
                    data.roles = cleanArray( data.roles );
                    drawAccessOptions();
                }
                
            }
            
        });       

        //FORM SUBMISSION
        $('.user-editor .submit-form').click(function(){

            $('.user-editor .submit-form').html( i18n.gettext("Working" ) + 
                                                 " <div class='loading'></div>" );

            //Assemble complete json object.
            var data = {};
            var form = $('.user-editor');
            var formArray = form.serializeArray();

            for( var z in formArray ){
                var element = formArray[z];
                data[element.name] = element.value;
            }

            $.extend( data, extractAccess() );
            $.extend( data, extractData() );
            console.log( data );

            //Post json to server.
            $.ajax({
                url: '/en/users/update_user/' + data.original_username,
                type: 'post',
                success: function (data) {
                    alert(data);
                    drawUserEditor("");
                    $('#user-table table').bootstrapTable('refresh');
                },
                error: function (data) {
                    alert( i18n.gettext("There has been a server error. " + 
                                        "Please contact administrator and try again later.") );
                    $('.user-editor .submit-form').text( buttonText );
                    $('#user-table table').bootstrapTable('refresh');
                },
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify(data, null, '\t')
            });
        });

    });

}

//Reindexes an array with undefined values in it. 
function cleanArray( array ){
    first = array.shift();
    if( array.length === 0 ) return first === undefined ? [] : [first];
    else if( first === undefined ) return cleanArray( array );
    else return [first].concat( cleanArray( array ) );
} 

//Captitalise the first letter of each word.    
function caps(str){
    return str.replace(/\w\S*/g, function(txt){
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}

//Check that two form fields are equal
function checkEqual( id1, id2 ) {

    var email1 = document.getElementById(id1);
    var email2 = document.getElementById(id2);

    if ( email2.value != email1.value ) {
        email2.setCustomValidity( i18n.gettext('Fields must be Matching.') );
        return false;
    } else {
        //Input is valid -- reset the error message
        email2.setCustomValidity('');
        return true;
    }
}

//Check that the usernamE field is valid.
function checkValidUsername(){
    
    var original = $('.user-editor input.original_username').val();
    var current = $('.user-editor input.username').val();
    var element = document.getElementById('username');

    if( current != original ){
        $.getJSON( '/en/users/check_username/' + current, function( data ){
            if( !data.valid ){
                element.setCustomValidity( 
                    i18n.gettext("Invalid username.  Username already exists." )
                );
            }else{
                element.setCustomValidity( "" );
            }   
        });
    }
}


function extractAccess(){

    var countries = [];
    var roles = [];

    $('select.access-levels option').each( function(){
        countries.push( $(this).attr('country') );
        roles.push( $(this).attr('role') );
    });

    return {
        'countries':countries,
        'roles':roles
    };
}

function extractData(){

    var data = {};

    $('select.data-elements option').each( function(){
        obj = { "val": $(this).attr('datavalue') };
        if( $(this).attr('datastatus') ) obj.status = $(this).attr('datastatus');
        data[$(this).attr('datakey')] = obj;
    });

    return {'data':data};
}

