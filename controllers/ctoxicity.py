# -*- coding: utf-8 -*-
import tg
from tg import expose, flash, redirect, request, url
from tg.i18n import ugettext as _, lazy_ugettext as l_
from molgears import model
from molgears.model import DBSession, Projects, Tags, User
from molgears.model.auth import UserLists
from molgears.model import Compound, Names, PCompound, SCompound, LCompound, LPurity
from molgears.model import TestCT, CTResults, CTHistory, CTFiles
from molgears.controllers.error import ErrorController
from molgears.lib.base import BaseController
import os
from pkg_resources import resource_filename
from sqlalchemy import desc, asc

from rdkit import Chem
from molgears.widgets.structure import checksmi
from molgears.widgets.format import raw_path_basename
from datetime import datetime

#from tg.decorators import paginate
from webhelpers import paginate
from tg.predicates import has_permission
from molgears.widgets.rgbTuple import htmlRgb100

__all__ = ['CytotoxicityController']

public_dirname = os.path.join(os.path.abspath(resource_filename('molgears', 'public')))
files_dir = os.path.join(public_dirname, 'files')
result_files_dir = os.path.join(files_dir, 'resultsct')
photo_files_dir = os.path.join(result_files_dir, 'photo')

# -------- Cytotoxicity controller ----------------------------------------------------------------------------------------------------------------------------------

class CytotoxicityController(BaseController):
    @expose('molgears.templates.users.results.ctoxicity.index')
    def index(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter_by(name=pname).first()
        import pickle
        try:
            celllines = pickle.loads([test.cell_line for test in project.tests if test.name == 'CT'][0])
        except:
            celllines = None
        userid = request.identity['repoze.who.userid']
        lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.ctoxicity != None)
        dsc = True
        order = LCompound.id
        tmpl = u''
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        selection, similarity = [None, None]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        ulist = None
        ulists = set([l for l in user.lists if l.table == 'CTResults'] + [l for l in user.tg_user_lists if l.table == 'CTResults'])
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
                        elements = [int(el) for el in pickle.loads(ulist.elements)]
                        if ulist.table == 'CTResults':
                            lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.id.in_(elements))
                        else:
                            flash(l_(u'Table error'), 'error')
                            redirect(request.headers['Referer'])
                else:
                    flash(l_(u'Permission denied'), 'error')
                    redirect(request.headers['Referer'])
            if kw.has_key('showall') and kw['showall']=='YES':
                lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname))
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    if v == 'lcode':
                        order = LCompound.lcode
                    elif hasattr(LCompound, v):
                        order = LCompound.__getattribute__(LCompound, v)
                    else:
                        if v == 'purity':
                            lcompound = lcompound.join(LCompound.purity)
                            order = LPurity.value
                        else:
                            all_lcompounds = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).all()
                            for l in all_lcompounds:
                                l.avg_ct = v
#                            lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname))
                            order = u'_avg_ct'
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
                        if method == 'smililarity':
#                            from razi.postgresql_rdkit import tanimoto_threshold
#                            DBSession.execute(tanimoto_threshold.set(threshold))
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            
                            search = DBSession.query(LCompound, tanimoto_sml).join(LCompound.mol).join(LCompound.purity).filter(Compound.project.any(Projects.name==pname)).filter(constraint)
                            if order != 'id' and order !=LCompound.id:
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
                            page_url = paginate.PageURL_WebOb(request)
                            currentPage = paginate.Page(lcompound, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage,tmpl=tmpl, page='ctoxicity', pname=pname, alltags=alltags, similarity=similarity,htmlRgb=htmlRgb100, celllines=celllines, ulists=ulists, ulist=ulist)
    
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
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    lcompound = lcompound.filter(CTResults.create_date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            lcompound = lcompound.filter(CTResults.create_date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        lcompound = lcompound.filter(CTResults.create_date < date_to)

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
                        tagi = [int(id) for id in tags]
                    lcompound = lcompound.filter(Compound.tags.any(Tags.id.in_(tagi)))
                if kw.has_key('text_test') and kw['text_test'] != u'':
                    test = [int(kw['text_test'])]
                    lcompound = lcompound.filter(LCompound.mdm2.any(ResultsFP.assey_id.in_(test)))
        
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
                    from xhtml2pdf.pisa import CreatePDF, startViewer
                    from tg.render import render as render_template
                    import cStringIO
                    html = render_template({"length":len(lcompounds), "lcompound":lcompounds, "celllines":celllines, "options":options, "size":size}, "genshi", "molgears.templates.users.results.ctoxicity.print2", doctype=None)
                    dest = './molgears/files/pdf/' + filename
                    result = file(dest, "wb")
                    pdf = CreatePDF(cStringIO.StringIO(html.encode("UTF-8")), result, encoding="utf-8")
                    result.close()
                    import paste.fileapp
                    f = paste.fileapp.FileApp('./molgears/files/pdf/'+ filename)
                    from tg import use_wsgi_app
                    return use_wsgi_app(f)
                elif kw['file_type'] == 'xls':
                    filename = userid + '_ctox.xls'
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
                    if 'creator' in options:
                        sheet.write(0,j,u'Chemist')
                        j+=1
                    if 'create_date' in options:
                        sheet.write(0,j,u'Date')
                        j+=1
                    if 'tags' in options:
                        sheet.write(0,j,u'Tags')
                        j+=1
                    if 'notes' in options:
                        sheet.write(0,j,u'Notes')
                        j+=1
                    for cell in celllines:
                        if '_CT_%s' % cell in options:
                            sheet.write(0,j,u'%s' % cell)
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
                        if 'creator' in options:
                            sheet.write(i,j, row.owner)
                            j+=1
                        if 'create_date' in options:
                            sheet.write(i,j, str(row.create_date))
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
                        for cell in celllines:
                            if '_CT_%s' % cell in options:
                                res = []
                                if row.ctoxicity:
                                    for ct in sorted(row.ctoxicity, key=lambda ct: ct.id):
                                        if ct.cell_line==cell:
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
                            if 'purity' in options:
                                pur = u''
                                for p in sorted(row.purity, key=lambda p: p.value, reverse=True):
                                    pur += u'%s : %s\n' % (p.value, p.type)
                                line.append(pur)
                            if 'create_date' in options:
                                line.append(unicode(row.create_date))
                            if 'creator' in options:
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
                            for cell in celllines:
                                if '_CT_%s' % cell in options:
                                    res = []
                                    if row.ctoxicity:
                                        for ct in sorted(row.ctoxicity, key=lambda ct: ct.id):
                                            if ct.cell_line==cell:
                                                res.append(ct.ic50)
                                    if len(res)>0:
                                        line.append(str(round(sum(res)/len(res), 3)))
                                    else:
                                        line.append('-')
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
            elif kw['akcja'] == u'plot':
                redirect('/%s/results/ctoxicity/plot%s' % (pname, argv))    
            elif kw['akcja'] == u'results':
                if len(selection) == 1:
                    redirect('/%s/results/ctoxicity/readresult%s' % (pname, argv))
                else:
                    redirect('/%s/results/multiresults/index%s' % (pname, argv))
            else:
                redirect('/%s/results/ctoxicity/%s%s' % (pname, kw['akcja'], argv))

        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(lcompound, page, url=page_url, items_per_page=items)

        return dict(currentPage=currentPage,tmpl=tmpl, page='ctoxicity', htmlRgb=htmlRgb100, pname=pname, alltags=alltags, similarity=similarity, celllines=celllines, ulists=ulists, ulist=ulist)
        
    @expose('molgears.templates.users.results.ctoxicity.tests')
    def tests(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        tests = DBSession.query(TestCT).order_by('TestCT.id').all()
        return dict(tests=tests, page='ctoxicity', pname=pname)

    @expose('molgears.templates.users.results.ctoxicity.addtest')
    def addtest(self, *args, **kw):
        """Display a page to show a new record."""
        pname = request.environ['PATH_INFO'].split('/')[1]
        if kw:
            userid = request.identity['repoze.who.userid']
            if kw.has_key('name') and kw['name'] != u'' and kw.has_key('type') and kw['type'] != u'':
                testct = TestCT()
                testct.name = kw['name']
                testct.type  = kw['type']
                testct.project = pname
                if kw.has_key('time') and kw['time'] != u'':
                    testct.time = float(kw['time'].replace(',', '.'))
                if kw.has_key('notes') and kw['notes'] != u'':
                    testct.notes = kw['notes']
                DBSession.add(testct)
                DBSession.flush()
                flash(l_(u'Tasks completed successfully'))
                redirect(request.headers['Referer'])
            else:
                flash(l_(u'Name and type of test are required'), 'error')
                redirect(request.headers['Referer'])
        return dict(page='ctoxicity', pname=pname)
        
        
    @expose('molgears.templates.users.results.ctoxicity.readresults')
    def readresult(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter_by(name=pname).first()
        project_ct_test = [test for test in project.tests if test.name == 'CT'][0]
        import pickle
        cell_line = pickle.loads(project_ct_test.cell_line)
        lcompound = None
        tests = DBSession.query(TestCT).order_by('TestCT.id').all()
        come_from = request.headers['Referer']
        if kw:
            changes = u''
            userid = request.identity['repoze.who.userid']
            if kw.has_key('come_from'):
                come_from = kw['come_from']
            else:
                come_from = request.headers['Referer']
            try:
                filename = raw_path_basename(kw['file'].filename)
            except Exception as msg:
                flash(l_(msg), 'error')
                redirect(request.headers['Referer'])
                filename = None
                pass
            if filename and userid:
                number = DBSession.query(CTFiles).count() + 1
                newfilename = 'TEMP_' + str(number) + '_' + userid + '_' + '_' + filename
                newfilename.replace(' ', '_')
                f_path = os.path.join(result_files_dir, newfilename)
                try:
                    f = file(f_path, "w")
                    f.write(kw['file'].value)
                    f.close()
                except Exception as msg:
                    flash(l_(msg), 'error')
                    redirect(request.headers['Referer'])
            else:
                flash(l_(u'File error'), 'error')
                redirect(request.headers['Referer'])
            if kw.has_key('testname') and kw['testname'] != u'':
                test = DBSession.query(TestCT).get(kw['testname'])
                changes += u'; TestCT: ' + test.name
            else:
                flash(l_(u'test is required'), 'error')
                redirect(request.headers['Referer'])
            if kw.has_key('cell_line') and kw['cell_line'] != u'':
                cline = kw['cell_line']
                changes += u'; Linia: ' + cline
            else:
                flash(l_(u'Cell line is required'), 'error')
                redirect(request.headers['Referer'])
            if kw.has_key('date') and kw['date'] != u'':
                date = datetime.strptime(str(kw['date']), '%Y-%m-%d')
                changes == u'; Data: ' +  kw['date']
            else:
                date = None
            if kw.has_key('notes') and kw['notes'] != u'':
                notes = kw['notes']
                changes += u';Notes: ' + kw['notes']
            else:
                notes = None
            from molgears.widgets.ct_result import read_many, save_fix_data, write_result
            X, M = read_many(f_path)
            name, top, data=[None, None, None]
            for row in M:
                if not (M.index(row) %3):
                    if name and top and data:
                        try:
                            box = int(name[0])
                        except Exception:
                            box = None
                        if box:
                            lcompound= DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.box.like(str(box))).filter(LCompound.entry.like(name[1:].replace(' ', ''))).first()
                        else:
                            lcompound= DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(Compound.name==name).first()
                        if not lcompound:
                            lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(Compound.names.any(Names.name.like(name))).first()
                            if not lcompound:
                                flash(l_(u'Compound name not found: %s' % name), 'error')
                                redirect('/%s/results/ctoxicity/readresult' % pname)
                        result = CTResults()
                        rhistory = CTHistory()
                        if date:
                            result.date = date
                        rhistory.gid = lcompound.gid
                        rhistory.lid = lcompound.id
                        rhistory.project = pname
                        rhistory.user = userid
                        rhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        rhistory.status = u'Wczytaj wynik'
                        result.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        result.gid = lcompound.gid
                        changes += u'GID: ' + str(lcompound.gid)
                        result.history += [rhistory]
                        lcompound.ctoxicity += [result]
                        DBSession.add(rhistory)
                        DBSession.add(result)
                        DBSession.flush()
                        last_result = DBSession.query(CTResults).order_by(desc('id')).first()
                        fname = '%s_%s' % (name, filename)
                        newfname = '%s_%s.csv' % (last_result.lid, last_result.id)
                        fpath = os.path.join(result_files_dir, newfname)
                        write_result(top, X, data, fpath)
                        for line in data:
                            for el in line:
                                line[line.index(el)] = 100.0*el/(sum(top)/len(top))
                        rfile = CTFiles()
                        rfile.name = fname
                        rfile.filename = newfname
                        changes += u'; Plik: ' + filename + u' ( ' + newfilename + u' )'
                        last_result.history.changes = changes
                        last_result.files = [rfile]
                        last_result.test = test
                        if notes:
                            last_result.notes = notes
                        last_result.cell_line = cline
                        graphs_path = os.path.join(public_dirname, 'img/graphsct/%s_%s.png' % (last_result.lid, last_result.id))
#                        thumb_graphs_path = os.path.join(public_dirname, 'img/graphsct/thumb_%s_%s.png' % (last_result.lid, last_result.id))
#                        save_fix_data(X, data, thumb_graphs_path, dpi=50)
                        ic50, hillslope, r2 = save_fix_data(X, data, graphs_path)
                        
                        if ic50 <1000:
                            last_result.ic50 = ic50
                        else:
                            last_result.ic50 = 1000
                        last_result.hillslope = hillslope
                        last_result.r2 =r2
                        DBSession.add(rfile)
                        DBSession.flush()
                        name, top, data=[None, None, None]
                    name = row[0]
                    top = [float(row[1].replace(',', ''))]
                    list = []
                    data =[]
                    for el in row[2:]:
                        if str(el) != '*':
                            el = float(el.replace(',', ''))
                            list.append(round(el, 3))
                    data.append(list)
                    
                else:
                    assert row[0] == name, u'Zły format pliku'
                    top.append(float(row[1].replace(',', '')))
                    i=0
                    list=[]
                    for el in row[2:]:
                        if str(el) != '*':
                            el =float(el.replace(',', ''))
                            list.append(round(el, 3))
                    data.append(list)
            try:
                box = int(name[0])
            except Exception:
                box = None
            if box:
                lcompound= DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.box.like(str(box))).filter(LCompound.entry.like(name[1:].replace(' ', ''))).first()
            else:
                lcompound= DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(Compound.name==name).first()
            if not lcompound:
                lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(Compound.names.any(Names.name.like(name))).first()
                if not lcompound:
                    flash(l_(u'Compound name not found: %s' % name), 'error')
                    redirect('/%s/results/ctoxicity/readresult' % pname)
            result = CTResults()
            rhistory = CTHistory()
            rhistory.gid = lcompound.gid
            rhistory.lid = lcompound.id
            rhistory.project = pname
            rhistory.user = userid
            rhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rhistory.status = u'Wczytaj wynik'
            result.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result.gid = lcompound.gid
            changes += u'GID: ' + str(lcompound.gid)
            result.history += [rhistory]
            lcompound.ctoxicity += [result]
            DBSession.add(rhistory)
            DBSession.add(result)
            DBSession.flush()
            last_result = DBSession.query(CTResults).order_by(desc('id')).first()
            fname = '%s_%s' % (name, filename)
            newfname = '%s_%s.csv' % (last_result.lid, last_result.id)
            fpath = os.path.join(result_files_dir, newfname)
            write_result(top, X, data, fpath)
            for line in data:
                for el in line:
                    line[line.index(el)] = 100.0*el/(sum(top)/len(top))
            rfile = CTFiles()
            rfile.name = fname
            rfile.filename = newfname
            changes += u'; Plik: ' + filename + u' ( ' + newfilename + u' )'
            last_result.history.changes = changes
            last_result.files = [rfile]
            last_result.test = test
            if notes:
                last_result.notes = notes
            last_result.cell_line = cline
            graphs_path = os.path.join(public_dirname, 'img/graphsct/%s_%s.png' % (last_result.lid, last_result.id))
#            thumb_graphs_path = os.path.join(public_dirname, 'img/graphsct/thumb_%s_%s.png' % (last_result.lid, last_result.id))
#            save_fix_data(X, data, thumb_graphs_path, dpi=50)
            ic50, hillslope, r2 = save_fix_data(X, data, graphs_path)
            
            if ic50<1000:
                last_result.ic50 = ic50
            else:
                last_result.ic50 = 1000
            last_result.hillslope = hillslope
            last_result.r2 =r2
            DBSession.add(rfile)
            DBSession.flush()
#            os.remove(f_path)
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        return dict(lcompound=lcompound, tests=tests, come_from=come_from, cell_line=cell_line, page='ctoxicity', pname=pname)
        
    @expose('molgears.templates.users.results.ctoxicity.details')
    def details(self, *args, **kw):
        gid = int(args[0])
        lid = int(args[1])
        pname = request.environ['PATH_INFO'].split('/')[1]
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter_by(name=pname).first()
        import pickle
        celllines = pickle.loads([test.cell_line for test in project.tests if test.name == 'CT'][0])
        lcompound = DBSession.query(LCompound).filter_by(id=lid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').first()
        from rdkit.Chem.rdMolDescriptors import CalcMolFormula
        formula = CalcMolFormula(Chem.MolFromSmiles(str(lcompound.mol.structure)))
        scompound = DBSession.query(SCompound).filter_by(id=lcompound.sid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').first()
        pcompound = ()
        result = DBSession.query(ResultsFP).filter_by(lid=lcompound.id).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('ResultsFP.id').first()
        assert lcompound.gid == gid,  "GID error."
        if scompound:
            assert scompound.gid == gid,  "GID error."
            pcompound = DBSession.query(PCompound).filter_by(id=scompound.pid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).first()
        if pcompound:
            assert pcompound.gid == gid,  "GID error."
        if result:
            assert result.gid == gid,  "GID error."
        scompounds = DBSession.query(SCompound).filter_by(gid=gid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        pcompounds = DBSession.query(PCompound).filter(PCompound.gid==gid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        lcompounds = DBSession.query(LCompound).filter_by(gid=gid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        results = DBSession.query(ResultsFP).filter_by(gid=gid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('ResultsFP.id').all()
        return dict(pcompound=pcompound, scompound=scompound, lcompound=lcompound, result=result, pcompounds=pcompounds, scompounds=scompounds, lcompounds=lcompounds, results=results, formula=formula, page='ctoxicity', pname=pname, celllines=celllines)
    
    @expose('molgears.templates.users.results.ctoxicity.showoneresult')
    def showoneresult(self, *args, **kw):
        try:
            id = int(args[0])
            pname = request.environ['PATH_INFO'].split('/')[1]
            result = DBSession.query(CTResults).get(id)
            import pickle as pcl
        except Exception as msg:
            flash(l_(u'The choosen test does not exists.'), 'error')
            redirect(request.headers['Referer'])
        return dict(result=result, pcl=pcl, page='ctoxicity', pname=pname)
        
    @expose()
    def del_result(self, *args, **kw):
        id = args[1]
        lid = args[0]
        lcompound = DBSession.query(LCompound).get(lid)
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        result = DBSession.query(CTResults).get(id)
        assert result.lid == lcompound.id
        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        rhistory = CTHistory()
        rhistory.gid = result.gid
        rhistory.project = pname
        rhistory.user = userid
        rhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rhistory.status = u'Usuń'
        changes = u''
        for k, v in vars(result).items():
            changes += u'%s: %s; ' % (k, v)
        rhistory.changes = changes
        result.history += [rhistory]
        DBSession.add(rhistory)
        lcompound.ctoxicity.remove(result)
        DBSession.delete(result)
        DBSession.flush()
        flash(l_(u'Task completed successfully'))
        redirect('/%s/results/ctoxicity/details/%s/%s' % (pname, lcompound.gid, lcompound.id))
        
    @expose()
    def _lookup(self, cell_line, *remainder):
        """
        expose lookup controler for each cell line in project.tests if test.name == 'CT'][0]
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter_by(name=pname).first()
        import pickle
        celllines = pickle.loads([test.cell_line for test in project.tests if test.name == 'CT'][0])
        if cell_line in celllines:
            class CellLineController(BaseController):
                @expose('molgears.templates.users.results.ctoxicity.clines')
                def index(self, page=1, *args, **kw):
                    """Lookup controler for cell lines"""
                    lcompound = DBSession.query(CTResults).join(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(CTResults.cell_line==cell_line).join(LCompound.purity)
                    dsc = True
                    order = CTResults.id
                    tmpl = u''
                    alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
                    selection = None
                    similarity = None
                    userid = request.identity['repoze.who.userid']
                    user = DBSession.query(User).filter_by(user_name=userid).first()
                    items = user.items_per_page
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
                                if hasattr(CTResults, v):
                                    order = CTResults.__getattribute__(CTResults, v)
                                elif v == u'purity':
                                    order = LPurity.value
                                else:
                                    order = v
                            if str(k) != 'select' and str(k) != 'remove' and str(v) != u'':
                                tmpl += str(k).encode('utf-8') + u'=' + str(v).encode('utf-8') + u'&'
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
                                    if method == 'smililarity':
#                                        from razi.postgresql_rdkit import tanimoto_threshold
#                                        DBSession.execute(tanimoto_threshold.set(threshold))
                                        query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                                        constraint = Compound.morgan.tanimoto_similar(query_bfp)
                                        tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                                        
                                        search = DBSession.query(CTResults, tanimoto_sml).join(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(CTResults.cell_line==cell_line).filter(constraint).order_by(desc(tanimoto_sml)).all()
                                        lcompound = ()
                                        similarity = ()
                                        for row in search:
                                            lcompound += (row[0], )
                                            similarity += (row[1], )
                                        page_url = paginate.PageURL_WebOb(request)
                                        currentPage = paginate.Page(lcompound, page, url=page_url, items_per_page=items)
                                        return dict(currentPage=currentPage,tmpl=tmpl, page='ctoxicity', pname=pname, alltags=alltags, htmlRgb=htmlRgb100, similarity=similarity, celllines=celllines, cell_line=cell_line)
                
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
                            if kw.has_key('text_image') and kw['text_image'] !=u'':
                                if kw['text_image'] == u"show":
                                    lcompound = lcompound.filter(CTResults.photofiles!=None)
                                elif kw['text_image'] == u"hide":
                                    lcompound = lcompound.filter(CTResults.photofiles==None)
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
                                    tagi = [int(id) for id in tags]
                    
                                import sqlalchemy
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
                                            lcompounds += (DBSession.query(CTResults).get(el), )
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
                                    from xhtml2pdf.pisa import CreatePDF, startViewer
                                    from tg.render import render as render_template
                                    import cStringIO
                                    html = render_template({"length":len(lcompounds), "lcompound":lcompounds, "celllines":celllines, "options":options, "size":size}, "genshi", "molgears.templates.users.results.ctoxicity.print3", doctype=None)
                                    dest = './molgears/files/pdf/' + filename
                                    result = file(dest, "wb")
                                    pdf = CreatePDF(cStringIO.StringIO(html.encode("UTF-8")), result, encoding="utf-8")
                                    result.close()
                                    import paste.fileapp
                                    f = paste.fileapp.FileApp('./molgears/files/pdf/'+ filename)
                                    from tg import use_wsgi_app
                                    return use_wsgi_app(f)
                                elif kw['file_type'] == 'xls':
                                    filename = userid + '_ctox.xls'
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
                                    if 'create_date' in options:
                                        sheet.write(0,j,u'Date')
                                        j+=1
                                    if 'tags' in options:
                                        sheet.write(0,j,u'Tags')
                                        j+=1
                                    if 'notes' in options:
                                        sheet.write(0,j,u'Notes')
                                        j+=1
                                    if 'ic50' in options:
                                        sheet.write(0,j,u'IC50')                                        
                                        j+=1
                                    if 'hillslope' in options:
                                        sheet.write(0,j,u'Hillslope')
                                        j+=1
                                    if 'r2' in options:
                                        sheet.write(0,j,u'R^2')
                                        j+=1
                                    if 'test_name' in options:
                                        sheet.write(0,j,u'Test')
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
                                        if 'name' in options:
                                            sheet.write(i,j, row.lcompounds.mol.name)
                                            j+=1
                                        if 'names' in options:
                                            names = u''
                                            for n in row.lcompounds.mol.names:
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
                                            sheet.write(i,j, str(row.lcompounds.mol.structure))
                                            j+=1
                                        if 'inchi' in options:
                                            sheet.write(i,j, str(row.lcompounds.mol.inchi))
                                            j+=1
                                        if 'num_atoms' in options:
                                            sheet.write(i,j,str(row.lcompounds.mol.num_hvy_atoms)+'/'+str(row.lcompounds.mol.num_atoms))
                                            j+=1
                                        if 'mw' in options:
                                            sheet.write(i,j, str(row.lcompounds.mol.mw))
                                            j+=1
                                        if 'hba' in options:
                                            sheet.write(i,j, str(row.lcompounds.mol.hba))
                                            j+=1
                                        if 'hbd' in options:
                                            sheet.write(i,j, str(row.lcompounds.mol.hbd))
                                            j+=1
                                        if 'tpsa' in options:
                                            sheet.write(i,j, str(row.lcompounds.mol.tpsa))
                                            j+=1
                                        if 'logp' in options:
                                            sheet.write(i,j, str(row.lcompounds.mol.logp))
                                            j+=1
                                        if 'create_date' in options:
                                            sheet.write(i,j, str(row.create_date))
                                            j+=1
                                        if 'tags' in options:
                                            tagsy=u''
                                            for tag in row.lcompounds.mol.tags:
                                                tagsy += tag.name + u', '
                                            sheet.write(i,j,tagsy)
                                            j+=1
                                        if 'notes' in options:
                                            sheet.write(i,j, row.notes)
                                            j+=1
                                        if 'ic50' in options:
                                            sheet.write(i,j, row.ic50)
                                            j+=1
                                        if 'hillslope' in options:
                                            sheet.write(i,j, row.hillslope)
                                            j+=1
                                        if 'r2' in options:
                                            sheet.write(i,j, row.r2)
                                            j+=1
                                        if 'test_name' in options:
                                            sheet.write(i,j, row.test.name)
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
                                                line.append(str(row.lcompounds.mol.structure))
                                            if 'name' in options:
                                                line.append(row.lcompounds.mol.name)
                                            if 'nr' in options:
                                                line.append(unicode(lcompounds.index(row)+1))
                                            if 'gid' in options:
                                                line.append(unicode(row.gid))
                                            if 'id' in options:
                                                line.append(unicode(row.id))
                                            if 'names' in options:
                                                names = u''
                                                for n in row.lcompounds.mol.names:
                                                    names += n.name + u', '
                                                line.append(names)
                                            if 'inchi' in options:
                                                line.append(row.lcompounds.mol.inchi)
                                            if 'lso' in options:
                                                line.append(row.lso)
                                            if 'num_atoms' in options:
                                               line.append(unicode(row.lcompounds.mol.num_hvy_atoms)+'/'+unicode(row.lcompounds.mol.num_atoms))
                                            if 'mw' in options:
                                                line.append(unicode(row.lcompounds.mol.mw))
                                            if 'logp' in options:
                                                line.append(unicode(row.lcompounds.mol.logp))
                                            if 'hba' in options:
                                                line.append(unicode(row.lcompounds.mol.hba))
                                            if 'hbd' in options:
                                                line.append(unicode(row.lcompounds.mol.hbd))
                                            if 'tpsa' in options:
                                                line.append(unicode(row.lcompounds.mol.tpsa))
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
                                                for tag in row.lcompounds.mol.tags:
                                                    tagsy += tag.name + ', '
                                                line.append(tagsy)
                                            if 'notes' in options:
                                                line.append(row.notes)
                                            if 'ic50' in options:
                                                line.append(unicode(row.ic50))
                                            if 'hillslope' in options:
                                                line.append(unicode(row.hillslope))
                                            if 'r2' in options:
                                                line.append(unicode(row.r2))
                                            if 'test_name' in options:
                                                line.append(unicode(row.test.name))
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
                                    redirect('/%s/results/edit%s' % (pname, argv))
                                else:
                                    redirect('/%s/results/multiedit/index%s' % (pname, argv))
                            elif kw['akcja'] == u'plot':
                                redirect('/%s/results/ctoxicity/graphs%s' % (pname, argv))
                            elif kw['akcja'] == u'editresult':
                                if len(selection) == 1:
                                    redirect('/%s/results/edit_result%s' % (pname, argv))
                                else:
                                    flash(l_(u'Select only one item'))
                                    redirect('/%s/results/mdm2' % pname)
                            elif kw['akcja'] == u'results':
                                if len(selection) == 1:
                                    redirect('/%s/results/results%s' % (pname, argv))
                                else:
                                    redirect('/%s/results/multiresults/index%s' % (pname, argv))
    

                    page_url = paginate.PageURL_WebOb(request)
                    currentPage = paginate.Page(lcompound, page, url=page_url, items_per_page=items)
                    lcompound = lcompound.all()
                    return dict(lcompound=currentPage.items, currentPage=currentPage,tmpl=tmpl, page='ctoxicity', htmlRgb=htmlRgb100, pname=pname, alltags=alltags, similarity=similarity, celllines=celllines, cell_line=cell_line)
            cell = CellLineController()
        else:
            cell = ErrorController()
        return cell, remainder
      
    @expose('molgears.templates.users.results.ctoxicity.edit_result')
    def edit_result(self, *args, **kw):
        lid = args[0]
        id = args[1]
        lcompound = DBSession.query(LCompound).get(lid)
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter_by(name=pname).first()
        project_ct_test = [test for test in project.tests if test.name == 'CT'][0]
        import pickle
        celllines = pickle.loads(project_ct_test.cell_line)
        tests = DBSession.query(TestCT).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by(TestCT.id).all()
        result = DBSession.query(CTResults).get(id)
        if not result:
            flash(l_(u'Object does not exist or has been deleted'), 'warning')
            redirect('/%s/results/ctoxicity/details/%s/%s' % (pname, lcompound.gid, lcompound.id))
        assert result.lid == lcompound.id, u"Niewłaściwy wynik"
        come_from = request.headers['Referer']
        if kw:
            userid = request.identity['repoze.who.userid']
            changes = u''
            if kw.has_key('come_from'):
                come_from = kw['come_from']
            else:
                come_from = request.headers['Referer']
            if kw.has_key('testname') and kw['testname'] != u'':
                test = DBSession.query(TestCT).get(kw['testname'])
            else:
                flash(l_('Test is required'), 'error')
                redirect(request.headers['Referer'])
            if kw.has_key('cell_line') and kw['cell_line'] != u'':
                if kw['cell_line'] !=result.cell_line:
                    result.cell_line = kw['cell_line']
                    changes += u'; Linia: ' + cline
            else:
                flash(l_(u'Cell line is required'), 'error')
                redirect(come_from)

            rhistory = CTHistory()
            rhistory.gid = lcompound.gid
            rhistory.lid = lcompound.id
            rhistory.project = pname
            rhistory.user = userid
            rhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rhistory.status = u'Edycja'
            if test and test != result.test:
                result.test = test
                changes += u'; TestCT: ' + str(test.name)
            if kw.has_key('ic50') and float(kw['ic50'].replace(',', '.')) != result.ic50:
                result.ic50 = float(kw['ic50'].replace(',', '.'))
                changes += u'; IC50: ' + kw['ic50']
            if kw.has_key('hillslope') and result.hillslope != float(kw['hillslope'].replace(',', '.')):
                result.hillslope = float(kw['hillslope'].replace(',', '.'))
                changes += u'; Hillslope: ' + kw['hillslope']
            if kw.has_key('r2') and result.r2 != float(kw['r2'].replace(',', '.')):
                result.r2 = float(kw['r2'].replace(',', '.'))
                changes += u'; R2: ' + kw['r2']
            if kw.has_key('status') and kw['status'] != u'':
                if kw['status'] == u"True":
                    result.active = True
                    changes += u'; Status: Active'
                elif kw['status'] == u"False":
                    result.active = False
                    changes += u'; Status: Inactive'
                else:
                    flash(l_(u'Status error.'), 'error')
                    redirect(come_from)
            if kw.has_key('notes') and kw['notes'] != result.notes:
                result.notes = kw['notes']
                changes += u';Notes: ' + kw['notes']
            try:
                filename = raw_path_basename(kw['file'].filename)
            except Exception as msg:
                filename = None
                pass
            if filename and userid:
                number = DBSession.query(ResultFiles).count() + 1
                newfilename = str(number) + '_' + userid + '_' + str(lid) + '_' + filename
                newfilename.replace(' ', '_')
                f_path = os.path.join(result_files_dir, newfilename)
                try:
                    f = file(f_path, "w")
                    f.write(kw['file'].value)
                    f.close()
                except Exception as msg:
                    flash(l_(msg), 'error')
                    redirect(request.headers['Referer'])
                rfile = CTFiles()
                rfile.name = filename
                rfile.filename = newfilename
                changes += u'; Plik: ' + filename + u' ( ' + newfilename + u' )'
                result.files = [rfile]
                DBSession.add(rfile)
            elif result.files:
                f_path = os.path.join(result_files_dir, result.files[0].filename)
            else:
                flash(l_(u'File error'), 'error')
                redirect('come_from')
            from molgears.widgets.ct_result import read_one, save_fix_data, write_result
            X, M = read_one(f_path)
            top = []
            data =[]
            for row in M:
                list = []
                top.append(float(row[0].replace(',', '')))
                for el in row[1:]:
                    el =float(el.replace(',', ''))
                    list.append(round(el, 3))
                data.append(list)
            if top and data:
                rhistory.changes =changes
                result.history += [rhistory]
                DBSession.add(rhistory)
                write_result(top, X, data, f_path)
                for line in data:
                    for el in line:
                        line[line.index(el)] = 100.0*el/(sum(top)/len(top))
                graphs_path = os.path.join(public_dirname, 'img/graphsct/%s_%s.png' % (result.lid, result.id))
#                thumb_graphs_path = os.path.join(public_dirname, 'img/graphsct/%s_%s.png' % (result.lid, result.id))
#                abc, acb, cba = save_fix_data(X, data, thumb_graphs_path, dpi=50)
                ic50, hillslope, r2 = save_fix_data(X, data, graphs_path)
                if ic50<1000:
                    result.ic50 = ic50
                else:
                    result.ic50 = 1000
                result.hillslope = hillslope
                result.r2 =r2
            DBSession.add(rhistory)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
            
        return dict(lcompound=lcompound, tests=tests, result=result, come_from=come_from, page='ctoxicity', pname=pname, celllines=celllines)
        
    @expose()
    def graphs(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        if args:
            userid = request.identity['repoze.who.userid']
            graphs_path = os.path.join(files_dir, '%s.png' % userid)
            CONCS = []
            DATAS = []
            NAMES = ()
            for arg in args:
                result = DBSession.query(CTResults).filter_by(id=int(arg)).first()
                lcompound = DBSession.query(LCompound).get(result.lid)
                if lcompound:
                    if lcompound.entry and lcompound.box:
                        NAMES += (str(lcompound.box)+str(lcompound.entry) + '_' + result.cell_line + ' | ' + str(result.ic50), )
                    else:
                        NAMES += (str(lcompound.mol.name) + '_' + result.cell_line + ' | ' + str(result.ic50), )
                if not result:
                    flash(l_(u'Result error'), 'error')
                    redirect(request.headers['Referer'])
                else:
                    if result.files:
                        f_path = os.path.join(result_files_dir, result.files[0].filename)
                    else:
                        flash(l_(u'File error'), 'error')
                        redirect('come_from')
                    from molgears.widgets.ct_result import read_one
                    X, M = read_one(f_path)
                    CONCS.append(X)
                    top = []
                    data =[]
                    for row in M:
                        list = []
                        top.append(float(row[0].replace(',', '')))
                        for el in row[1:]:
                            el =float(el.replace(',', ''))
                            list.append(round(el, 3))
                        data.append(list)
                    if top and data:
                        for line in data:
                            for el in line:
                                line[line.index(el)] = 100.0*el/(sum(top)/len(top))
                    DATAS.append(data)
            from molgears.widgets.ct_result import multigraph
            multigraph(CONCS, DATAS, NAMES, graphs_path)
            import paste.fileapp
            f = paste.fileapp.FileApp(graphs_path)
            from tg import use_wsgi_app
            return use_wsgi_app(f)
        else:
            flash(l_(u'args error'), 'error')
            redirect('/%s/results/ctoxicity' %pname)
            
    @expose()
    def plot(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        if args:
            userid = request.identity['repoze.who.userid']
            graphs_path = os.path.join(files_dir, '%s.png' % userid)
            CONCS = []
            DATAS = []
            NAMES = ()
            for arg in args:
                lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.id==int(arg)).first()
                if lcompound.ctoxicity:
                    resss = []
                    for result in lcompound.ctoxicity:
                        if lcompound:
                            if lcompound.entry and lcompound.box:
                                NAMES += (str(lcompound.box)+str(lcompound.entry) + '_' + result.cell_line + ' | ' + str(result.ic50), )
                            else:
                                NAMES += (str(lcompound.mol.name) + '_' + result.cell_line + ' | ' + str(result.ic50), )
                        if not result:
                            flash(l_(u'Result error'), 'error')
                            redirect(request.headers['Referer'])
                        else:
                            if result.files:
                                f_path = os.path.join(result_files_dir, result.files[0].filename)
                            else:
                                flash(l_(u'File error'), 'error')
                                redirect('come_from')
                            from molgears.widgets.ct_result import read_one
                            X, M = read_one(f_path)
                            CONCS.append(X)
                            top = []
                            data =[]
                            for row in M:
                                list = []
                                top.append(float(row[0].replace(',', '')))
                                for el in row[1:]:
                                    el =float(el.replace(',', ''))
                                    list.append(round(el, 3))
                                data.append(list)
                            if top and data:
                                for line in data:
                                    for el in line:
                                        line[line.index(el)] = 100.0*el/(sum(top)/len(top))
                            DATAS.append(data)
            from molgears.widgets.ct_result import multigraph
            multigraph(CONCS, DATAS, NAMES, graphs_path)
            import paste.fileapp
            f = paste.fileapp.FileApp(graphs_path)
            from tg import use_wsgi_app
            return use_wsgi_app(f)
        else:
            flash(l_(u'args error'), 'error')
            redirect('/%s/results/ctoxicity' %pname)
            
    @expose('molgears.templates.users.results.ctoxicity.history')
    def history(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        history = DBSession.query(CTHistory).filter_by(project=pname)
        order='CTHistory.id'
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
                        order = CTHistory.results_id
                    elif v == 'user':
                        order = CTHistory.user
                    elif v == 'date':
                        order = CTHistory.date
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
                    history = history.filter(CTHistory.user.like(kw['text_user'].replace('*', '%')))
                if kw.has_key('text_status') and kw['text_status'] !=u'':
                    history = history.filter(CTHistory.status.like(kw['text_status'].replace('*', '%')))
                if kw.has_key('text_changes') and kw['text_changes'] !=u'':
                    history = history.filter(CTHistory.changes.like(kw['text_changes'].replace('*', '%')))
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    history = history.filter(CTHistory.date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            history = history.filter(CTHistory.date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        history = history.filter(CTHistory.date < date_to)
        if dsc:
            history = history.order_by(desc(order).nullslast())
        else:
            history = history.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(history, page, url=page_url, items_per_page=items)
        return dict(history=currentPage.items, currentPage=currentPage, tmpl=tmpl, one_day=one_day, now=now, page='ctoxicity', pname=pname)
        
    @expose()
    def deletefromlist(self, ulist_id, *args):
        """
            Delete compound from User List.
        """
        ulist = DBSession.query(UserLists).get(ulist_id)
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        ulists = [l for l in user.lists if l.table == 'CTResults']
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
        
    @expose()
    def graphpad_results(self, *args, **kw):
        """
        Controler for downloading file in graphpad format (csv extension) for all results from selected compounds.
         - first column is contcentration
         - next 3 columns are results for for cell line ctoxicity
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except:
            come_from = '/%s/results/' %pname
        if args:
            import pickle
            filename = userid + '%s_results_ct.csv' % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filepath = os.path.join('./molgears/files/download/', filename)
            DX = {}
            for arg in args:
                try:
                    lcompound = DBSession.query(LCompound).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).filter(LCompound.id==int(arg)).first()
                except:
                    flash(l_(u'ARGS error'), 'error')
                    redirect(come_from)
                if lcompound and lcompound.ctoxicity != None:
                    for result in sorted(lcompound.ctoxicity, key=lambda x: x.cell_line):
                        if result.files and result.files[0]:
                            name = lcompound.mol.name + ' ' + result.cell_line
                            f_path = os.path.join(result_files_dir, result.files[0].filename)
                            from molgears.widgets.ct_result import read_one, save_fix_data, write_result
                            X, M = read_one(f_path)
                            top = []
                            data =[]
                            for row in M:
                                list = []
                                top.append(float(row[0].replace(',', '')))
                                for el in row[1:]:
                                    el =float(el.replace(',', ''))
                                    list.append(round(el, 3))
                                data.append(list)
                            for line in data:
                                for el in line:
                                    line[line.index(el)] = round(100.0*el/(sum(top)/len(top)), 2)
                            
                            key = pickle.dumps(X)
                            DX.setdefault(key, []).append([name, data])
#                            for conc in X:
#                                row = [conc, data[0][X.index(conc)], data[1][X.index(conc)], data[2][X.index(conc)]]
                        else:
                            flash(l_(u'File error'), 'error')
                            redirect(come_from)
            import csv
            with open(filepath, 'wb') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                suma = 0
                pre = 0
                for k, v in DX.iteritems():
                    suma+=len(v)
                suma = 3*suma
                namerow = ['Concentration', 'Concentration']
                rows = []
                for k, v in DX.iteritems():
                    X = pickle.loads(k)
                    
                    for conc in X:
                        row = []
                        row.append(conc)
                        row.append(conc)
                        if pre >0:
                            for j in range(pre):
                                row.append('')
                        i = 0
                        for name, data in v:
                            if X.index(conc) == 0:
                                for ne in 3*[name]:
                                    namerow.append(ne)
                            row.append(data[0][X.index(conc)])
                            row.append(data[1][X.index(conc)])
                            row.append(data[2][X.index(conc)])
                            i+=3
                        rows.append(row)
                    pre+=i
#                        
                spamwriter.writerow(namerow)
                for line in rows:
                    spamwriter.writerow(line)
            import paste.fileapp
            f = paste.fileapp.FileApp(filepath)
            from tg import use_wsgi_app
            return use_wsgi_app(f)
        else:
            flash(l_(u'ARGS error'), 'error')
            redirect(come_from)
