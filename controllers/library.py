# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
from tg import expose, flash, redirect, request
from tg.i18n import lazy_ugettext as l_
from molgears.model import DBSession, Tags, SFiles, LCompound, LPurity, LHistory, Group, Names, SCompound
from molgears.model import Compound, User, Projects, PCompound, LContentFiles, LContent, MinusState
from molgears.model.auth import UserLists
from molgears.lib.base import BaseController
import os
from pkg_resources import resource_filename
from sqlalchemy import desc

from rdkit import Chem
from molgears.widgets.structure import checksmi
from molgears.widgets.format import raw_path_basename
from datetime import datetime

from webhelpers import paginate
from tg.predicates import has_permission

__all__ = ['LibraryController']

public_dirname = os.path.join(os.path.abspath(resource_filename('molgears', 'public')))
files_dir = os.path.join(public_dirname, 'files')

# -------- LCompound controller ----------------------------------------------------------------------------------------------------------------------------------

class LibraryController(BaseController):
    @expose('molgears.templates.users.library.index')
    def index(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        threshold = float(user.threshold)/100.0
        items = user.items_per_page
        page_url = paginate.PageURL_WebOb(request)
        lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname))
        dsc = True
        order = 'id'
        tmpl = ''
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        selection = None
        similarity = None
        ulist = None
        ulists = set([l for l in user.lists if l.table == 'LCompounds'] + [l for l in user.tg_user_lists if l.table == 'LCompounds'])
        order = "id"
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
                        if ulist.table == 'LCompounds':
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
                    if v in ('gid', 'create_date', 'box', 'form', 'state', 'entry', 'source'):
                        order = LCompound.__getattribute__(LCompound, v)
                    elif v=='lcode':
                        order = LCompound.lcode
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
                    method = str(kw['method'])
                except Exception:
                    smiles = None
                    method = None
                    pass
                if smiles:
                    if checksmi(smiles):
                        from razi.functions import functions
                        from razi.expression import TxtMoleculeElement
                        if method == 'similarity':
                            from razi.postgresql_rdkit import tanimoto_threshold
                            DBSession.execute(tanimoto_threshold.set(threshold))
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            
                            search = DBSession.query(LCompound, tanimoto_sml).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint).order_by(desc(tanimoto_sml)).all()
                            lcompound = ()
                            similarity = ()
                            for row in search:
                                lcompound += (row[0], )
                                similarity += (row[1], )
                            currentPage = paginate.Page(lcompound, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage,tmpl=tmpl, page='library', pname=pname, alltags=alltags, similarity=similarity, ulists=ulists, ulist=ulist)
    
                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                        elif method == 'identity':
                            lcompound = DBSession.query(LCompound).filter(Compound.project.any(Projects.name==pname)).join(LCompound.mol).filter(Compound.structure.equals(smiles))
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
                if kw.has_key('text_owner') and kw['text_owner'] !=u'':
                    lcompound = lcompound.filter(LCompound.owner.like(kw['text_owner'].replace('*', '%')))
                if kw.has_key('text_source') and kw['text_source'] !=u'':
                    lcompound = lcompound.filter(LCompound.source.like(kw['text_source'].replace('*', '%')))
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
                    html = render_template({"length":len(lcompounds), "lcompound":lcompounds, "options":options, "size":size}, "genshi", "molgears.templates.users.library.print2", doctype=None)
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
                    sheet = wbk.add_sheet('arkusz1')
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
                    if 'formula' in options:
                        sheet.write(0,j,u'Formula')
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
                    if 'logp' in options:
                        sheet.write(0,j,u'logP')
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
                    if 'form' in options:
                        sheet.write(0,j,u'Forma')
                        j+=1
                    if 'state' in options:
                        sheet.write(0,j,u'Stan mag. [mg]')
                        j+=1
                    if 'purity' in options:
                        sheet.write(0,j, u'Purity')
                        j+=1
                    if 'create_date' in options:
                        sheet.write(0,j,u'Date')
                        j+=1
                    if 'owner' in options:
                        sheet.write(0,j,u'synthesis')
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
                        if 'formula' in options:
                            from rdkit.Chem.rdMolDescriptors import CalcMolFormula
                            formula = CalcMolFormula(Chem.MolFromSmiles(str(row.mol.structure)))
                            sheet.write(i,j, str(formula))
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
                        if 'logp' in options:
                            sheet.write(i,j, str(row.mol.logp))
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
                        if 'form' in options:
                            sheet.write(i,j, row.form)
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
                        i += 1
                    wbk.save(filepath)
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
                            if 'id' in options:
                                line.append(unicode(row.id))
                            if 'names' in options:
                                names = u''
                                for n in row.mol.names:
                                    names += n.name + u', '
                                line.append(names)
                            if 'inchi' in options:
                                line.append(row.mol.inchi)
                            if 'lso' in options:
                                line.append(row.lso)
                            if 'formula' in options:
                                from rdkit.Chem.rdMolDescriptors import CalcMolFormula
                                formula = CalcMolFormula(Chem.MolFromSmiles(str(row.mol.structure)))
                                line.append(formula)
                            if 'num_atoms' in options:
                                line.append(unicode(row.mol.num_hvy_atoms)+'/'+unicode(row.mol.num_atoms))
                            if 'mw' in options:
                                line.append(unicode(row.mol.mw))
                            if 'logp' in options:
                                line.append(unicode(row.mol.logp))
                            if 'hba' in options:
                                line.append(unicode(row.mol.hba))
                            if 'hbd' in options:
                                line.append(unicode(row.mol.hbd))
                            if 'tpsa' in options:
                                line.append(unicode(row.mol.tpsa))
                            if 'logp' in options:
                                line.append(unicode(row.mol.logp))
                            if 'form' in options:
                                line.append(row.form)
                            if 'state' in options:
                                line.append(unicode(row.state))
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
            for arg in selection:
                argv += '/' + arg
            if kw['akcja'] == u'edit':
                if len(selection) == 1:
                    redirect('/%s/library/edit%s' % (pname, argv))
                else:
                    redirect('/%s/library/multiedit/index%s' % (pname, argv))

        currentPage = paginate.Page(lcompound, page, url=page_url, items_per_page=items)
        return dict(currentPage=currentPage,tmpl=tmpl, page='library', pname=pname, alltags=alltags, similarity=similarity, ulists=ulists, ulist=ulist)

    @expose('molgears.templates.users.library.details')
    def details(self, *args, **kw):
        gid = int(args[0])
        lid = int(args[1])
        pname = request.environ['PATH_INFO'].split('/')[1]
        lcompound = DBSession.query(LCompound).filter_by(id=lid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').first()
        from rdkit.Chem.rdMolDescriptors import CalcMolFormula
        formula = CalcMolFormula(Chem.MolFromSmiles(str(lcompound.mol.structure)))
        scompound = DBSession.query(SCompound).filter_by(id=lcompound.sid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').first()
        pcompound = ()
        assert lcompound.gid == gid,  "GID error."
        if scompound:
            assert scompound.gid == gid,  "GID error."
            pcompound = DBSession.query(PCompound).filter_by(id=scompound.pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        if pcompound:
            assert pcompound.gid == gid,  "GID error."
        scompounds = DBSession.query(SCompound).filter_by(gid=gid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        pcompounds = DBSession.query(PCompound).filter(PCompound.gid==gid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        lcompounds = DBSession.query(LCompound).filter_by(gid=gid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        return dict(pcompound=pcompound, scompound=scompound, lcompound=lcompound, pcompounds=pcompounds, scompounds=scompounds, lcompounds=lcompounds, formula=formula, page='library', pname=pname)
        
    @expose('molgears.templates.users.library.edit')
    def edit(self, id):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(id)
        lcompound = DBSession.query( LCompound ).filter_by(id=id).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        come_from = request.headers['Referer']
        group = DBSession.query(Group).get(2)
        users = [u.display_name for u in group.users]
        users.sort()
        try:
            tags = [tag for tag in lcompound.mol.tags]
        except Exception:
            tags = [lcompound.mol.tags]
            pass
        return dict(lcompound=lcompound, alltags=alltags, tags=tags, come_from=come_from, users=users, page='library', pname=pname)

    @expose()
    def put(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = args[0]
        userid = request.identity['repoze.who.userid']
        lcompound = DBSession.query(LCompound).filter_by(id=id).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        try:
            if isinstance(kw['text_tags'], basestring):
                tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
            else:
                tagi = [DBSession.query( Tags ).get(int(tid)) for tid in kw['text_tags']]
        except Exception as msg:
            flash(l_(u'Tags error: %s' %msg))
            redirect(request.headers['Referer'])
        changes = u''
        if tagi and lcompound.mol.tags != tagi:
            lcompound.mol.tags = tagi
            changes += u' Tags: '
        for tag in tagi:
            changes += tag.name + ', '
        lhistory = LHistory()
        lhistory.gid = lcompound.mol.gid
#        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        lhistory.project = pname
        lhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lhistory.user = userid
        lhistory.status = 'Edit'
        try:
            if kw.has_key('acid'):
                kwas = str(kw['acid'])
            elif kw.has_key('kwasowa'):
                kwas = str(kw['kwasowa'])
            else:
                kwas = ''
            kwas = kwas.replace(',', '.') 
            kwas = float(kwas)
            if kw.has_key('basic'):
                zasada = str(kw['basic'])
            elif kw.has_key('zasadowa'):
                zasada = str(kw['zasadowa'])
            else:
                zasada = ''
            zasada = zasada.replace(',', '.') 
            zasada = float(zasada)
        except Exception as msg:
            kwas = None
            zasada = None
            flash(l_(u'Purity error. Float required: %s' % msg), 'error')
            redirect(request.headers['Referer'])
        if lcompound.purity:
            if lcompound.purity[0].type == 'kwasowa' or lcompound.purity[0].type == 'acid':
                kpurity = lcompound.purity[0]
                zpurity = lcompound.purity[1]
            else:
                kpurity = lcompound.purity[1]
                zpurity = lcompound.purity[0]
        else:
            kpurity = LPurity()
            kpurity.type = 'acid'
            kpurity.value = 0
            zpurity = LPurity()
            zpurity.type = 'basic'
            zpurity.value = 0
            DBSession.add(kpurity)
            DBSession.add(zpurity)
            lcompound.purity = [kpurity, zpurity]
        if kwas and kwas >= 0.0:
            if kpurity.type == 'kwasowa' or kpurity.type == 'acid':
                if kpurity.value != kwas:
                    kpurity.value = kwas
                    changes += u'; Acid Purity: ' + str(kwas)
                try:
                    if kw.has_key('file_acid'):
                        kwas_file = raw_path_basename(kw['file_acid'].filename)
                    elif kw.has_key('file_kwasowa'):
                        kwas_file = raw_path_basename(kw['file_kwasowa'].filename)
                    else:
                        kwas_file = None
                except Exception as msg:
                    kwas_file = None
                    pass
                if kwas_file:
                    number = DBSession.query(SFiles).count() + 1
                    new_kwas_file_name = str(number) + '_' + userid + '_' + str(id) + '_' + kwas_file
                    new_kwas_file_name.replace(' ', '_')
                    f_path = os.path.join(files_dir, new_kwas_file_name)
                    try:
                        f = file(f_path, "w")
                        if kw.has_key('file_acid'):
                            f.write(kw['file_acid'].value)
                        elif kw.has_key('file_kwasowa'):
                            f.write(kw['file_kwasowa'].value)
                        f.close()
                    except Exception as msg:
                        flash(l_(msg), 'error')
                        redirect(request.headers['Referer'])
                    sfile1 = SFiles()
                    sfile1.name = kwas_file
                    sfile1.filename = new_kwas_file_name
                    changes += '; File for acid analitics: ' + kwas_file + ' (' + new_kwas_file_name + ')'
                    kpurity.filename = [sfile1]
                else:
                    sfile1 = None
            else:
                sfile1 = None
                flash(l_(u'Acid purity not added'), 'warning')
        else:
            sfile1 = None
                
        if zasada and zasada >= 0.0:
            if zpurity.type == 'zasadowa' or zpurity.type == 'basic':
                if zpurity.value != zasada:
                    zpurity.value = zasada
                    changes += u'; Basic Purity: ' + str(zasada)
                try:
                    if kw.has_key('file_basic'):
                        zasada_file = raw_path_basename(kw['file_basic'].filename)
                    elif kw.has_key('file_zasadowa'):
                        zasada_file = raw_path_basename(kw['file_basic'].filename)
                    else:
                        zasada_file = None
                except Exception as msg:
                    zasada_file = None
                    pass
                if zasada_file:
                    number = DBSession.query(SFiles).count() + 1
                    new_zasada_file_name = str(number) + '_' + userid + '_' + str(id) + '_' + zasada_file
                    new_zasada_file_name.replace(' ', '_')
                    f_path = os.path.join(files_dir, new_zasada_file_name)
                    try:
                        f = file(f_path, "w")
                        if kw.has_key('file_basic'):
                            f.write(kw['file_basic'].value)
                        elif kw.has_key('file_zasadowa'):
                            f.write(kw['file_zasadowa'].value)
                        f.close()
                    except Exception as msg:
                        flash(l_(msg), 'error')
                        redirect(request.headers['Referer'])
                    sfile2 = SFiles()
                    sfile2.name = zasada_file
                    sfile2.filename = new_zasada_file_name
                    changes += '; File for basic analitics: ' + zasada_file + ' (' + new_zasada_file_name +')'
                    zpurity.filename = [sfile2]
                else:
                    sfile2 = None
            else:
                sfile2 = None
                flash(l_(u'Basic purity not added'), 'warning')
        else:
            sfile2 = None
        if kw.has_key('showme'):
            if kw['showme'] == "True":
                lcompound.showme = True
                changes += u'; Pokaż w testach: ' + kw['showme']
            else:
                lcompound.showme = False
                changes += u'; Pokaż w testach: ' + kw['showme']
            
        if kw.has_key('notes')  and kw['notes'] != lcompound.notes:
            lcompound.notes = kw['notes']
            changes += u';Notes: ' + kw['notes']
        if kw.has_key('forma') and kw['forma'] != lcompound.form:
            lcompound.form = kw['forma']
            changes += u'; Forma: ' + kw['forma']
        if kw.has_key('minusstate') and kw['minusstate'] !=u'':
            state = str(kw['minusstate'])
            state = state.replace(',', '.') 
            try:
                if lcompound.state - float(state)>=0:
                    lcompound.state = lcompound.state - float(state)
                    minus = MinusState()
                    minus.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    minus.value = float(state)
                    lcompound.minusstate.append(minus)
                    DBSession.add(minus)
                    changes += '; Stan mag.[mg]: ' + str(lcompound.state)
                else:
                    flash(l_(u'Stock status should be positive'), 'error')
                    redirect(request.headers['Referer'])
            except Exception as msg:
                flash(l_(u'Error %s. Float required' % msg), 'error')
                redirect(request.headers['Referer'])
        if kw.has_key('box') and kw['box'] != lcompound.box:
            lcompound.box = kw['box']
            changes += '; Pudelko: ' + kw['box']
        if kw.has_key('entry') and kw['entry'] != lcompound.entry:
            lcompound.entry = kw['entry']
            changes += '; Pozycja: ' + kw['entry']
        if kw.has_key('lso') and kw['lso'].upper() != lcompound.lso:
            lcompound.lso = kw['lso'].upper()
            changes += '; LSO: ' + kw['lso']
        if kw.has_key('source') and kw['source'] != lcompound.source:
            lcompound.source = kw['source']
            changes += '; Source: ' + kw['source']
        if kw.has_key('chemist') and kw['chemist'] != lcompound.owner:
            lcompound.owner = kw['chemist']
            changes += '; synthesis: ' + kw['chemist']
            
        try:
            lcontentfile1 = raw_path_basename(kw['lcontentfile1'].filename)
        except Exception as msg:
            lcontentfile1 = None
            pass
        try:
            lcontentfile2 = raw_path_basename(kw['lcontentfile2'].filename)
        except Exception as msg:
            lcontentfile2 = None
            pass
        try:
            lcontentvalue = str(kw['lcontent'])
            lcontentvalue = lcontentvalue.replace(',', '.') 
            lcontentvalue = float(lcontentvalue)
        except Exception as msg:
            lcontentvalue = None

        if lcontentvalue and lcompound.content and lcontentvalue != lcompound.content.value:
            lcontent = lcompound.content
            lcontent.value = lcontentvalue
            changes += u'; Zawartość: ' + kw['lcontent']
        elif lcontentvalue and lcompound.content and lcontentvalue == lcompound.content.value:
            lcontent = lcompound.content
        elif lcontentvalue and not lcompound.content:
            lcontent = LContent()
            lcontent.value = lcontentvalue
            changes += u'; Zawartość: ' + kw['lcontent']
            DBSession.add(lcontent)
        else:
            lcontent = None
        if lcontent:
            if lcontent.files:
                for lfile in lcontent.files:
                    lfile_replace_name = "lcontentfile_replace_%s" % lfile.id
                    if kw.has_key(lfile_replace_name) and kw[lfile_replace_name] != u'':
                        lcontentfile_replace_name = raw_path_basename(kw[lfile_replace_name].filename)
                        number = lfile.id
                        new_lcontentfile_name = str(number) + '_' + userid + '_' + str(id) + '_' + lcontentfile_replace_name
                        new_lcontentfile_name.replace(' ', '_')
                        fpath = os.path.join(files_dir, 'lcontent', new_lcontentfile_name)
                        try:
                            f = file(fpath, "w")
                            f.write(kw[lfile_replace_name].value)
                            f.close()
                        except Exception as msg:
                            flash(l_(msg), 'error')
                            redirect(request.headers['Referer'])
                        lfile.name = lcontentfile_replace_name
                        lfile.filename = new_lcontentfile_name
                        changes += u'; Zmaina pliku zawartości %s na : ' %lfile.id + lcontentfile_replace_name + ' (' + new_lcontentfile_name +')'
            if lcontentfile1:
                number = DBSession.query(LContentFiles).count() + 1
                new_lcontentfile_name = str(number) + '_' + userid + '_' + str(id) + '_' + lcontentfile1
                new_lcontentfile_name.replace(' ', '_')
                fpath = os.path.join(files_dir, 'lcontent', new_lcontentfile_name)
                try:
                    f = file(fpath, "w")
                    f.write(kw['lcontentfile1'].value)
                    f.close()
                except Exception as msg:
                    flash(l_(msg), 'error')
                    redirect(request.headers['Referer'])
                lcfile1 = LContentFiles()
                lcfile1.name = lcontentfile1
                lcfile1.filename = new_lcontentfile_name
                changes += u'; Plik zawartość: ' + lcontentfile1 + ' (' + new_lcontentfile_name +')'
                lcontent.files += [lcfile1]
            else:
                lcfile1 = None
            if lcontentfile2:
                number = DBSession.query(LContentFiles).count() + 1
                new_lcontentfile_name = str(number) + '_' + userid + '_' + str(id) + '_' + lcontentfile2
                new_lcontentfile_name.replace(' ', '_')
                fpath = os.path.join(files_dir, 'lcontent', new_lcontentfile_name)
                try:
                    f = file(fpath, "w")
                    f.write(kw['lcontentfile2'].value)
                    f.close()
                except Exception as msg:
                    flash(l_(msg), 'error')
                    redirect(request.headers['Referer'])
                lcfile2 = LContentFiles()
                lcfile2.name = lcontentfile2
                lcfile2.filename = new_lcontentfile_name
                changes += u'; Plik zawartość: ' + lcontentfile2 + ' (' + new_lcontentfile_name +')'
                lcontent.files += [lcfile2]
            else:
                lcfile2 = None
            lcompound.content = lcontent
            
        else:
            lcfile1 = None
            lcfile2 = None
        lhistory.changes = changes
        lcompound.history += [lhistory]
        
        if sfile1:
            DBSession.add(sfile1)
        if sfile2:
            DBSession.add(sfile2)
        if lcfile1:
            DBSession.add(lcfile1)
        if lcfile2:
            DBSession.add(lcfile2)
        
        DBSession.add(lhistory)
        DBSession.flush()
        if kw and kw.has_key('come_from'):
            come_from = kw['come_from']
        else:
            come_from = request.headers['Referer']
        redirect(come_from)
        
    @expose('molgears.templates.users.library.multiedit')
    def multiedit(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        come_from = request.headers['Referer']
        group = DBSession.query(Group).get(2)
        users = [u.display_name for u in group.users]
        if kw:
            try:
                if isinstance(kw['argv'], basestring):
                    argv = [kw['argv']]
                else:
                    argv = [id for id in kw['argv']]
            except Exception:
                argv = None
            try:
                if kw.has_key('notes') != u'':
                    notes = kw['notes']
                else:
                    notes = None
            except Exception:
                notes = None
            try:
                if kw.has_key('source') != u'':
                    source = kw['source']
                else:
                    source = None
            except Exception:
                source = None
            try:
                if kw.has_key('box') != u'':
                    box = kw['box']
                else:
                    box = None
            except Exception:
                box = None
            if argv:
                userid = request.identity['repoze.who.userid']
                for arg in argv:
                    try:
                        if isinstance(kw['text_tags'], basestring):
                            tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                        else:
                            tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
                    except Exception:
                        tagi = None
                    lcompound = DBSession.query(LCompound).filter_by(id=int(arg)).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
                    lhistory = LHistory()
                    lhistory.gid = lcompound.mol.gid
#                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    lhistory.project = pname
                    lhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    lhistory.user = userid
                    lhistory.status = u'Multi - edit'
                    lhistory.changes = u''
                    if tagi and lcompound.mol.tags != tagi:
                        lcompound.mol.tags = tagi
                        lhistory.changes += u' Tags: '
                        for tag in tagi:
                            lhistory.changes += tag.name + u';'
                    if box and box != lcompound.box:
                        lcompound.box = box
                        lhistory.changes += u' Pudełko: ' + box + u';'
                    if source and source != lcompound.source:
                        lcompound.source = source
                        lhistory.changes += u' Źródło: ' + source + u';'
                    if notes and notes != lcompound.notes:
                        lcompound.notes = notes
                        lhistory.changes += u' Notes: ' + notes + u';'
                    if kw.has_key('chemist') and kw['chemist'] != u'' and kw['chemist'] != lcompound.owner:
                        lcompound.owner = kw['chemist']
                        lhistory.changes += '; synthesis: ' + kw['chemist']
                    lcompound.history += [lhistory]
                    DBSession.add(lhistory)
                    DBSession.flush()
                    #transaction.commit()
                if kw.has_key('come_from'):
                    come_from = kw['come_from']
                else:
                    come_from = request.headers['Referer']
                flash(l_(u'Task completed successfully'))
                redirect(come_from)
                
        return dict(alltags=alltags, args=args, come_from=come_from, users=users, page='library', pname=pname)
        
    @expose()
    def download(self, *args):
        pname = request.environ['PATH_INFO'].split('/')[1]
        if not args:
            redirect(request.headers['Referer'])
        else:
            filename = args[-1]
            ext = args[-2]
            filepath = os.path.join('./molgears/files/download/', str(filename + '.' + ext))
#            userid = request.identity['repoze.who.userid']
        if has_permission('user'):
            if len(args)>=3:
                lcompound = ()
                gids = []
                for arg in args[:-2]:
                    test=DBSession.query(LCompound).filter(LCompound.id==int(arg)).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
                    if test.gid not in gids:
                        lcompound += (test, )
                        gids.append(test.gid)
            else:
                lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
                
            if ext == u'xls':
                import xlwt
                wbk = xlwt.Workbook()
                sheet = wbk.add_sheet('arkusz1')
                sheet.write(0,0,u'GID')
                sheet.write(0,1,u'ID')
                sheet.write(0,2,u'Name')
                sheet.write(0,3,u'SMILES')
                sheet.write(0,4,u'LSO')
                sheet.write(0,5,u'Stan')
                sheet.write(0,6,u'Forma')
                sheet.write(0,7,u'Pudełko')
                sheet.write(0,8,u'Pozycja')
                sheet.write(0,9,u'Źródło')
                sheet.write(0,10,u'Notes')
                i = 1
                for row in lcompound:
                    sheet.write(i,0, str(row.gid))
                    sheet.write(i,1, str(row.id))
                    sheet.write(i,2, str(row.mol.name))
                    sheet.write(i,3, str(row.mol.structure))
                    sheet.write(i,4, row.lso)
                    sheet.write(i,5, row.state)
                    sheet.write(i,6, row.form)
                    sheet.write(i,7, row.box)
                    sheet.write(i,8, row.entry)
                    sheet.write(i,9, row.source)
                    sheet.write(i,10, row.notes)
                    i += 1
                wbk.save(filepath)
            if ext == u'txt':
                f = open(filepath, 'w')
                for row in lcompound:
                    f.write('%s %s \n' % (row.mol.structure, row.mol.name))
                f.close()
            import paste.fileapp
            f = paste.fileapp.FileApp(filepath)
            from tg import use_wsgi_app
            return use_wsgi_app(f)
        else:
            flash(l_('Error 404'),'error')
            redirect(request.headers['Referer'])
                    
    @expose('molgears.templates.users.library.history')
    def history(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        history = DBSession.query( LHistory ).filter(LHistory.project.any(Projects.name==pname))
        order='LHistory.id'
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        items = user.items_per_page
        tmpl = ''
        dsc = True
        from datetime import timedelta
        now=datetime.now()
        one_day=timedelta(days=1)
        try:
            if kw['search'] != u'':
                search_clicked = kw['search']
            else:
                search_clicked = None
        except Exception:
            search_clicked = None
        if kw:
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    if v == 'gid':
                        order = LHistory.lcompound_id
                    elif v == 'user':
                        order = LHistory.user
                    elif v == 'date':
                        order = LHistory.date
                    else:
                        order = v
                if str(k) != 'remove':
                    tmpl += str(k) + '=' + str(v) + '&'
            if search_clicked:
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_gid'])
                        history = history.filter(LCompound.id == gid )
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_user') and kw['text_user'] !=u'':
                    history = history.filter(LHistory.user.like(kw['text_user'].replace('*', '%')))
                if kw.has_key('text_status') and kw['text_status'] !=u'':
                    history = history.filter(LHistory.status.like(kw['text_status'].replace('*', '%')))
                if kw.has_key('text_changes') and kw['text_changes'] !=u'':
                    history = history.filter(LHistory.changes.like(kw['text_changes'].replace('*', '%')))
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    history = history.filter(LHistory.date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            history = history.filter(LHistory.date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        history = history.filter(LHistory.date < date_to)
        if dsc:
            history = history.order_by(desc(order).nullslast())
        else:
            history = history.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(history, page, url=page_url, items_per_page=items)
        return dict(history=currentPage.items, currentPage=currentPage, tmpl=tmpl, one_day=one_day, now=now, page='library', pname=pname)

    @expose()
    def delete(self, *args):
        lid = args[0]
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        come_from = "/MDM/library/"
        if has_permission('kierownik') or userid == 'urszula.bulkowska':
            if len(args) == 1:
                lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.id==lid).first()
            else:
                flash(l_(u'Remove only one by one'), 'error')
                redirect(come_from)
            if lcompound:
                if len(lcompound.mdm2) < 1:
                    history = LHistory()
                    history.user = userid
                    history.status = u'nowy związek'
                    history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    history.project = pname
                    history.changes = u'Usuwanie związku o numerze GID: %s' % lid
                    lcompound.history += [history]
                    DBSession.add(history)
                    DBSession.delete(lcompound)
                    flash(l_(u'Task completed successfully'))
                else:
                    flash(l_(u'Removing disabled due other connections')) # compound has related information in other tables
            else:
                flash(l_(u'Compound disabled or not exist'))
        else:
            flash(l_(u'Permission denied'), 'error')
        redirect(come_from)

    @expose()
    def deletefromlist(self, ulist_id, *args):
        """
            Delete compound from User List.
        """
        ulist = DBSession.query(UserLists).get(ulist_id)
#        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
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
