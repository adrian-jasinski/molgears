# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
from tg import expose, flash, redirect, request
from tg.i18n import lazy_ugettext as l_
from tg.predicates import has_permission
from molgears.model import DBSession, Tags, SCompound, SStatus, SFiles, SHistory, SPurity, LCompound, LPurity, LHistory, PCompound,  PHistory,  PStatus
from molgears.model import Compound, Names, Efforts, User, Group, Projects
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

__all__ = ['SynthesisController']

public_dirname = os.path.join(os.path.abspath(resource_filename('molgears', 'public')))
files_dir = os.path.join(public_dirname, 'files')

# -------- SCompound controller ----------------------------------------------------------------------------------------------------------------------------------

class SynthesisController(BaseController):
    @expose('molgears.templates.users.synthesis.index')
    def index(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        status = DBSession.query(SStatus).get(3)
        scompound = DBSession.query(SCompound).join(SCompound.mol).filter(SCompound.owner.contains(userid)).filter(Compound.project.any(Projects.name==pname))
        dsc = True
        order = 'id'
        selection = None
        tmpl = ''
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        allstatus = [stat for stat in DBSession.query( SStatus ).all()]
        similarity = None
        user = DBSession.query(User).filter_by(user_name=userid).first()
        ulists = set([l for l in user.lists if l.table == 'SCompounds'] + [l for l in user.tg_user_lists if l.table == 'SCompounds'])
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
                        order = SCompound.gid
                    elif v == 'create_date':
                        order = SCompound.create_date
                    elif v == 'etap_diff':
                        order = SCompound.etap_diff
                    elif v == 'status_id':
                        for sc in DBSession.query(SCompound).all():
                            if sc.stat2_date:
                                sc.diff_date = (datetime.now()-sc.stat2_date).days/7
                            else:
                                sc.diff_date = 0
                        order = (SCompound.status_id, SCompound.diff_date)
                    else:
                        order = v
                if str(k) != 'select' and str(k) != 'remove' and str(v) != u'':
                    if str(k) == 'statusy':
                        if isinstance(kw['text_status'], (list, tuple)):
                            for stat in kw['text_status']:
                                tmpl += 'statusy' + '=' + str(stat) + '&'
                        else:
                            tmpl += 'statusy' + '=' + str(kw['text_status']) + '&'
                    else:
                        tmpl += str(k) + '=' + str(v) + '&'
                else:
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
                            threshold = float(user.threshold)/100.0
                            DBSession.execute(tanimoto_threshold.set(threshold))
                            limit = user.limit_sim
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            
                            search = DBSession.query(SCompound, tanimoto_sml).join(SCompound.mol).filter(SCompound.owner.contains(userid)).filter(Compound.project.any(Projects.name==pname)).filter(constraint).order_by(desc(tanimoto_sml)).limit(limit).all()
                            scompound = ()
                            similarity = ()
                            for row in search:
                                scompound += (row[0], )
                                similarity += (row[1], )
                            items = user.items_per_page
                            page_url = paginate.PageURL_WebOb(request)
                            currentPage = paginate.Page(scompound, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage, user=user, status=status, tmpl=tmpl, page='synthesis', alltags=alltags, allstatus=allstatus, similarity=similarity, pname=pname, ulists=ulists)
                            
                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            scompound = DBSession.query(SCompound).join(SCompound.mol).filter(SCompound.owner.contains(userid)).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                        elif method == 'identity':
                            scompound = DBSession.query(SCompound).join(SCompound.mol).filter(SCompound.owner.contains(userid)).filter(Compound.project.any(Projects.name==pname)).filter(Compound.structure.equals(smiles))
                    else:
                        flash(l_(u'SMILES error'), 'warning')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_GID'])
                        scompound = scompound.filter_by(gid = gid )
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_ID') and kw['text_ID'] !=u'':
                    try:
                        id = int(kw['text_ID'])
                        scompound = scompound.filter(SCompound.id == id)
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_name') and kw['text_name'] !=u'':
                    scompound = scompound.filter(Compound.names.any(Names.name.like(kw['text_name'].strip().replace('*', '%'))))
                if kw.has_key('text_lso') and kw['text_lso'] !=u'':
                    scompound = scompound.filter(Compound.names.any(Names.name.like(kw['text_lso'].replace('*', '%'))))
                if kw.has_key('text_owner') and kw['text_owner'] !=u'':
                    scompound = scompound.filter(SCompound.owner.like(kw['text_owner'].replace('*', '%')))
                if kw.has_key('text_principal') and kw['text_principal'] !=u'':
                    scompound = scompound.filter(SCompound.principal.like(kw['text_principal'].replace('*', '%')))
                if kw.has_key('text_notes') and kw['text_notes'] !=u'':
                    scompound = scompound.filter(SCompound.notes.like(kw['text_notes'].replace('*', '%')))
                if kw.has_key('text_priority') and kw['text_priority'] !=u'':
                    try:
                        id = int(kw['text_priority'])
                        scompound = scompound.filter(SCompound.priority == id)
                    except Exception as msg:
                        flash(l_(u'Priority should be a number from 0 to 5'), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    scompound = scompound.filter(SCompound.create_date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            scompound = scompound.filter(SCompound.create_date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        scompound = scompound.filter(SCompound.create_date < date_to)    
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

                    scompound = scompound.filter(Compound.tags.any(Tags.id.in_(tagi)))
    
                try:
                    statusy = kw['text_status']
                    if isinstance(statusy, basestring):
                        statusy = [int(statusy)]
                        statusy.sort()
                    else:
                        statusy = [int(sid) for sid in statusy]
                except Exception:
                    statusy = None
                    pass
                if statusy:
                    scompound = scompound.filter(SCompound.status_id.in_(statusy))
    
                for k, v in kw.iteritems():
                    if str(k) == 'desc' and str(v) != '1':
                        dsc = None
                    elif str(k) == 'order_by':
                        order = v
                        if order == 'gid':
                            order = SCompound.gid
                        elif order == 'status':
                            order = SCompound.status_id
                        elif order == 'create_date':
                            order = SCompound.create_date
                        elif order == 'priority':
                            order = SCompound.priority
                        elif v == 'status_id':
                            for sc in DBSession.query(SCompound).all():
                                if sc.stat2_date:
                                    sc.diff_date = (datetime.now()-sc.stat2_date).days/7
                                else:
                                    sc.diff_date = 0
                            order = (SCompound.status_id, SCompound.diff_date)

        if dsc:
            if kw.has_key('order_by') and kw['order_by'] == 'status_id':
                scompound = scompound.order_by(desc(order[0]).nullslast(), order[1])
            else:    
                scompound = scompound.order_by(desc(order).nullslast())
        else:
            if kw.has_key('order_by') and kw['order_by'] == 'status_id':
                scompound = scompound.order_by(order[0], desc(order[1]))
            else:
                scompound = scompound.order_by((order))
                
            
        if search_clicked and kw['search'] == "Download":
            if kw['file_type'] and kw['file_type'] != u'' and kw['sell_type'] and kw['sell_type'] != u'':
                if kw['sell_type'] == u'all':
                    scompounds = scompound.all()
                elif kw['sell_type'] == u'selected':
                    if selection:
                        scompounds = ()
                        for el in selection:
                            scompounds += (DBSession.query(SCompound).get(el), )
                    else:
                        flash(l_(u'Lack of selected structures for download'), 'error')
                        redirect(request.headers['Referer'])
                elif kw['sell_type'] == u'range':
                    scompounds = scompound.all()
                    if kw.has_key('select_from') and kw['select_from'] != u'':
                        try:
                            select_from = int(kw['select_from']) -1 
                            if select_from<1 or select_from>len(scompounds):
                                select_from = 0
                        except Exception:
                            select_from = 0
                    else:
                        select_from = 0
                    if kw.has_key('select_to') and kw['select_to'] != u'':
                        try:
                            select_to = int(kw['select_to'])
                            if select_to<2 or select_to>len(scompounds):
                                select_to = len(scompounds)
                        except Exception:
                            select_to = len(scompounds)
                    else:
                        select_to = len(scompounds)
                    scompounds_new = ()
                    for el in range(select_from, select_to):
                        scompounds_new += (scompounds[el], )
                    scompounds = scompounds_new
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
                    html = render_template({"length":len(scompounds), "scompound":scompounds, "options":options, "size":size}, "genshi", "molgears.templates.users.synthesis.print2", doctype=None)
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
                        sheet.write(0,j,u'Dodany przez')
                        j+=1
                    if 'principal' in options:
                        sheet.write(0,j,u'Principal')
                        j+=1
                    if 'priority' in options:
                        sheet.write(0,j,u'Priority')
                        j+=1
                    if 'etap' in options:
                        sheet.write(0,j,u'Etap')
                        j+=1
                    if 'status' in options:
                        sheet.write(0,j,u'Status')
                        j+=1
                    if 'tags' in options:
                        sheet.write(0,j,u'Tags')
                        j+=1
                    if 'notes' in options:
                        sheet.write(0,j,u'Notes')
                        j+=1
                    i = 1
                    for row in scompounds:
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
                        if 'principal' in options:
                            sheet.write(i,j, row.principal)
                            j+=1
                        if 'priority' in options:
                            sheet.write(i,j, row.priority)
                            j+=1
                        if 'etap' in options:
                            sheet.write(i,j, str(next(obj.etap for obj in row.effort if obj.id==row.effort_default)) + '/' + str(next(obj.etap_max for obj in row.effort if obj.id==row.effort_default)))
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
                        for row in scompounds:
                            line =[]
                            if 'smiles' in options:
                                line.append(str(row.mol.structure))
                            if 'name' in options:
                                line.append(row.mol.name)
                            if 'nr' in options:
                                line.append(unicode(scompounds.index(row)+1))
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
                            if 'principal' in options:
                                line.append(row.principal)
                            if 'priority' in options:
                                line.append(unicode(row.priority))
                            if 'etap' in options:
                                line.append(unicode(next(obj.etap for obj in row.effort if obj.id==row.effort_default)) + u'/' + unicode(next(obj.etap_max for obj in row.effort if obj.id==row.effort_default)))
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
                    redirect('/%s/synthesis/edit%s' % (pname, argv))
                else:
                    redirect('/%s/synthesis/multiedit/get_all%s' % (pname, argv))
            elif kw['akcja'] == u'etap':
                if len(selection) == 1:
                    redirect('/%s/synthesis/etap%s' % (pname, argv))
                else:
                    redirect('/%s/synthesis/multietap/get_all%s' % (pname, argv))
            elif kw['akcja'] == u'addreag':
                if len(selection) == 1:
                    redirect('/%s/synthesis/addreag%s' % (pname, argv))
                else:
                    redirect('/%s/synthesis/multiaddreag/get_all%s' % (pname, argv))
            elif kw['akcja'] == u'recive':
                if len(selection) == 1:
                    redirect('/%s/synthesis/accept%s' % (pname, argv))
                else:
                    flash(l_(u'Recive Compounds one by one'), 'error')
                    redirect('/%s/synthesis/get_all' % pname)
            else:
                redirect('/%s/synthesis/%s%s' % (pname, kw['akcja'], argv))

        user = DBSession.query(User).filter_by(user_name=userid).first()
        items = user.items_per_page
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(scompound, page, url=page_url, items_per_page=items)
        return dict(currentPage=currentPage, user=user, status=status, tmpl=tmpl, page='synthesis', alltags=alltags, allstatus=allstatus, similarity=similarity, pname=pname, ulists=ulists)
        
    @expose('molgears.templates.users.synthesis.get_all')
    def get_all(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        status = DBSession.query(SStatus).get(3)
        scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname))
        dsc = True
        order = 'id'
        selection = None
        ulist=None
        tmpl = ''
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        allstatus = [stat for stat in DBSession.query( SStatus ).all()]
        similarity = None
        kierownik = has_permission('kierownik')
        user = DBSession.query(User).filter_by(user_name=userid).first()
        ulists = [l for l in user.lists if l.table == 'SCompounds']
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
                        if ulist.table == 'SCompounds':
                            scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(SCompound.id.in_(elements))
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
                        order = SCompound.gid
                    elif v == 'create_date':
                        order = SCompound.create_date
                    elif v == 'etap_diff':
                        order = SCompound.etap_diff
                    elif v == 'status':
                        order = SCompound.status_id
                    elif v == 'priority':
                        order = SCompound.priority
                    elif v == 'status_id':
                        for sc in DBSession.query(SCompound).all():
                            if sc.stat2_date:
                                sc.diff_date = (datetime.now()-sc.stat2_date).days/7
                            else:
                                sc.diff_date = 0
                        order = (SCompound.status_id, SCompound.diff_date)
                    else:
                        order = v
                if str(k) != 'select' and str(k) != 'remove' and str(v) != u'':
                    if str(k) == 'statusy':
                        if isinstance(kw['text_status'], (list, tuple)):
                            for stat in kw['text_status']:
                                tmpl += 'statusy' + '=' + str(stat) + '&'
                        else:
                            tmpl += 'statusy' + '=' + str(kw['text_status']) + '&'
                    else:
                        tmpl += str(k) + '=' + str(v) + '&'
                else:
                    try:
                        if isinstance(kw['select'], basestring):
                            selection = [kw['select']]
                        else:
                            selection = [id for id in kw['select']]
                    except Exception:
                        selection = None
#SERCH OPTIONS START:
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
                            threshold = float(user.threshold)/100.0
                            DBSession.execute(tanimoto_threshold.set(threshold))
                            limit = user.limit_sim
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            
                            search = DBSession.query(SCompound, tanimoto_sml).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint).order_by(desc(tanimoto_sml)).limit(limit).all()
                            scompound = ()
                            similarity = ()
                            for row in search:
                                scompound += (row[0], )
                                similarity += (row[1], )
                            items = user.items_per_page
                            page_url = paginate.PageURL_WebOb(request)
                            currentPage = paginate.Page(scompound, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage, user=user, status=status, tmpl=tmpl, kierownik = kierownik, page='synthesis', alltags=alltags, allstatus=allstatus, similarity=similarity, pname=pname, ulists=ulists, ulist=ulist)
                            
                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                        elif method == 'identity':
                            scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(Compound.structure.equals(smiles))
                    else:
                        flash(l_(u'SMILES error'), 'warning')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_GID'])
                        scompound = scompound.filter_by(gid = gid )
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_ID') and kw['text_ID'] !=u'':
                    try:
                        id = int(kw['text_ID'])
                        scompound = scompound.filter(SCompound.id == id)
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_name') and kw['text_name'] !=u'':
                    scompound = scompound.filter(Compound.names.any(Names.name.like(kw['text_name'].strip().replace('*', '%'))))
                if kw.has_key('text_lso') and kw['text_lso'] !=u'':
                    scompound = scompound.filter(SCompound.lso.like(kw['text_lso'].replace('*', '%')))
                if kw.has_key('text_owner') and kw['text_owner'] !=u'':
                    scompound = scompound.filter(SCompound.owner.like(kw['text_owner'].replace('*', '%')))
                if kw.has_key('text_principal') and kw['text_principal'] !=u'':
                    scompound = scompound.filter(SCompound.principal.like(kw['text_principal'].replace('*', '%')))
                if kw.has_key('text_notes') and kw['text_notes'] !=u'':
                    scompound = scompound.filter(SCompound.notes.like(kw['text_notes'].replace('*', '%')))
                if kw.has_key('text_priority') and kw['text_priority'] !=u'':
                    try:
                        id = int(kw['text_priority'])
                        scompound = scompound.filter(SCompound.priority == id)
                    except Exception as msg:
                        flash(l_(u'Priority should be a number from 0 to 5'), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    scompound = scompound.filter(SCompound.create_date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            scompound = scompound.filter(SCompound.create_date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        scompound = scompound.filter(SCompound.create_date < date_to) 
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
        
                    scompound = scompound.filter(Compound.tags.any(Tags.id.in_(tagi)))
    
                try:
                    statusy = kw['text_status']
                    if isinstance(statusy, basestring):
                        statusy = [int(statusy)]
                    else:
                        statusy = [int(sid) for sid in statusy]
                        statusy.sort()
                except Exception as msg:
                    statusy = None
                    pass
                if statusy:
                    scompound = scompound.filter(SCompound.status_id.in_(statusy))
                    lower_num = statusy[0]
                    if not lower_num <5:
                        lower_num = 1;
                    if kw.has_key('date_stat_from') and kw['date_stat_from'] !=u'':
                        date_stat_from = datetime.strptime(str(kw['date_stat_from']), '%Y-%m-%d')
                        scompound = scompound.filter(SCompound.__getattribute__(SCompound,'stat%s_date' % lower_num) > date_stat_from)
                    else:
                        date_stat_from = None
                    if kw.has_key('date_stat_to') and kw['date_stat_to'] !=u'':
                        date_stat_to = datetime.strptime(str(kw['date_stat_to']), '%Y-%m-%d')
                        if date_stat_from:
                            if date_stat_to>date_stat_from:
                                scompound = scompound.filter(SCompound.__getattribute__(SCompound,'stat%s_date' % lower_num)  < date_stat_to)
                            else:
                                flash(l_(u'The End date must be later than the initial'), 'error')
                                redirect(request.headers['Referer'])
                        else:
                            scompound = scompound.filter(SCompound.__getattribute__(SCompound,'stat%s_date' % lower_num)  < date_stat_to)

        if dsc:
            if kw.has_key('order_by') and kw['order_by'] == 'status_id':
                scompound = scompound.order_by(desc(order[0]).nullslast(), order[1])
            else:    
                scompound = scompound.order_by(desc(order).nullslast())
        else:
            if kw.has_key('order_by') and kw['order_by'] == 'status_id':
                scompound = scompound.order_by(order[0], desc(order[1]))
            else:
                scompound = scompound.order_by((order))

        if search_clicked and kw['search'] == "Download":
            if kw['file_type'] and kw['file_type'] != u'' and kw['sell_type'] and kw['sell_type'] != u'':
                if kw['sell_type'] == u'all':
                    scompounds = scompound.all()
                elif kw['sell_type'] == u'selected':
                    if selection:
                        scompounds = ()
                        for el in selection:
                            scompounds += (DBSession.query(SCompound).get(el), )
                    else:
                        flash(l_(u'Lack of selected structures for download'), 'error')
                        redirect(request.headers['Referer'])
                elif kw['sell_type'] == u'range':
                    scompounds = scompound.all()
                    if kw.has_key('select_from') and kw['select_from'] != u'':
                        try:
                            select_from = int(kw['select_from']) -1 
                            if select_from<1 or select_from>len(scompounds):
                                select_from = 0
                        except Exception:
                            select_from = 0
                    else:
                        select_from = 0
                    if kw.has_key('select_to') and kw['select_to'] != u'':
                        try:
                            select_to = int(kw['select_to'])
                            if select_to<2 or select_to>len(scompounds):
                                select_to = len(scompounds)
                        except Exception:
                            select_to = len(scompounds)
                    else:
                        select_to = len(scompounds)
                    scompounds_new = ()
                    for el in range(select_from, select_to):
                        scompounds_new += (scompounds[el], )
                    scompounds = scompounds_new
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
                    html = render_template({"length":len(scompounds), "scompound":scompounds, "options":options, "size":size}, "genshi", "molgears.templates.users.synthesis.print2", doctype=None)
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
                        sheet.write(0,j,u'Dodany przez')
                        j+=1
                    if 'principal' in options:
                        sheet.write(0,j,u'Principal')
                        j+=1
                    if 'priority' in options:
                        sheet.write(0,j,u'Priority')
                        j+=1
                    if 'etap' in options:
                        sheet.write(0,j,u'Etap')
                        j+=1
                    if 'status' in options:
                        sheet.write(0,j,u'Status')
                        j+=1
                    if 'tags' in options:
                        sheet.write(0,j,u'Tags')
                        j+=1
                    if 'notes' in options:
                        sheet.write(0,j,u'Notes')
                        j+=1
                    i = 1
                    for row in scompounds:
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
                        if 'principal' in options:
                            sheet.write(i,j, row.principal)
                            j+=1
                        if 'priority' in options:
                            sheet.write(i,j, row.priority)
                            j+=1
                        if 'etap' in options:
                            sheet.write(i,j, str(next(obj.etap for obj in row.effort if obj.id==row.effort_default)) + '/' + str(next(obj.etap_max for obj in row.effort if obj.id==row.effort_default)))
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
                        for row in scompounds:
                            line =[]
                            if 'smiles' in options:
                                line.append(str(row.mol.structure))
                            if 'name' in options:
                                line.append(row.mol.name)
                            if 'nr' in options:
                                line.append(unicode(scompounds.index(row)+1))
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
                            if 'principal' in options:
                                line.append(row.principal)
                            if 'priority' in options:
                                line.append(unicode(row.priority))
                            if 'etap' in options:
                                line.append(unicode(next(obj.etap for obj in row.effort if obj.id==row.effort_default)) + u'/' + unicode(next(obj.etap_max for obj in row.effort if obj.id==row.effort_default)))
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
                    redirect('/%s/synthesis/edit%s' % (pname, argv))
                else:
                    redirect('/%s/synthesis/multiedit/get_all%s' % (pname, argv))
            elif kw['akcja'] == u'etap':
                if len(selection) == 1:
                    redirect('/%s/synthesis/etap%s' % (pname, argv))
                else:
                    redirect('/%s/synthesis/multietap/get_all%s' % (pname, argv))
            elif kw['akcja'] == u'addreag':
                if len(selection) == 1:
                    redirect('/%s/synthesis/addreag%s' % (pname, argv))
                else:
                    redirect('/%s/synthesis/multiaddreag/get_all%s' % (pname, argv))
            elif kw['akcja'] == u'recive':
                if len(selection) == 1:
                    redirect('/%s/synthesis/accept%s' % (pname, argv))
                else:
                    flash(l_(u'Recive Compounds one by one'), 'error')
                    redirect('/%s/synthesis/get_all' % pname)
            else:
                redirect('/%s/synthesis/%s%s' % (pname, kw['akcja'], argv))
        items = user.items_per_page
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(scompound, page, url=page_url, items_per_page=items)
        return dict(currentPage=currentPage, user=user, status=status, tmpl=tmpl, kierownik = kierownik, page='synthesis', alltags=alltags, allstatus=allstatus, similarity=similarity, pname=pname, ulists=ulists, ulist=ulist)
        
    @expose('molgears.templates.users.synthesis.index')
    def recieve(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        ulists = [l for l in user.lists if l.table == 'SCompounds']
        kierownik = has_permission('kierownik')
        status = DBSession.query(SStatus).get(3)
        scompound = DBSession.query(SCompound).filter(SCompound.status ==status).filter(SCompound.principal.contains(userid)).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname))
        dsc = True
        order = 'id'
        selection = None
        tmpl = ''
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        allstatus = [stat for stat in DBSession.query( SStatus ).all()]
        similarity = None
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
                        order = SCompound.gid
                    elif v == 'create_date':
                        order = SCompound.create_date
                    else:
                        order = v
                if str(k) != 'select' and str(k) != 'remove' and str(v) != u'':
                    if str(k) == 'statusy':
                        if isinstance(kw['text_status'], (list, tuple)):
                            for stat in kw['text_status']:
                                tmpl += 'statusy' + '=' + str(stat) + '&'
                        else:
                            tmpl += 'statusy' + '=' + str(kw['text_status']) + '&'
                    else:
                        tmpl += str(k) + '=' + str(v) + '&'
                else:
                    try:
                        if isinstance(kw['select'], basestring):
                            selection = [kw['select']]
                        else:
                            selection = [id for id in kw['select']]
                    except Exception:
                        selection = None
#SERCH OPTIONS START:
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
#                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
#                            constraint = Compound.morgan.dice_similar(query_bfp)
#                            dice_sml = Compound.morgan.dice_similarity(query_bfp).label('dice')
                            limit = user.limit_sim
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            
                            search = DBSession.query(SCompound, tanimoto_sml).join(SCompound.mol).filter(SCompound.owner.contains(userid)).filter(Compound.project.any(Projects.name==pname)).filter(constraint).order_by(desc(tanimoto_sml)).limit(limit).all()
                            scompound = ()
                            similarity = ()
                            for row in search:
                                scompound += (row[0], )
                                similarity += (row[1], )
                            user = DBSession.query(User).filter_by(user_name=userid).first()
                            items = user.items_per_page
                            page_url = paginate.PageURL_WebOb(request)
                            currentPage = paginate.Page(scompound, page, url=page_url, items_per_page=items)
                            return dict(length=len(scompound), scompound=currentPage.items, currentPage=currentPage, user=userid, status=status, tmpl=tmpl, kierownik = kierownik, page='synthesis', alltags=alltags, allstatus=allstatus, similarity=similarity, pname=pname, ulists=ulists)
                            
                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            scompound = DBSession.query(SCompound).join(SCompound.mol).filter(SCompound.owner.contains(userid)).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                        elif method == 'identity':
                            scompound = DBSession.query(SCompound).join(SCompound.mol).filter(SCompound.owner.contains(userid)).filter(Compound.project.any(Projects.name==pname)).filter(Compound.structure.equals(smiles))
                    else:
                        flash(l_(u'SMILES error'), 'warning')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_GID'])
                        scompound = scompound.filter_by(gid = gid )
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_ID') and kw['text_ID'] !=u'':
                    try:
                        id = int(kw['text_ID'])
                        scompound = scompound.filter(SCompound.id == id)
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_name') and kw['text_name'] !=u'':
                    scompound = scompound.filter(Compound.names.any(Names.name.like(kw['text_name'].strip().replace('*', '%'))))
                if kw.has_key('text_lso') and kw['text_lso'] !=u'':
                    scompound = scompound.filter(SCompound.lso.like(kw['text_lso'].replace('*', '%')))
                if kw.has_key('text_owner') and kw['text_owner'] !=u'':
                    scompound = scompound.filter(SCompound.owner.like(kw['text_owner'].replace('*', '%')))
                if kw.has_key('text_principal') and kw['text_principal'] !=u'':
                    scompound = scompound.filter(SCompound.principal.like(kw['text_principal'].replace('*', '%')))
                if kw.has_key('text_notes') and kw['text_notes'] !=u'':
                    scompound = scompound.filter(SCompound.notes.like(kw['text_notes'].replace('*', '%')))
                if kw.has_key('text_priority') and kw['text_priority'] !=u'':
                    try:
                        id = int(kw['text_priority'])
                        scompound = scompound.filter(SCompound.priority == id)
                    except Exception as msg:
                        flash(l_(u'Priority should be a number from 0 to 5'), 'error')
                        redirect(request.headers['Referer'])
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

                    scompound = scompound.filter(Compound.tags.any(Tags.id.in_(tagi)))
    
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
                    scompound = scompound.filter(SCompound.status_id.in_(statusy))
    
                for k, v in kw.iteritems():
                    if str(k) == 'desc' and str(v) != '1':
                        dsc = None
                    elif str(k) == 'order_by':
                        order = v
                        if order == 'gid':
                            order = SCompound.gid
                        elif order == 'status':
                            order = SCompound.status_id
                        elif order == 'create_date':
                            order = SCompound.create_date
                        elif order == 'priority':
                            order = SCompound.priority

#SERCH OPTIONS END:
        else:
            order = 'id'
        if selection and not search_clicked:
            argv =''
            for arg in selection:
                argv += '/' + arg
            if kw['akcja'] == u'edit':
                if len(selection) == 1:
                    redirect('/%s/synthesis/edit%s' % (pname, argv))
                else:
                    redirect('/%s/synthesis/multiedit/get_all%s' % (pname, argv))
            elif kw['akcja'] == u'etap':
                if len(selection) == 1:
                    redirect('/%s/synthesis/etap%s' % (pname, argv))
                else:
                    redirect('/%s/synthesis/multietap/get_all%s' % (pname, argv))
            elif kw['akcja'] == u'recive':
                if len(selection) == 1:
                    redirect('/%s/synthesis/accept/%s' % (pname, argv))
                else:
                    flash(l_(u'Recive Compounds one by one'), 'error')
                    redirect('/%s/synthesis/get_all' % pname)
            else:
                redirect('/%s/synthesis/%s%s' % (pname, kw['akcja'], argv))
        if dsc:
            scompound = scompound.order_by(desc(order).nullslast())
        else:
            scompound = scompound.order_by((order))
        user = DBSession.query(User).filter_by(user_name=userid).first()
        items = user.items_per_page
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(scompound, page, url=page_url, items_per_page=items)
        scompound = scompound.all()
#        tmpl = re.sub(r'(.*)remove1\=[a-zA-Z_]*&(.*)', r'\1\2', tmpl)
#        tmpl = re.sub(r'(.*)remove2\=[a-zA-Z_]*&(.*)', r'\1\2', tmpl)
        return dict(length=len(scompound), scompound=currentPage.items, currentPage=currentPage, user=userid, status=status, tmpl=tmpl, kierownik = kierownik, page='synthesis', alltags=alltags, allstatus=allstatus, similarity=similarity, pname=pname, ulists=ulists)
        
    @expose('molgears.templates.users.synthesis.details')
    def details(self, *args, **kw):
        gid = int(args[0])
        sid = int(args[1])
        pname = request.environ['PATH_INFO'].split('/')[1]
        scompound = DBSession.query(SCompound).filter_by(id=sid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').first()
        from rdkit.Chem.rdMolDescriptors import CalcMolFormula
        formula = CalcMolFormula(Chem.MolFromSmiles(str(scompound.mol.structure)))
        pcompound = DBSession.query(PCompound).filter_by(id=scompound.pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        lcompound = DBSession.query(LCompound).filter_by(sid=sid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').first()
        assert scompound.gid == gid,  "GID error."
        if pcompound:
            assert pcompound.gid == gid,  "GID error."
        scompounds = DBSession.query(SCompound).filter_by(gid=gid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        pcompounds = DBSession.query(PCompound).filter(PCompound.gid==gid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        lcompounds = DBSession.query(LCompound).filter_by(gid=gid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()        
        return dict(pcompound=pcompound, scompound=scompound, lcompound=lcompound, pcompounds=pcompounds, scompounds=scompounds, lcompounds=lcompounds, formula=formula, page='synthesis', pname=pname)

    @expose('molgears.templates.users.synthesis.etap')
    def etap(self, *args, **kw):
        id = int(args[0])
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        scompound = DBSession.query( SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        come_from = request.headers['Referer']
        try:
            effort_id = int(args[1])
        except Exception:
            effort_id = None
        if effort_id:
            effort = DBSession.query( Efforts ).get(effort_id)
        else:
            effort = DBSession.query( Efforts ).get(scompound.effort_default)
        if scompound.owner == userid:
            etap_max = effort.etap_max
            etap = effort.etap
            if not kw and etap < etap_max - 1:
                return dict(scompound=scompound, effort=effort, etap=etap, etap_max=etap_max, kierownik = None, come_from=come_from, page='synthesis', pname=pname)
            elif not kw and etap == etap_max - 1:
                flash(l_(u'Analytics informations are required'), 'warning')
                redirect('/%s/synthesis/analitics/%s' % (pname, id))
            else:
                flash(l_(u'Permission denied'), 'error')    # IF status finished. Changing etap not allowed.
                redirect(request.headers['Referer'])
        else:
            flash(l_(u'Permission denied'), 'error')
            redirect(request.headers['Referer'])

    @expose()
    def save_etap(self, *args, **kw):
        id = int(args[0])
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        scompound = DBSession.query( SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        try:
            effort_id = int(args[1])
        except Exception:
            effort_id = None
        if effort_id:
            effort = DBSession.query( Efforts ).get(effort_id)
        else:
            effort = DBSession.query( Efforts ).get(scompound.effort_default)
        shistory = SHistory()
        shistory.gid = scompound.mol.gid
        shistory.project = pname
        shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shistory.user = userid
        shistory.status = 'stage change'
        schanges = u''
        lso = kw['lso']
        notes = kw['notes']
        etap = effort.etap
        etap_max = effort.etap_max
        if etap < etap_max - 1:
            if etap >= 0:
                effort.etap = etap +1
                schanges = u'Current stage: ' + str(etap+1)
            else:
                effort.etap = etap +1
                next_status = DBSession.query( SStatus ).get(2)
                scompound.status = next_status
                scompound.stat2_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                schanges = u'Current stage: ' + str(etap+1) + u'; Status: ' + str(next_status.name)

        elif etap == etap_max - 1:
            flash(l_(u'Analytics informations are required'), 'warning')
            redirect(request.headers['Referer'])
        else:
            flash(l_(u'Status error. Permission denied'), 'warning')
            redirect('/%s/sythesis/' % pname)
        
        if effort.id == scompound.effort_default:
            scompound.etap_diff = effort.etap_max - effort.etap
        if lso and lso.upper() != scompound.lso:
            scompound.lso = lso.upper()
            schanges += u'; LSO: ' + lso
        if notes and notes != scompound.notes:
            scompound.notes = notes
            schanges += u'; Notes: ' + notes
        
        shistory.changes = schanges
        scompound.history += [shistory]
        DBSession.add(shistory)
        DBSession.flush()
        if kw and kw.has_key('come_from'):
            come_from = kw['come_from']
        else:
            come_from = request.headers['Referer']
        flash(l_(u'Task completed successfully'))
        redirect(come_from)
        
    @expose('molgears.templates.users.synthesis.edit')
    def edit(self, id):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(id)
        come_from = request.headers['Referer']
        userid = request.identity['repoze.who.userid']
        principals = DBSession.query (Group).get(3)

        scompound = DBSession.query( SCompound ).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        if scompound.owner == userid:
            try:
                tags = [tag for tag in scompound.mol.tags]
            except Exception:
                tags = [scompound.mol.tags]
                pass
            try:
                files = scompound.filename
            except Exception:
                files = None
                pass
            effort = DBSession.query(Efforts).get(scompound.effort_default)
            etap_max = effort.etap_max
            etap = effort.etap
            return dict(scompound=scompound, etap=etap, etap_max=etap_max, tags=tags, alltags=alltags, files=files, users=principals.users, kierownik = None, come_from=come_from, page='synthesis', pname=pname)
        else:
            flash(l_(u'Permission denied'), 'warning')
            redirect(request.headers['Referer'])

    @expose()
    def put(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        sid = int(args[0])
        userid = request.identity['repoze.who.userid']
        scompound = DBSession.query(SCompound).filter_by(id=sid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        
        if scompound.owner == userid:
            try:
                if isinstance(kw['text_tags'], basestring):
                    tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                else:
                    tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
            except Exception as msg:
                flash(l_(u'Tags are required'))
                redirect(request.headers['Referer'])
            
            shistory = SHistory()
            shistory.gid = scompound.mol.gid
            shistory.project = pname
            shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            shistory.user = userid
            shistory.status = 'Edit'
            schanges = u''
            
#            scompound.status_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if tagi and tagi != scompound.mol.tags:
                scompound.mol.tags = tagi
            if kw.has_key('lso') and kw['lso'].upper() != scompound.lso:
                scompound.lso = kw['lso'].upper()
                schanges += u' LSO: ' + kw['lso']
            if kw.has_key('form') and kw['form'] != scompound.form:
                scompound.form = kw['form']
                schanges += u'; Form: ' + kw['form']
            if kw.has_key('principal') and kw['principal'] != scompound.principal:
                scompound.principal = kw['principal']
                schanges += u'; Recipient: ' + kw['principal']
            if kw.has_key('retention_kwasowa') and kw['retention_kwasowa'] != u'':
                retention_kwasowa = str(kw['retention_kwasowa']).replace(',', '.') 
            else:
                retention_kwasowa = None
            if kw.has_key('retention_zasadowa') and kw['retention_zasadowa'] != u'':
                retention_zasadowa = str(kw['retention_zasadowa']).replace(',', '.') 
            else:
                retention_zasadowa = None
            for purity in scompound.purity:
                if (purity.type == 'zasadowa' or purity.type == 'basic') and retention_zasadowa:
                    if purity.retention_time != float(retention_zasadowa):
                        purity.retention_time = float(retention_zasadowa)
                        schanges += u'; Retention time (basic) ' + retention_zasadowa
                if (purity.type == 'kwasowa' or purity.type == 'acid') and retention_kwasowa:
                    if purity.retention_time != float(retention_kwasowa):
                        purity.retention_time = float(retention_kwasowa)
                        schanges += u'; Retention time (acid) ' + retention_kwasowa
            if kw.has_key('state') and kw['state'] != u'':
                try:
                    state = str(kw['state'])
                    state = state.replace(',', '.') 
                except Exception as msg:
                    flash(l_(u'Float required: %s' % msg), 'error')
                    redirect(request.headers['Referer'])
                if scompound.state != float(state):
                    scompound.state = float(state)
                    schanges += u'; State.[mg]: ' + kw['state']
            else:
                scompound.state = 0
            if kw.has_key('notes') and kw['notes'] != scompound.notes:
                scompound.notes = kw['notes']
                schanges += u';Notes: ' + kw['notes']
            
            if kw.has_key('priority') and int(kw['priority']) != scompound.priority:
                scompound.priority = int(kw['priority'])
                schanges += u'; Priority:' + kw['priority']
                pcompound = DBSession.query(PCompound).get(scompound.pid)
                if pcompound:
                    pcompound.priority = int(kw['priority'])
                    phistory = PHistory()
                    phistory.project = pname
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.user = userid
                    phistory.status = 'Priority'
                    phistory.changes = u'Priority: ' + kw['priority']
                    pcompound.history += [phistory]
                    DBSession.add(phistory)
            
            try:
                reason = kw['reason']
            except Exception:
                reason = None
                pass
            if reason and reason != u'':
                schanges += u'Warning! Non standard change for the reason:' + reason
                new_etap = int(kw['etap']) 
                new_etap_max = int(kw['etap_max'])
                effort = DBSession.query( Efforts ).get(scompound.effort_default)
                if new_etap < new_etap_max:
                    effort.etap = new_etap
                    effort.etap_max = new_etap_max
                    scompound.status = DBSession.query( SStatus ).get(2)
                    scompound.stat2_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    schanges += u'; Current phase: ' + str(new_etap)
                    schanges += u'; Number of Phases: ' + str(new_etap_max)
                else:
                    flash(l_(u'Finished etap should be lower than amount of etaps'), 'error')
                    redirect(request.headers['Referer'])    
            try:
                if kw.has_key('acid'):
                    kwas = str(kw['acid'])
                else:
                    kwas = str(kw['kwasowa'])
                kwas = kwas.replace(',', '.') 
                kwas = float(kwas)
                if kw.has_key('basic'):
                    zasada = str(kw['basic'])
                else:
                    zasada = str(kw['zasadowa'])
                zasada = zasada.replace(',', '.') 
                zasada = float(zasada)
            except Exception as msg:
                kwas = None
                zasada = None
            if scompound.purity:
                if scompound.purity[0].type == 'kwasowa' or scompound.purity[0].type == 'acid':
                    kpurity = scompound.purity[0]
                    zpurity = scompound.purity[1]
                else:
                    kpurity = scompound.purity[1]
                    zpurity = scompound.purity[0]

                if kwas and kwas >= 0.0:#        if not has_permission('odbiorca'):
#            flash(l_(u'Permission denied'), 'warning')
#            redirect(request.headers['Referer'])

                    if kpurity.type == 'kwasowa' or kpurity.type == 'acid':
                        if kpurity.value != kwas:
                            kpurity.value = kwas
                            schanges += u'; Acid Purity: ' + str(kwas)
                        try:
                            kwas_file = raw_path_basename(kw['file_acid'].filename)
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
                                f.write(kw['file_acid'].value)
                                f.close()
                            except Exception as msg:
                                flash(l_(msg), 'error')
                                redirect(request.headers['Referer'])
                            sfile1 = SFiles()
                            sfile1.name = kwas_file
                            sfile1.filename = new_kwas_file_name
                            schanges += '; File for acid analitics: ' + kwas_file + ' (' + new_kwas_file_name + ')'
                            kpurity.filename = [sfile1]
                            DBSession.add(sfile1)

                        
                if zasada and zasada >= 0.0:
                    if zpurity.type == 'zasadowa' or zpurity.type == 'basic':
                        if zpurity.value != zasada:
                            zpurity.value = zasada
                            schanges += u'; Basic Purity: ' + str(zasada)
                        try:
                            zasada_file = raw_path_basename(kw['file_basic'].filename)
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
                                f.write(kw['file_basic'].value)
                                f.close()
                            except Exception as msg:
                                flash(l_(msg), 'error')
                                redirect(request.headers['Referer'])
                            sfile2 = SFiles()
                            sfile2.name = zasada_file
                            sfile2.filename = new_zasada_file_name
                            schanges += '; File for basic analitics: ' + zasada_file + ' (' + new_zasada_file_name +')'
                            zpurity.filename = [sfile2]
                            DBSession.add(sfile2)

                    
                
            try:
                filename = raw_path_basename(kw['loadfile'].filename)
            except Exception as msg:
                filename = None
                pass
            if filename:
                number = DBSession.query(SFiles).count() + 1
                newfilename = str(number) + '_' + userid + '_' + str(sid) + '_' + filename
                newfilename.replace(' ', '_')
                f_path = os.path.join(files_dir, newfilename)
                try:
                    f = file(f_path, "w")
                    f.write(kw['loadfile'].value)
                    f.close()
                except Exception as msg:
                    flash(l_(msg), 'error')
                    redirect(request.headers['Referer'])
                sfile = SFiles()
                sfile.name = filename
                sfile.filename = newfilename
                if kw['opis']:
                    sfile.description = kw['opis']
                schanges += u' File: ' + filename + u' ( ' + newfilename + u' )'
                DBSession.add(sfile)  
                shistory.changes = schanges
                scompound.history += [shistory]
                DBSession.add(shistory)
                DBSession.flush()
                #transaction.commit()
                scompound2 = DBSession.query(SCompound).filter_by(id=sid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
                if filename:
                    sfile2 = [sfile]
                    sfile2 += scompound2.filename
                    scompound2.filename = sfile2
                    flash(l_(u'Task completed successfully'))
            else:
                shistory.changes = schanges
                scompound.history += [shistory]
                DBSession.add(shistory)
                DBSession.flush()
                flash(l_(u'task completed successfully'))
        else:
            flash(l_(u'Permission denied'), 'warning')
            redirect(request.headers['Referer'])
        if kw and kw.has_key('come_from'):
            come_from = kw['come_from']
        else:
            come_from = request.headers['Referer']
        redirect(come_from)
    
    @expose()
    def delfile(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        file_id = int(args[0])
        sid = int(args[1])
        scompound = DBSession.query(SCompound).filter_by(id=sid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        if scompound.owner == userid:
            shistory = SHistory()
            shistory.gid = scompound.mol.gid
            shistory.project = pname
            shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            shistory.user = userid
            shistory.status = u'Delete File'
            
            file = DBSession.query(SFiles).get(file_id)
            shistory.changes = u'Deleted file: %s (%s)' % (file.name, file.filename) 
            scompound.history += [shistory]
            
            scompound.filename.remove(file)
            DBSession.delete(file)
            DBSession.add(shistory)
        else:
            flash(l_(u'Permission denied'), 'warning')
            redirect(request.headers['Referer'])
        flash(l_(u'Task completed successfully'))
        redirect(request.headers['Referer'])

    @expose('molgears.templates.users.synthesis.analitics') 
    def analitics(self, id, *kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(id)
        userid = request.identity['repoze.who.userid']
        scompound = DBSession.query( SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        effort = DBSession.query( Efforts ).get(scompound.effort_default)
        come_from = request.headers['Referer']
        if scompound.owner == userid:
            etap_max = effort.etap_max
            etap = effort.etap
            if etap == (etap_max - 1):
                flash(u'Please wait for saving.', 'warning')
                return dict(scompound=scompound, kierownik = None, come_from=come_from, page='synthesis', pname=pname)
            else:
                flash(l_(u'This is not the last etap'), 'error')
                redirect('/%s/synthesis' % pname)
        else:
            flash(l_(u'Permission denied'), 'error')
            redirect(request.headers['Referer'])

    @expose('')
    def save_analitics(self, id, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(id)
        userid = request.identity['repoze.who.userid']
        shistory = SHistory()
        shistory.project = pname
        shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shistory.user = userid
        shistory.status = 'Analytics'
        scompound = DBSession.query( SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        shistory.gid = scompound.mol.gid
        effort = DBSession.query( Efforts ).get(scompound.effort_default)
        schanges = u''
        if not (effort.etap < effort.etap_max):
            flash(l_(u'Etap number error'), 'error') # Błąd: Etap wiekszy lub równy maksymalnej liczbie etapów. Prawdopodobnie analityka już została dodana
            redirect('/%s/synthesis' % pname)
        etap = effort.etap
        next_status = DBSession.query( SStatus ).get(3)
        if not scompound.purity:
            try:
                kwas = str(kw['kwas'])
                kwas = kwas.replace(',', '.') 
                kwas = float(kwas)
                zasada = str(kw['zasada'])
                zasada = zasada.replace(',', '.') 
                zasada = float(zasada)
            except Exception as msg:
                kwas = None
                zasada = None
                flash(l_(u'Purity error. Float required: %s' % msg), 'error')
                redirect(request.headers['Referer'])
            if (kwas or zasada) >= 0:
                schanges = u'Current phase: ' + str(etap + 1) + u'; Status: ' + str(next_status.name)
                if kwas >= 0:
                    spurity1 = SPurity()
                    spurity1.value = kwas
                    spurity1.type = 'acid'
                    schanges += u'; Acid purity: ' + kw['kwas']
                    if kw.has_key('retention_kwas') and kw['retention_kwas'] != u'':
                        retention_kwas = str(kw['retention_kwas']).replace(',', '.') 
                        spurity1.retention_time = float(retention_kwas)
                        schanges += u'; Retention time (acid): ' + retention_kwas
                    scompound.purity += [spurity1]
                    try:
                        kwas_file = raw_path_basename(kw['kwas_file'].filename)
    
                    except Exception as msg:
                        kwas_file = None
                        pass
                    if kwas_file and userid:
                        number = DBSession.query(SFiles).count() + 1
                        new_kwas_file_name = str(number) + '_' + userid + '_' + str(id) + '_' + kwas_file
                        new_kwas_file_name.replace(' ', '_')
                        f_path = os.path.join(files_dir, new_kwas_file_name)
                        try:
                            f = file(f_path, "w")
                            f.write(kw['kwas_file'].value)
                            f.close()
                        except Exception as msg:
                            flash(l_(msg), 'error')
                            redirect(request.headers['Referer'])
                        sfile1 = SFiles()
                        sfile1.name = kwas_file
                        sfile1.filename = new_kwas_file_name
                        schanges += u'; Acid analytics: ' + kwas_file + u' (' + new_kwas_file_name + u')'
                        spurity1.filename = [sfile1]
                    else:
                        sfile1 = None
                else:
                    spurity1 = None
                    
                if zasada >= 0:
                    spurity2 = SPurity()
                    spurity2.value = zasada
                    spurity2.type = 'basic'
                    schanges += u'; Basic purity: ' + str(kw['zasada'])
                    if kw.has_key('retention_zasada') and kw['retention_zasada'] != u'':
                        retention_zasada = str(kw['retention_zasada']).replace(',', '.') 
                        spurity2.retention_time = float(retention_zasada)
                        schanges += u'; Retention time (basic): ' + retention_zasada
                    scompound.purity += [spurity2]
                    try:
                        zasada_file = raw_path_basename(kw['zasada_file'].filename)
                    except Exception as msg:
                        zasada_file = None
                        pass
                    if zasada_file and userid:
                        number = DBSession.query(SFiles).count() + 1
                        new_zasada_file_name = str(number) + '_' + userid + '_' + str(id) + '_' + zasada_file
                        new_zasada_file_name.replace(' ', '_')
                        f_path = os.path.join(files_dir, new_zasada_file_name)
                        try:
                            f = file(f_path, "w")
                            f.write(kw['zasada_file'].value)
                            f.close()
                        except Exception as msg:
                            flash(l_(msg), 'error')
                            redirect(request.headers['Referer'])
                        sfile2 = SFiles()
                        sfile2.name = zasada_file
                        sfile2.filename = new_zasada_file_name
                        schanges += u'; Basic analtytics: ' + zasada_file + ' (' + new_zasada_file_name +')'
                        spurity2.filename = [sfile2]
                    else:
                        sfile2 = None
                else:
                    spurity2 = None
            else:
                flash(l_(u'Acid or Basic purity is required'), 'error')
                redirect(request.headers['Referer'])
        else:
            spurity2 = None
            spurity1 = None
        if not kw['lso']:
            flash(l_(u'LSO is required'), 'error')
            redirect(request.headers['Referer'])
        if kw.has_key('lso') and kw['lso'] != u'' and kw['lso'].upper() != scompound.lso:
            scompound.lso = kw['lso'].upper()
            schanges += u' LSO: ' + kw['lso']

        if kw.has_key('form') and kw['form'] != scompound.form:
            scompound.form = kw['form']
            schanges += u'; Form: ' + kw['form']

        if kw.has_key('state') and kw['state'] != u'':
            try:
                state = str(kw['state'])
                state = state.replace(',', '.') 
            except Exception as msg:
                flash(l_(u'Float required: %s' % msg), 'error')
                redirect(request.headers['Referer'])
            if scompound.state != float(state):
                scompound.state = float(state)
                schanges += u'; State [mg]: ' + kw['state']
        else:
            scompound.state = 0
            
        if kw.has_key('notes') and kw['notes'] != scompound.notes:
            scompound.notes = kw['notes']
            schanges += u';Notes: ' + kw['notes']
        
        scompound.status = next_status
        scompound.stat3_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = u'Synthesis of Compound (GID: {0} & ID: {1}) finished\n, Details of compound: http://molgears/molgears/{2}/synthesis/details/{0}/{1}\n Recive compound: http://molgears/molgears/{2}/synthesis/accept/{1}'.format(scompound.gid, scompound.id, pname)
        effort.etap = etap +1
        scompound.etap_diff = effort.etap_max - effort.etap
        shistory.changes = schanges
        scompound.history += [shistory]
        purity_list = []
        if spurity1:
            purity_list.append(spurity1)
            if sfile1:
                DBSession.add(sfile1)
            DBSession.add(spurity1)
        if spurity2:
            purity_list.append(spurity2)
            if sfile2:
                DBSession.add(sfile2)
            DBSession.add(spurity2)
        DBSession.add(shistory)
        scompound.purity = purity_list
        from molgears.model import User
        from molgears.widgets.my_mail import sendmail
        user = DBSession.query(User).filter(User.display_name == scompound.principal).first()
        toaddrs = user.email_address
        sendmail(toaddrs, msg)
        DBSession.flush()
        #transaction.commit()
        if kw and kw.has_key('come_from'):
            come_from = kw['come_from']
        else:
            come_from = request.headers['Referer']
        flash(l_(u'Task completed successfully'))
        redirect(come_from)
        
    @expose("molgears.templates.users.synthesis.accept")
    def accept(self, id):
        """Odbiór związku"""
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(id)
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = '/MDM/synthesis/get_all'
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        scompound = DBSession.query( SCompound ).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        if not (scompound.status == DBSession.query(SStatus).get(3)):
            flash(l_(u'status error') , 'warning')
            redirect(come_from)
        if user.display_name == scompound.principal:
            return dict(scompound=scompound, kierownik = None, come_from=come_from, page='synthesis', pname=pname)
        else:
            flash(l_(u'Permission denied') , 'warning')
            redirect(come_from)
        
    @expose()
    def add_to_library(self, id, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(id)
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        scompound = DBSession.query( SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        if not scompound:
            flash(l_(u'Permission denied') , 'warning')
            redirect(request.headers['Referer'])
        if not (user.display_name == scompound.principal):
            flash(l_(u'Permission denied') , 'warning')
            redirect(request.headers['Referer'])
        if not (scompound.status == DBSession.query(SStatus).get(3)):
            flash(l_(u'status error') , 'warning')
            redirect(request.headers['Referer'])
        compound = DBSession.query( Compound ).get(scompound.gid)
        lcompound = LCompound()
        lcompound.mol = compound
        lcompound.sid = id
        lcompound.seq = scompound.seq
        lcompound.avg_ki_mdm2 = 0.0
        lcompound.avg_ic50_mdm2 = 0.0
        lcompound.avg_hillslope_mdm2 = 0.0
        lcompound.avg_r2_mdm2 = 0.0
#        lcompound.avg_bg_ic50_mdm2 = 0.0
#        lcompound.avg_bg_hillslope_mdm2 = 0.0
#        lcompound.avg_bg_r2_mdm2 = 0.0
        lcompound.avg_ki_mdm4 = 0.0
        lcompound.avg_ic50_mdm4 = 0.0
        lcompound.avg_hillslope_mdm4 = 0.0
        lcompound.avg_r2_mdm4 = 0.0
#        lcompound.avg_bg_ic50_mdm4 = 0.0
#        lcompound.avg_bg_hillslope_mdm4 = 0.0
#        lcompound.avg_bg_r2_mdm4 = 0.0
        lcompound.source = u'INTERNAL'
        lcompound.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if scompound.lso:
            lcompound.lso = scompound.lso.split(';')[-1]
        lcompound.owner = scompound.owner
        shistory = SHistory()
        shistory.gid = scompound.mol.gid
        shistory.project = pname
        shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shistory.user = userid
        shistory.status = u'Recive'
        shistory.changes = u'Status: received'
        lhistory = LHistory()
        lhistory.gid = lcompound.mol.gid
        lhistory.project = pname
        lhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lhistory.user = userid
        lhistory.status = u'Created'
        lchanges = u'Recived from no %s' % id 
        if scompound.purity:
            for purity in scompound.purity:
                lpurity = LPurity()
                lpurity.value = purity.value
                lpurity.type = purity.type
                lpurity.filename = purity.filename
                lcompound.purity += [lpurity]
                DBSession.add(lpurity)
        
        if kw.has_key('form'):
            lcompound.form = kw['form']
            lchanges += u'; Form: ' + kw['form']
        if kw.has_key('state'):
            try:
                state = str(kw['state'])
                state = state.replace(',', '.') 
                lcompound.state = float(state)
                lcompound.synthesisvalue = float(state)
            except Exception as msg:
                flash(l_(u'Float required: %s' % msg), 'error')
                redirect(request.headers['Referer'])
            lchanges += u'; Stan mag.[mg]: ' + kw['state']
        else:
            lcompound.state = 0
            lcompound.synthesisvalue = 0
        if kw.has_key('box'):
            lcompound.box = kw['box']
            lchanges += u'; Box: ' + kw['box']
        if kw.has_key('entry'):
            lcompound.entry = kw['entry']
            lchanges += u'; Entry: ' + kw['entry']
        if kw.has_key('showme'):
            if kw['showme'] == "True":
                lcompound.showme = True
            else:
                lcompound.showme = False
            lchanges += u'; Show in activity: ' + kw['showme']
        if kw.has_key('notes'):
            lcompound.notes = kw['notes']
            lchanges += u';Notes: ' + kw['notes']
        lhistory.changes = lchanges
        scompound.history += [shistory]
        lcompound.history = [lhistory]
        next_status = DBSession.query( SStatus ).get(4)
        scompound.status = next_status
        scompound.stat4_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        DBSession.add(lcompound)
        DBSession.add(shistory)
        DBSession.add(lhistory)
        DBSession.flush()
        compound.lnum = DBSession.query( LCompound ).filter_by(gid=scompound.gid).count()
        if kw and kw.has_key('come_from'):
            come_from = kw['come_from']
        else:
            come_from = request.headers['Referer']
        flash(l_(u'Task completed successfully'))
        redirect(come_from)
        

    @expose('molgears.templates.users.synthesis.multiedit')
    def multiedit(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
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
                    scompound = DBSession.query(SCompound).filter_by(id=int(arg)).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
#                    scompound.priority = int(kw['priority'])
                    shistory = SHistory()
                    shistory.gid = scompound.mol.gid
                    shistory.project = pname
                    shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    shistory.user = userid
                    shistory.status = u'Multi - edit'
                    schanges = u''
                    if kw.has_key('priority') and int(kw['priority']) != scompound.priority:
                        scompound.priority = int(kw['priority'])
                        schanges += u' Priority:' + kw['priority'] + u';'
                        pcompound = DBSession.query(PCompound).get(scompound.pid)
                        if pcompound:
                            pcompound.priority = int(kw['priority'])
                            phistory = PHistory()
                            phistory.project = pname
                            phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            phistory.user = userid
                            phistory.status = 'Priority'
                            phistory.changes = u'Priority: ' + kw['priority']
                            pcompound.history += [phistory]
                            DBSession.add(phistory)
                    if tagi and scompound.mol.tags != tagi:
                        scompound.mol.tags = tagi
                        schanges += u' Tags: '
                        for tag in tagi:
                            schanges += str(tag.name) + ';'
                    if notes and notes != scompound.notes:
                        scompound.notes = notes
                        schanges += u' Notes: ' + notes + u';'
                    scompound.history += [shistory]
                    DBSession.add(shistory)
                    DBSession.flush()
                    #transaction.commit()
                if kw.has_key('come_from'):
                    come_from = kw['come_from']
                else:
                    come_from = request.headers['Referer']
                flash(l_(u'Task completed successfully'))
                redirect(come_from)
                
        return dict(alltags=alltags, args=args, come_from=come_from, page='synthesis', pname=pname)
        
    @expose()
    def multietap(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        error = u''
        if args:
            for arg in args[1:]:
                scompound = DBSession.query(SCompound).filter_by(id=int(arg)).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
                effort = DBSession.query( Efforts ).get(scompound.effort_default)
                shistory = SHistory()
                shistory.gid = scompound.mol.gid
                shistory.project = pname
                shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                shistory.user = userid
                shistory.status = 'Phase change'
                schanges = ''
                etap = effort.etap
                etap_max = effort.etap_max
                if etap < etap_max - 1:
                    if etap >= 0:
                        effort.etap = etap +1
                        schanges = u'Current phase: ' + str(etap+1)
                    else:
                        effort.etap = etap +1
                        next_status = DBSession.query( SStatus ).get(2)
                        scompound.status = next_status
                        scompound.stat2_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                        scompound.status_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        schanges = u'Current phase: ' + str(etap+1) + u'; Status: ' + str(next_status.name)
                    if effort.id == scompound.effort_default:
                        scompound.etap_diff = effort.etap_max - effort.etap
                    shistory.changes = schanges
                    scompound.history += [shistory]
                    DBSession.add(shistory)
                    DBSession.flush()
                    #transaction.commit()
                else:
                    error += str(scompound.gid) + ' [' + str(scompound.id) + ']' + ', '
            flash(l_(u'Task completed successfully'))
        if error and error != u'':
            flash(u'Etap zmieniony tylko dozwolonym cząsteczkom. Nie można zmienić etapu dla cząsteczek o numerach GID [ID]: %s.' % error, 'error')
        
        redirect(request.headers['Referer'])

    @expose('molgears.templates.users.synthesis.allefforts')
    def allefforts(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = args[0]
        scompound = DBSession.query( SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        efforts = sorted(scompound.effort, key=lambda x: x.id)
        return dict(scompound=scompound, efforts =efforts, page='synthesis', pname=pname)
        
    @expose('molgears.templates.users.synthesis.allefforts')
    def effort_default(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        id = int(args[0])
        effort_id = int(args[1])
        scompound = DBSession.query( SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        effort = DBSession.query( Efforts ).get(effort_id)
        if scompound.owner == userid:
            scompound.effort_default = effort_id
            schanges = u''
            schanges += u'Default etap change from ID: %s; ' % effort_id
            shistory = SHistory()
            shistory.gid = scompound.mol.gid
            shistory.project = pname
            shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            shistory.user = userid
            if effort.etap<effort.etap_max:
                scompound.status = DBSession.query( SStatus ).get(2)
                scompound.stat2_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                schanges += u'Status: synthesis; '
            elif effort.etap==effort.etap_max:
                scompound.status = DBSession.query( SStatus ).get(3)
                scompound.stat3_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                schanges += u'Status: finished; '
            shistory.changes = schanges
            scompound.history += [shistory]
            DBSession.add(shistory)
            DBSession.flush()
            redirect(request.headers['Referer'])
        else:
            flash(l_(u'Permission denied'),'error')
            redirect(request.headers['Referer'])
        
    @expose('molgears.templates.users.synthesis.edit_effort')
    def edit_effort(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(args[0])
        scompound = DBSession.query(SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        try:
            effort_id = int(args[1])
        except Exception:
            effort_id = None
        if effort_id:
            effort = DBSession.query( Efforts ).get(effort_id)
        else:
            effort = DBSession.query( Efforts ).get(scompound.effort_default)
        userid = request.identity['repoze.who.userid']
        if scompound.owner == userid:
            if kw:
                shistory = SHistory()
                shistory.gid = scompound.mol.gid
                shistory.project = pname
                shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                shistory.user = userid
                shistory.status = u'Edit effort'
                schanges = u''
                if kw.has_key('effort_name') and kw['effort_name'] != u'':
                    effort.name = kw['effort_name']
                    schanges += u'Effort name: ' + kw['effort_name']
                if kw.has_key('notes') and kw['notes'] != u'':
                    effort.notes = kw['notes']
                    schanges += u';Notes: ' + kw['notes']
                try:
                    reaction_file = raw_path_basename(kw['reaction'].filename)
                except Exception as msg:
                    reaction_file = None
                    pass
                if reaction_file:
                    ext = os.path.splitext(reaction_file)[-1].lower()
                    if ext not in ['.jpg', '.jpeg', '.png']:
                        flash(l_(u'File extension error'), 'error')
                        redirect(request.headers['Referer'])
                    number2 = DBSession.query(SFiles).count() + 1
                    newfilename2 = str(number2) + '_' + userid + '_' + str(id) + '_' + reaction_file
                    newfilename2.replace(' ', '_')
                    f_path2 = os.path.join(files_dir, newfilename2)
                    try:
                        f2 = file(f_path2, "w")
                        f2.write(kw['reaction'].value)
                        f2.close()
                    except Exception as msg:
                        flash(l_(msg), 'error')
                        redirect(request.headers['Referer'])
                    if ext in ['.jpg', '.jpeg', '.png']:
                        reaction_sfile = SFiles()
                        reaction_sfile.name = reaction_file
                        reaction_sfile.filename = newfilename2
                        schanges += u' Reaction path: ' + reaction_file + u' ( ' + newfilename2 + u' )'
                        effort.reaction = [reaction_sfile]                    
                        DBSession.add(reaction_sfile)
                    else:
                        flash(l_(u'File extension error'))
                        redirect(request.headers['Referer'])
                shistory.changes = schanges
                scompound.history += [shistory]
                DBSession.add(shistory)
                DBSession.flush()
                flash(l_(u'Task completed successfully'))
                redirect(request.headers['Referer'])
            else:
                return dict(scompound=scompound, effort=effort, page='synthesis', pname=pname)
        else:
            flash(l_(u'Permission denied'), 'error')
            redirect(request.headers['Referer'])
        return dict(scompound=scompound, page='synthesis', pname=pname)

    @expose('molgears.templates.users.synthesis.effort_next')
    def effort_next(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(args[0])
        userid = request.identity['repoze.who.userid']
        scompound = DBSession.query( SCompound).filter_by(id=id).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        if scompound.owner == userid:
            if kw:
                try:
                    reason = kw['reason']
                except Exception:
                    reason = None
                if reason and reason != u'':
                    schanges = u'Warning! Adding etap for reason:' + reason
                    etap = int(kw['etap']) 
                    etap_max = int(kw['etap_max'])
                    if etap < etap_max:
                        effort= Efforts()
                        effort.etap = etap
                        effort.etap_max = etap_max
                        scompound.status = DBSession.query( SStatus ).get(2)
                        scompound.stat2_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if kw.has_key('effort_name') and kw['effort_name'] != u'':
                            effort.name = kw['effort_name']
                            schanges += u'; Effort name: ' + kw['effort_name']
                        schanges += u'; Current phase: ' + str(etap)
                        schanges += u'; No of phases: ' + str(etap_max)
                        try:
                            reaction_file = raw_path_basename(kw['reaction'].filename)
                        except Exception as msg:
                            reaction_file = None
                            pass
                        if reaction_file:
                            number2 = DBSession.query(SFiles).count() + 1
                            newfilename2 = str(number2) + '_' + userid + '_' + str(id) + '_' + reaction_file
                            newfilename2.replace(' ', '_')
                            f_path2 = os.path.join(files_dir, newfilename2)
                            try:
                                f2 = file(f_path2, "w")
                                f2.write(kw['reaction'].value)
                                f2.close()
                            except Exception as msg:
                                flash(l_(msg), 'error')
                                redirect(request.headers['Referer'])
                            reaction_sfile = SFiles()
                            reaction_sfile.name = reaction_file
                            reaction_sfile.filename = newfilename2
                            schanges += u' Reaction path: ' + reaction_file + u' ( ' + newfilename2 + u' )'
                            effort.reaction += [reaction_sfile]
                            DBSession.add(reaction_sfile)
                        scompound.effort += [effort]
                        DBSession.add(effort)
                        shistory = SHistory()
                        shistory.gid = scompound.mol.gid
                        shistory.project = pname
                        shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        shistory.user = userid
                        shistory.status = 'Add effort'
                        shistory.changes = schanges
                        scompound.history += [shistory]
                        DBSession.add(shistory)
                        flash(l_(u'Task completed successfully'))
                        redirect(request.headers['Referer'])
                    else:
                        flash(l_(u'Etap error'), 'error')
                        redirect(request.headers['Referer'])
                else:
                    flash(l_(u'Reasons are required'), 'error')
                    redirect(request.headers['Referer'])
            else:
                effort = DBSession.query( Efforts ).get(scompound.effort_default)
                etap_max = effort.etap_max
                etap = effort.etap
                return dict(scompound=scompound, etap=etap, etap_max=etap_max, page='synthesis', pname=pname)
        else:
            flash(l_(u'Permission denied'), 'warning')
            redirect(request.headers['Referer'])

    @expose()
    def discontinue(self, *args, **kw):
        """
        Chemist discontinue of synthesis (if synthesis status <=2 and is synthesis owner).
        Chamge status of synthesis compound as discontinue.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if args:
            for arg in args:
                try:
                    scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(SCompound.id==int(arg)).first()
                except Exception as msg:
                    flash(l_(u'Compound number error %s' % msg), 'error')
                    redirect(come_from)
                if scompound.owner == userid:
                    if scompound.status_id <= 2:
                        scompound.status = DBSession.query(SStatus).get(6)
                        shistory = SHistory()
                        shistory.gid = scompound.mol.gid
                        shistory.project = pname
                        shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        shistory.user = userid
                        shistory.status = 'Discontinue'
                        shistory.changes = 'Status: discontinue'
                        scompound.history += [shistory]
                        DBSession.add(shistory)
                    else:
                        flash(l_(u'Status error'), 'error')
                        redirect(come_from)
                else:
                    flash(l_(u'Permission denied'), 'error')
                    redirect(come_from)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        else:
            flash(l_(u'Select Compounds'), 'error')
            redirect(come_from)
            
    @expose()
    def enable(self, *args, **kw):
        """
        Chemist continue of synthesis (if user is synthesis owner).
        Chamge status of synthesis compound as pending if phase is -1 or synthesis if phase is >-1.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if args:
            for arg in args:
                try:
                    scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(SCompound.id==int(arg)).first()
                except Exception as msg:
                    flash(l_(u'Compound number error %s' % msg), 'error')
                    redirect(come_from)
                if scompound.owner == userid:
                    if scompound.status_id == 9:
                        default_effort = next(obj for obj in scompound.effort if obj.id==scompound.effort_default)
                        assert default_effort != None, "Effort errror"
                        if default_effort.etap == -1:
                            scompound.status = DBSession.query(SStatus).get(1)
                        else:
                            if default_effort.etap == default_effort.max_etap:
                                scompound.status = DBSession.query(SStatus).get(4)
                            else:
                                scompound.status = DBSession.query(SStatus).get(2)
                        shistory = SHistory()
                        shistory.gid = scompound.mol.gid
                        shistory.project = pname
                        shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        shistory.user = userid
                        shistory.status = 'Continue'
                        shistory.changes = 'Status: continue'
                        scompound.history += [shistory]
                        DBSession.add(shistory)
                    else:
                        flash(l_(u'Status error'), 'error')
                        redirect(come_from)
                else:
                    flash(l_(u'Permission denied'), 'error')
                    redirect(come_from)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        else:
            flash(l_(u'Select Compounds'), 'error')
            redirect(come_from)

    @expose()
    def reject(self, *args, **kw):
        """
        Chemist rejection of synthesis (if synthesis status <=2 and is synthesis owner).
        Chamge status of synthesis compound as rejected and set request compound status as canceled.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if args:
            for arg in args:
                try:
                    scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(SCompound.id==int(arg)).first()
                except Exception:
                    flash(l_(u'Compound number error'), 'error')
                    redirect(come_from)
                if scompound and scompound.status_id <= 2 and scompound.owner == userid:
                    pcompound = DBSession.query(PCompound).get(scompound.pid)
                    shistory = SHistory()
                    shistory.gid = scompound.mol.gid
                    shistory.project = pname
                    shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    shistory.user = userid
                    shistory.status = u'Reject'
                    shistory.changes = u'Reject synthesis compound of GID %s (ID %s)' % (scompound.gid, arg)
                    phistory = PHistory()
                    phistory.gid = pcompound.gid
                    phistory.project = pname
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.user = userid
                    phistory.status = u'Reject'
                    phistory.changes = u'Status change due rejection of synthesis compound of GID %s (request ID %s)' % (scompound.gid, scompound.pid)
                    if pcompound:
                        pcompound.status = DBSession.query(PStatus).get(3)
                        scompound.status = DBSession.query(SStatus).get(5)
                        scompound.history += [shistory]
                        pcompound.history += [phistory]
                    else:
                        flash(l_(u'Request compound error'), 'error')
                        redirect(come_from)
                    DBSession.add(shistory)
                    DBSession.add(phistory)
                else:
                    flash(l_(u'Permission denied. Check the owner or status.'), 'error')
                    redirect(come_from)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        else:
            flash(l_(u'Select Compounds'), 'error')
            redirect(come_from)
            
    @expose()
    def resign(self, *args, **kw):
        """
        Chemist resignation of synthesis (if synthesis status <=2 and is synthesis owner).
        Chamge status of synthesis compound as discontinue and set request compound status as proposed.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if args:
            for arg in args:
                try:
                    scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(SCompound.id==int(arg)).first()
                except Exception:
                    flash(l_(u'Compound number error'), 'error')
                    redirect(come_from)
                if scompound and scompound.status_id <= 2 and scompound.owner == userid:
                    pcompound = DBSession.query(PCompound).get(scompound.pid)
                    shistory = SHistory()
                    shistory.gid = scompound.mol.gid
                    shistory.project = pname
                    shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    shistory.user = userid
                    shistory.status = u'Resign'
                    shistory.changes = u'Resign from synthesis of GID %s (ID projektowe %s)' % (scompound.gid, arg)
                    phistory = PHistory()
                    phistory.gid = pcompound.gid
                    phistory.project = pname
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.user = userid
                    phistory.status = u'Resign'
                    phistory.changes = u'Status change due chemist resign of synthesis compound of GID %s (request ID %s)' % (scompound.gid, scompound.pid)
                    if pcompound:
                        pcompound.status = DBSession.query(PStatus).get(1)
                        scompound.status = DBSession.query(SStatus).get(6)
                        scompound.history += [shistory]
                        pcompound.history += [phistory]
                    else:
                        flash(l_(u'Request compound error'), 'error')
                        redirect(come_from)
                    DBSession.add(shistory)
                    DBSession.add(phistory)
                else:
                    flash(l_(u'Permission denied. Check the owner or status.'), 'error')
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
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if has_permission('manage'):
            if args:
                for arg in args:
                    try:
                        scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(SCompound.id==int(arg)).first()
                    except Exception:
                        flash(l_(u'Compound number error'), 'error')
                        redirect(come_from)
                    if scompound and scompound.status_id <= 2 and has_permission('manage'):
                        pcompound = DBSession.query(PCompound).get(scompound.pid)
                        shistory = SHistory()
                        shistory.gid = scompound.mol.gid
                        shistory.project = pname
                        shistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        shistory.user = userid
                        shistory.status = u'Withdraw'
                        shistory.changes = u'Withdraw synthesis compound of GID %s (ID projektowe %s)' % (scompound.gid, arg)
                        phistory = PHistory()
                        phistory.gid = pcompound.gid
                        phistory.project = pname
                        phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        phistory.user = userid
                        phistory.status = u'Withdraw'
                        phistory.changes = u'Status change due withdraw of synthesis compound of GID %s (request ID %s)' % (scompound.gid, scompound.pid)
                        if pcompound:
                            pcompound.status = DBSession.query(PStatus).get(3)
                            scompound.status = DBSession.query(SStatus).get(6)
                            scompound.history += [shistory]
                            pcompound.history += [phistory]
                        else:
                            flash(l_(u'Request compound error'), 'error')
                            redirect(come_from)
                        DBSession.add(shistory)
                        DBSession.add(phistory)
                    else:
                        flash(l_(u'Permission denied.'), 'error')
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
    def download(self, *args):
        pname = request.environ['PATH_INFO'].split('/')[1]
        if not args:
            redirect(request.headers['Referer'])
        else:
            filename = args[-1]
            ext = args[-2]
            filepath = os.path.join('./molgears/files/download/', str(filename + '.' + ext))
            userid = request.identity['repoze.who.userid']
        if has_permission('user'):
            if len(args)>=3:
                scompound = ()
                for arg in args[:-2]:
                    scompound += (DBSession.query(SCompound).filter(SCompound.id==int(arg)).first(), )
            else:
                if filename == u'02_synthesis_my':
                    scompound = DBSession.query(SCompound).join(SCompound.mol).filter(SCompound.owner.contains(userid)).filter(Compound.project.any(Projects.name==pname))
                elif filename == u'02_synthesis_recive':
                    status = DBSession.query(SStatus).get(3)
                    scompound = DBSession.query(SCompound).filter(SCompound.status ==status).filter(SCompound.principal.contains(userid)).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname))
                else:
                    scompound = DBSession.query(SCompound).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
            if ext == u'xls':
                import xlwt
                wbk = xlwt.Workbook()
                sheet = wbk.add_sheet('sheet1')
                sheet.write(0,0,u'GID')
                sheet.write(0,1,u'ID')
                sheet.write(0,2,u'Name')
                sheet.write(0,3,u'SMILES')
                sheet.write(0,4,u'Owner')
                sheet.write(0,5,u'Principal')
                sheet.write(0,6,u'Priority')
                sheet.write(0,7,u'Notes')
                i = 1
                for row in scompound:
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
                for row in scompound:
                    f.write('%s %s \n' % (row.mol.structure, row.mol.name))
                f.close()
            import paste.fileapp
            f = paste.fileapp.FileApp(filepath)
            from tg import use_wsgi_app
            return use_wsgi_app(f)
        else:
            flash(l_('Error 404'),'error')
            redirect(request.headers['Referer'])
            

    @expose('molgears.templates.users.synthesis.history')
    def history(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        history = DBSession.query( SHistory ).filter(SHistory.project.any(Projects.name==pname))
        order='SHistory.id'
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
                        order = SHistory.scompound_id
                    elif v == 'user':
                        order = SHistory.user
                    elif v == 'date':
                        order = SHistory.date
                    else:
                        order = v
                if str(k) != 'remove':
                    tmpl += str(k) + '=' + str(v) + '&'
            if search_clicked:
                if kw.has_key('text_gid') and kw['text_gid'] !=u'':
                    try:
                        gid = int(kw['text_gid'])
                        history = history.filter(SCompound.id == gid )
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_user') and kw['text_user'] !=u'':
                    history = history.filter(SHistory.user.like(kw['text_user'].replace('*', '%')))
                if kw.has_key('text_status') and kw['text_status'] !=u'':
                    history = history.filter(SHistory.status.like(kw['text_status'].replace('*', '%')))
                if kw.has_key('text_changes') and kw['text_changes'] !=u'':
                    history = history.filter(SHistory.changes.like(kw['text_changes'].replace('*', '%')))
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    history = history.filter(SHistory.date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            history = history.filter(SHistory.date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        history = history.filter(SHistory.date < date_to)
        if dsc:
            history = history.order_by(desc(order).nullslast())
        else:
            history = history.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(history, page, url=page_url, items_per_page=items)
        return dict(history=currentPage.items, currentPage=currentPage, tmpl=tmpl, one_day=one_day, now=now, page='synthesis', pname=pname)
        
    @expose()
    def deletefromlist(self, ulist_id, *args):
        ulist = DBSession.query(UserLists).get(ulist_id)
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

