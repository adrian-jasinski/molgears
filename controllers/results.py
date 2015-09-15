# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
from tg import expose, flash, redirect, request
from tg.i18n import lazy_ugettext as l_
from molgears.model import DBSession, Tags, LCompound, LPurity, Names
from molgears.model import Compound, User, Projects
from molgears.model.auth import UserLists
from molgears.lib.base import BaseController
import os
from sqlalchemy import desc

from rdkit import Chem
from molgears.widgets.structure import checksmi
from datetime import datetime

#from tg.decorators import paginate
from webhelpers import paginate
from molgears.widgets.rgbTuple import htmlRgb, htmlRgb100, Num2Rgb

from molgears.controllers.ctoxicity import CytotoxicityController

__all__ = ['ResultsController']

class ResultsController(BaseController):
    ctoxicity=CytotoxicityController()
    
    @expose('molgears.templates.users.results.index')
    def index(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter_by(name=pname).first()
        page_url = paginate.PageURL_WebOb(request)
        import pickle
        try:
            cells = pickle.loads([test.cell_line for test in project.tests if test.name == 'CT'][0])
        except:
            cells = None
        lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.showme==True)
        
        dsc = True
        order = LCompound.id
        tmpl = ''
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        selection = None
        similarity = None
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        ulist = None
        ulists = set([l for l in user.lists if l.table == 'Results'] + [l for l in user.tg_user_lists if l.table == 'Results'])
        items = user.items_per_page
        
        try:
            if kw['search'] != u'':
                search_clicked = kw['search']
            else:
                search_clicked = None
        except Exception:
            search_clicked = None
        if kw:
            if kw.has_key('mylist'):
                try:
                    ulist_id = int(kw['mylist'])
                    ulist = DBSession.query(UserLists).get(ulist_id)
                except Exception:
                    flash(l_(u'List error'), 'error')
                    redirect(request.headers['Referer'])
                if (ulist in user.lists) or (user in ulist.permitusers):
                    if ulist.elements:
                        import pickle
                        elements = [int(el) for el in pickle.loads(ulist.elements)]
                        if ulist.table == 'Results':
                            lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.id.in_(elements))
                        else:
                            flash(l_(u'Table error'), 'error')
                            redirect(request.headers['Referer'])
                else:
                    flash(l_(u'Permission denied'), 'error')
                    redirect(request.headers['Referer'])
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    if v in ('gid', 'create_date', 'box', 'form', 'state', 'entry', 'source', 'MDM2', 'MDM4', 'lcode'):
                        if v=='lcode':
                            order = LCompound.lcode
                        else:
                            order = LCompound.__getattribute__(LCompound, v)
                    else:
                        if v=='last_point':
                            lcompound=lcompound.join(LCompound.solubility)
                            order = v
                        elif hasattr(LCompound, v):
                            order = LCompound.__getattribute__(LCompound, v)
                        elif 'CTOX_' in v:
                            v = v.replace('CTOX_', '')
                            all_lcompounds = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).all()
                            for l in all_lcompounds:
                                l.avg_ct = v.replace('pp', '+')
                            order = '_avg_ct'
                        else:
                            order = v
                if str(k) != 'select' and str(k) != 'remove' and str(v) != u'':
                    tmpl += str(k) + '=' + str(v) + '&'
                elif str(k) == 'select':
                    try:
                        if isinstance(kw['select'], basestring):
                            selection = [kw['select']]
                        else:
                            selection = [id for id in kw['select']]
                    except Exception:
                        selection = None
                        
            if search_clicked:
                try:
                    smiles = str(kw['smiles'])
                    if 'pp' in smiles:
                        smiles = smiles.replace('pp', '+')
                    method = str(kw['method'])
                except Exception:
                    smiles = None
                    method = None
                if smiles:
                    if checksmi(smiles):
                        from razi.functions import functions
                        from razi.expression import TxtMoleculeElement
                        if method == 'similarity':
#                            from razi.postgresql_rdkit import tanimoto_threshold
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            search = DBSession.query(LCompound, tanimoto_sml).join(LCompound.mol).join(LCompound.purity).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                            if order != LCompound.id:
                                if order == 'purity':
                                    order = LPurity.value
                                if dsc:
                                    search = search.order_by(desc(order).nullslast())
                                else:
                                    search = search.order_by(order)
                            else:
                                search = search.order_by(desc(tanimoto_sml)).all()
                            lcompound = ()
                            similarity = ()
                            for row in search:
                                lcompound += (row[0], )
                                similarity += (row[1], )
                            currentPage = paginate.Page(lcompound, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage,tmpl=tmpl, page='results', pname=pname, alltags=alltags, similarity=similarity,htmlRgb=htmlRgb, htmlRgb100=htmlRgb100, Num2Rgb=Num2Rgb, cells=cells, ulists=ulists, ulist=ulist)
    
                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                        elif method == 'identity':
                            lcompound = DBSession.query(LCompound).filter(Compound.project.any(Projects.name==pname)).join(LCompound.mol).filter(Compound.structure.equals(smiles))
                    else:
                        if method == 'smarts':
                            if dsc:
                                lcompound = lcompound.order_by(desc(order).nullslast())
                            else:
                                lcompound = lcompound.order_by(order)
                            search = lcompound.all()
                            sub_lcompounds = ()
                            patt = Chem.MolFromSmarts(smiles)
                            if not patt:
                                flash(l_(u'SMARTS error'), 'warning')
                                redirect(request.headers['Referer'])
                            for row in search:
                                m = Chem.MolFromSmiles(str(row.mol.structure))
                                mol = Chem.AddHs(m)
                                if mol.HasSubstructMatch(patt):
                                    sub_lcompounds += (row, )
                            currentPage = paginate.Page(sub_lcompounds, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage,tmpl=tmpl, page='results', pname=pname, alltags=alltags, similarity=similarity,htmlRgb=htmlRgb, htmlRgb100=htmlRgb100, Num2Rgb=Num2Rgb, cells=cells, ulists=ulists, ulist=ulist)
                        else:
                            flash(l_(u'SMILES error'), 'warning')
                            redirect(request.headers['Referer'])
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_GID'])
                        lcompound = lcompound.filter(LCompound.gid == gid)
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_ID') and kw['text_ID'] !=u'':
                    try:
                        id = int(kw['text_ID'])
                        lcompound = lcompound.filter(LCompound.id == id)
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_name') and kw['text_name'] !=u'':
                    lcompound = lcompound.filter(Compound.names.any(Names.name.like(kw['text_name'].strip().replace('*', '%'))))
                if kw.has_key('text_notes') and kw['text_notes'] !=u'':
                    lcompound = lcompound.filter(LCompound.notes.like(kw['text_notes'].replace('*', '%')))
                if kw.has_key('text_lso') and kw['text_lso'] !=u'':
                    lcompound = lcompound.filter(LCompound.lso.like(kw['text_lso'].replace('*', '%')))
                if kw.has_key('text_entry') and kw['text_entry'] !=u'':
                    lcompound = lcompound.filter(LCompound.entry.like(kw['text_entry'].replace('*', '%')))
                if kw.has_key('text_box') and kw['text_box'] !=u'':
                    lcompound = lcompound.filter(LCompound.box.like(kw['text_box'].replace('*', '%')))
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    lcompound = lcompound.filter(LCompound.create_date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            lcompound = lcompound.filter(LCompound.create_date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        lcompound = lcompound.filter(LCompound.create_date < date_to)
                        
                if kw.has_key('text_mdm2_hill_from') and kw['text_mdm2_hill_from'] !=u'':
                    text_mdm2_hill_from = float(kw['text_mdm2_hill_from'])
                    lcompound = lcompound.filter(LCompound.avg_hillslope_mdm2 >= text_mdm2_hill_from)
                else:
                    text_mdm2_hill_from = None
                if kw.has_key('text_mdm2_hill_to') and kw['text_mdm2_hill_to'] !=u'':
                    text_mdm2_hill_to = float(kw['text_mdm2_hill_to'])
                    if text_mdm2_hill_from:
                        if text_mdm2_hill_to>=text_mdm2_hill_from:
                            lcompound = lcompound.filter(LCompound.avg_hillslope_mdm2 <= text_mdm2_hill_to)
                        else:
                            flash(l_(u'The final value must be greater than the initial'))
                            redirect(request.headers['Referer'])
                    else:
                        lcompound = lcompound.filter(LCompound.avg_hillslope_mdm2 <= text_mdm2_hill_to)
                if kw.has_key('text_mdm2_fluor_from') and kw['text_mdm2_fluor_from'] !=u'':
                    text_mdm2_fluor_from = float(kw['text_mdm2_fluor_from'])
                    lcompound = lcompound.filter(LCompound.avg_fluorescence_mdm2 >= text_mdm2_fluor_from)
                else:
                    text_mdm2_fluor_from = None
                if kw.has_key('text_mdm2_fluor_to') and kw['text_mdm2_fluor_to'] !=u'':
                    text_mdm2_fluor_to = float(kw['text_mdm2_fluor_to'])
                    if text_mdm2_fluor_from:
                        if text_mdm2_fluor_to>=text_mdm2_fluor_from:
                            lcompound = lcompound.filter(LCompound.avg_fluorescence_mdm2 <= text_mdm2_fluor_to)
                        else:
                            flash(l_(u'The final value must be greater than the initial'))
                            redirect(request.headers['Referer'])
                    else:
                        lcompound = lcompound.filter(LCompound.avg_fluorescence_mdm2 <= text_mdm2_fluor_to)
                if kw.has_key('text_mdm2_ki_from') and kw['text_mdm2_ki_from'] !=u'':
                    text_mdm2_ki_from = float(kw['text_mdm2_ki_from'])
                    lcompound = lcompound.filter(LCompound.avg_ki_mdm2 >= text_mdm2_ki_from)
                else:
                    text_mdm2_ki_from = None
                if kw.has_key('text_mdm2_ki_to') and kw['text_mdm2_ki_to'] !=u'':
                    text_mdm2_ki_to = float(kw['text_mdm2_ki_to'])
                    if text_mdm2_ki_from:
                        if text_mdm2_ki_to>=text_mdm2_ki_from:
                            lcompound = lcompound.filter(LCompound.avg_ki_mdm2 <= text_mdm2_ki_to)
                        else:
                            flash(l_(u'The final value must be greater than the initial'))
                            redirect(request.headers['Referer'])
                    else:
                        lcompound = lcompound.filter(LCompound.avg_ki_mdm2 <= text_mdm2_ki_to)

                if kw.has_key('text_mdm4_hill_from') and kw['text_mdm4_hill_from'] !=u'':
                    text_mdm4_hill_from = float(kw['text_mdm4_hill_from'])
                    lcompound = lcompound.filter(LCompound.avg_hillslope_mdm4 >= text_mdm4_hill_from)
                else:
                    text_mdm4_hill_from = None
                if kw.has_key('text_mdm4_hill_to') and kw['text_mdm4_hill_to'] !=u'':
                    text_mdm4_hill_to = float(kw['text_mdm4_hill_to'])
                    if text_mdm4_hill_from:
                        if text_mdm4_hill_to>=text_mdm4_hill_from:
                            lcompound = lcompound.filter(LCompound.avg_hillslope_mdm4 <= text_mdm4_hill_to)
                        else:
                            flash(l_(u'The final value must be greater than the initial'))
                            redirect(request.headers['Referer'])
                    else:
                        lcompound = lcompound.filter(LCompound.avg_hillslope_mdm4 <= text_mdm4_hill_to)
                        
                if kw.has_key('text_mdm4_fluor_from') and kw['text_mdm4_fluor_from'] !=u'':
                    text_mdm4_fluor_from = float(kw['text_mdm4_fluor_from'])
                    lcompound = lcompound.filter(LCompound.avg_fluorescence_mdm4 >= text_mdm4_fluor_from)
                else:
                    text_mdm4_fluor_from = None
                if kw.has_key('text_mdm4_fluor_to') and kw['text_mdm4_fluor_to'] !=u'':
                    text_mdm4_fluor_to = float(kw['text_mdm4_fluor_to'])
                    if text_mdm4_fluor_from:
                        if text_mdm4_fluor_to>=text_mdm4_fluor_from:
                            lcompound = lcompound.filter(LCompound.avg_fluorescence_mdm4 <= text_mdm4_fluor_to)
                        else:
                            flash(l_(u'The final value must be greater than the initial'))
                            redirect(request.headers['Referer'])
                    else:
                        lcompound = lcompound.filter(LCompound.avg_fluorescence_mdm4 <= text_mdm4_fluor_to)
                        
                if kw.has_key('text_mdm4_ki_from') and kw['text_mdm4_ki_from'] !=u'':
                    text_mdm4_ki_from = float(kw['text_mdm4_ki_from'])
                    lcompound = lcompound.filter(LCompound.avg_ki_mdm4 >= text_mdm4_ki_from)
                else:
                    text_mdm4_ki_from = None
                if kw.has_key('text_mdm4_ki_to') and kw['text_mdm4_ki_to'] !=u'':
                    text_mdm4_ki_to = float(kw['text_mdm4_ki_to'])
                    if text_mdm4_ki_from:
                        if text_mdm4_ki_to>=text_mdm4_ki_from:
                            lcompound = lcompound.filter(LCompound.avg_ki_mdm4 <= text_mdm4_ki_to)
                        else:
                            flash(l_(u'The final value must be greater than the initial'))
                            redirect(request.headers['Referer'])
                    else:
                        lcompound = lcompound.filter(LCompound.avg_ki_mdm4 <= text_mdm4_ki_to)

                try:
                        tags = kw['text_tags']
                except Exception:
                    tags = None
                    pass
                if tags:
                    if isinstance(tags, basestring):
                        tagi = eval(tags)
                        if type(tagi) != type([]):
                            tagi = [int(tags)]
                    else:
                        tagi = [int(tid) for tid in tags]
                    lcompound = lcompound.filter(Compound.tags.any(Tags.id.in_(tagi)))
                    
        if dsc:
            lcompound = lcompound.order_by(desc(order).nullslast())
        else:
            lcompound = lcompound.order_by(order)
            
        if search_clicked and kw['search'] == "Download":
            if kw['file_type'] and kw['file_type'] != u'' and kw['sell_type'] and kw['sell_type'] != u'':
                if kw['sell_type'] == u'all':
                    lcompounds = lcompound.all()
                elif kw['sell_type'] == u'selected':
                    if selection:
                        lcompounds = ()
                        for el in selection:
                            lcompounds += (DBSession.query(LCompound).get(el), )
                    else:
                        flash(l_(u'Lack of selected structures for download'), 'error')
                        redirect(request.headers['Referer'])
                elif kw['sell_type'] == u'range':
                    lcompounds = lcompound.all()
                    if kw.has_key('select_from') and kw['select_from'] != u'':
                        try:
                            select_from = int(kw['select_from']) -1 
                            if select_from<1 or select_from>len(lcompounds):
                                select_from = 0
                        except Exception:
                            select_from = 0
                    else:
                        select_from = 0
                    if kw.has_key('select_to') and kw['select_to'] != u'':
                        try:
                            select_to = int(kw['select_to'])
                            if select_to<2 or select_to>len(lcompounds):
                                select_to = len(lcompounds)
                        except Exception:
                            select_to = len(lcompounds)
                    else:
                        select_to = len(lcompounds)
                    lcompounds_new = ()
                    for el in range(select_from, select_to):
                        lcompounds_new += (lcompounds[el], )
                    lcompounds = lcompounds_new
                else:
                    flash(l_(u'Lack of items to download'), 'error')
                    redirect(request.headers['Referer'])
                try:
                    if isinstance(kw['options'], basestring):
                        options = [kw['options']]
                    else:
                        options = kw['options']
                except Exception:
                    flash(l_('Choose download options'), 'error')
                    redirect(request.headers['Referer'])
                if 'getsize' in kw:
                    size = int(kw['getsize']), int(kw['getsize'])
                else:
                    size = 100, 100
                if kw['file_type'] == 'pdf':
                    filename = userid + '_selected.pdf'
                    from xhtml2pdf.pisa import CreatePDF
                    from tg.render import render as render_template
                    import cStringIO
                    html = render_template({"length":len(lcompounds), "lcompound":lcompounds, "cells":cells, "options":options, "size":size}, "genshi", "molgears.templates.users.results.print2", doctype=None)
                    dest = './molgears/files/pdf/' + filename
                    result = file(dest, "wb")
                    CreatePDF(cStringIO.StringIO(html.encode("UTF-8")), result, encoding="utf-8")
                    result.close()
                    import paste.fileapp
                    f = paste.fileapp.FileApp('./molgears/files/pdf/'+ filename)
                    from tg import use_wsgi_app
                    return use_wsgi_app(f)
                elif kw['file_type'] == 'xls':
                    filename = userid + '_selected.xls'
                    filepath = os.path.join('./molgears/files/download/', filename)
                    from PIL import Image
                    import xlwt
                    wbk = xlwt.Workbook()
                    sheet = wbk.add_sheet('sheet1')
                    j=0
                    if 'nr' in options:
                        sheet.write(0,j,u'Nr.')
                        j+=1
                    if 'gid' in options:
                        sheet.write(0,j,u'GID')
                        j+=1
                    if 'id' in options:
                        sheet.write(0,j,u'ID')
                        j+=1
                    if 'name' in options:
                        sheet.write(0,j,u'Name')
                        j+=1
                    if 'names' in options:
                        sheet.write(0,j,u'Names')
                        j+=1
                    if 'image' in options:
                        sheet.write(0,j,u'Image')
                        j+=1
                    if 'smiles' in options:
                        sheet.write(0,j,u'SMILES')
                        j+=1
                    if 'inchi' in options:
                        sheet.write(0,j,u'InChi')
                        j+=1
                    if 'lso' in options:
                        sheet.write(0,j,u'LSO')
                        j+=1
                    if 'num_atoms' in options:
                        sheet.write(0,j,u'Atoms')
                        j+=1
                    if 'mw' in options:
                        sheet.write(0,j,u'MW')
                        j+=1
                    if 'hba' in options:
                        sheet.write(0,j,u'hba')
                        j+=1
                    if 'hbd' in options:
                        sheet.write(0,j,u'hbd')
                        j+=1
                    if 'tpsa' in options:
                        sheet.write(0,j,u'tpsa')
                        j+=1
                    if 'logp' in options:
                        sheet.write(0,j,u'logP')
                        j+=1
                    if 'purity' in options:
                        sheet.write(0,j, u'Purity')
                        j+=1
                    if 'create_date' in options:
                        sheet.write(0,j,u'Date')
                        j+=1
                    if 'box' in options:
                        sheet.write(0,j,u'Box')
                        j+=1
                    if 'entry' in options:
                        sheet.write(0,j,u'Entry')
                        j+=1
                    if 'source' in options:
                        sheet.write(0,j,u'Source')
                        j+=1
                    if 'content' in options:
                        sheet.write(0,j,u'Content')
                        j+=1
                    if 'tags' in options:
                        sheet.write(0,j,u'Tags')
                        j+=1
                    if 'notes' in options:
                        sheet.write(0,j,u'Notes')
                        j+=1
                    for cell_line in cells:
                        if '_CT_%s' % cell_line in options:
                            sheet.write(0,j,u'CT %s' % cell_line)
                            j+=1
                    i = 1
                    for row in lcompounds:
                        j=0
                        if 'nr' in options:
                            sheet.write(i,j, str(i))
                            j+=1
                        if 'gid' in options:
                            sheet.write(i,j, row.gid)
                            j+=1
                        if 'id' in options:
                            sheet.write(i,j, row.id)
                            j+=1
                        if 'name' in options:
                            sheet.write(i,j, row.mol.name)
                            j+=1
                        if 'names' in options:
                            names = u''
                            for n in row.mol.names:
                                names += n.name + u', '
                            sheet.write(i,j, names)
                            j+=1
                        if 'image' in options:
                            file_in = './molgears/public/img/%s.png' % row.gid
                            img = Image.open(file_in)
                            file_out = './molgears/public/img/bitmap/thumb%s.bmp' %row.gid
                            img.thumbnail(size, Image.ANTIALIAS)
                            img.save(file_out)
                            sheet.insert_bitmap(file_out , i,j, 5, 5)
                            j+=1
                        if 'smiles' in options:
                            sheet.write(i,j, str(row.mol.structure))
                            j+=1
                        if 'inchi' in options:
                            sheet.write(i,j, str(row.mol.inchi))
                            j+=1
                        if 'lso' in options:
                            sheet.write(i,j, row.lso)
                            j+=1
                        if 'num_atoms' in options:
                            sheet.write(i,j,str(row.mol.num_hvy_atoms)+'/'+str(row.mol.num_atoms))
                            j+=1
                        if 'mw' in options:
                            sheet.write(i,j, str(row.mol.mw))
                            j+=1
                        if 'hba' in options:
                            sheet.write(i,j, str(row.mol.hba))
                            j+=1
                        if 'hbd' in options:
                            sheet.write(i,j, str(row.mol.hbd))
                            j+=1
                        if 'tpsa' in options:
                            sheet.write(i,j, str(row.mol.tpsa))
                            j+=1
                        if 'logp' in options:
                            sheet.write(i,j, str(row.mol.logp))
                            j+=1
                        if 'state' in options:
                            sheet.write(i,j, str(row.state))
                            j+=1
                        if 'purity' in options:
                            pur = u''
                            for p in sorted(row.purity, key=lambda p: p.value, reverse=True):
                                pur += u'%s : %s\n' % (p.value, p.type)
                            sheet.write(i,j, pur)
                            j+=1
                        if 'create_date' in options:
                            sheet.write(i,j, str(row.create_date))
                            j+=1
                        if 'owner' in options:
                            sheet.write(i,j, row.owner)
                            j+=1
                        if 'box' in options:
                            sheet.write(i,j, row.box)
                            j+=1
                        if 'entry' in options:
                            sheet.write(i,j, row.entry)
                            j+=1
                        if 'source' in options:
                            sheet.write(i,j, row.source)
                            j+=1
                        if 'content' in options:
                            if row.content:
                                sheet.write(i,j, str(row.content.value))
                            else:
                                sheet.write(i,j, 'None')
                            j+=1
                        if 'tags' in options:
                            tagsy=u''
                            for tag in row.mol.tags:
                                tagsy += tag.name + u', '
                            sheet.write(i,j,tagsy)
                            j+=1
                        if 'notes' in options:
                            sheet.write(i,j, row.notes)
                            j+=1
                        for cell_line in cells:
                            if '_CT_%s' % cell_line in options:
                                res = []
                                if row.ctoxicity:
                                    for ct in sorted(row.ctoxicity, key=lambda ct: ct.id):
                                        if ct.cell_line==cell_line:
                                            res.append(ct.ic50)
                                if len(res)>0:
                                    sheet.write(i,j, str(round(sum(res)/len(res), 3)))
                                else:
                                    sheet.write(i,j, '')
                                j+=1
                        i += 1
                    wbk.save(filepath)
                    import paste.fileapp
                    f = paste.fileapp.FileApp(filepath)
                    from tg import use_wsgi_app
                    return use_wsgi_app(f)
                    
                elif kw['file_type'] == 'sdf':
                    filepath = './molgears/files/download/out.sdf'
                    ww = Chem.SDWriter(filepath)
                    from rdkit.Chem import AllChem
                    for row in lcompounds:
                        m2 = Chem.MolFromSmiles(str(row.mol.structure))
                        AllChem.Compute2DCoords(m2)
                        AllChem.EmbedMolecule(m2)
                        AllChem.UFFOptimizeMolecule(m2)
                        if 'smiles' in options:
                            m2.SetProp("smiles", str(row.mol.structure))
                        if 'name' in options:
                            m2.SetProp("_Name", str(row.mol.name.encode('ascii', 'ignore')))
                        if 'nr' in options:
                            m2.SetProp("Nr", str(lcompounds.index(row)+1))
                        if 'gid' in options:
                            m2.SetProp("GID", str(row.gid))
                        if 'names' in options:
                            names = u''
                            for n in row.mol.names:
                                names += n.name + ', '
                            m2.SetProp("names", str(names.encode('ascii', 'ignore')))
                        if 'inchi' in options:
                            m2.SetProp("InChi", str(row.mol.inchi))
                        if 'lso' in options:
                            m2.SetProp("LSO", str(row.lso))
                        if 'num_atoms' in options:
                           m2.SetProp("atoms", str(row.mol.num_hvy_atoms)+'/'+str(row.mol.num_atoms))
                        if 'mw' in options:
                            m2.SetProp("mw", str(row.mol.mw))
                        if 'hba' in options:
                            m2.SetProp("hba", str(row.mol.hba))
                        if 'hbd' in options:
                            m2.SetProp("hbd", str(row.mol.hbd))
                        if 'tpsa' in options:
                            m2.SetProp("TPSA", str(row.mol.tpsa))
                        if 'logp' in options:
                            m2.SetProp("logP", str(row.mol.tpsa))
                        if 'create_date' in options:
                            m2.SetProp("create_date", str(row.create_date))
                        if 'owner' in options:
                            m2.SetProp("owner", str(row.owner))
                        if 'tags' in options:
                            tagsy=u''
                            for tag in row.mol.tags:
                                tagsy += tag.name + u', '
                            m2.SetProp("tagi", str(tagsy.encode('ascii', 'ignore')))
                        if 'purity' in options:
                            pur = u''
                            for p in sorted(row.purity, key=lambda p: p.value, reverse=True):
                                pur += u'%s : %s \n' % (p.value, p.type)
                            m2.SetProp("purity", str(pur.encode('ascii', 'ignore')))
                        if 'content' in options:
                            if row.content:
                                m2.SetProp("content", str(row.content.value))
                            else:
                                m2.SetProp("content", "None")
                            j+=1
                        if 'box' in options:
                            m2.SetProp("box", str(row.box))
                        if 'entry' in options:
                            m2.SetProp("entry", str(row.entry))
                        if 'notes' in options:
                            if row.notes:
                                m2.SetProp("notes", str(row.notes.encode('ascii', 'ignore')))
                            else:
                                m2.SetProp("notes", " ")
                        for cell_line in cells:
                            if '_CT_%s' % cell_line in options:
                                res = []
                                if row.ctoxicity:
                                    for ct in sorted(row.ctoxicity, key=lambda ct: ct.id):
                                        if ct.cell_line==cell_line:
                                            res.append(ct.ic50)
                                if len(res)>0:
                                    m2.SetProp('CT_%s' % cell_line, str(round(sum(res)/len(res), 3)))
                                else:
                                    m2.SetProp('CT_%s' % cell_line, ' ')
                                
                        ww.write(m2)
                    ww.close()
                    import paste.fileapp
                    f = paste.fileapp.FileApp(filepath)
                    from tg import use_wsgi_app
                    return use_wsgi_app(f)
                    
                elif kw['file_type'] == 'csv' or 'txt':
                    filename = userid + '_selected.' + kw['file_type']
                    filepath = os.path.join('./molgears/files/download/', filename)
                    from molgears.widgets.unicodeCSV import UnicodeWriter
                    import csv
                    if kw['file_type'] == u'csv':
                        delimiter = ';'
                    else:
                        delimiter = ' '
                    with open(filepath, 'wb') as csvfile:
                        
                        spamwriter = UnicodeWriter(csvfile, delimiter=delimiter,
                                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
                        for row in lcompounds:
                            line =[]
                            if 'smiles' in options:
                                line.append(str(row.mol.structure))
                            if 'name' in options:
                                line.append(row.mol.name)
                            if 'nr' in options:
                                line.append(unicode(lcompounds.index(row)+1))
                            if 'gid' in options:
                                line.append(unicode(row.gid))
                            if 'names' in options:
                                names = u''
                                for n in row.mol.names:
                                    names += n.name + u', '
                                line.append(names)
                            if 'inchi' in options:
                                line.append(row.mol.inchi)
                            if 'lso' in options:
                                line.append(row.lso)
                            if 'num_atoms' in options:
                               line.append(unicode(row.mol.num_hvy_atoms)+'/'+unicode(row.mol.num_atoms))
                            if 'mw' in options:
                                line.append(unicode(row.mol.mw))
                            if 'hba' in options:
                                line.append(unicode(row.mol.hba))
                            if 'hbd' in options:
                                line.append(unicode(row.mol.hbd))
                            if 'tpsa' in options:
                                line.append(unicode(row.mol.tpsa))
                            if 'logp' in options:
                                line.append(unicode(row.mol.logp))
                            if 'purity' in options:
                                pur = u''
                                for p in sorted(row.purity, key=lambda p: p.value, reverse=True):
                                    pur += u'%s : %s\n' % (p.value, p.type)
                                line.append(pur)
                            if 'create_date' in options:
                                line.append(unicode(row.create_date))
                            if 'owner' in options:
                                line.append(row.owner)
                            if 'box' in options:
                                line.append(row.box)
                            if 'entry' in options:
                                line.append(row.entry)
                            if 'source' in options:
                                line.append(row.source)
                            if 'content' in options:
                                if row.content:
                                    line.append(unicode(row.content.value))
                                else:
                                    line.append(u'None')
                            if 'tags' in options:
                                tagsy= ''
                                for tag in row.mol.tags:
                                    tagsy += tag.name + ', '
                                line.append(tagsy)
                            if 'notes' in options:
                                line.append(row.notes)
                            spamwriter.writerow(line)
                    import paste.fileapp
                    f = paste.fileapp.FileApp(filepath)
                    from tg import use_wsgi_app
                    return use_wsgi_app(f)

        if selection and not search_clicked:
            argv =''
            gids = ''
            for arg in selection:
                argv += '/' + arg
                tmp_result = DBSession.query(LCompound).get(arg)
                gids += '/' + str(tmp_result.gid)
            if kw['akcja'] == u'edit':
                redirect('/%s/molecules/multiedit/index%s' % (pname, gids))
            elif kw['akcja'] == u'results':
                if len(selection) == 1:
                    redirect('/%s/results/new_result%s' % (pname, argv))
                else:
                    redirect('/%s/results/multiresults/index%s' % (pname, argv))
            elif kw['akcja'] == u'htrf':
                if len(selection) == 1:
                    redirect('/%s/results/htrf/add_result2%s' % (pname, argv))
        currentPage = paginate.Page(lcompound, page, url=page_url, items_per_page=items)
        return dict(currentPage=currentPage,tmpl=tmpl, page='results', htmlRgb=htmlRgb, htmlRgb100=htmlRgb100, Num2Rgb=Num2Rgb, pname=pname, alltags=alltags, similarity=similarity, cells=cells, ulists=ulists, ulist=ulist)

    @expose()
    def deletefromlist(self, ulist_id, *args):
        """
            Delete compound from User List.
        """
        ulist = DBSession.query(UserLists).get(ulist_id)
#        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
#        ulists = [l for l in user.lists if l.table == 'Results']
        if (ulist in user.lists) or (user in ulist.permitusers):
            if ulist.elements:
                import pickle
                elements = [int(el) for el in pickle.loads(ulist.elements)]
                for arg in args:
                    if int(arg) in elements:
                        elements.remove(int(arg))
                ulist.elements = pickle.dumps(elements)
                flash(l_(u'Task completed successfully'))
        else:
            flash(l_(u'Permission denied'), 'error')
        redirect(request.headers['Referer'])
        
