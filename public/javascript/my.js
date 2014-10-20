var smiles = "";
var jme = "0 0";

function startEditor() {
  // Start JSME Editor
  // smiles = document.form.smiles.value;
  smiles = document.getElementsByName('smiles')[0].value;
  window.open('/jsme/' + smiles,'JME','width=700,height=790,scrollbars=yes,resizable=yes');
}
function fromEditor2(smiles,jme) {
  // this function is called from jme_window
  // editor fills variable smiles & jme
  if (smiles=="") {
    alert ("no molecule submitted");
    return;
  }
  document.selection.smiles.value = smiles; 
}

function saveJMECookie() {
  var jme = document.JME.jmeFile();
  document.cookie = "jme="+jme+";expires=Thu, 31 Dec 2020 00:00:00 GMT; path=/";
}

function readJMECookie() {
  var editor = document.JME;
  if (editor.smiles().length > 0) return; // editing already started
  var ca = document.cookie.split(';');
  for(var i=0;i < ca.length;i++) {
    var c = ca[i];
    while (c.charAt(0)==' ') c = c.substring(1,c.length);
    if (c.indexOf("jme=") == 0) {
      var jme = c.substring(4,c.length);
      //alert("jme="+jme);
      editor.readMolecule(jme);
      return;
    }
  }
}

function clearForm(oForm) {
  var elements = oForm.elements; 
  oForm.reset();
  for(i=0; i<elements.length; i++) {
	field_type = elements[i].type.toLowerCase();
	switch(field_type) {
	
		case "text": 
		case "password": 
		case "textarea":
	        case "hidden":	
			
			elements[i].value = ""; 
			break;
        
		case "checkbox":
  			if (elements[i].checked) {
   				elements[i].checked = false; 
			}
			break;

		case "select-one":
		case "select-multi":
            		elements[i].selectedIndex = 0;
			break;

		default: 
			break;
	}
    }
}

function ChangeMe(box,theId) {
   if(document.getElementById(theId)) {
      var cell = document.getElementById(theId);
      if(box.checked) {
         cell.className = cell.className.replace("_on", "");
         cell.className = cell.className + "_on";
      }
      else {
        cell.className = cell.className.replace("_on", "");
      }
   }
}

function CheckIfSelected(){
    var chkboxes=document.getElementsByName('select');
    var sell = document.getElementById('selected');
    var chk=true;
    for(var i=0;i<chkboxes.length;i++){
        if(chkboxes[i].checked){
            chk=false;
        }
    }
    if(chk && sell.checked){
        alert("Brak zaznaczonych. Wybierz elementy.");
    }
}
function ShowLength(){
    var chkboxes=document.getElementsByName('select');
    var sel_box = document.getElementById('selection_box');
    var sell = document.getElementById('selected');
    var j = 0;
    for(var i=0;i<chkboxes.length;i++){
        if(chkboxes[i].checked){
            j=j+1;
        }
    }
    if (sel_box && j>0){
        sell.checked = true;
        sel_box.style.display = "inline";
    }
    else{
        sel_box.style.display = "none";
    }
    document.getElementById("myResults").innerHTML = "(" + j + ")";
    document.getElementById("myResultsBottom").innerHTML = "(" + j + ")";
}

function otherSelect() {
    var other = document.getElementById("otherBox");
    ShowLength();
    if (document.getElementById("other").checked == true) {
        other.style.display = "inline-block";
    }
    else {
        other.style.display = "none";
    }
}

function ChangeAll(source){
  var checkboxes = document.getElementsByName('select');
  var trs = document.getElementsByTagName("tr");
    for(var j=0; j<trs.length; j++){
        trs[j].className = trs[j].className.replace("_on","");
    }
  for(var i=0; i<checkboxes.length;i++) {
    if(checkboxes[i].checked){
      for(var j=0; j<trs.length; j++){
        if(trs[j].id==checkboxes[i].value){
          trs[j].className = trs[j].className.replace("_on","");
          trs[j].className = trs[j].className + "_on";
        }
      }
    }
  }
}

function toggle(source) {
  var checkboxes = document.getElementsByName('select');
  var trs = document.getElementsByTagName("tr");
    for (i=0; i<checkboxes.length; i++){
    checkboxes[i].checked = source.checked;
  }
  if(source.checked) {
     for(var j=0; j<trs.length; j++){
         trs[j].className = trs[j].className.replace("_on","");
         trs[j].className = trs[j].className +"_on"
    }
  }
  else{
     for(var j=0; j<trs.length; j++){
       trs[j].className = trs[j].className.replace("_on","");
    }
  }
}

function uncheckselected() {
  var mainchk = document.getElementById('maincheckbox');
  var checkboxes = document.getElementsByName('select');
  var trs = document.getElementsByTagName("tr");
  mainchk.checked = false;
  for (i=0; i<checkboxes.length; i++){
    checkboxes[i].checked = false;
    trs[i].className = trs[i].className.replace("_on","");
  }
}

function ChooseAll(source) {
  var checkboxes = document.getElementsByName('choosen');
  var box = document.getElementById('search_box');
  var cap = document.getElementById('caption');
  var man = document.getElementById('manager');
  otherSelect();
  if(man){
      showID(man, 'download')
  }
  box.style.display = "none";
  cap.style.display = "none";
  /*for(var i in checkboxes) {*/
  for (var i=0; i<checkboxes.length; i++){
    var name = checkboxes[i].id +'1';
    var ele = document.getElementById(name);
    if(ele){
        if(checkboxes[i].checked) {
            ele.style.display = "table-row";
            box.style.display = "table-row";
            cap.style.display = "table-caption";
        }
        else {
            ele.style.display = "none";
        }
    }
  }
}

function showID(source, theId) {
    var ele = document.getElementById(theId);
    if(source.checked) {
        ele.style.display = "block";
    }
    else {
        ele.style.display = "none";
    }
}

function search_toggle(source) {
  checkboxes = document.getElementsByName('choosen');
  for (i=0; i<checkboxes.length; i++){
    checkboxes[i].checked = source.checked;
  }
  ChooseAll();
}

function ColorMe(box, colorval,colormin,colormax) {
    var intvalue = parseInt(100*(parseFloat(colorval)-parseFloat(colormin))/(parseFloat(colormax)-parseFloat(colormin)));
    if(intvalue<1){
        var intvalue = 1;
    }
    else if(intvalue> parseInt(colormax)){
        var intvalue =  100;
    }
    var colorid = 'color' + intvalue;
    var ele = document.getElementById(colorid);
    if(box.checked) {
        ele.style.backgroundColor = 'black';
    }
}
