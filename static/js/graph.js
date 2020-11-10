

var FDL_Graph_Vis = function( svg_name, _graph_data ) {

    // Copy of the graph
    let g_data = _graph_data;

    // General Variables
    let svg = d3.select(svg_name);
    let svg_width  = $(svg_name).width();
    let svg_height = $(svg_name).height();

    // Variables specific to this function
    let svg_g = svg.append("g");
    let svg_txt = svg.append("g");



    let link = svg_g.append( "g" )
        .attr( "class", "links" )
        .selectAll( "line" )
        .data( g_data.links )
        .enter().append( "line" )
        .attr( "stroke-width", 1 )
        .attr( "stroke", "lightgray" );

    let node = svg_g.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(g_data.nodes).enter()
        .append("circle")
        .attr("r", 5 )
        .attr("fill", "black" )
        .attr('stroke','black')
        .attr('stroke-width','1px')
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended) );

    let simulation = d3.forceSimulation()
        .force( "link",   d3.forceLink().id( function(d) { return d.id; } ) )
        .force( "charge", d3.forceManyBody() )
        .force( "center", d3.forceCenter(svg_width / 2, svg_height / 2) )
        .nodes(g_data.nodes)
        .on("tick", ticked )
        //.on("end", function(){console.log("end")});

    simulation.force("link").links(g_data.links);

    let zoom_handler = d3.zoom().on("zoom", zoom_actions);
    zoom_handler(svg);


    function ticked() {
        link
            .attr("x1", d => d.source.x )
            .attr("y1", d => d.source.y )
            .attr("x2", d => d.target.x )
            .attr("y2", d => d.target.y );

        node
            .attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            } );
    }

    function clicked(d) {
        //document.getElementById("object_details").innerHTML = JSON.stringify(d, undefined, 2);
    }

    function dragstarted(d) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
        //document.getElementById("object_details").innerHTML = JSON.stringify(d, undefined, 2);
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        if (!d3.event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    function zoom_actions(){
        svg_g.attr("transform", d3.event.transform);
    }


    function zoom_to_fit(paddingPercent, transitionDuration) {
        let bounds = svg_g.node().getBBox();
        let midX = bounds.x + bounds.width / 2,
            midY = bounds.y + bounds.height / 2;

        if (bounds.width == 0 || bounds.height == 0) return; // nothing to fit

        let scale = (paddingPercent || 0.75) / Math.max(bounds.width / svg_width, bounds.height / svg_height);
        let translate = [svg_width / 2 - scale * midX, svg_height / 2 - scale * midY];

        let transform = d3.zoomIdentity
            .translate(translate[0], translate[1])
            .scale(scale);

        node
            .transition()
            .duration(transitionDuration || 0) // milliseconds
            .call(zoom_handler.transform, transform);
    }

    svg_txt.append("svg:image")
            .attr('x', svg_width-25)
            .attr('y', 5)
            .attr('width', 20)
            .attr('height', 20)
            .attr("xlink:href", "static/img/fit-to-width.png")
            .on("click",zoom_to_fit )


    return {
        update_node_radius : function( radius_func ){
            node.attr("r", radius_func );
        },

        update_link_width : function( width_func ){
            link.attr("stroke-width", width_func );
        },

        update_node_color : function( color_scheme, _func, _data=null ){
            //color_data = _color_data;
            if( _data == null ){
                _data = g_data.nodes
                ext = d3.extent( _data, _func )
                node.attr("fill", d => color_scheme( _func(d) ) );
            }
            else{
                ext = d3.extent( Object.keys(_data), _func );
                color_scheme.domain( ext );
                node.attr("fill", d => color_scheme( _func(_data[d.id]) ) );
            }
        },

        set_end_callback : function( cb ){
            simulation.on('end',cb)
        },

        restart_simulation : function(){
            simulation.alphaTarget(0).restart();
        },

        remove : function(){
            simulation.stop();
            svg_g.remove();
            svg_txt.remove();
        },

        add_count_labels : function(){
            svg_txt.append("text")
                .attr("x", svg_width-5 )
                .attr("y", svg_height-15 )
                .text(  g_data.nodes.length + " nodes")
                    .attr("font-family", "sans-serif")
                    .attr("text-anchor", "end")
                    .attr("font-size", "10px")
                    .attr("fill", "red");
            svg_txt.append("text")
                .attr("x", svg_width-5 )
                .attr("y", svg_height -5 )
                .text(  g_data.links.length + " edges")
                    .attr("font-family", "sans-serif")
                    .attr("text-anchor", "end")
                    .attr("font-size", "10px")
                    .attr("fill", "red");
        },

        zoomFit : function(paddingPercent, transitionDuration) {
            zoom_to_fit( paddingPercent, transitionDuration);
        },

        send_to_url : function(url){
            var xhr = new XMLHttpRequest();
            xhr.open("POST", url, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            tmp_data = {'nodes':g_data.nodes,'links':[]};
            g_data.links.forEach( function(L){
               tmp_data.links.push({'value':L.value,'source':L.source.id,'target':L.target.id});
            });
            xhr.send(JSON.stringify(tmp_data));
        }
    }

}

