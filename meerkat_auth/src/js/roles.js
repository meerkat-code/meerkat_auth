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
                level: data[i].ranking
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
            layout:{
                hierarchical:{
                    enabled: true,
                    direction: 'UD',
                    //parentCentralization: true,
                    sortMethod: 'directed',
                    nodeSpacing: 50,
                    levelSeparation: 50
                    
                }
            }
        };
        var network = new vis.Network(container,graph, options);

    });
}


