function drawVis(country){
    $.getJSON( '/en/roles/get_roles/'+country, function(data){

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



