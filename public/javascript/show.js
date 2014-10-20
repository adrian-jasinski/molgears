function ShowNotEmpty(source) {
    var box = document.getElementById('search_box');
    var elements = document.getElementsByClassName('filternotempty');
    for(var i=0;i<elements.length;i++) {
        var el = elements[i];
        if (el.type=="text" || el.type=="select-multiple" || el.type=="select"){
            if (el.value){
                var name = el.name;
                if (name.indexOf("date") !=-1) {
                    var name = 'text_date';
                }
                else if (name.indexOf("text_") ==-1) {
                    var name = 'text_' + el.name;
                }
                var bx = document.getElementById(name+"1");
                var chk = document.getElementById(name);
                bx.style.display = "table-row";
                box.style.display = "table-row";
                chk.checked = true;
            }
        }
        else if (el.type=="checkbox"){
            if (el.checked){
                var name = el.name;
                if (name.indexOf("text_") ==-1) {
                    var name = 'text_' + el.name;
                }
                var bx = document.getElementById(name+"1");
                var chk = document.getElementById(name);
                bx.style.display = "table-row";
                box.style.display = "table-row";
                chk.checked = true;
            }
        }
    }
}

function showNotEmpty0(source) {
  var box = document.getElementById('search_box');
  var smiles = document.getElementById('p1');
  if (smiles.value){
      var el = document.getElementById('structure1');
      var chk = document.getElementById('structure');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  var p2 = document.getElementById('p2');
  if (p2.value){
      var el = document.getElementById('text_GID1');
      var chk = document.getElementById('text_GID');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  var p3 = document.getElementById('p3');
  if (p3.value){
      var el = document.getElementById('text_name1');
      var chk = document.getElementById('text_name');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var p4 = document.getElementById('p4');
  if (p4.value){
      var el = document.getElementById('text_creator1');
      var chk = document.getElementById('text_creator');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var p5 = document.getElementById('p5');
  if (p5.value){
      var el = document.getElementById('text_notes1');
      var chk = document.getElementById('text_notes');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var date1 = document.getElementById('date1');
  var date2 = document.getElementById('date2');
  if (date1.value || date2.value){
      var el = document.getElementById('text_date1');
      var chk = document.getElementById('text_date');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var tagsy = document.getElementsByName('tags');
  for (var i=0; i < tagsy.length; i++){
      var el = document.getElementById('text_tags1');
      var chk = document.getElementById('text_tags');
      if(tagsy[i].checked){
        el.style.display = "table-row";
        box.style.display = "table-row";
        chk.checked = true;
      }
  }
}

/*+++++++++++++++++++++++++++++++++++++++++++++++++++++*/
function showNotEmpty1(source) {
  var box = document.getElementById('search_box');
  var smiles = document.getElementById('p1');
  if (smiles.value){
      var el = document.getElementById('structure1');
      var chk = document.getElementById('structure');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  var p2 = document.getElementById('p2');
  if (p2.value){
      var el = document.getElementById('text_GID1');
      var chk = document.getElementById('text_GID');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  var p3 = document.getElementById('p3');
  if (p3.value){
      var el = document.getElementById('text_name1');
      var chk = document.getElementById('text_name');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var p4 = document.getElementById('p4');
  if (p4.value){
      var el = document.getElementById('text_owner1');
      var chk = document.getElementById('text_owner');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var p5 = document.getElementById('p5');
  if (p5.value){
      var el = document.getElementById('text_principal1');
      var chk = document.getElementById('text_principal');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var p6 = document.getElementById('p6');
  if (p6.value){
      var el = document.getElementById('text_notes1');
      var chk = document.getElementById('text_notes');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }

  var p7 = document.getElementById('p7');
  if (p7.value){
      var el = document.getElementById('text_priority1');
      var chk = document.getElementById('text_priority');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var date1 = document.getElementById('date1');
  var date2 = document.getElementById('date2');
  if (date1.value || date2.value){
      var el = document.getElementById('text_date1');
      var chk = document.getElementById('text_date');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var tagsy = document.getElementsByName('tags');
  for (var i=0; i < tagsy.length; i++){
      var el = document.getElementById('text_tags1');
      var chk = document.getElementById('text_tags');
      if(tagsy[i].checked){
        el.style.display = "table-row";
        box.style.display = "table-row";
        chk.checked = true;
      }
  }

  var id_add = document.getElementById('px1');
  if (id_add.value){
      var el = document.getElementById('text_ID1');
      var chk = document.getElementById('text_ID');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var sel = document.getElementById('statusy').selectedIndex;
  if (document.getElementById('statusy').options[sel].value) {
      var el = document.getElementById('text_status1');
      var chk = document.getElementById('text_status');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
}

/*+++++++++++++++++++++++++++++++++++++++++++++++++++++*/

function showNotEmpty3(source) {
  var box = document.getElementById('search_box');
  var smiles = document.getElementById('p1');
  if (smiles.value){
      var el = document.getElementById('structure1');
      var chk = document.getElementById('structure');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  var p2 = document.getElementById('p2');
  if (p2.value){
      var el = document.getElementById('text_GID1');
      var chk = document.getElementById('text_GID');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  var p3 = document.getElementById('p3');
  if (p3.value){
      var el = document.getElementById('text_name1');
      var chk = document.getElementById('text_name');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var p4 = document.getElementById('p4');
  if (p4.value){
      var el = document.getElementById('text_lso1');
      var chk = document.getElementById('text_lso');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var p5 = document.getElementById('p5');
  if (p5.value){
      var el = document.getElementById('text_notes1');
      var chk = document.getElementById('text_notes');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var date1 = document.getElementById('date1');
  var date2 = document.getElementById('date2');
  if (date1.value || date2.value){
      var el = document.getElementById('text_date1');
      var chk = document.getElementById('text_date');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  
  var tagsy = document.getElementsByName('tags');
  for (var i=0; i < tagsy.length; i++){
      var el = document.getElementById('text_tags1');
      var chk = document.getElementById('text_tags');
      if(tagsy[i].checked){
        el.style.display = "table-row";
        box.style.display = "table-row";
        chk.checked = true;
      }
  }

  var id_add = document.getElementById('px1');
  if (id_add.value){
      var el = document.getElementById('text_ID1');
      var chk = document.getElementById('text_ID');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }

  var ent = document.getElementById('entry');
  if (ent.value){
      var el = document.getElementById('text_entry1');
      var chk = document.getElementById('text_entry');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
  var bx = document.getElementById('box');
  if (bx.value){
      var el = document.getElementById('text_box1');
      var chk = document.getElementById('text_box');
      el.style.display = "table-row";
      box.style.display = "table-row";
      chk.checked = true;
  }
}
/****************************************************************/
