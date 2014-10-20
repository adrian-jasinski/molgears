function showNotEmpty(source) {
  var box = document.getElementById('search_box');
    
  var p2 = document.getElementById('p2');
  if (p2.value){
      var el = document.getElementById('text_GID1');
      var chk = document.getElementById('text_GID');
      el.style.display = "inline";
      box.style.display = "inline";
      chk.checked = true;
  }
  var p3 = document.getElementById('p3');
  if (p3.value){
      var el = document.getElementById('text_name1');
      var chk = document.getElementById('text_name');
      el.style.display = "inline";
      box.style.display = "inline";
      chk.checked = true;
  }
  
  var p4 = document.getElementById('p4');
  if (p4.value){
      var el = document.getElementById('text_creator1');
      var chk = document.getElementById('text_creator');
      el.style.display = "inline";
      box.style.display = "inline";
      chk.checked = true;
  }
  
  var p5 = document.getElementById('p5');
  if (p5.value){
      var el = document.getElementById('text_notes1');
      var chk = document.getElementById('text_notes');
      el.style.display = "inline";
      box.style.display = "inline";
      chk.checked = true;
  }
  
  var date1 = document.getElementById('date1');
  var date2 = document.getElementById('date2');
  if (date1.value || date2.value){
      var el = document.getElementById('text_date1');
      var chk = document.getElementById('text_date');
      el.style.display = "inline";
      box.style.display = "inline";
      chk.checked = true;
  }
  
  var tagsy = document.getElementsByName('tags');
  for (var i=0; i < tagsy.length; i++){
      var el = document.getElementById('text_tags1');
      var chk = document.getElementById('text_tags');
      if(tagsy[i].checked){
        el.style.display = "inline";
        box.style.display = "inline";
        chk.checked = true;
      }
  }
}
