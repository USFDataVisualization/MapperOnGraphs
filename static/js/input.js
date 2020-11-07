
function generate_checkbox(id, label, onclick='', width=-1){

    _html = ''
    _html += '<div class="btn-group-toggle" data-toggle="buttons">';
    _html += '<label class="btn btn-outline-secondary" '
    if( width > 0 ) _html += 'style="width:' + width + 'px;" '
    _html += '>'
    _html += '<input type="checkbox" id="'+id+'" name="'+id+'" autocomplete="off" onclick="toggle_button(this);'+onclick+'">'+label+'</label><br>'
    _html += '</div>'

    return {
        getHTML : function(){return _html},
        isChecked : function(){ return document.getElementById(id).checked; }
    }
}

function generate_radiogroup(name, options, onchange='', width=-1){
    _html = ''
    _html += '<div class="btn-group-toggle" data-toggle="buttons">';
    options.forEach(L=>{
        if(('checked' in L) && L.checked)
            _html += '<label class="btn btn-primary" '
        else
            _html += '<label class="btn btn-outline-secondary" '
        if( width > 0 ) _html += 'style="width:' + width + 'px;" '
        _html += '>'
        _html += '<input type="radio" id="'+name+'" name="'+name+'" autocomplete="off" value="'+L.value+'" '
                    + ((('checked' in L) && L.checked)?'checked ':'')
                    + 'onchange="toggle_radio(this);'+onchange+'">'+L.label+'</label><br>'
    })
    _html += '</div>'

    return {
        getHTML : function(){return _html},
        getSelected : function(){
            let sel = null;
            document.getElementsByName(name).forEach( E=>{
                if( E.checked ) sel = E.value;
            })
            return sel;
        }
    };
}

function toggle_button(obj){
    if(obj.checked)
        obj.parentElement.className = "btn btn-primary"
    else
        obj.parentElement.className = "btn btn-outline-secondary"
}

function toggle_radio(obj){
    document.getElementsByName(obj.name).forEach( R => {
        if(R.checked)
            R.parentElement.className = "btn btn-primary"
        else
            R.parentElement.className = "btn btn-outline-secondary"
    })
}