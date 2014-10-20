# -*- coding: utf-8 -*-
"""
Molecules Controller is submodule for *RootController*
"""
import tg
from tg import expose, flash, redirect, url, lurl, request
from tg.i18n import ugettext as _, lazy_ugettext as l_
from molgears import model
from molgears.model import DBSession, PCompound, PHistory, PStatus, Tags, SCompound, SFiles, LCompound, LPurity, LHistory
from molgears.model import Compound, Names, History, User, Group, Projects, PAINS1, PAINS2, PAINS3, CompoundsFiles, NameGroups
from molgears.model.auth import UserLists
from molgears.lib.base import BaseController
import transaction, os
from pkg_resources import resource_filename
from sqlalchemy import desc
from molgears.widgets.format import raw_path_basename
from molgears.widgets.structure import create_image, addsmi, checksmi
from datetime import datetime
from webhelpers import paginate
from tg.predicates import has_permission
from rdkit import Chem
from tg import cache
__all__ = ['MoleculesController']

public_dirname = os.path.join(os.path.abspath(resource_filename('molgears', 'public')))
img_dir = os.path.join(public_dirname, 'img')
files_dir = os.path.join(public_dirname, 'files')
models_dir = os.path.join(files_dir, 'models')

class MoleculesController(BaseController):
    """
    Class for managing molecules controler.
    """

    @expose('molgears.templates.users.molecules.get_all')
    def index(self, page=1, *args, **kw):
        """
        Index controller for molecules.
        """
        pname = request.environ['PATH_INFO'].split('/')[1] # get project name
        project = DBSession.query(Projects).filter(Projects.name==pname).first() # get project by name
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all()] # get a list of all tags
        compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname))
        dsc = True # default sorting by dsc
        tmpl = ''
        selection = None
        similarity = None
        ulist = None
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        threshold = float(user.threshold)/100.0
        items = user.items_per_page
        ulists = set([l for l in user.lists if l.table == 'Compounds'] + [l for l in user.tg_user_lists if l.table == 'Compounds'])
        page_url = paginate.PageURL_WebOb(request)
        order = "gid" #default order value
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        # check if search clicked
        try:
            if kw['search'] != u'':
                search_clicked = kw['search']
            else:
                search_clicked = None
        except Exception:
            search_clicked = None
        if kw:
            # checki lists
            if kw.has_key('mylist'):
                try:
                    ulist_id = int(kw['mylist'])
                    ulist = DBSession.query(UserLists).get(ulist_id)
                except Exception:
                    flash(l_(u'List error'), 'error')
                    redirect(come_from)
                if (ulist in user.lists) or (user in ulist.permitusers):
                    if ulist.elements:
                        import pickle
                        elements = [int(el) for el in pickle.loads(ulist.elements)]
                        if ulist.table == 'Compounds':
                            compound=DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter(Compound.gid.in_(elements))
                        else:
                            flash(l_(u'Table error'), 'error')
                            redirect(come_from)
                else:
                    flash(l_(u'Permission denied'), 'error')
                    redirect(come_from)
            delkw = []  #delete dubled kw
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
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
                elif str(v) == u'':
                    delkw.append(k)
            for k in delkw:
                del kw[k]
                
            if search_clicked:
                try:
                    smiles = str(kw['smiles'])
                except Exception:
                    smiles = None
                    pass
                try:
                    method = str(kw['method'])
                except Exception:
                    method = None
                    pass
                if smiles:
                    if checksmi(smiles):
                        from razi.functions import functions
                        from razi.expression import TxtMoleculeElement
                        if method == 'smililarity':
                            from razi.postgresql_rdkit import tanimoto_threshold
                            DBSession.execute(tanimoto_threshold.set(threshold))
                            query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                            constraint = Compound.morgan.tanimoto_similar(query_bfp)
                            tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
                            limit = user.limit_sim
                            search = DBSession.query(Compound, tanimoto_sml).filter(constraint).filter(Compound.project.any(Projects.name==pname)).order_by(desc(tanimoto_sml)).limit(limit).all()
                            compound = ()
                            similarity = ()
                            for row in search:
                                compound += (row[0], )
                                similarity += (row[1], )
                            currentPage = paginate.Page(compound, page, url=page_url, items_per_page=items)
                            return dict(currentPage=currentPage, tmpl=tmpl, page='molecules', pname=pname, alltags=alltags, ulists=ulists, ulist=ulist, similarity=similarity)

                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            compound = DBSession.query(Compound).filter(constraint).filter(Compound.project.any(Projects.name==pname))
                        elif method == 'identity':
                            compound = DBSession.query(Compound).filter(Compound.structure.equals(smiles)).filter(Compound.project.any(Projects.name==pname))
                    else:
                        flash(l_(u'Smiles error'), 'error')
                        redirect('/%s/molecules' % pname)
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_GID'])
                        compound = compound.filter_by(gid=gid)
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(come_from)
                if kw.has_key('text_name') and kw['text_name'] !=u'':
                    compound = compound.filter(Compound.names.any(Names.name.like(kw['text_name'].strip().replace('*', '%'))))
                if kw.has_key('text_creator') and kw['text_creator'] !=u'':
                    compound = compound.filter(Compound.creator.like(kw['text_creator'].replace('*', '%')))
                if kw.has_key('text_notes') and kw['text_notes'] !=u'':
                    compound = compound.filter(Compound.notes.like(kw['text_notes'].replace('*', '%')))
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    compound = compound.filter(Compound.create_date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            compound = compound.filter(Compound.create_date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(come_from)
                    else:
                        compound = compound.filter(Compound.create_date < date_to)
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
                    compound = compound.filter(Compound.tags.any(Tags.id.in_(tagi)))
        if dsc:
            compound = compound.order_by(desc(order).nullslast())
        else:
            compound = compound.order_by((order))

        if search_clicked and kw['search'] == "Download":
            if kw['file_type'] and kw['file_type'] != u'' and kw['sell_type'] and kw['sell_type'] != u'':
                if kw['sell_type'] == u'all':
                    compounds = compound.all()
                elif kw['sell_type'] == u'selected':
                    if selection:
                        compounds = ()
                        for el in selection:
                            compounds += (DBSession.query(Compound).get(el), )
                    else:
                        flash(l_(u'Lack of selected structures for download'), 'error')
                        redirect(come_from)
                elif kw['sell_type'] == u'range':
                    compounds = compound.all()
                    if kw.has_key('select_from') and kw['select_from'] != u'':
                        try:
                            select_from = int(kw['select_from']) -1 
                            if select_from<1 or select_from>len(compounds):
                                select_from = 0
                        except Exception:
                            select_from = 0
                    else:
                        select_from = 0
                    if kw.has_key('select_to') and kw['select_to'] != u'':
                        try:
                            select_to = int(kw['select_to'])
                            if select_to<2 or select_to>len(compounds):
                                select_to = len(compounds)
                        except Exception:
                            select_to = len(compounds)
                    else:
                        select_to = len(compounds)
                    compounds_new = ()
                    for el in range(select_from, select_to):
                        compounds_new += (compounds[el], )
                    compounds = compounds_new
                else:
                    flash(l_(u'Lack of items to download'), 'error')
                    redirect(come_from)
                
                try:
                    if isinstance(kw['options'], basestring):
                        options = [kw['options']]
                    else:
                        options = kw['options']
                except Exception:
                    flash(l_('Choose download options'), 'error')
                    redirect(come_from)
                if 'getsize' in kw:
                    size = int(kw['getsize']), int(kw['getsize'])
                else:
                    size = 100, 100
                if kw['file_type'] == 'pdf':
                    filename = userid + '_molecules.pdf'
                    from xhtml2pdf.pisa import CreatePDF, startViewer
                    from tg.render import render as render_template
                    import cStringIO
                    html = render_template({"length":len(compounds), "compound":compounds, "options":options, "size":size}, "genshi", "molgears.templates.users.molecules.print2", doctype=None)
                    dest = './molgears/files/pdf/' + filename
                    result = file(dest, "wb")
                    pdf = CreatePDF(cStringIO.StringIO(html.encode("UTF-8")), result, encoding="utf-8")
                    result.close()
                    import paste.fileapp
                    f = paste.fileapp.FileApp('./molgears/files/pdf/'+ filename)
                    from tg import use_wsgi_app
                    return use_wsgi_app(f)
                elif kw['file_type'] == 'xls':
                    filename = userid + '_molecules.xls'
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
                    if 'creator' in options:
                        sheet.write(0,j,'Creator')
                        j+=1
                    if 'tags' in options:
                        sheet.write(0,j,'Tags')
                        j+=1
                    if 'notes' in options:
                        sheet.write(0,j,'Notes')
                        j+=1
                    i = 1
                    for row in compounds:
                        j=0
                        if 'nr' in options:
                            sheet.write(i,j, str(i))
                            j+=1
                        if 'gid' in options:
                            sheet.write(i,j, row.gid)
                            j+=1
                        if 'name' in options:
                            sheet.write(i,j, row.name)
                            j+=1
                        if 'names' in options:
                            names = u''
                            for n in row.names:
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
                            sheet.write(i,j, str(row.structure))
                            j+=1
                        if 'inchi' in options:
                            sheet.write(i,j, str(row.inchi))
                            j+=1
                        if 'num_atoms' in options:
                            sheet.write(i,j,str(row.num_hvy_atoms)+'/'+str(row.num_atoms))
                            j+=1
                        if 'mw' in options:
                            sheet.write(i,j, str(row.mw))
                            j+=1
                        if 'logp' in options:
                            sheet.write(i,j, str(row.logp))
                            j+=1
                        if 'hba' in options:
                            sheet.write(i,j, str(row.hba))
                            j+=1
                        if 'hbd' in options:
                            sheet.write(i,j, str(row.hbd))
                            j+=1
                        if 'tpsa' in options:
                            sheet.write(i,j, str(row.tpsa))
                            j+=1
                        if 'create_date' in options:
                            sheet.write(i,j, row.create_date)
                            j+=1
                        if 'creator' in options:
                            sheet.write(i,j, row.creator)
                            j+=1
                        if 'tags' in options:
                            tagsy=u''
                            for tag in row.tags:
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
                elif kw['file_type'] == 'sdf':
                    filepath = './molgears/files/download/out.sdf'
                    ww = Chem.SDWriter(filepath)
                    from rdkit.Chem import AllChem
                    for row in compounds:
                        m2 = Chem.MolFromSmiles(str(row.structure))
                        AllChem.Compute2DCoords(m2)
                        AllChem.EmbedMolecule(m2)
                        AllChem.UFFOptimizeMolecule(m2)
                        if 'smiles' in options:
                            m2.SetProp("smiles", str(row.structure))
                        if 'name' in options:
                            m2.SetProp("_Name", str(row.name.encode('ascii', 'ignore')))
                            m2.SetProp("Primary_Name", str(row.name.encode('ascii', 'ignore')))
                        if 'nr' in options:
                            m2.SetProp("Nr", str(compounds.index(row)+1))
                        if 'gid' in options:
                            m2.SetProp("GID", str(row.gid))
                        if 'names' in options:
                            names = u''
                            for n in row.names:
                                names += n.name + ', '
                            m2.SetProp("names", str(names.encode('ascii', 'ignore')))
                        if 'inchi' in options:
                            m2.SetProp("InChi", str(row.inchi))
                        if 'num_atoms' in options:
                           m2.SetProp("atoms", str(row.num_hvy_atoms)+'/'+str(row.num_atoms))
                        if 'mw' in options:
                            m2.SetProp("mw", str(row.mw))
                        if 'logp' in options:
                            m2.SetProp("logp", str(row.logp))
                        if 'hba' in options:
                            m2.SetProp("hba", str(row.hba))
                        if 'hbd' in options:
                            m2.SetProp("hbd", str(row.hbd))
                        if 'tpsa' in options:
                            m2.SetProp("tpsa", str(row.tpsa))
                        if 'create_date' in options:
                            m2.SetProp("create_date", str(row.create_date))
                        if 'creator' in options:
                            m2.SetProp("dodane_przez", str(row.creator))
                        if 'tags' in options:
                            tagsy=u''
                            for tag in row.tags:
                                tagsy += tag.name + u', '
                            m2.SetProp("tagi", str(tagsy.encode('ascii', 'ignore')))
                        if 'notes' in options:
                            if row.notes:
                                m2.SetProp("uwagi", str(row.notes.encode('ascii', 'ignore')))
                            else:
                                m2.SetProp("uwagi", " ")
                        ww.write(m2)
                    ww.close()
                    import paste.fileapp
                    f = paste.fileapp.FileApp(filepath)
                    from tg import use_wsgi_app
                    return use_wsgi_app(f)
                elif kw['file_type'] == 'csv' or 'txt':
                    filename = userid + '_molecules.' + kw['file_type']
                    filepath = os.path.join('./molgears/files/download/', filename)
                    import csv
                    if kw['file_type'] == u'csv':
                        delimiter = ';'
                    else:
                        delimiter = ' '
                    with open(filepath, 'wb') as csvfile:

                        spamwriter = csv.writer(csvfile, delimiter=delimiter,
                                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
                        for row in compounds:
                            line =[]
                            if 'smiles' in options:
                                line.append(str(row.structure).strip())
                            if 'name' in options:
                                line.append(row.name.strip())
                            if 'nr' in options:
                                line.append(compounds.index(row)+1)
                            if 'gid' in options:
                                line.append(row.gid)
                            if 'names' in options:
                                names = u''
                                for n in row.names:
                                    names += n.name + u', '
                                line.append(names)
                            if 'inchi' in options:
                                line.append(str(row.inchi))
                            if 'num_atoms' in options:
                               line.append(str(row.num_hvy_atoms)+'/'+str(row.num_atoms))
                            if 'mw' in options:
                                line.append(str(row.mw))
                            if 'logp' in options:
                                line.append(str(row.logp))
                            if 'hba' in options:
                                line.append(str(row.hba))
                            if 'hbd' in options:
                                line.append(str(row.hbd))
                            if 'tpsa' in options:
                                line.append(str(row.tpsa))
                            if 'create_date' in options:
                                line.append(row.create_date)
                            if 'creator' in options:
                                line.append(row.creator)
                            if 'tags' in options:
                                tagsy=u''
                                for tag in row.tags:
                                    tagsy += tag.name + u', '
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
                    redirect('/%s/molecules/edit%s' % (pname, argv))
                else:
                    redirect('/%s/molecules/multiedit/index%s' % (pname, argv))
            elif kw['akcja'] == u'accept':
                if len(selection) == 1:
                    redirect('/%s/molecules/accept%s' % (pname, argv))
                else:
                    redirect('/%s/molecules/multiaccept/index%s' % (pname, argv))
            elif kw['akcja'] == u'library':
                if len(selection) == 1:
                    redirect('/%s/molecules/library%s' % (pname, argv))
                else:
                    redirect('/%s/molecules/multilibrary/index%s' % (pname, argv))
            elif kw['akcja'] == u'delete':
                redirect('/%s/molecules/remove%s' % (pname, argv))
            else:
                flash(l_(u'Action error'), 'error')
                redirect(come_from)
        
        currentPage = paginate.Page(compound, page, url=page_url, items_per_page=items)
        return dict(currentPage=currentPage, tmpl=tmpl, page='molecules', pname=pname, alltags=alltags, ulists = ulists, similarity=similarity, ulist=ulist)

    @expose('molgears.templates.users.molecules.new')
    def new(self, *args, **kw):
        """Display a page to show a new record."""
        pname = request.environ['PATH_INFO'].split('/')[1]
        alltags =[tag for tag in DBSession.query( Tags ).order_by('name').all() ]
        try:
            gid = args[0]
        except Exception:
            gid = None
            pass
        ngroups = DBSession.query(NameGroups).order_by(NameGroups.id).all()
        return dict(alltags=alltags, ngroups=ngroups, page='molecules', gid=gid, pname=pname)

    @expose()
    def post(self, **kw):
        """Save a new record."""
        pname = request.environ['PATH_INFO'].split('/')[1]
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if kw:
            try:
                userid = request.identity['repoze.who.userid']
                name = kw['name']
                structure = kw['smiles']
                notes = kw['notes']
#                status = DBSession.query( Status ).get(1)
                if isinstance(kw['text_tags'], basestring):
                    tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                else:
                    tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
            except Exception as msg:
                flash(l_(u'Tags error: %s.' % msg), 'error')
                redirect(come_from)
            if (name and structure):
                try:
                    smiles = str(structure)
                except Exception:
                    smiles = structure.encode("ascii", "ignore")
                changes = u'Nazwa: ' + name + u'; SMILES: ' + smiles + u'; Tagi: '
                if kw.has_key('isomer') and kw['isomer'] ==u'yes':
                    check = False
                    isomer = True
                else:
                    try:
                        check = DBSession.query(Compound).filter(Compound.structure.equals(smiles)).first()
                    except Exception as msg:
                        flash(l_(u'SMILES error'), 'error')
                        redirect(come_from)
                    isomer = False
                if check:
                    flash(l_(u'The Compound exist in DB for project %s on GID number: %s' % (pname, check.gid)), 'warning')
                    redirect(come_from)
                if u'ngroups' in kw and kw['ngroups'] != u'':
                    ngroup = DBSession.query(NameGroups).get(kw['ngroups'])
                    ngroup.next += 1
                for tag in tagi:
                    changes += str(tag.name)
                compound = Compound(name, structure, creator=userid)
                if isomer:
                    compound.isomer = True
                    changes += u'; IZOMER! '
                else:
                    compound.isomer = False
                compound.tags = tagi
                compound.seq = 1
                compound.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                project = DBSession.query(Projects).filter(Projects.name==pname).first()
                compound.project = [project]
                try:
                    newname= Names()
                    newname.name = name
                    DBSession.add(newname)
                    compound.names += [newname]
                except Exception as msg:
                    flash(l_(u'Name error'), 'warning')
                    redirect(come_from)
                from rdkit import Chem
                from rdkit.Chem.inchi import MolToInchi
                from silicos_it.descriptors import qed
                mol = Chem.MolFromSmiles(smiles)
                compound.inchi = MolToInchi(mol)                
                compound.qed = round(qed.default(mol), 2)
                history = History()
                history.user = userid
                history.status = u'create new'
                history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                project = DBSession.query(Projects).filter(Projects.name==pname).first()
                history.project = pname
#                compound.status = status
#                compound.status_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if notes:
                    compound.notes = notes
                    changes += u'; Notes: ' + notes
                history.changes = changes
                compound.history += [history]
                compound.pnum = 0
                compound.snum = 0
                compound.lnum = 0
                if not Chem.MolFromSmiles(smiles):
                    flash(l_(u'SMILES error: %s' % smiles), 'error')
                    redirect(come_from)
                else:
                    if kw['pains'] == 'yes':
                        pains1 = DBSession.query(PAINS1).all()
                        pains2 = DBSession.query(PAINS2).all()
                        pains3 = DBSession.query(PAINS3).all()
                        m = Chem.MolFromSmiles(smiles)
                        mol = Chem.AddHs(m)
                        for p1 in pains1:
                            patt = Chem.MolFromSmarts(str(p1.structure))
                            if patt:
                                if mol.HasSubstructMatch(patt):
                                    compound.pains1 = p1
                            else:
                                flash(l_(u'Pattern error'), 'error')
                                redirect(come_from)
                        for p2 in pains2:
                            patt = Chem.MolFromSmarts(str(p2.structure))
                            if patt:
                                if mol.HasSubstructMatch(patt):
                                    compound.pains2 = p2
                            else:
                                flash(l_(u'Pattern error'), 'error')
                                redirect(come_from)
                        for p3 in pains3:
                            patt = Chem.MolFromSmarts(str(p3.structure))
                            if patt:
                                if mol.HasSubstructMatch(patt):
                                    compound.pains3 = p3
                            else:
                                flash(l_(u'Pattern error'), 'error')
                                redirect(come_from)
                    DBSession.add(history)
                    DBSession.add(compound)
                    DBSession.flush()
#                    #transaction.commit()

                for q in DBSession.query(Compound).order_by('gid')[-1:]:
                    create_image(q.gid, q.structure, img_dir)

                flash(l_(u'Task completed successfully'))
                redirect(come_from)

            else:
                flash(l_(u'Name and structure are required'), 'error')
                redirect(come_from)
        redirect(come_from)

    @expose('molgears.templates.users.molecules.edit')
    def edit(self, id):
        """Display a page to edit a record."""
        pname = request.environ['PATH_INFO'].split('/')[1]
        gid = int(id)
        compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=gid).first()
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if compound:
            alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
            try:
                tags = [tag for tag in compound.tags]
            except Exception as msg:
                tags = [compound.tags]
                pass
            ngroups = DBSession.query(NameGroups).order_by(NameGroups.id).all()
            return dict(compound=compound, ngroups=ngroups, alltags=alltags, tags=tags, come_from=come_from, page='molecules', pname=pname)
        else:
            flash(l_(u'Access error'), 'error')
            redirect(come_from)

    @expose()
    def put(self, *args, **kw):
        """Save a edited record."""
        pname = request.environ['PATH_INFO'].split('/')[1]
        from razi.functions import functions
        from razi.expression import TxtMoleculeElement
        from rdkit import Chem
        gid = args[0]
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if kw:
            if kw.has_key('come_from'):
                come_from = kw['come_from']
        try:
            if isinstance(kw['text_tags'], basestring):
                tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
            else:
                tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
        except Exception as msg:
            flash(l_(u'Tags error: %s' %msg))
            redirect(come_from)
        if kw.has_key('smiles') and Chem.MolFromSmiles(str(kw['smiles'])):
            compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=gid).first()
            if compound:
#            compound.name = kw['name']
                smiles = str(kw['smiles'])
                if compound.structure != kw['smiles']:
                    if kw.has_key('isomer') and kw['isomer'] ==u'yes':
                        check = False
                        isomer = True
                    else:
                        check = DBSession.query(Compound).filter(Compound.structure.equals(smiles)).first()
                        isomer = False
                    if check and check.gid != compound.gid:
                        flash(l_(u'The Compound exist in DB for project %s on GID number: %s' % (pname, check.gid)), 'warning')
                        redirect(come_from)
                    changes = u''
                    if isomer:
                        if compound.isomer != isomer:
                            compound.isomer = True
                            changes += u'; ISOMER! '
                    else:
                        compound.isomer = False
                if kw.has_key('new_compound'):
                    try:
                        name = kw['mainname']
                        structure = kw['smiles']
                        notes = kw['notes']
                        if isinstance(kw['text_tags'], basestring):
                            tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                        else:
                            tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
                    except Exception as msg:
                        flash(l_(u'Tags error: %s.' % msg), 'error')
                        redirect(come_from)
                    if (name and structure):
                        smiles = str(structure)
                        if kw.has_key('isomer') and kw['isomer'] ==u'yes':
                            check = False
                            isomer = True
                        else:
                            check = DBSession.query(Compound).filter(Compound.structure.equals(smiles)).first()
                            isomer = False
                        if check:
                            flash(l_(u'The Compound exist in DB for project %s on GID number: %s' % (pname, check.gid)), 'warning')
                            redirect(come_from)
                        changes = u'Nazwa: ' + name + u'; SMILES: ' + smiles + u'; Tagi: '
                        for tag in tagi:
                            changes += str(tag.name)
                        compound = Compound(name, structure, creator=userid)
                        if isomer:
                            compound.isomer = True
                            changes += u'; ISOMER! '
                        else:
                            compound.isomer = False
                        compound.tags = tagi
                        compound.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        project = DBSession.query(Projects).filter(Projects.name==pname).first()
                        compound.project = [project]
                        try:
                            newname= Names()
                            newname.name = name
                            DBSession.add(newname)
                            compound.names += [newname]
                        except Exception as msg:
                            flash(l_(u'Name error'), 'warning')
                            redirect(come_from)
                        from rdkit.Chem.inchi import MolToInchi
                        mol = Chem.MolFromSmiles(smiles)
                        compound.inchi = MolToInchi(mol)
                        from silicos_it.descriptors import qed
                        compound.qed = round(qed.default(mol), 2)
                        history = History()
                        history.user = userid
                        history.status = u'create new'
                        history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        project = DBSession.query(Projects).filter(Projects.name==pname).first()
                        history.project = pname
        #                compound.status = status
        #                compound.status_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if notes:
                            compound.notes = notes
                            changes += u'; Notes: ' + notes
                        history.changes = changes
                        compound.history += [history]
                        compound.pnum = 0
                        compound.snum = 0
                        compound.lnum = 0
                        if not Chem.MolFromSmiles(smiles):
                            flash(l_(u'SMILES error: %s' % smiles), 'error')
                            redirect(come_from)
                        else:
                            DBSession.add(history)
                            DBSession.add(compound)
                            DBSession.flush()
#                            #transaction.commit()

                        for q in DBSession.query( Compound ).order_by('gid')[-1:]:
                            create_image(q.gid, q.structure, img_dir)

                        flash(l_(u'Task completed successfully'))
                        redirect(come_from)
                    else:
                        flash(l_(u'Name and structure are required'), 'error')
                        redirect(come_from)
                allnames = [n.name for n in compound.names]
                changes = u'';
                if kw['mainname'] != compound.name:
                    mainname = DBSession.query(Names).filter(Names.name==compound.name).first()
                    
                    mainname.name = kw['mainname']
                    compound.name = kw['mainname']
                    if mainname not in compound.names:
                        compound.names.append(mainname)
                    changes += u';main name: ' + kw['mainname']
                if kw['name'] not in allnames and kw['name'] != u'':
                    newname = Names()
                    newname.name = kw['name']
                    DBSession.add(newname)
                    compound.names += [newname]
                    changes += u' Name: ' + kw['name'] + u';'
                    if kw.has_key('newmain') and kw['newmain'] != u'':
                        compound.name = kw['name']
                        changes += u'; Nazwa główna: ' + kw['name']
                if u'ngroups' in kw and kw['ngroups'] != u'':
                    ngroup = DBSession.query(NameGroups).get(kw['ngroups'])
                    ngroup.next += 1
                if u'ngroupsmain' in kw and kw['ngroupsmain'] != u'':
                    ngroup_main = DBSession.query(NameGroups).get(kw['ngroupsmain'])
                    ngroup_main.next += 1
                if kw.has_key('newfile'):
                    try:
                        newfile = raw_path_basename(kw['newfile'].filename)
                    except Exception:
                        newfile = None
                    pass
                    if newfile:
                        number = DBSession.query(CompoundsFiles).count() + 1
                        new_file_name = str(number) + '_' + userid + '_' + str(gid) + '_' + newfile
                        new_file_name.replace(' ', '_')
                        f_path = os.path.join(models_dir, new_file_name)
                        try:
                            f = file(f_path, "w")
                            f.write(kw['newfile'].value)
                            f.close()
                        except Exception as msg:
                            flash(l_(msg), 'error')
                            redirect(come_from)
                        if not new_file_name[:-2]=='gz':
                            new_file_name += '.gz'
                            fout_path = os.path.join(models_dir, new_file_name)
                            import gzip
                            f_in = open(f_path, 'rb')
                            f_out = gzip.open(fout_path, 'wb')
                            f_out.writelines(f_in)
                            f_out.close()
                            f_in.close()
                            os.remove(f_path)
                        file1 = CompoundsFiles()
                        file1.name = newfile
                        file1.filename = new_file_name
                        changes += '; Plik modelowanie: ' + newfile + ' (' + new_file_name + ')'
                        compound.files += [file1]
                        DBSession.add(file1)
                for k, v in kw.iteritems():
                    if len(k.split(':'))==2:
                        k1 = k.split(':')
                        if k1[0] == u'othernames':
                            if v not in allnames:
                                othername = DBSession.query(Names).get(k1[1])
                                othername.name = v
                                changes += (u'; Change name from %s: to ' % k1[1]) + v

                history = History()
                history.user = userid
                history.status = 'Edit'
                project = DBSession.query(Projects).filter(Projects.name==pname).first()
                history.project = pname
                history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if smiles and smiles != str(compound.structure):
                    compound.structure = smiles
                    changes += u' SMILES: ' + kw['smiles'] + u';'
                for tag in tagi:
                    if tagi != compound.tags:
                        changes += u' Tags: '
                        compound.tags = tagi
                    if tag not in compound.tags:
                        changes += str(tag.name) + ', '
                if kw.has_key('notes') and kw['notes'] != compound.notes:
                    changes += u' Notes: ' + kw['notes'] + ';'
                    compound.notes = kw['notes']
                if kw['pains'] == 'yes':
                    pains1 = DBSession.query(PAINS1).all()
                    pains2 = DBSession.query(PAINS2).all()
                    pains3 = DBSession.query(PAINS3).all()
                    m = Chem.MolFromSmiles(smiles)
                    mol = Chem.AddHs(m)
                    for p1 in pains1:
                        patt = Chem.MolFromSmarts(str(p1.structure))
                        if patt:
                            if mol.HasSubstructMatch(patt):
                                compound.pains1 = p1
                        else:
                            flash(l_(u'Pattern error'), 'error')
                            redirect(come_from)
                    for p2 in pains2:
                        patt = Chem.MolFromSmarts(str(p2.structure))
                        if patt:
                            if mol.HasSubstructMatch(patt):
                                compound.pains2 = p2
                        else:
                            flash(l_(u'Pattern error'), 'error')
                            redirect(come_from)
                    for p3 in pains3:
                        patt = Chem.MolFromSmarts(str(p3.structure))
                        if patt:
                            if mol.HasSubstructMatch(patt):
                                compound.pains3 = p3
                        else:
                            flash(l_(u'Pattern error'), 'error')
                            redirect(come_from)
                history.changes = changes
                compound.history += [history]
                DBSession.add(history)
                DBSession.flush()
#                #transaction.commit()
                compound2 = DBSession.query( Compound ).get(int(gid))
                from rdkit.Chem.inchi import MolToInchi
                mol = Chem.MolFromSmiles(smiles)
                compound.inchi = MolToInchi(mol)
                compound2.atompair = compound2.structure.atompair_b()
                compound2.torsion = compound2.structure.torsion_b()
                compound2.morgan = compound2.structure.morgan_b(2)
                compound2.mw = compound2.structure.mw.label('mw')
                compound2.logp = compound2.structure.logp.label('logp')
                compound2.hba = compound2.structure.hba.label('hba')
                compound2.hbd = compound2.structure.hbd.label('hbd')
                compound2.tpsa = compound2.structure.tpsa.label('tpsa')
                compound2.num_atoms = compound2.structure.num_atoms.label('num_atoms')
                compound2.num_hvy_atoms = compound2.structure.num_hvy_atoms.label('num_hvy_atoms')
                compound2.num_rings = compound2.structure.num_rings.label('num_rings')
                create_image(gid, str(compound2.structure), img_dir)
                DBSession.flush()
            else:
                redirect(come_from)
        else:
#            msg='ERROR: wrong SMILES'
            flash(l_(u'SMILES error'), 'error')
            redirect(come_from)
        flash(l_(u'Task completed successfully'))
        redirect(come_from)

    @expose('molgears.templates.users.molecules.readfile')
    def read_from_file(self, **kw):
        """
        Read data from selected file. Allowed formats of file:
        * SMILES (smi or txt containing SMILES and a name of compound in each line)
        * sdf
        * mol
        """
        from rdkit import Chem
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        userid = request.identity['repoze.who.userid']
        errors = []
        changes = ''
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if kw:
            try:
                notes = kw['notes']
                files_dirname = os.path.join(os.path.abspath(resource_filename('molgears', 'files')))
                struct_dirname = os.path.join(files_dirname, 'select_st')
                if isinstance(kw['text_tags'], basestring):
                    tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                else:
                    tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
            except Exception as msg:
                flash(l_(u'Fill required fields'), 'error')
                redirect(come_from)
            try:
                filename = kw['file'].filename
            except Exception as msg:
                filename = None
                pass
            if filename and userid:
                now = datetime.now()
                nowstr =  now.strftime("%Y-%m-%d_%H%M")
                newfilename = nowstr + '_' + userid + '_' + filename
                f_path = os.path.join(struct_dirname, newfilename)

                try:
                    f = file(f_path, "w")
                    f.write(kw['file'].value)
                    f.close()
                except Exception as msg:
                    flash(l_(msg), 'error')
                    redirect(come_from)

                from rdkit.Chem.inchi import MolToInchi
                errors_msg = ''
                for name,  smiles,  error, count in addsmi(f_path, limit=0):
                    if error != None:
                        errors.append(error)
                    else:
                        compound = Compound(name, smiles, creator=userid)

                        if kw.has_key('savefile') and kw['savefile'] == "yes":
                            number = DBSession.query(CompoundsFiles).count() + 1
                            public_file_name = str(number) + '_' + userid + '_' + nowstr + '_' + filename
                            public_file_name.replace(' ', '_')
                            public_f_path = os.path.join(models_dir, public_file_name)
                            try:
                                mol = Chem.MolFromSmiles(smiles)
                                writer = Chem.SDWriter(public_f_path)
                                writer.write(mol)
                                writer.close()
                            except Exception as msg:
                                flash(l_(msg), 'error')
                                redirect(come_from)

                            if not public_file_name[:-2]=='gz':
                                public_file_name += '.gz'
                                fout_path = os.path.join(models_dir, public_file_name)
                                import gzip
                                f_in = open(public_f_path, 'rb')
                                f_out = gzip.open(fout_path, 'wb')
                                f_out.writelines(f_in)
                                f_out.close()
                                f_in.close()
                                os.remove(public_f_path)
                            file1 = CompoundsFiles()
                            file1.name = filename
                            file1.filename = public_file_name
                            changes += '; Plik modelowanie: ' + filename + ' (' + public_file_name + ')'
                            compound.files += [file1]
                            DBSession.add(file1)
                        newname = Names()
                        newname.name = name
                        compound.names += [newname]
                        compound.project = [project]
                        compound.tags = tagi
                        compound.pnum = 0
                        compound.snum = 0
                        compound.lnum = 0
                        compound.seq = 1
                        try:
                            mol = Chem.MolFromSmiles(smiles)
                            compound.inchi = MolToInchi(mol)
                            from silicos_it.descriptors import qed
                            compound.qed = round(qed.default(mol), 2)
                        except Exception as msg:
                            flash(l_(u'Error: %s' % msg),'error')
                            redirect(come_from)
#                        compound.status = status
                        history = History()
                        history.user = userid
                        history.status = 'Wczytywanie pliku'
                        project = DBSession.query(Projects).filter(Projects.name==pname).first()
                        history.project = pname
                        history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        changes = u'Nazwa:' + name + u'; SMILES:' + smiles + u'; Tags:'
                        for tag in tagi:
                            changes += str(tag.name) + '; '
                        if notes:
                            compound.notes = notes
                            changes += u'Notes: ' + notes + '; '
                        if kw['pains'] == 'yes':
                            pains1 = DBSession.query(PAINS1).all()
                            pains2 = DBSession.query(PAINS2).all()
                            pains3 = DBSession.query(PAINS3).all()
                            m = Chem.MolFromSmiles(smiles)
                            mol = Chem.AddHs(m)
                            for p1 in pains1:
                                patt = Chem.MolFromSmarts(str(p1.structure))
                                if patt:
                                    if mol.HasSubstructMatch(patt):
                                        compound.pains1 = p1
                                else:
                                    flash(l_(u'Pattern error'), 'error')
                                    redirect(come_from)
                            for p2 in pains2:
                                patt = Chem.MolFromSmarts(str(p2.structure))
                                if patt:
                                    if mol.HasSubstructMatch(patt):
                                        compound.pains2 = p2
                                else:
                                    flash(l_(u'Pattern error'), 'error')
                                    redirect(come_from)
                            for p3 in pains3:
                                patt = Chem.MolFromSmarts(str(p3.structure))
                                if patt:
                                    if mol.HasSubstructMatch(patt):
                                        compound.pains3 = p3
                                else:
                                    flash(l_(u'Pattern error'), 'error')
                                    redirect(come_from)
                        history.changes = changes
                        check = DBSession.query(Compound).filter(Compound.structure.equals(smiles)).first()
                        if check:
                            flash(l_(u'Compound on number: %s exist in DB on GID number: %s ' % (count, check.gid) ), 'error')
#                            redirect(come_from)
                            errors_msg += u'Structure Error:'
                            errors_msg += u' Nr: ' + str(count) + u'; Smiles: ' + str(smiles) + u'; GID: '+ str(check.gid)
                        else:
                            compound.history = [history]
                            DBSession.add(newname)
                            DBSession.add(history)
                            DBSession.add(compound)
                DBSession.flush()

                if count and count<len(DBSession.query(Compound).all()):
                    for q in DBSession.query(Compound).order_by('gid')[-count:]:
                            create_image(q.gid, q.structure, img_dir)
                elif count and count>len(DBSession.query(Compound).all()):
                    for q in DBSession.query(Compound).order_by('gid')[1:]:
                            create_image(q.gid, q.structure, img_dir)
                if errors:
                    flash(l_(errors),'error')
                    redirect(come_from)
                elif errors_msg and errors_msg != '':
                    flash(l_(errors_msg), 'error')
                    redirect(come_from)
                else:
                    flash(l_(u'Task completed successfully'))
                    redirect(come_from)
            else:
                flash(l_(u'Tags and file required'), 'warning')
        return dict(page='molecules', value=kw, errors=errors, alltags=alltags, pname=pname)

    @expose("molgears.templates.users.molecules.accept")
    def accept(self, id):
        """
        Display a page to accept compound for requests.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        gid = int(id)
        principals = DBSession.query(Group).get(3)
        userid = request.identity['repoze.who.userid']
#        alltags =[tag.name for tag in DBSession.query( Tags ).all() ]
        compound = DBSession.query( Compound ).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=gid).first()
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if compound:
            alltags = [tag for tag in DBSession.query(Tags).order_by('name').all() ]
            try:
                ctags = [c for c in compound.tags]
            except Exception as msg:
                ctags = [compound.tags.name]
                pass
            default_user = userid
            return dict(compound=compound, users=principals.users, default_user=default_user, alltags=alltags, ctags=ctags, page='molecules', pname=pname)
        else:
            redirect(come_from)

    @expose()
    def add_to_select(self, id, **kw):
        """
        Save data commitet from accept form.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        gid = int(id)
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        try:
            if isinstance(kw['text_tags'], basestring):
                tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
            else:
                tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
        except Exception as msg:
            flash(l_(u'Tags error: %s' %msg), 'error')
            redirect(come_from)
        try:
            notes = kw['notes']
        except Exception:
            notes = None
            pass
        compound = DBSession.query( Compound ).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=gid).first()
        if compound:
            compound.tags = tagi

            userid = request.identity['repoze.who.userid']
            pcompound = PCompound()
            pcompound.gid = gid
            if not compound.seq:
                compound.seq = 1
            pcompound.seq = compound.seq
            compound.seq += 1
            pcompound.owner = userid
            pcompound.principal = kw['principal']
            pcompound.mol = compound
            pcompound.priority = int(kw['priority'])

            phistory = PHistory()
            phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            phistory.user = userid
            phistory.gid = pcompound.gid
            project = DBSession.query(Projects).filter(Projects.name==pname).first()
            phistory.project = pname
            phistory.status = 'accepted'
            pchanges = u'Gid: ' + str(gid) + u'; Owner:' + userid + '; '
    #        pchanges = 'Gid: ' + str(gid) + '; Właściciel:' + str(userid) + '; LSO: '  + str(lso) + '; '
            pchanges += u'priority: ' + kw['priority']
            if notes:
                pcompound.notes = notes
                pchanges += u'Notes: ' + notes

            history = History()
            history.user = userid
            history.status = 'Akceptacja do projektu'
            project = DBSession.query(Projects).filter(Projects.name==pname).first()
            history.project = pname
            history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            changes = u'Owner: ' + userid + u'; ' + u'Tags: '
            pchanges += u' Tags: '
            for tag in tagi:
                changes += str(tag.name) + '; '
                pchanges  += str(tag.name) + '; '
            pcompound.status = DBSession.query( PStatus).get(1)
            phistory.changes = pchanges
            history.changes = changes
            pcompound.history += [phistory]
            compound.history += [history]

            DBSession.add(phistory)
            DBSession.add(history)
            DBSession.add(pcompound)
            DBSession.flush()
            compound.pnum = DBSession.query(PCompound).filter_by(gid=gid).count()
            ##transaction.commit()

            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        else:
            redirect(come_from)

    @expose('molgears.templates.users.molecules.details')
    def details(self, *args, **kw):
        """
        Display a page with details of molecule structure.
        """
        gid = int(args[0])
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        limit = user.limit_sim
        threshold = float(user.threshold)/100.0
        compound = DBSession.query(Compound).filter_by(gid=gid).filter(Compound.project.any(Projects.name==pname)).first()
        assert compound.gid == gid,  "GID Error."
        from rdkit.Chem.rdMolDescriptors import CalcMolFormula
        formula = CalcMolFormula(Chem.MolFromSmiles(str(compound.structure)))

        pcompounds = DBSession.query(PCompound).filter(PCompound.gid==gid).join(PCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        scompounds = DBSession.query(SCompound).filter_by(gid=gid).join(SCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        lcompounds = DBSession.query(LCompound).filter_by(gid=gid).join(LCompound.mol).filter(Compound.project.any(Projects.name==pname)).order_by('id').all()
        from razi.functions import functions
        from razi.expression import TxtMoleculeElement
        from razi.postgresql_rdkit import tanimoto_threshold
        DBSession.execute(tanimoto_threshold.set(threshold))
        query_bfp = functions.morgan_b(TxtMoleculeElement(str(compound.structure)), 2)
        constraint = Compound.morgan.tanimoto_similar(query_bfp)
        tanimoto_sml = Compound.morgan.tanimoto_similarity(query_bfp).label('tanimoto')
        similars = DBSession.query(Compound, tanimoto_sml).filter(constraint).filter(Compound.project.any(Projects.name==pname)).order_by(desc(tanimoto_sml)).limit(limit).all()
        return dict(compound=compound, pcompounds=pcompounds, scompounds=scompounds, lcompounds=lcompounds, formula=formula, similars=similars, page='molecules', pname=pname)
        
    @expose('molgears.templates.users.molecules.astex')
    def astex(self, *args, **kw):
        """
        It servs Astex Viewer page for user in molecules controller.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        try:
            smiles = str(args[0])
            mol = Chem.MolFromSmiles(smiles)
            from rdkit.Chem import AllChem
            AllChem.EmbedMolecule(mol)
            AllChem.UFFOptimizeMolecule(mol)
            mol = Chem.MolToMolBlock(mol)
        except Exception:
            mol = None
            smiles = None
        return dict(mol = mol, smiles = smiles, page='molecules', pname=pname)

    @expose("molgears.templates.users.molecules.library")
    def library(self, id):
        pname = request.environ['PATH_INFO'].split('/')[1]
        gid = int(id)
        compound = DBSession.query( Compound ).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=gid).first()
        group = DBSession.query(Group).get(2)
        users = [u.display_name for u in group.users]
        users.sort()
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if compound:
            alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
            return dict(compound=compound, alltags=alltags, users=users, page='molecules', pname=pname)
        else:
            redirect(come_from)

    @expose()
    def add_to_library(self, id, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        gid = int(id)
        try:
            if isinstance(kw['text_tags'], basestring):
                tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
            else:
                tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
        except Exception as msg:
            flash(l_(u'Tags error: %s' %msg), 'error')
            redirect(request.headers['Referer'])
        userid = request.identity['repoze.who.userid']
        compound = DBSession.query( Compound ).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=gid).first()
        compound.tags = tagi
        lcompound = LCompound()
        lcompound.mol = compound
        lcompound.seq = compound.seq
        compound.seq += 1
        lcompound.sid = 0
        lcompound.avg_ki_mdm2 = 0.0
        lcompound.avg_ic50_mdm2 = 0.0
        lcompound.avg_hillslope_mdm2 = 0.0
        lcompound.avg_r2_mdm2 = 0.0
        lcompound.avg_bg_ic50_mdm2 = 0.0
        lcompound.avg_bg_hillslope_mdm2 = 0.0
        lcompound.avg_bg_r2_mdm2 = 0.0
        lcompound.avg_ki_mdm4 = 0.0
        lcompound.avg_ic50_mdm4 = 0.0
        lcompound.avg_hillslope_mdm4 = 0.0
        lcompound.avg_r2_mdm4 = 0.0
        lcompound.avg_bg_ic50_mdm4 = 0.0
        lcompound.avg_bg_hillslope_mdm4 = 0.0
        lcompound.avg_bg_r2_mdm4 = 0.0
        lcompound.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#        lcompound.source = 'LSO: ADAMED'
        history = History()
        history.user = userid
        history.status = 'library'
        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        history.project = pname
        history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.changes = u'Added to library; Tags: '
        for tag in tagi:
            history.changes += tag.name + '; '

        lhistory = LHistory()
        lhistory.user = userid
        lhistory.status = 'Created'
        lhistory.gid = lcompound.mol.gid
        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        lhistory.project = pname
        lhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lchanges = u''
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
            if kwas >= 0:
                lpurity1 = LPurity()
                lpurity1.value = kwas
                lpurity1.type = 'kwasowa'
                lcompound.purity += [lpurity1]
                lchanges += u'; Acid purity: ' + str(kw['kwas'])
                try:
                    kwas_file = kw['kwas_file'].filename
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
                    lfile1 = SFiles()
                    lfile1.name = kwas_file
                    lfile1.filename = new_kwas_file_name
                    lchanges += u'; Analitics files for acid: ' + kwas_file + u' (' + new_kwas_file_name + u')'
                    lpurity1.filename = [lfile1]
                else:
                    lfile1 = None
            else:
                lpurity1 = None

            if zasada >= 0:
                lpurity2 = LPurity()
                lpurity2.value = zasada
                lpurity2.type = 'zasadowa'
                lcompound.purity += [lpurity2]
                lchanges += u'; Basic purity: ' + str(kw['zasada'])
                try:
                    zasada_file = kw['zasada_file'].filename
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
                    lfile2 = SFiles()
                    lfile2.name = zasada_file
                    lfile2.filename = new_zasada_file_name
                    lchanges += u'; Basic file: ' + zasada_file + ' (' + new_zasada_file_name +')'
                    lpurity2.filename = [lfile2]
                else:
                    lfile2 = None
            else:
                lpurity2 = None
        else:
            flash(l_(u'Acid or Basic purity is required'), 'error')
            redirect(request.headers['Referer'])

        if kw.has_key('lso') and kw['lso'] != u'':
            lcompound.lso = kw['lso']
            lchanges += u' LSO: ' + kw['lso']

        if kw.has_key('form'):
            lcompound.form = kw['form']
            lchanges += u'; Forma: ' + kw['form']
        if kw.has_key('state') and kw['state'] !=u'':
            try:
                state = str(kw['state'])
                state = state.replace(',', '.') 
                lcompound.state = float(state)
            except Exception as msg:
                flash(l_(u'Float required: %s' % msg), 'error')
                redirect(request.headers['Referer'])
            lchanges += u'; Stan mag.[mg]: ' + str(kw['state'])
        if kw.has_key('box'):
            lcompound.box = kw['box']
            lchanges += u'; Box: ' + kw['box']
        if kw.has_key('entry'):
            lcompound.entry = kw['entry']
            lchanges += u'; Entry: ' + kw['entry']
        if kw.has_key('chemist'):
            lcompound.owner = kw['chemist']
            lchanges += '; synthesis: ' + kw['chemist']
        if kw.has_key('showme'):
            if kw['showme'] == "True":
                lcompound.showme = True
            else:
                lcompound.showme = False
            lchanges += u'; Show in activity: ' + kw['showme']
        if kw.has_key('notes'):
            lcompound.notes = kw['notes']
            lchanges += u';Notes: ' + kw['notes']
        if kw.has_key('source'):
            lcompound.source = kw['source']
            lchanges += u'; Source: ' + kw['source']
        lhistory.changes = lchanges
        compound.history += [history]
        lcompound.history = [lhistory]


        if lpurity1:
            if lfile1:
                DBSession.add(lfile1)
            DBSession.add(lpurity1)
        if lpurity2:
            if lfile2:
                DBSession.add(lfile2)
            DBSession.add(lpurity2)
        flash(l_(u'Task completed successfully'))
        DBSession.add(lcompound)
        DBSession.add(history)
        DBSession.add(lhistory)
        DBSession.flush()
        compound.lnum = DBSession.query( LCompound ).filter_by(gid=id).count()
        redirect(request.headers['Referer'])

    @expose()
    def delname(self, id, came_from, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        id = int(id)
        name = DBSession.query(Names).get(id)
        compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=name.compound_id).first()
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if compound:
            if compound.name == name.name:
                flash(l_(u'Main Name can not be deleted'), 'warning')
                redirect(come_from)
            else:
                userid = request.identity['repoze.who.userid']
                history = History()
                history.user = userid
                history.status = 'Delete name'
                history.changes = u'Name "%s" deleted.' % name.name
                project = DBSession.query(Projects).filter(Projects.name==pname).first()
                history.project = pname
                history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                compound.names.remove(name)
                compound.history += [history]
                DBSession.delete(name)
                DBSession.add(history)
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        else:
            redirect(come_from)

    @expose()
    def setname(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        try:
            name = args[0]
            id = int(args[1])
            came_from = args[2]
        except Exception:
            name = None
        compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=id).first()
        if compound:
            if name:
                allnames = [n.name for n in compound.names]
                if compound.name != name and (name in allnames):
                    userid = request.identity['repoze.who.userid']
                    history = History()
                    history.user = userid
                    history.status = 'name change'
                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    history.project = pname
                    history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    history.changes = u'main name changed from "%s" to "%s".' % (compound.name, name)
                    compound.name = name
                    compound.history += [history]
                    flash(l_(u'Task completed successfully'))
                    redirect(request.headers['Referer'])
            flash(l_(u'Main Name not changed'), 'warning')
            if came_from == 'edit':
                redirect(request.headers['Referer'])
            elif came_from == 'details':
                redirect(request.headers['Referer'])
        else:
            redirect(request.headers['Referer'])

    @expose('molgears.templates.users.molecules.multiedit')
    def multiedit(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        alltags = [tag for tag in DBSession.query( Tags ).all() ]
        compound = ()
        newalltags = []
        come_from = request.headers['Referer']
        for tag in alltags:
            ispresentinall = True
            ispresent = False
            for arg in args[1:]:
                compound = DBSession.query(Compound).get(arg)
                if tag not in compound.tags:
                    ispresentinall = False
                else:
                    ispresent = True
            if ispresentinall:
                newalltags += [(tag, 'ALL')]
            else:
                if ispresent:
                    newalltags += [(tag, 'SOME')]
                else:
                    newalltags += [(tag, False)]
        alltags = newalltags
        if kw:
            try:
                if isinstance(kw['text_tags'], basestring):
                    tagsids = [int(kw['text_tags'])]
                else:
                    tagsids = [int(id) for id in kw['text_tags']]
            except Exception as msg:
                tagsids = []
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
                for k, v in kw.iteritems():
                    if v == 'on':
                        kid = int(k)
                        if kid in tagsids:
                            for arg in argv:
                                tag = DBSession.query( Tags ).get(kid)
                                compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=int(arg)).first()
                                if not compound:
                                    redirect(request.headers['Referer'])
                                history = History()
                                history.user = userid
                                project = DBSession.query(Projects).filter(Projects.name==pname).first()
                                history.project = pname
                                history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                history.status = u'Multi - edit'
                                changes = u''
                                if tag not in compound.tags:
                                    compound.tags += [tag]
                                    changes += u' Tag: ' + tag.name
                                if notes:
                                    compound.notes = notes
                                    changes += u'; Notes: ' + notes
                                history.changes = changes
                                compound.history += [history]
                                DBSession.add(history)
                                DBSession.flush()
                                ##transaction.commit()
                        else:
                            for arg in argv:
                                tag = DBSession.query(Tags).get(kid)
                                compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=int(arg)).first()
                                if not compound:
                                    redirect(request.headers['Referer'])
                                history = History()
                                history.user = userid
                                project = DBSession.query(Projects).filter(Projects.name==pname).first()
                                history.project = pname
                                history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                history.status = u'Multi - edit'
                                changes = u''
                                if tag in compound.tags:
                                    compound.tags.remove(tag)
                                    changes += u'Tag deleted: ' + tag.name
                                if notes:
                                    compound.notes = notes
                                    changes += u'; Notes: ' + notes
                                history.changes = changes
                                compound.history += [history]
                                DBSession.add(history)
                                DBSession.flush()
                                ##transaction.commit()
                if kw.has_key('come_from'):
                    come_from = kw['come_from']
                else:
                    come_from = request.headers['Referer']
                flash(l_(u'Task completed successfully'))
                redirect(come_from)

        return dict(alltags=alltags, args=args, come_from=come_from, page='molecules', pname=pname)

    @expose('molgears.templates.users.molecules.multiaccept')
    def multiaccept(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        userid = request.identity['repoze.who.userid']
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

            if argv:
                for arg in argv:
                    try:
                        if isinstance(kw['text_tags'], basestring):
                            tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                        else:
                            tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
                    except Exception:
                        tagi = None
                    compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=int(arg)).first()
                    if not compound:
                        redirect(request.headers['Referer'])
                    pcompound = PCompound()
                    pcompound.mol = compound
                    if not compound.seq:
                        compound.seq =1
                    pcompound.seq = compound.seq
                    compound.seq += 1
                    pcompound.priority = int(kw['priority'])
                    pcompound.owner = userid
                    pcompound.principal = kw['principal']
                    pcompound.status = DBSession.query( PStatus).get(1)
                    history = History()
                    history.user = userid
                    history.status = u'Multi - accept'
                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    history.project = pname
                    history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    history.changes = u'Add to requests;'
                    phistory = PHistory()
                    phistory.user = userid
                    phistory.gid = pcompound.gid
                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    phistory.project = pname
                    phistory.status = u'Multi - accept'
                    phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    phistory.changes = u'Accepted; Status: proposed; '
                    if tagi:
                        if compound.tags != tagi:
                            compound.tags = tagi
                            history.changes += u' Tags: '
                            for tag in tagi:
                                history.changes += tag.name
                    if notes:
                        pcompound.notes = notes
                        phistory.changes += u' Notes: ' + notes
                    else:
                        if compound.notes:
                            pcompound.notes = compound.notes
                            phistory.changes += u' Notes: ' + compound.notes
                    compound.history += [history]
                    pcompound.history += [phistory]
                    DBSession.add(history)
                    DBSession.add(phistory)
                    DBSession.add(pcompound)
                    DBSession.flush()
                    compound.pnum = DBSession.query(PCompound).filter_by(gid=int(arg)).count()
                    ##transaction.commit()
                if kw.has_key('come_from'):
                    come_from = kw['come_from']
                else:
                    come_from = request.headers['Referer']
                flash(l_(u'Task completed successfully'))
                redirect(come_from)
        return dict(alltags=alltags, default_user=userid, users=principals.users, args=args, come_from=come_from, page='molecules', pname=pname)

    @expose('molgears.templates.users.molecules.multilibrary')
    def multilibrary(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        come_from = request.headers['Referer']
        group = DBSession.query(Group).get(2)
        users = [u.display_name for u in group.users]
        users.sort()
        if kw:
            try:
                if isinstance(kw['argv'], basestring):
                    argv = [kw['argv']]
                else:
                    argv = [id for id in kw['argv']]
            except Exception:
                argv = None
            try:
                if isinstance(kw['text_tags'], basestring):
                    tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                else:
                    tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
            except Exception:
                tagi = None
            if argv:
                userid = request.identity['repoze.who.userid']
                for arg in argv:
                    compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=int(arg)).first()
                    if not compound:
                        redirect(request.headers['Referer'])
                    lcompound = LCompound()
                    lcompound.mol = compound
                    lcompound.seq = compound.seq
                    compound.seq += 1
                    lcompound.sid = 0
                    lcompound.avg_ki_mdm2 = 0.0
                    lcompound.avg_ic50_mdm2 = 0.0
                    lcompound.avg_hillslope_mdm2 = 0.0
                    lcompound.avg_r2_mdm2 = 0.0
                    lcompound.avg_bg_ic50_mdm2 = 0.0
                    lcompound.avg_bg_hillslope_mdm2 = 0.0
                    lcompound.avg_bg_r2_mdm2 = 0.0
                    lcompound.avg_ki_mdm4 = 0.0
                    lcompound.avg_ic50_mdm4 = 0.0
                    lcompound.avg_hillslope_mdm4 = 0.0
                    lcompound.avg_r2_mdm4 = 0.0
                    lcompound.avg_bg_ic50_mdm4 = 0.0
                    lcompound.avg_bg_hillslope_mdm4 = 0.0
                    lcompound.avg_bg_r2_mdm4 = 0.0
                    lcompound.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    history = History()
                    history.user = userid
                    history.status = 'library'
                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    history.project = pname
                    history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    history.changes = u'Compound added to library; '
                    if tagi:
                        compound.tags = tagi
                        history.changes += u'Tags: '
                        for tag in tagi:
                            history.changes += tag.name + '; '

                    lhistory = LHistory()
                    lhistory.user = userid
                    lhistory.gid = lcompound.mol.gid
                    project = DBSession.query(Projects).filter(Projects.name==pname).first()
                    lhistory.project = pname
                    lhistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    lhistory.status = 'Created'
                    lchanges = u''
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
                        flash(l_(u'Float required: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                    if (kwas or zasada) >= 0:
                        if kwas >= 0:
                            lpurity1 = LPurity()
                            lpurity1.value = kwas
                            lpurity1.type = 'acid'
                            lcompound.purity += [lpurity1]
                            lchanges += u'; Acid purity: ' + str(kw['kwas'])
                        else:
                            lpurity1 = None

                        if zasada >= 0:
                            lpurity2 = LPurity()
                            lpurity2.value = zasada
                            lpurity2.type = 'basic'
                            lcompound.purity += [lpurity2]
                            lchanges += u'; Basic purity: ' + str(kw['zasada'])
                        else:
                            lpurity2 = None
                    else:
                        lpurity1 = None
                        lpurity2 = None
                        flash(l_(u'Purity required'), 'warning')

                    if kw.has_key('lso') and kw['lso'] != u'':
                        lcompound.lso = kw['lso']
                        lchanges += u' LSO: ' + kw['lso']
                    if kw.has_key('form') and kw['form'] != u'':
                        lcompound.form = kw['form']
                        lchanges += u'; Forma: ' + kw['form']
                    if kw.has_key('state') and kw['state'] != u'':
                        try:
                            state = str(kw['state'])
                            state = state.replace(',', '.') 
                            lcompound.state = float(state)
                        except Exception as msg:
                            flash(l_(u'Float required: %s' % msg), 'error')
                            redirect(request.headers['Referer'])
                        lchanges += u'; amount [mg]: ' + str(kw['state'])
                    if kw.has_key('box') and kw['box'] != u'':
                        lcompound.box = kw['box']
                        lchanges += u'; Box: ' + kw['box']
                    if kw.has_key('entry') and kw['entry'] != u'':
                        lcompound.entry = kw['entry']
                        lchanges += u'; Entry: ' + kw['entry']
                    if kw.has_key('chemist'):
                        lcompound.owner = kw['chemist']
                        lchanges += '; synthesis: ' + kw['chemist']
                    if kw.has_key('notes') and kw['notes'] != u'':
                        lcompound.notes = kw['notes']
                        lchanges += u';Notes: ' + kw['notes']
                    else:
                        lcompound.notes = compound.notes
                        lchanges += u'; Notes: ' + unicode(compound.notes)
                    if kw.has_key('source'):
                        lcompound.source = kw['source']
                        lchanges += u'; Source: ' + kw['source']
                    lhistory.changes = lchanges
                    compound.history += [history]
                    lcompound.history = [lhistory]

                    if lpurity1:
                        DBSession.add(lpurity1)
                    if lpurity2:
                        DBSession.add(lpurity2)
                    DBSession.add(lcompound)
                    DBSession.add(history)
                    DBSession.add(lhistory)
                    DBSession.flush()
                    compound.lnum = DBSession.query(LCompound).filter_by(gid=int(arg)).count()
            if kw.has_key('come_from'):
                come_from = kw['come_from']
            else:
                come_from = request.headers['Referer']
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        return dict(alltags=alltags, args=args, come_from=come_from, users=users, page='molecules', pname=pname)

#    @expose()
#    def images(self):
#        """
#        recreate images for all compounds
#        """
#        pname = request.environ['PATH_INFO'].split('/')[1]
#        for q in DBSession.query(Compound).order_by('gid')[:]:
#            create_image(q.gid, q.structure, img_dir)
#        flash('gotowe')
#        redirect(request.headers['Referer'])
#
#    @expose()
#    def fprint(self):
#    '''recalculate all fingerprints'''
#        for q in DBSession.query( Compound ).order_by('gid')[:]:
#            q.morgan = q.structure.morgan_b(2)
#        flash('gotowe')
#        redirect(request.headers['Referer'])


    @expose()
    def nums(self):
        """recalculate nums"""
        compound = DBSession.query(Compound).all()
        for c in compound:
            c.pnum = DBSession.query( PCompound ).filter_by(gid=c.gid).count()
            c.snum = DBSession.query( SCompound ).filter_by(gid=c.gid).count()
            c.lnum = DBSession.query( LCompound ).filter_by(gid=c.gid).count()
        flash('gotowe')
        redirect('/')


#    @expose()
#    def read_pains1(self):
#        inputfile = open('/home/adrian/Downloads/p_l15.txt', 'rb')
#        import re
#        from rdkit.Chem import Draw,  MolFromSmiles, AllChem
#        from rdkit.Chem.inchi import MolToInchi
#        for line in inputfile:
#            error = None
#            try:
#                smarts, name = line.split()
#            except Exception as msg:
#                print msg
#            if name:
#                m=re.compile('"(.*?)"').search(name)
#                rawname = m.group(1)
#            patt = Chem.MolFromSmarts(smarts)
#            if patt:
#                p = PAINS1(rawname, smarts)
#            else:
#                flash('blad %s' % smarts)
#                redirect(request.headers['Referer'])
#            DBSession.add(p)
#            DBSession.flush()                
#        flash('jestok')
#        redirect(request.headers['Referer'])
#        
#    @expose()
#    def read_pains2(self):
#        inputfile = open('/home/adrian/Downloads/p_l150.txt', 'rb')
#        import re
#        from rdkit.Chem import Draw,  MolFromSmiles, AllChem
#        from rdkit.Chem.inchi import MolToInchi
#        for line in inputfile:
#            error = None
#            try:
#                smarts, name = line.split()
#            except Exception as msg:
#                print msg
#            if name:
#                m=re.compile('"(.*?)"').search(name)
#                rawname = m.group(1)
#            patt = Chem.MolFromSmarts(smarts)
#            if patt:
#                p = PAINS2(rawname, smarts)
#            else:
#                flash('blad %s' % smarts)
#                redirect(request.headers['Referer'])
#            DBSession.add(p)
#            DBSession.flush()                
#        flash('jestok')
#        redirect(request.headers['Referer'])
#        
#    @expose()
#    def read_pains3(self):
#        inputfile = open('/home/adrian/Downloads/p_m150.txt', 'rb')
#        import re
#        from rdkit.Chem import Draw,  MolFromSmiles, AllChem
#        from rdkit.Chem.inchi import MolToInchi
#        for line in inputfile:
#            error = None
#            try:
#                smarts, name = line.split()
#            except Exception as msg:
#                print msg
#            if name:
#                m=re.compile('"(.*?)"').search(name)
#                rawname = m.group(1)
#            patt = Chem.MolFromSmarts(smarts)
#            if patt:
#                p = PAINS3(rawname, smarts)
#            else:
#                flash('blad %s' % smarts)
#                redirect(request.headers['Referer'])
#            DBSession.add(p)
#            DBSession.flush()                
#        flash('jestok')
#        redirect(request.headers['Referer'])
#        
    @expose()
    def pains1(self):
        pains = DBSession.query(PAINS1).all()
        compound = DBSession.query(Compound).all()
        ID = ''
        for c in compound:
            m = Chem.MolFromSmiles(str(c.structure))
            mol = Chem.AddHs(m)
            for p in pains:
                patt = Chem.MolFromSmarts(str(p.structure))
                if patt:
                    if mol.HasSubstructMatch(patt):
                        c.pains1 = p
                        ID += '%s - %s; ' % (c.gid, p.structure)
                else:
                    flash(l_(u'Pattern error'), 'error')
                    redirect(request.headers['Referer'])
        flash(ID)
        redirect(request.headers['Referer'])

    @expose()
    def pains2(self):
        pains = DBSession.query(PAINS2).all()
        compound = DBSession.query(Compound).all()
        ID = ''
        for c in compound:
            m = Chem.MolFromSmiles(str(c.structure))
            mol = Chem.AddHs(m)
            for p in pains:
                patt = Chem.MolFromSmarts(str(p.structure))
                if patt:
                    if mol.HasSubstructMatch(patt):
                        c.pains2 = p
                        ID += '%s - %s; ' % (c.gid, p.structure)
                else:
                    flash(l_(u'Pattern error'), 'error')
                    redirect(request.headers['Referer'])
        flash(ID)
        redirect(request.headers['Referer'])

    @expose()
    def pains3(self):
        pains = DBSession.query(PAINS3).all()
        compound = DBSession.query(Compound).all()
        ID = ''
        for c in compound:
            m = Chem.MolFromSmiles(str(c.structure))
            mol = Chem.AddHs(m)
            for p in pains:
                patt = Chem.MolFromSmarts(str(p.structure))
                if patt:
                    if mol.HasSubstructMatch(patt):
                        c.pains3 = p
                        ID += '%s - %s; ' % (c.gid, p.structure)
                else:
                    flash(l_(u'Pattern error'), 'error')
                    redirect(request.headers['Referer'])
        flash(ID)
        redirect(request.headers['Referer'])

    @expose()
    def remove(self, *args):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if has_permission('kierownik'):
            if args:
                for arg in args:
                    compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter_by(gid=int(arg)).first()
                    if compound:
                        if compound.pnum == 0 and compound.snum == 0 and compound.lnum == 0:
                            history = History()
                            history.user = userid
                            history.status = u'delete'
                            history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            project = DBSession.query(Projects).filter(Projects.name==pname).first()
                            history.project = pname
                            history.changes = u'Delete compound'
                            compound.history += [history]
                            DBSession.add(history)
                            DBSession.delete(compound)
                            flash(l_(u'Task completed successfully'))
                        else:
                            flash(l_(u'Removing disabled on compound: %s due other connections') % arg, "error")
                            redirect(come_from)
                    else:
                        flash(l_(u'Compound: %s disabled or not exist') % arg, "error")
                        redirect(come_from)
            else:
                flash(u"args error", "error")
                redirect(come_from)
        else:
            flash(l_(u'Permission denied'), 'error')
        redirect(come_from)

    @expose()
    def deletefromlist(self, ulist_id, *args):
        ulist = DBSession.query(UserLists).get(ulist_id)
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        ulists = [l for l in user.lists if l.table == 'LCompounds']
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
        
    @expose('molgears.templates.users.molecules.similaritymap')
    def similaritymap(self, mol_id, refmol_id):
        userid = request.identity['repoze.who.userid']
        pname = request.environ['PATH_INFO'].split('/')[1]
        db_mol = DBSession.query(Compound).get(mol_id)
        db_refmol = DBSession.query(Compound).get(refmol_id)
        
        mol = Chem.MolFromSmiles(str(db_mol.structure))
        refmol = Chem.MolFromSmiles(str(db_refmol.structure))
        
        from rdkit import DataStructs
        from rdkit.Chem import AllChem
        
        fps_mol = AllChem.GetMorganFingerprint(mol, 2)
        fps_refmol = AllChem.GetMorganFingerprint(refmol, 2)
        similarity = DataStructs.TanimotoSimilarity(fps_mol, fps_refmol)
        
        from rdkit.Chem import Draw
        from rdkit.Chem.Draw import SimilarityMaps
        fig, maxweight = SimilarityMaps.GetSimilarityMapForFingerprint(refmol, mol, lambda m,idx: SimilarityMaps.GetMorganFingerprint(m, atomId=idx, radius=1, fpType='count'), metric=DataStructs.TanimotoSimilarity)
        filename = '%s_similarity_map.png' % userid
        filepath = os.path.join('../public/files/download/', filename)
        fig.savefig(filepath, bbox_inches='tight')
#        import paste.fileapp
#        f = paste.fileapp.FileApp(filepath)
#        from tg import use_wsgi_app
#        return use_wsgi_app(f)
        return dict(mol=db_mol, refmol=db_refmol, filename=filename, similarity=round(similarity*100, 2), page="molecules", pname=pname)

    @expose('molgears.templates.users.molecules.addgroup')
    def addgroup(self, *args, **kw):
        """
        Add new group to NameGroups.
            Target:
             - automatization in molecules naming
            DB relationship with Compound.
        """
        
        pname = request.environ['PATH_INFO'].split('/')[1]
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if kw:
            if u'come_from' in kw and kw['come_from'] != u'':
                come_from = kw['come_from']
                
            ngroup = NameGroups()
            
            if (u'prefix' not in kw and u'sufix' not in kw):
                flash(l_(u'Prefix or Sufix is required'), 'error')
                redirect(come_from)
            else:
                if u'prefix' in kw and kw['prefix'] != u'':
                    ngroup.prefix = kw['prefix']
                if u'sufix' in kw and kw['sufix'] != u'':
                    ngroup.sufix = kw['sufix']
            if u'precision' in kw and kw['precision'] != u'':
                try:
                    ngroup.precision = int(kw['precision'])
                except Exception as msg:
                    flash(l_(u'Presision should be an integer'), 'error')
                    redirect(come_from)
            else:
                ngroup.precision = 3
            ngroup.next = 1
            DBSession.add(ngroup)
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
                
        return dict(come_from=come_from, page='molecules', pname=pname)
        
        
    @expose('molgears.templates.users.molecules.editgroup')
    def editgroup(self, *args, **kw):
        """
        Edit group from NameGroups.
        """
        group_id = args[0]
        pname = request.environ['PATH_INFO'].split('/')[1]
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        ngroup = DBSession.query(NameGroups).get(group_id)
        if kw:
            if u'come_from' in kw and kw['come_from'] != u'':
                come_from = kw['come_from']
                
            
            if (u'prefix' not in kw and u'sufix' not in kw):
                flash(l_(u'Prefix or Sufix is required'), 'error')
                redirect(come_from)
            else:
                if u'prefix' in kw and kw['prefix'] != ngroup.prefix:
                    ngroup.prefix = kw['prefix']
                if u'sufix' in kw and kw['sufix'] != ngroup.sufix:
                    ngroup.sufix = kw['sufix']
            if u'precision' in kw and int(kw['precision']) != ngroup.precision:
                try:
                    ngroup.precision = int(kw['precision'])
                except Exception as msg:
                    flash(l_(u'Presision should be an integer'), 'error')
                    redirect(come_from)
            if u'next' in kw and kw['next'] != u'':
                try:
                    next = int(kw['next'])
                except Exception:
                    flash(l_(u'Float required'), 'error')
                    redirect('come_from')
                if next != ngroup.next:
                    ngroup.next = next
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
                
        return dict(come_from=come_from, ngroup=ngroup, page='molecules', pname=pname)
        
    @expose('molgears.templates.users.molecules.showgroups')
    def showgroups(self, *args, **kw):
        """
        Edit group from NameGroups.
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        
        ngroups = DBSession.query(NameGroups).order_by(NameGroups.id).all()
        return dict(come_from=come_from, ngroups=ngroups, page='molecules', pname=pname)

    @expose()
    def images(self):
        pname = request.environ['PATH_INFO'].split('/')[1]
       # recreate images for all structures
        for q in DBSession.query(Compound).order_by('gid')[:]:
            create_image(q.gid, q.structure, img_dir)
        flash('gotowe')
        redirect("/")
