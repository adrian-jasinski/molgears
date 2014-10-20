function set_option(val){
document.getElementById("crud_search_field").value=val;
document.selection.submit();
}
function set_confirm_option(val){
var answer = confirm("Confirm acition.");
if (answer){ 
    document.getElementById("crud_search_field").value=val;
    document.selection.submit();
}
}
function set_delete(){
var answer = confirm("Confirm action.");
if (answer){ 
    document.getElementById("crud_search_field").value="delete";
    document.selection.submit();
}
}

function set_deletefromlist(pname,tablename,listid){
var answer = confirm("Confirm action.");
if (answer){ 
	checkboxes = document.getElementsByName('select');
	var args="";
	for(var i=0; i<checkboxes.length;i++) {
		if(checkboxes[i].checked){
			args+="/"+checkboxes[i].value;
    }
}
var link = pname+"/"+tablename+"/deletefromlist/"+listid+args;
window.location.replace(link);
}
}
function set_reset()
{
document.getElementById("crud_search_field").value="";
document.selection.submit()
}

function create_list(table){
checkboxes = document.getElementsByName('select');
var args="";
for(var i=0; i<checkboxes.length;i++) {
    if(checkboxes[i].checked){
        args+="/"+checkboxes[i].value;
    }
}
var link = "/myaccount/addlist/"+table+args;
window.location.replace(link);
}

function add_to_list(listid, table){
checkboxes = document.getElementsByName('select');
var args="";
for(var i=0; i<checkboxes.length;i++) {
    if(checkboxes[i].checked){
        args+="/"+checkboxes[i].value;
    }
}
var link = "/myaccount/add_to_list/"+listid+"/"+table+args;
window.location.replace(link);
}

function add_to_orderlist(listid){
checkboxes = document.getElementsByName('select');
var args="";
for(var i=0; i<checkboxes.length;i++) {
    if(checkboxes[i].checked){
        args+="/"+checkboxes[i].value;
    }
}
var link = "/reagents/orders/add_to_list/"+listid+args;
window.location.replace(link);
}

function set_stability(pname){
checkboxes = document.getElementsByName('select');
var args="";
for(var i=0; i<checkboxes.length;i++) {
    if(checkboxes[i].checked){
        args+="/"+checkboxes[i].value;
    }
}
var link = pname+"/results/stability/results"+args;
window.location.replace(link);
}
function set_solubility(pname){
checkboxes = document.getElementsByName('select');
var args="";
for(var i=0; i<checkboxes.length;i++) {
    if(checkboxes[i].checked){
        args+="/"+checkboxes[i].value;
    }
}
var link = pname+"/results/solubility/read"+args;
window.location.replace(link);
}
function set_ppb(pname){
checkboxes = document.getElementsByName('select');
var args="";
for(var i=0; i<checkboxes.length;i++) {
    if(checkboxes[i].checked){
        args+="/"+checkboxes[i].value;
    }
}
var link = pname+"/results/ppb/results"+args;
window.location.replace(link);
}
