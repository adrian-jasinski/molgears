# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
from tg import expose, flash, redirect, request
from tg.i18n import lazy_ugettext as l_
from molgears.model import DBSession, PCompound, PHistory, PStatus, Tags, SCompound, SStatus, SHistory, LCompound
from molgears.model import Compound, Names, Efforts, User, Group, Projects
from molgears.model.auth import UserLists
from molgears.lib.base import BaseController
import os
#from pkg_resources import resource_filename
from sqlalchemy import desc

from rdkit import Chem
from molgears.widgets.structure import checksmi
from datetime import datetime
from webhelpers import paginate
from tg.predicates import has_permission

__all__ = ['SelectController']

class SelectController(BaseController):
    @expose('molgears.templates.users.select.index')
    def index(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        page_url = paginate.PageURL_WebOb(request)
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        threshold = float(user.threshold)/100.0
        items = user.items_per_page
        pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(PCompound.status==DBSession.query(PStatus).get(1)).filter(Compound.project.any(Projects.name==pname))
        dsc = True
        order = 'id'
        selection = None
        similarity = None
        tmpl = ''
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        allstatus = [stat for stat in DBSession.query(PStatus).all()]
        ulists = set([l for l in user.lists if l.table == 'PCompounds'] + [l for l in user.tg_user_lists if l.table == 'PCompounds'])
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
                        order = PCompound.gid
                    elif v == 'create_date':
                        order = PCompound.create_date
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
                    smiles = str(kw['text_smiles'])
                    method = str(kw['method'])
                except Exception:
                    smiles = None
                    method = None
                    pass
                if smiles:
                    if checksmi(smiles):
                        from razi.functions import functions
                        from razi.expression import TxtMoleculeElement
                        from razi.postgresql_rdkit import tanimoto_threshold
                        if method == 'similarity':
                            DBSession.execute(tanimoto_threshold.set(threshold))
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            limit = user.limit_sim
                            search = DBSession.query(PCompound, tanimoto_sml).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint).order_by(desc(tanimoto_sml)).limit(limit).all()
                            pcompound = ()
                            similarity = ()
                            for row in search:
                                pcompound += (row[0], )
                                similarity += (row[1], )
                            currentPage = paginate.Page(pcompound, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage, tmpl=tmpl, page='select', pname=pname, similarity=similarity, alltags=alltags, ulists=ulists, allstatus=allstatus)
    
                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                        elif method == 'identity':
                            pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(Compound.structure.equals(smiles))
                    else:
                        flash(l_(u'SMILES error'), 'warning')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_GID'])
                        pcompound = pcompound.filter_by(gid = gid )
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_ID') and kw['text_ID'] !=u'':
                    try:
                        id = int(kw['text_ID'])
                        pcompound = pcompound.filter(PCompound.id == id)
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_name') and kw['text_name'] !=u'':
                    pcompound = pcompound.filter(Compound.names.any(Names.name.like(kw['text_name'].strip().replace('*', '%'))))
                if kw.has_key('text_owner') and kw['text_owner'] !=u'':
                    pcompound = pcompound.filter(PCompound.owner.like(kw['text_owner'].replace('*', '%')))
                if kw.has_key('text_principal') and kw['text_principal'] !=u'':
                    pcompound = pcompound.filter(PCompound.principal.like(kw['text_principal'].replace('*', '%')))
                if kw.has_key('text_notes') and kw['text_notes'] !=u'':
                    pcompound = pcompound.filter(PCompound.notes.like(kw['text_notes'].replace('*', '%')))
                if kw.has_key('text_priority') and kw['text_priority'] !=u'':
                    try:
                        id = int(kw['text_priority'])
                        pcompound = pcompound.filter(PCompound.priority == id)
                    except Exception as msg:
                        flash(l_(u'Priority should be a number from 0 to 5'), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    pcompound = pcompound.filter(PCompound.create_date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            pcompound = pcompound.filter(PCompound.create_date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        pcompound = pcompound.filter(PCompound.create_date < date_to)                        
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
                    pcompound = pcompound.filter(Compound.tags.any(Tags.id.in_(tagi)))
                
                try:
                    statusy = kw['text_status']
                    if isinstance(statusy, basestring):
                        statusy = [int(statusy)]
                    else:
                        statusy = [int(sid) for sid in statusy]
                except Exception:
                    statusy = None
                    pass
                if statusy:
                    pcompound = pcompound.filter(PCompound.status_id.in_(statusy))
                for k, v in kw.iteritems():
                    if str(k) == 'desc' and str(v) != '1':
                        dsc = None
                    elif str(k) == 'order_by':
                        order = v
                        if order == 'gid':
                            order = PCompound.gid
                        elif order == 'status':
                            order = PCompound.status_id
                        elif order == 'create_date':
                            order = PCompound.create_date
        if dsc:
            pcompound = pcompound.order_by(desc(order).nullslast())
        else:
            pcompound = pcompound.order_by(order)

        if search_clicked and kw['search'] == "Download":
            if kw['file_type'] and kw['file_type'] != u'' and kw['sell_type'] and kw['sell_type'] != u'':
                if kw['sell_type'] == u'all':
                    pcompounds = pcompound.all()
                elif kw['sell_type'] == u'selected':
                    if selection:
                        pcompounds = ()
                        for el in selection:
                            pcompounds += (DBSession.query(PCompound).get(el), )
                    else:
                        flash(l_(u'Lack of selected structures for download'), 'error')
                        redirect(request.headers['Referer'])
                elif kw['sell_type'] == u'range':
                    pcompounds = pcompound.all()
                    if kw.has_key('select_from') and kw['select_from'] != u'':
                        try:
                            select_from = int(kw['select_from']) -1 
                            if select_from<1 or select_from>len(pcompounds):
                                select_from = 0
                        except Exception:
                            select_from = 0
                    else:
                        select_from = 0
                    if kw.has_key('select_to') and kw['select_to'] != u'':
                        try:
                            select_to = int(kw['select_to'])
                            if select_to<2 or select_to>len(pcompounds):
                                select_to = len(pcompounds)
                        except Exception:
                            select_to = len(pcompounds)
                    else:
                        select_to = len(pcompounds)
                    pcompounds_new = ()
                    for el in range(select_from, select_to):
                        pcompounds_new += (pcompounds[el], )
                    pcompounds = pcompounds_new
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
                    html = render_template({"length":len(pcompounds), "pcompound":pcompounds, "options":options, "size":size}, "genshi", "molgears.templates.users.select.print2", doctype=None)
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
                        sheet.write(0,j,'Nr.')
                        j+=1
                    if 'gid' in options:
                        sheet.write(0,j,'GID')
                        j+=1
                    if 'id' in options:
                        sheet.write(0,j,'ID')
                        j+=1
                    if 'name' in options:
                        sheet.write(0,j,'Name')
                        j+=1
                    if 'names' in options:
                        sheet.write(0,j,'Names')
                        j+=1
                    if 'image' in options:
                        sheet.write(0,j,'Image')
                        j+=1
                    if 'smiles' in options:
                        sheet.write(0,j,'SMILES')
                        j+=1
                    if 'inchi' in options:
                        sheet.write(0,j,'InChi')
                        j+=1
                    if 'num_atoms' in options:
                        sheet.write(0,j,'Atoms')
                        j+=1
                    if 'mw' in options:
                        sheet.write(0,j,'MW')
                        j+=1
                    if 'logp' in options:
                        sheet.write(0,j,'logP')
                        j+=1
                    if 'hba' in options:
                        sheet.write(0,j,'hba')
                        j+=1
                    if 'hbd' in options:
                        sheet.write(0,j,'hbd')
                        j+=1
                    if 'tpsa' in options:
                        sheet.write(0,j,'tpsa')
                        j+=1
                    if 'create_date' in options:
                        sheet.write(0,j,'Date')
                        j+=1
                    if 'owner' in options:
                        sheet.write(0,j,'Creator')
                        j+=1
                    if 'principal' in options:
                        sheet.write(0,j,'principal')
                        j+=1
                    if 'priority' in options:
                        sheet.write(0,j,'Priorytet')
                        j+=1
                    if 'status' in options:
                        sheet.write(0,j,'Status')
                        j+=1
                    if 'tags' in options:
                        sheet.write(0,j,'Tags')
                        j+=1
                    if 'notes' in options:
                        sheet.write(0,j,'Notes')
                        j+=1
                    i = 1
                    for row in pcompounds:
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
                        if 'create_date' in options:
                            sheet.write(i,j, str(row.create_date))
                            j+=1
                        if 'owner' in options:
                            sheet.write(i,j, row.owner)
                            j+=1
                        if 'principal' in options:
                            sheet.write(i,j, row.principal)
                            j+=1
                        if 'priority' in options:
                            sheet.write(i,j, row.priority)
                            j+=1
                        if 'status' in options:
                            sheet.write(i,j, row.status.name)
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
                        for row in pcompounds:
                            line =[]
                            if 'smiles' in options:
                                line.append(str(row.mol.structure))
                            if 'name' in options:
                                line.append(row.mol.name)
                            if 'nr' in options:
                                line.append(unicode(pcompounds.index(row)+1))
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
                            if 'create_date' in options:
                                line.append(unicode(row.create_date))
                            if 'owner' in options:
                                line.append(row.owner)
                            if 'principal' in options:
                                line.append(row.principal)
                            if 'priority' in options:
                                line.append(unicode(row.priority))
                            if 'status' in options:
                                line.append(row.status.name)
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
            argv = ''
            for arg in selection:
                argv += '/' + arg
            if kw['akcja'] == u'edit':
                if len(selection) == 1:
                    redirect('/%s/select/edit%s' % (pname, argv))
                else:
                    redirect('/%s/select/multiedit/index%s' % (pname, argv))
            elif kw['akcja'] == u'accept':
                if len(selection) == 1:
                    redirect('/%s/select/accept%s' % (pname, argv))
                else:
                    redirect('/%s/select/multiaccept/index%s' % (pname, argv))
            elif kw['akcja'] == u'delete':
                if len(selection) == 1:
                    redirect('/%s/select/post_delete%s' % (pname, argv))
                else:
                    redirect('/%s/select/multidelete/index%s' % (pname, argv))
            else:
                redirect('/%s/select/%s%s' % (pname, kw['akcja'], argv))

        currentPage = paginate.Page(pcompound, page, url=page_url, items_per_page=items)
        return dict(currentPage=currentPage, tmpl=tmpl, page='select', pname=pname, similarity=similarity, alltags=alltags, allstatus=allstatus, ulists=ulists)
        
    @expose('molgears.templates.users.select.get_all')
    def get_all(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        page_url = paginate.PageURL_WebOb(request)
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        ulists = [l for l in user.lists if l.table == 'PCompounds']
        threshold = float(user.threshold)/100.0
        items = user.items_per_page
        dsc = True
        order = 'id'
        selection = None
        similarity = None
        ulist = None
        tmpl = ''
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        allstatus = [stat for stat in DBSession.query( PStatus ).all()]
        pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname))
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
                        if ulist.table == 'PCompounds':
                            pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(PCompound.id.in_(elements))
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
                    if v == 'gid':
                        order = PCompound.gid
                    elif v == 'create_date':
                        order = PCompound.create_date
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
                    smiles = str(kw['text_smiles'])
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
                            from razi.postgresql_rdkit import tanimoto_threshold as t_threshold
                            DBSession.execute(t_threshold.set(threshold))
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            limit = user.limit_sim
                            search = DBSession.query(PCompound, tanimoto_sml).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint).order_by(desc(tanimoto_sml)).limit(limit).all()
                            pcompound = ()
                            similarity = ()
                            for row in search:
                                pcompound += (row[0], )
                                similarity += (row[1], )
                            currentPage = paginate.Page(pcompound, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage, tmpl=tmpl, page='select', pname=pname, similarity=similarity, alltags=alltags, allstatus=allstatus, ulists=ulists, ulist=ulist)
    
                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                        elif method == 'identity':
                            pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(Compound.structure.equals(smiles))
                    else:
                        flash(l_(u'SMILES error'), 'warning')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_GID'])
                        pcompound = pcompound.filter_by(gid = gid )
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_ID') and kw['text_ID'] !=u'':
                    try:
                        id = int(kw['text_ID'])
                        pcompound = pcompound.filter(PCompound.id == id)
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_name') and kw['text_name'] !=u'':
                    pcompound = pcompound.filter(Compound.names.any(Names.name.like(kw['text_name'].strip().replace('*', '%'))))
                if kw.has_key('text_owner') and kw['text_owner'] !=u'':
                    pcompound = pcompound.filter(PCompound.owner.like(kw['text_owner'].replace('*', '%')))
                if kw.has_key('text_principal') and kw['text_principal'] !=u'':
                    pcompound = pcompound.filter(PCompound.principal.like(kw['text_principal'].replace('*', '%')))
                if kw.has_key('text_notes') and kw['text_notes'] !=u'':
                    pcompound = pcompound.filter(PCompound.notes.like(kw['text_notes'].replace('*', '%')))
                if kw.has_key('text_priority') and kw['text_priority'] !=u'':
                    try:
                        id = int(kw['text_priority'])
                        pcompound = pcompound.filter(PCompound.priority == id)
                    except Exception as msg:
                        flash(l_(u'Priority should be a number from 0 to 5'), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    pcompound = pcompound.filter(PCompound.create_date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            pcompound = pcompound.filter(PCompound.create_date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        pcompound = pcompound.filter(PCompound.create_date < date_to)
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
                    pcompound = pcompound.filter(Compound.tags.any(Tags.id.in_(tagi)))
                
                try:
                    statusy = kw['text_status']
                    if isinstance(statusy, basestring):
                        statusy = [int(statusy)]
                    else:
                        statusy = [int(sid) for sid in statusy]
                except Exception:
                    statusy = None
                    pass
                if statusy:
                    pcompound = pcompound.filter(PCompound.status_id.in_(statusy))
                for k, v in kw.iteritems():
                    if str(k) == 'desc' and str(v) != '1':
                        dsc = None
                    elif str(k) == 'order_by':
                        order = v
                        if order == 'gid':
                            order = PCompound.gid
                        elif order == 'status':
                            order = PCompound.status_id
                        elif order == 'create_date':
                            order = PCompound.create_date
                            
        if dsc:
            pcompound = pcompound.order_by(desc(order).nullslast())
        else:
            pcompound = pcompound.order_by(order)

        if search_clicked and kw['search'] == "Download":
            if kw['file_type'] and kw['file_type'] != u'' and kw['sell_type'] and kw['sell_type'] != u'':
                if kw['sell_type'] == u'all':
                    pcompounds = pcompound.all()
                elif kw['sell_type'] == u'selected':
                    if selection:
                        pcompounds = ()
                        for el in selection:
                            pcompounds += (DBSession.query(PCompound).get(el), )
                    else:
                        flash(l_(u'Lack of selected structures for download'), 'error')
                        redirect(request.headers['Referer'])
                elif kw['sell_type'] == u'range':
                    pcompounds = pcompound.all()
                    if kw.has_key('select_from') and kw['select_from'] != u'':
                        try:
                            select_from = int(kw['select_from']) -1 
                            if select_from<1 or select_from>len(pcompounds):
                                select_from = 0
                        except Exception:
                            select_from = 0
                    else:
                        select_from = 0
                    if kw.has_key('select_to') and kw['select_to'] != u'':
                        try:
                            select_to = int(kw['select_to'])
                            if select_to<2 or select_to>len(pcompounds):
                                select_to = len(pcompounds)
                        except Exception:
                            select_to = len(pcompounds)
                    else:
                        select_to = len(pcompounds)
                    pcompounds_new = ()
                    for el in range(select_from, select_to):
                        pcompounds_new += (pcompounds[el], )
                    pcompounds = pcompounds_new
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
                    html = render_template({"length":len(pcompounds), "pcompound":pcompounds, "options":options, "size":size}, "genshi", "molgears.templates.users.select.print2", doctype=None)
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
                        sheet.write(0,j,'Nr.')
                        j+=1
                    if 'gid' in options:
                        sheet.write(0,j,'GID')
                        j+=1
                    if 'id' in options:
                        sheet.write(0,j,'ID')
                        j+=1
                    if 'name' in options:
                        sheet.write(0,j,'Name')
                        j+=1
                    if 'names' in options:
                        sheet.write(0,j,'Names')
                        j+=1
                    if 'image' in options:
                        sheet.write(0,j,'Image')
                        j+=1
                    if 'smiles' in options:
                        sheet.write(0,j,'SMILES')
                        j+=1
                    if 'inchi' in options:
                        sheet.write(0,j,'InChi')
                        j+=1
                    if 'num_atoms' in options:
                        sheet.write(0,j,'Atoms')
                        j+=1
                    if 'mw' in options:
                        sheet.write(0,j,'MW')
                        j+=1
                    if 'logp' in options:
                        sheet.write(0,j,'logP')
                        j+=1
                    if 'hba' in options:
                        sheet.write(0,j,'hba')
                        j+=1
                    if 'hbd' in options:
                        sheet.write(0,j,'hbd')
                        j+=1
                    if 'tpsa' in options:
                        sheet.write(0,j,'tpsa')
                        j+=1
                    if 'create_date' in options:
                        sheet.write(0,j,'Date')
                        j+=1
                    if 'owner' in options:
                        sheet.write(0,j,'Creator')
                        j+=1
                    if 'principal' in options:
                        sheet.write(0,j,'principal')
                        j+=1
                    if 'priority' in options:
                        sheet.write(0,j,'Priorytet')
                        j+=1
                    if 'status' in options:
                        sheet.write(0,j,'Status')
                        j+=1
                    if 'tags' in options:
                        sheet.write(0,j,'Tags')
                        j+=1
                    if 'notes' in options:
                        sheet.write(0,j,'Notes')
                        j+=1
                    i = 1
                    for row in pcompounds:
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
                        if 'create_date' in options:
                            sheet.write(i,j, str(row.create_date))
                            j+=1
                        if 'owner' in options:
                            sheet.write(i,j, row.owner)
                            j+=1
                        if 'principal' in options:
                            sheet.write(i,j, row.principal)
                            j+=1
                        if 'priority' in options:
                            sheet.write(i,j, row.priority)
                            j+=1
                        if 'status' in options:
                            sheet.write(i,j, row.status.name)
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
                        for row in pcompounds:
                            line =[]
                            if 'smiles' in options:
                                line.append(str(row.mol.structure))
                            if 'name' in options:
                                line.append(row.mol.name)
                            if 'nr' in options:
                                line.append(unicode(pcompounds.index(row)+1))
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
                            if 'create_date' in options:
                                line.append(unicode(row.create_date))
                            if 'owner' in options:
                                line.append(row.owner)
                            if 'principal' in options:
                                line.append(row.principal)
                            if 'priority' in options:
                                line.append(unicode(row.priority))
                            if 'status' in options:
                                line.append(row.status.name)
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
                    redirect('/%s/select/edit%s' % (pname, argv))
                else:
                    redirect('/%s/select/multiedit/index%s' % (pname, argv))
            elif kw['akcja'] == u'accept':
                if len(selection) == 1:
                    redirect('/%s/select/accept%s' % (pname, argv))
                else:
                    redirect('/%s/select/multiaccept/index%s' % (pname, argv))
            elif kw['akcja'] == u'delete':
                if len(selection) == 1:
                    redirect('/%s/select/post_delete%s' % (pname, argv))
                else:
                    redirect('/%s/select/multidelete/index%s' % (pname, argv))
            else:
                redirect('/%s/select/%s%s' % (pname, kw['akcja'], argv))
        
        currentPage = paginate.Page(pcompound, page, url=page_url, items_per_page=items)
        return dict(currentPage=currentPage, tmpl=tmpl, page='select', pname=pname, similarity=similarity, alltags=alltags, allstatus=allstatus, ulists=ulists, ulist=ulist)
 

    @expose('molgears.templates.users.select.edit')
    def edit(self, id):
        pname = request.environ['PATH_INFO'].split('/')[1]
        pid = int(id)
        pcompound = DBSession.query( PCompound ).filter_by(id=pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        principals = DBSession.query (Group).get(3)
        if not pcompound:
            flash(l_(u'Permission denied'), 'warning')
            redirect(request.headers['Referer'])
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        try:
            tags = [tag for tag in pcompound.mol.tags]
        except Exception:
            tags = [pcompound.mol.tags]
            pass
        come_from = request.headers['Referer']
        return dict(pcompound=pcompound, alltags=alltags, tags=tags, come_from=come_from, page='select', pname=pname, users=principals.users)
        
    @expose()
    def put(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
#        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        pid = int(args[0])
        userid = request.identity['repoze.who.userid']
        pcompound = DBSession.query(PCompound).filter_by(id=pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        
        try:
            if isinstance(kw['text_tags'], basestring):
                tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
            else:
                tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
        except Exception as msg:
            flash(l_(u'Tags error: %s' %msg))
            redirect(request.headers['Referer'])
        try:
            notes = kw['notes']
        except Exception:
            notes = None
            pass
        pchanges = u''
        if kw and kw.has_key('principal'):
            if kw['principal'] != pcompound.principal:
                pcompound.principal = kw['principal']
                pchanges += u' Odbiorca: ' + kw['principal'] + u';'
        if notes and notes != pcompound.notes:
            pcompound.notes = notes
            pchanges += u' Notes: ' + notes + u';'
        pchanges += u' Tags: '
        if tagi != pcompound.mol.tags:
            for tag in tagi:
                pchanges += str(tag.name) + '; '
            pcompound.mol.tags = tagi
        if int(kw['priority']) != pcompound.priority:
            pchanges += u' Priorytet' + str(kw['priority']) + u';'
            pcompound.priority = int(kw['priority'])
            scompound = DBSession.query(SCompound).filter_by(pid=pid).all()
            if scompound:
                for sc in scompound:
                    sc.priority = int(kw['priority'])
                    shistory = SHistory()
                    shistory.project = pname
                    shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    shistory.user = userid
                    shistory.status = u'Priority'
                    shistory.changes = u'Priority:' + kw['priority']
                    sc.history += [shistory]
                    DBSession.add(shistory)
        phistory = PHistory()
        phistory.project = pname
        phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        phistory.user = userid
        phistory.status = u'Edycja'
        phistory.changes = pchanges
        phistory.gid = pcompound.gid
        pcompound.history += [phistory]
        
        DBSession.add(phistory)
        DBSession.flush()
        if kw and kw.has_key('come_from'):
            come_from = kw['come_from']
        else:
            come_from = request.headers['Referer']
        flash(l_(u'Task completed successfully'))
        redirect(come_from)

    @expose()
    def reject(self, *args, **kw):
        """
        Chemist rejection of synthesis (if synthesis status <=2 and is synthesis owner).
        Chamge status of synthesis compound as rejected and set request compound status as canceled.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
#        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if args:
            for arg in args:
                try:
                    pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(PCompound.id==int(arg)).first()
                except Exception:
                    flash(l_(u'Compound number error'), 'error')
                    redirect(come_from)
                if pcompound:
                    scompounds = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(SCompound.pid==pcompound.id).all()
                    if scompounds:
                        for scompound in scompounds:
                            if scompound.status_id <= 2 and (scompound.owner == userid or has_permission('kierownik')):
                                shistory = SHistory()
                                shistory.gid = scompound.mol.gid
                                shistory.project = pname
                                shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                shistory.user = userid
                                shistory.status = u'Reject'
                                shistory.changes = u'Reject synthesis compound of GID %s (ID projektowe %s)' % (scompound.gid, arg)
                                scompound.status = DBSession.query(SStatus).get(5)
                                scompound.history += [shistory]
                                DBSession.add(shistory)
                    phistory = PHistory()
                    phistory.gid = pcompound.gid
                    phistory.project = pname
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.user = userid
                    phistory.status = u'Reject'
                    phistory.changes = u'Reject requests compound of GID %s (request ID %s)' % (pcompound.gid, pcompound.id)
                    pcompound.status = DBSession.query(PStatus).get(3)
                    pcompound.history += [phistory]
                    DBSession.add(phistory)
                else:
                    flash(l_(u'Request compound error'), 'error')
                    redirect(come_from)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        else:
            flash(l_(u'Select Compounds'), 'error')
            redirect(come_from)
            
    @expose()
    def withdraw(self, *args, **kw):
        """
        Manager withdraw of synthesis (if synthesis status <=2).
        Chamge status of synthesis compound as discontinue and set request compound status as canceled.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
#        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if has_permission('kierownik'):
            if args:
                for arg in args:
                    try:
                        pcompound = DBSession.query(PCompound).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(PCompound.id==int(arg)).first()
                    except Exception:
                        flash(l_(u'Compound number error'), 'error')
                        redirect(come_from)
                    if pcompound:
                        scompounds = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(SCompound.pid==pcompound.id).all()
                        if scompounds:
                            for scompound in scompounds:
                                if scompound.status_id <= 2:
                                    shistory = SHistory()
                                    shistory.gid = scompound.mol.gid
                                    shistory.project = pname
                                    shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    shistory.user = userid
                                    shistory.status = u'Withdraw'
                                    shistory.changes = u'Withdraw synthesis compound of GID %s (ID projektowe %s)' % (scompound.gid, arg)
                                    scompound.status = DBSession.query(SStatus).get(9)
                                    scompound.history += [shistory]
                                    DBSession.add(shistory)
                        phistory = PHistory()
                        phistory.gid = pcompound.gid
                        phistory.project = pname
                        phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        phistory.user = userid
                        phistory.status = u'Withdraw'
                        phistory.changes = u'Withdraw requests compound of GID %s (request ID %s)' % (pcompound.gid, pcompound.id)
                        pcompound.status = DBSession.query(PStatus).get(3)
                        pcompound.history += [phistory]
                        DBSession.add(phistory)
                    else:
                        flash(l_(u'Request compound error'), 'error')
                        redirect(come_from)
                DBSession.flush()
                flash(l_(u'Task completed successfully'))
                redirect(come_from)
            else:
                flash(l_(u'Select Compounds'), 'error')
                redirect(come_from)
        else:
            flash(l_(u'Permission denied'), 'error')
            redirect(come_from)
        
    @expose()
    def post_delete(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        """This is the code that actually deletes the record"""
        pid = int(args[0])
        pcompound = DBSession.query(PCompound).filter_by(id=pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        userid = request.identity['repoze.who.userid']
        if pcompound.status != DBSession.query(PStatus).get(2):
            phistory = PHistory()
            phistory.gid = pcompound.gid
            phistory.user = userid
#            project = DBSession.query(Projects).filter(Projects.name==pname).first()
            phistory.project = pname
            phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            phistory.status = 'Usuwanie'
            phistory.changes = 'Usunięcie związku o GID %s (ID projektowe %s) z tabeli projektowej' % (pcompound.gid, pid)
#            phistory.pcompound_id = pid
            DBSession.delete(pcompound)
            DBSession.add(phistory)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
        else:
            flash(l_(u'Permission denied'), 'error')    #Nie mozna usuwac zaakceptowanych zwiazkow.
        redirect(request.headers['Referer'])
        
    @expose("molgears.templates.users.select.accept")
    def accept(self, id):
        pname = request.environ['PATH_INFO'].split('/')[1]
        pid = int(id)
        pcompound = DBSession.query( PCompound ).filter_by(id=pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        principals = DBSession.query (Group).get(3)
        come_from = request.headers['Referer']
        if pcompound.status_id !=1:
            flash(l_(u'Status error. Permission denied'), 'error')
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        try:
            tags = [tag for tag in pcompound.mol.tags]
        except Exception:
            tags = [pcompound.mol.tags]
            pass
        return dict(pcompound=pcompound, alltags=alltags, tags=tags, users=principals.users, default_user = pcompound.principal, come_from=come_from, page='select', pname=pname)
        
    @expose()
    def add_to_synthesis(self, id, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        pid = int(id)
        try:
            etap_max = int(kw['etap_max'])
            if isinstance(kw['text_tags'], basestring):
                tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
            else:
                tagi = [DBSession.query( Tags ).get(int(tid)) for tid in kw['text_tags']]
        except Exception as msg:
            flash(l_(u'Tags error: %s' %msg))
            redirect(request.headers['Referer'])
        try:
            notes = kw['notes']
        except Exception:
            notes = None
            pass
        pcompound = DBSession.query( PCompound ).filter_by(id=pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        if not pcompound:
            flash(l_(u'Permission denied'), 'error')
            redirect(request.headers['Referer'])
        compound = DBSession.query( Compound).get(pcompound.gid)
        userid = request.identity['repoze.who.userid']
        scompound = SCompound()
        scompound.owner = userid
        effort = Efforts()
        effort.etap = -1
        effort.etap_max = etap_max
        scompound.effort = [effort]
        scompound.principal = kw['principal']
        scompound.mol = compound
        scompound.pid = pid
        scompound.seq = pcompound.seq
        scompound.priority = pcompound.priority
        scompound.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        pchanges = u'Status: accepted;'
        schanges = u''
        
        shistory = SHistory()
        shistory.user = userid
        shistory.gid = scompound.mol.gid
#        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        shistory.project = pname
        shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shistory.status = u'accept'
        schanges = u'Principal: ' + kw['principal'] + u'; etaps num: ' + str(etap_max) + u'; Priority: ' + str(scompound.priority)
        if tagi != compound.tags:
            compound.tags = tagi
            pchanges += u'; Tags:'
            schanges += u'; Tags:'
            for tag in tagi:
                pchanges += tag.name + u'; '
                schanges += tag.name + u'; '
        if notes:
            scompound.notes = notes
            schanges += u'; Notes: ' + notes
        sstatus = DBSession.query( SStatus ).get(1)
        scompound.status = sstatus
        schanges += u' Status: pending'
        shistory.changes = schanges
        scompound.history = [shistory]
        
        pcompound.status = DBSession.query( PStatus).get(2)
        
        phistory = PHistory()
        phistory.gid = pcompound.gid
#        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        phistory.project = pname
        phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        phistory.user = userid
        phistory.status = 'accept'
                
        phistory.changes = pchanges
        pcompound.history += [phistory]
        
        DBSession.add(effort)
        DBSession.add(phistory)
        DBSession.add(shistory)
        DBSession.add(scompound)
        DBSession.flush()
        compound.snum = DBSession.query(SCompound).filter_by(gid=pcompound.gid).count()
        scompound.effort_default = effort.id
        #transaction.commit()
        if kw and kw.has_key('come_from'):
            come_from = kw['come_from']
        else:
            come_from = request.headers['Referer']
        flash(l_(u'Task completed successfully'))
        redirect(come_from)

    @expose('molgears.templates.users.select.details')
    def details(self, *args, **kw):
        gid = int(args[0])
        pid = int(args[1])
        pname = request.environ['PATH_INFO'].split('/')[1]
        pcompound = DBSession.query(PCompound).filter_by(id=pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        scompound = DBSession.query(SCompound).filter_by(pid=pid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').first()
        lcompound = ()
        assert pcompound.gid == gid,  "GID error."
        if scompound:
            assert scompound.gid == gid,  "GID error."
            lcompound = DBSession.query(LCompound).filter_by(sid=scompound.id).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').first()
        if lcompound:
            assert lcompound.gid == gid,  "GID error."
        pcompounds = DBSession.query(PCompound).filter(PCompound.gid==gid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        from rdkit.Chem.rdMolDescriptors import CalcMolFormula
        formula = CalcMolFormula(Chem.MolFromSmiles(str(pcompound.mol.structure)))
        scompounds = DBSession.query(SCompound).filter_by(gid=gid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        lcompounds = DBSession.query(LCompound).filter_by(gid=gid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        return dict(pcompound=pcompound, scompound=scompound, lcompound=lcompound, pcompounds=pcompounds, scompounds=scompounds, lcompounds=lcompounds, formula=formula, page='select', pname=pname)
        
    
    @expose('molgears.templates.users.select.multiedit')
    def multiedit(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        come_from = request.headers['Referer']
        principals = DBSession.query (Group).get(3)
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
            if argv:
#                project = DBSession.query(Projects).filter(Projects.name==pname).first()
                userid = request.identity['repoze.who.userid']
                for arg in argv:
                    try:
                        if isinstance(kw['text_tags'], basestring):
                            tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                        else:
                            tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
                    except Exception:
                        tagi = None
                    pcompound = DBSession.query(PCompound).get(int(arg))
                    if kw.has_key('priority'):
                        pcompound.priority = int(kw['priority'])
                        scompound = DBSession.query(SCompound).filter_by(pid=arg).all()
                        if scompound:
                            for sc in scompound:
                                sc.priority = int(kw['priority'])
                                shistory = SHistory()
                                shistory.project = pname
                                shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                shistory.user = userid
                                shistory.status = u'Priority'
                                shistory.changes = u'Priority:' + kw['priority']
                                sc.history += [shistory]
                                DBSession.add(shistory)
                    phistory = PHistory()
                    phistory.gid = pcompound.gid
                    phistory.project = pname
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.user = userid
                    phistory.status = u'Multi - edit'
                    phistory.changes = u''
                    if kw.has_key('principal'):
                        if kw['principal'] != u'0':
                            pcompound.principal = kw['principal']
                            phistory.changes += u' Odbiorca: ' + kw['principal'] + u';'
                    phistory.changes = u'Priority: ' + kw['priority'] + u';'
                    if tagi and pcompound.mol.tags != tagi:
                        pcompound.mol.tags = tagi
                        phistory.changes += u' Tags: '
                        for tag in tagi:
                            phistory.changes += str(tag.name) + ';'
                    if notes and notes !=pcompound.notes:
                        pcompound.notes = notes
                        phistory.changes += u' Notes: ' + notes
                    pcompound.history += [phistory]
                    DBSession.add(phistory)
                    DBSession.flush()
                    #transaction.commit()
                if kw.has_key('come_from'):
                    come_from = kw['come_from']
                else:
                    come_from = request.headers['Referer']
                flash(l_(u'Task completed successfully'))
                redirect(come_from)
                
        return dict(alltags=alltags, args=args, come_from=come_from, page='select', pname=pname, users=principals.users)
        
    @expose()
    def multireject(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        try:
            if isinstance(args, basestring):
                argv = [args]
            else:
                argv = args[1:]
        except Exception:
            argv = None
        if argv:
            userid = request.identity['repoze.who.userid']
            for arg in argv:
                pcompound = DBSession.query(PCompound).get(int(arg))
                if pcompound.status != DBSession.query( PStatus).get(2):
                    pcompound.status = DBSession.query( PStatus).get(3)
                    phistory = PHistory()
                    phistory.gid = pcompound.gid
#                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    phistory.project = pname
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.user = userid
                    phistory.status = u'Multi - reject'
                    phistory.changes = u'Status: rejected'
                    pcompound.history += [phistory]
                    DBSession.add(phistory)
                    DBSession.flush()
                    #transaction.commit()
                else:
                    flash(l_(u'Permission denied'), 'error')
                    redirect(request.headers['Referer'])
            flash(l_(u'Task completed successfully'))
            redirect(request.headers['Referer'])
        flash(l_(u'args error'), 'error')

    @expose('molgears.templates.users.select.multiaccept')
    def multiaccept(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        principals = DBSession.query (Group).get(3)
        come_from = request.headers['Referer']
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
            etap_max = int(kw['etap_max'])
            
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
                    pcompound = DBSession.query( PCompound).get(arg)
                    compound = DBSession.query( Compound).get(pcompound.gid)
                    userid = request.identity['repoze.who.userid']
                    scompound = SCompound()
                    scompound.owner = userid
                    effort = Efforts()
                    effort.etap = -1
                    effort.etap_max = etap_max
                    scompound.effort = [effort]
                    scompound.principal = kw['principal']
                    scompound.mol = compound
                    scompound.seq = pcompound.seq
                    scompound.pid = pcompound.id
                    scompound.priority = pcompound.priority
                    scompound.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    shistory = SHistory()
                    shistory.gid = scompound.mol.gid
#                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    shistory.project = pname
                    shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    shistory.user = userid
                    shistory.status = 'accept'
                    schanges = u'Principal: ' + kw['principal'] + u'; Etap nums: ' + str(etap_max) + u'; Priority: ' + str(scompound.priority) 
                    
                    pcompound.status = DBSession.query( PStatus).get(2)
                    phistory = PHistory()
                    phistory.gid = pcompound.gid
#                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    phistory.project = pname
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.user = userid
                    phistory.status = 'accept'
                    pchanges = u'Status: accepted'
                    if tagi and tagi != compound.tags:
                        compound.tags = tagi
                        schanges += u'; Tagi: '
                        pchanges += u'; Tagi: '
                        for tag in tagi:
                            schanges += str(tag.name) + u'; '
                            pchanges += str(tag.name) + u'; '
                    if notes:
                        scompound.notes = notes
                        schanges += u'; Notes: ' + notes
                    else:
                        if pcompound.notes:
                            scompound.notes = pcompound.notes
                            schanges += u'; Notes: ' + pcompound.notes
                    sstatus = DBSession.query( SStatus ).get(1)
                    scompound.status = sstatus
                    schanges += u' Status: pending'
                    shistory.changes = schanges
                    scompound.history = [shistory]
                        
                    phistory.changes = pchanges
                    pcompound.history += [phistory]
                    
                    DBSession.add(effort)
#                    DBSession.add(history)
                    DBSession.add(phistory)
                    DBSession.add(shistory)
                    DBSession.add(scompound)
                    DBSession.flush()
                    scompound.effort_default = effort.id
                    compound.snum = DBSession.query(LCompound).filter_by(gid=pcompound.gid).count()
                    #transaction.commit()
                if kw.has_key('come_from'):
                    come_from = kw['come_from']
                else:
                    come_from = request.headers['Referer']
                flash(l_(u'Task completed successfully'))
                redirect(come_from)
            else:
                flash(args)
                redirect(request.headers['Referer'])
        
        return dict(alltags=alltags, args=args, users=principals.users, come_from=come_from, page='select', pname=pname)


    @expose()
    def multidelete(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        """This is the code that actually deletes the record"""
        try:
            if isinstance(args, basestring):
                argv = [args]
            else:
                argv = args[1:]
        except Exception:
            argv = None
        if argv:
            userid = request.identity['repoze.who.userid']
            for arg in argv:
                pcompound = DBSession.query(PCompound).get(int(arg))
                if pcompound.status != DBSession.query(PStatus).get(2):
                    phistory = PHistory()
                    phistory.gid = pcompound.gid
#                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    phistory.project = pname
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.user = userid
                    phistory.status = 'delete'
                    phistory.changes = 'Delete compound GID %s (ID %s)' % (pcompound.gid, arg)
                    DBSession.delete(pcompound)
                    DBSession.add(phistory)
                    DBSession.flush()
                else:
                    flash(l_(u'Permission denied'), 'error') # Nie mozna usuwać zaakceptowanych zwiazkow
                    redirect(request.headers['Referer'])
            flash(l_(u'Task completed successfully'))
            redirect(request.headers['Referer'])
        flash(l_(u'args error'), 'error')
        redirect(request.headers['Referer'])
        
    @expose()
#    @allow_only(predicates.not_anonymous())
    def download(self, *args):
        userid = request.identity['repoze.who.userid']
#        pname = request.environ['PATH_INFO'].split('/')[1]
        if not args:
            redirect(request.headers['Referer'])
        else:
            filename = userid + '_' + args[-1]
            ext = args[-2]
            filepath = os.path.join('./molgears/files/download/', str(filename + '.' + ext))
        if has_permission('user'):
            if len(args)>=3:
                pcompound = ()
                for arg in args[:-2]:
                    if args[1] == u'01_select':
                        pcompound += (DBSession.query(PCompound).filter(PCompound.status==DBSession.query(PStatus)).filter(PCompound.id==int(arg)).first(), )
                    else:
                        pcompound += (DBSession.query(PCompound).filter(PCompound.id==int(arg)).first(), )
            else:
                if args[1] == u'01_select':
                    pcompound = DBSession.query(PCompound).filter(PCompound.status==DBSession.query(PStatus).get(1)).order_by('id').all()
                else:
                    pcompound = DBSession.query(PCompound).order_by('id').all()
            if ext == u'xls':
                import xlwt
                wbk = xlwt.Workbook()
                sheet = wbk.add_sheet('arkusz1')
                sheet.write(0,0,u'GID')
                sheet.write(0,1,u'ID')
                sheet.write(0,2,u'Name')
                sheet.write(0,3,u'SMILES')
                sheet.write(0,4,u'Owner')
                sheet.write(0,5,u'Principal')
                sheet.write(0,6,u'Priority')
                sheet.write(0,7,u'Notes')
                i = 1
                for row in pcompound:
                    sheet.write(i,0, str(row.gid))
                    sheet.write(i,1, str(row.id))
                    sheet.write(i,2, str(row.mol.name))
                    sheet.write(i,3, str(row.mol.structure))
                    sheet.write(i,4, str(row.owner))
                    sheet.write(i,5, str(row.principal))
                    sheet.write(i,6, str(row.priority))
                    sheet.write(i,7, row.notes)
                    i += 1
                wbk.save(filepath)
            if ext == u'txt':
                f = open(filepath, 'w')
                for row in pcompound:
                    f.write('%s %s \n' % (row.mol.structure, row.mol.name))
                f.close()
            import paste.fileapp
            f = paste.fileapp.FileApp(filepath)
            from tg import use_wsgi_app
            return use_wsgi_app(f)
        else:
            flash(l_('Error 404'),'error')
            redirect(request.headers['Referer'])

    @expose('molgears.templates.users.select.history')
    def history(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        history = DBSession.query( PHistory ).filter(PHistory.project.any(Projects.name==pname))
        order='PHistory.id'
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
                        order = PHistory.pcompound_id
                    elif v == 'user':
                        order = PHistory.user
                    elif v == 'date':
                        order = PHistory.date
                    else:
                        order = v
                if str(k) != 'remove':
                    tmpl += str(k) + '=' + str(v) + '&'
            if search_clicked:
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_gid'])
                        history = history.filter(PCompound.id == gid )
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_user') and kw['text_user'] !=u'':
                    history = history.filter(PHistory.user.like(kw['text_user'].replace('*', '%')))
                if kw.has_key('text_status') and kw['text_status'] !=u'':
                    history = history.filter(PHistory.status.like(kw['text_status'].replace('*', '%')))
                if kw.has_key('text_changes') and kw['text_changes'] !=u'':
                    history = history.filter(PHistory.changes.like(kw['text_changes'].replace('*', '%')))
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    history = history.filter(PHistory.date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            history = history.filter(PHistory.date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        history = history.filter(PHistory.date < date_to)
        if dsc:
            history = history.order_by(desc(order).nullslast())
        else:
            history = history.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(history, page, url=page_url, items_per_page=items)
        if kw:
            for k, v in kw.iteritems():
                currentPage.kwargs[k] = v
        return dict(history=currentPage.items, currentPage=currentPage, one_day=one_day, now=now, tmpl=tmpl, page='select', pname=pname)

    @expose()
    def deletefromlist(self, ulist_id, *args):
        ulist = DBSession.query(UserLists).get(ulist_id)
#        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
#        ulists = [l for l in user.lists if l.table == 'LCompounds']
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
