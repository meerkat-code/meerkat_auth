function drawVis(country){
    $.getJSON( root + '/en/roles/get_roles/'+country, function(data){

        data = data.roles;
        console.log( 'Drawing vis');
        console.log( data );

        var roles = [];
        var lookup = {};
        var inherits = [];
        
        //Create the nodes, and index data by label in a lookup object.
        for(var i in data){
            roles.push({
                id: i,
                label: data[i].role,
            });
            lookup[data[i].role] = i;
        }

        //Create the relationships between parents and children.
        for( var j in data ){
            var roleID = lookup[data[j].role];
            var parents = data[j].parents;
            for(var k in parents){
                var parentID = lookup[ parents[k] ];
                inherits.push({
                    from: roleID,
                    to: parentID,
                    arrows: 'from'
                });
            }
        }

        console.log( lookup );
        console.log( roles );
        console.log( inherits );

        // create an array with nodes
        var nodes = new vis.DataSet(roles);

        // create an array with edges
        var edges = new vis.DataSet(inherits);

        // create a network
        var container = document.getElementById('role-vis');
        var graph = { nodes: nodes, edges: edges };
        var options = {
            physics:false,
            layout:{
                hierarchical:{
                    enabled: true,
                    direction: 'UD',
                    parentCentralization: true,
                    sortMethod: 'directed',
                    nodeSpacing: 200,
                    levelSeparation: 75,
                    treeSpacing: 200
                    
                }
            }
        };

        var network = new vis.Network(container,graph, options);

        //The click event gives the id of the node selected in a params object.
        network.on("click", function (params) {

            //Conveniently the id is just the index of the level in the data object.
            var selected = data[params.nodes[0]];
            var url = root + '/en/roles/get_all_access/' + selected.country + '/' + selected.role;
            
            console.log( selected );
            console.log( selected.description.trim() || "(No Description)" );

            //Get the selected access levels complete access list from the server.
            $.getJSON( url, function(all_access){

                //Get the complete role objects for the specified role's access list.
                var roles = [];
                all_access.access.map( function( level ){
                    if( level != selected.role ) roles.push( getObj( data, 'role', level )[0] );
                });

                //Now we have all the data, we can start displaying it. 
                var html = "<table class='selected col-xs-12 col-md-8 col-md-offset-2'>" +
                           "<tbody class='selected-level'>"+
                           "<tr><td colspan=2><label>Selected access level:</label></td></tr>" +
                           "<tr class='level'><td class='level__title col-xs-6 col-sm-3 col-md-2'><div>" +
                           caps(selected.role) + "</div></td>" + 
                           "<td class='level__description no-pad col-xs-6 col-sm-9 col-md-10'><div>" +
                           (selected.description.trim() || "(No Description)") + "</div></td></tr></tbody>";

                if( roles.length > 0 ){
                    html += "<tr><td colspan=2><label>Also inherits access levels:</label></td></tr>" +
                            "<tbody class='inherits'>";
                    for( var r in roles ){
                        html += "<tr class='level'><td class='level__title col-xs-6 col-sm-3 col-md-2'><div>" +
                                caps(roles[r].role) + "</div></td>" + 
                                "<td class='level__description no-pad col-xs-6 col-sm-9 col-md-10'><div>" +
                                (roles[r].description.trim() || "(No Description)") + 
                                "</div></td></tr>";                    
                    }
                }else{
                    html += "<tr><td colspan=2><label>Doesn't inherit any other access.</label></td></tr>" +
                            "<tbody class='inherits'>";  
                }
                html += "</tbody></table>";

                //Draw!
                $('.selection-details').html(html);

            });
        });
    });
}

function getObj( array, key, value ){
    return array.filter( function( element ) {
        return element[key] == value;
    });
}

function drawVisForm(){

    var html = "<form id='access-network-form'>";

    html += "<div class='input-group row'>";
    html += "<label class='country-select'>" + i18n.gettext( "Country:" ) + "</label>" +
            "<select id='country-select' class='country-select'>";
    
    var countries = Object.keys(user.acc);

    for( var i in countries){
        country = countries[i];
        html += "<option value='" + country + "' ";
        if( i === 0 ) html += "selected";
        html += ">" + caps( country ) + "</option>";
    }

    html += "</select></div>";
    
    html += "</form>";

    $('.access-network-form').html( html );

    drawVis( $('#country-select').val() );

    $('#country-select').change(function(){
        drawVis( $('#country-select').val() );
    });
    
}



