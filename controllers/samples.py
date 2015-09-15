# -*- coding: utf-8 -*-
"""
Sample controller with all its actions protected.
"""
import tg
from tg import expose, flash, redirect, url, lurl, request
from tg.i18n import lazy_ugettext as l_
from molgears import model
from molgears.model import DBSession, PCompound, PHistory, PStatus, Tags, SCompound, SStatus, SFiles, SHistory, SPurity, LCompound
from molgears.model import Compound, Names, History, Efforts, User, Group, Projects, ResultsFP
from molgears.lib.base import BaseController
import transaction, os
from pkg_resources import resource_filename
from sqlalchemy import desc

from rdkit import Chem
from molgears.widgets.structure import checksmi
from datetime import datetime
from webhelpers import paginate
from tg.predicates import has_permission
from tg import cache

__all__ = ['SelectController']

#public_dirname = os.path.join(os.path.abspath(resource_filename('molgears', 'public')))
#img_dir = os.path.join(public_dirname, 'img')
#files_dir = os.path.join(public_dirname, 'files')

class SamplesController(BaseController):
    """Sample controller method"""
    
    @expose('molgears.templates.users.samples.index')
    def index(self, page=1, *args, **kw):
        """
        Index controller for molecules
        """
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        from sqlalchemy import or_
        compound = DBSession.query(Compound).filter(Compound.project.any(Projects.name==pname)).filter(or_(Compound.pcompounds != None, Compound.lcompounds != None))
        dsc = True
        tmpl = ''
        selection = None
        similarity = None
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        threshold = float(user.threshold)/100.0
        items = user.items_per_page
        order = "gid"
        try:
            if kw['search'] != u'':
                search_clicked = kw['search']
            else:
                search_clicked = None
        except Exception:
            search_clicked = None
        if kw:
            delkw = []
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
                        if method == 'similarity':
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
                            page_url = paginate.PageURL_WebOb(request)
                            currentPage = paginate.Page(compound, page, url=page_url, items_per_page=items)
                            return dict(length=len(compound), compound=currentPage.items, currentPage=currentPage, tmpl=tmpl, page='samples', pname=pname, alltags=alltags, similarity=similarity)
    
                        elif method == 'substructure':
                            constraint = Compound.structure.contains(smiles)
                            compound = DBSession.query(Compound).filter(constraint).filter(Compound.project.any(Projects.name==pname))
                        elif method == 'identity':
                            compound = DBSession.query(Compound).filter(Compound.structure.equals(smiles)).filter(Compound.project.any(Projects.name==pname))
                    else:
                        flash(l_(u'Smiles error'), 'warning')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_GID'])
                        compound = compound.filter_by(gid = gid )
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
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
                            redirect(request.headers['Referer'])
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
        
#                    import sqlalchemy
                    compound = compound.filter(Compound.tags.any(Tags.id.in_(tagi)))
                    
                    
        if selection and not search_clicked:
            argv =''
            for arg in selection:
                argv += '/' + arg
            if kw['akcja'] == u'edit':
                if len(selection) == 1:
                    redirect('/%s/samples/edit%s' % (pname, argv))
                else:
                    redirect('/%s/samples/multiedit/index%s' % (pname, argv))
            elif kw['akcja'] == u'accept':
                if len(selection) == 1:
                    redirect('/%s/samples/accept%s' % (pname, argv))
                else:
                    redirect('/%s/samples/multiaccept/index%s' % (pname, argv))
            elif kw['akcja'] == u'library':
                if len(selection) == 1:
                    redirect('/%s/samples/library%s' % (pname, argv))
                else:
                    redirect('/%s/samples/multilibrary/index%s' % (pname, argv))
            elif kw['akcja'] == u'pdf':
                redirect('/%s/samples/index/download%s/pdf/samples_selected.pdf' % (pname, argv))
            elif kw['akcja'] == u'xls':
                redirect('/%s/samples/download%s/xls/samples_selected.xls' % (pname, argv))
            elif kw['akcja'] == u'txt':
                redirect('/%s/samples/download%s/txt/samples_selected.txt' % (pname, argv))
            elif kw['akcja'] == u'delete':
                redirect('/%s/samples/remove%s' % (pname, argv))
            else:
                flash(l_(u'Action error'), 'error')
                redirect(request.headers['Referer'])
        else:
            try:
                akcja = kw['akcja']
            except Exception:
                akcja = None
            if akcja:
                if akcja == u'pdf':
                    redirect('/%s/samples/index/download/pdf/samples_all.pdf' % pname)
                elif akcja == u'xls':
                    redirect('/%s/samples/download/xls/samples_all.xls' % pname)
                elif akcja == u'txt':
                    redirect('/%s/samples/download/txt/samples_all.txt' % pname)
        if dsc:
            compound = compound.order_by(desc(order).nullslast())
        else:
            compound = compound.order_by((order))
        
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(compound, page, url=page_url, items_per_page=items)
        return dict(compound=currentPage.items, currentPage=currentPage, tmpl=tmpl, page='samples', pname=pname, alltags=alltags, similarity=similarity)
