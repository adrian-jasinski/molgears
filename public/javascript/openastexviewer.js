/*
 * Javascript functions that manage
 * communication with AstexViewer.
 */

function av_execute(command){
  document.av.execute(command);
  window.status = command;
}

function av_lipophilicity(obj){
  av_execute("run 'lipophilicity.properties';");
  av_execute("object '" + obj +"' texture lipophilicity u 7.0 aminoacid;");
}

function av_texture(obj, tex){
  if(tex == 'off'){
    av_execute("object '" + obj + "' texture 'off';");
  }else{
    if(tex == 'simple'){
      av_execute("texture '" + tex + "' simple;");
    }else{
      av_execute("texture load '" + tex + "' '" + tex + "';");
    }
    av_execute("object '" + obj + "' texture '" + tex + "';");
  }
}

function av_transparency(obj, tr){
  av_execute("object '" + obj + "' transparency " + tr + ";");
}

function av_display(obj, tr){
  var command = "object display '" + obj + "' " + tr + ";";
  av_execute(command);
}

function av_colour(obj, tr){
  var command = "object '" + obj + "' color " + tr + ";";
  av_execute(command);
}

function av_background(tr){
  var command = "background '" + tr + "';";
  av_execute(command);
}

/*
 * Javascript functions that manage interaction with
 * controls on the page.
 */

function js_transparency(sel){
  var val = sel.options[sel.selectedIndex].value;
  val = Math.round(val * 2.55);
  av_transparency('protein_surface', val);
}

function js_texture(sel){
  var val = sel.options[sel.selectedIndex].value;
  if(!sel.textured){
    av_lipophilicity('protein_surface');
    sel.textured = true;
  }
  av_texture('protein_surface', val);
}

function js_surface(obj){
  
  if(obj.checked){
    if(!obj.surface){
      av_execute('surface -solid true protein_surface white aminoacid;');
      obj.surface = true;
    }else{
      av_display('protein_surface', 'on');
    }
  }else{
    av_display('protein_surface', 'off');
  }
}

function js_atoms(obj){
  if(obj.checked){
    av_execute('display lines on not solvent;');
  }else{
    av_execute('display lines off not solvent;');
  }
}

function js_solvent(obj){
  if(obj.checked){
    av_execute('display lines on solvent;');
  }else{
    av_execute('display lines off solvent;');
  }
}


function js_spheres(obj){
  if(obj.checked){
    av_execute('display spheres aminoacid;');
  }else{
    av_execute('display spheres none;');
  }
}

function js_ligand_spheres(obj){
  if(obj.checked){
    av_execute('display spheres not (aminoacid or ions or solvent);');
  }else{
    av_execute('display spheres none;');
  }
}

function js_ligand_sticks(obj){
  if(obj.checked){
    av_execute('display cylinders on not (aminoacid or ions or solvent);');
  }else{
    av_execute('display cylinders off not (aminoacid or ions or solvent);');
  }
}

function js_schematic(obj){
  if(obj.checked){
    if(!obj.schematic){
      av_execute('color_by_rainbow aminoacid; secstruc all; schematic -name protein_schematic all; color_by_atom;');
      obj.schematic = true;
    }else{
      av_display('protein_schematic', 'on');
    }
  }else{
    av_display('protein_schematic', 'off');
  }
}

function js_colour(sel){
  var val = sel.options[sel.selectedIndex].value;
  av_colour('protein_surface', val);
}

function js_atomcolour(sel){
  var val = sel.options[sel.selectedIndex].value;
  av_execute(val);
}

function js_background(sel){
  var val = sel.options[sel.selectedIndex].value;
  av_background(val);
}

function js_antialias(sel){
  if(sel.checked){
    av_execute("view -antialias true;");
  }else{
    av_execute("view -antialias false;");
  }
}

function js_shadows(sel){
  if(sel.checked){
    av_execute("view -realspheres true; view -shadows true;");
  }else{
    av_execute("view -realspheres false; view -shadows false;");
  }
}
