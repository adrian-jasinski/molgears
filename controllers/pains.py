# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
import tg
from tg import expose, flash, redirect, request
from tg.i18n import lazy_ugettext as l_
from molgears import model
from molgears.model import DBSession, PCompound, PHistory, PStatus, Tags, SCompound, SFiles, LCompound, LPurity, LHistory
from molgears.model import Compound, Names, History, User, Group, Projects, PAINS1, PAINS2, PAINS3
from molgears.lib.base import BaseController
import transaction, os
from pkg_resources import resource_filename
from sqlalchemy import desc, asc

from rdkit import Chem
from molgears.widgets.structure import create_image, addsmi, checksmi
from datetime import datetime
from webhelpers import paginate
#from tg.decorators import allow_only
from tg.predicates import has_permission
from tg import cache
__all__ = ['PainsController']

public_dirname = os.path.join(os.path.abspath(resource_filename('molgears', 'public')))
img_dir = os.path.join(public_dirname, 'img')
files_dir = os.path.join(public_dirname, 'files')
#pains1_dir = os.path.join(public_dirname, 'img/pains1')
class Pains1Controller(BaseController):
    @expose('molgears.templates.users.pains.pains1')
    def index(self, page=1, *args, **kw):
        pains = DBSession.query(PAINS1)
        dsc = True
        tmpl = ''
        pname = 'pains'
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        threshold = float(user.threshold)/100.0
        items = user.items_per_page
        order = "id"
        if kw:
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    order = v
        if dsc:
            pains = pains.order_by(desc(order).nullslast())
        else:
            pains = pains.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(pains, page, url=page_url, items_per_page=items)
        pains = pains.all()

        return dict(length=len(pains), pains=currentPage.items, currentPage=currentPage, tmpl=tmpl, page='pains1', pname=pname)
        
    @expose('molgears.templates.users.pains.details_p1')
    def details(self, id, **kw):
        id = int(id)
        pains = DBSession.query(PAINS1).get(id)
        return dict(pains=pains, page='pains1', pname = 'pains')
class Pains2Controller(BaseController):
    @expose('molgears.templates.users.pains.pains2')
    def index(self, page=1, *args, **kw):
        pains = DBSession.query(PAINS2)
        dsc = True
        tmpl = ''
        pname = 'pains'
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        threshold = float(user.threshold)/100.0
        items = user.items_per_page
        order = "id"
        if kw:
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    order = v
        if dsc:
            pains = pains.order_by(desc(order).nullslast())
        else:
            pains = pains.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(pains, page, url=page_url, items_per_page=items)
        pains = pains.all()

        return dict(length=len(pains), pains=currentPage.items, currentPage=currentPage, tmpl=tmpl, page='pains2', pname=pname)
        
    @expose('molgears.templates.users.pains.details_p2')
    def details(self, id, **kw):
        id = int(id)
        pains = DBSession.query(PAINS2).get(id)
        return dict(pains=pains, page='pains2', pname = 'pains')

class Pains3Controller(BaseController):
    @expose('molgears.templates.users.pains.pains3')
    def index(self, page=1, *args, **kw):
        pains = DBSession.query(PAINS3)
        dsc = True
        tmpl = ''
        pname = 'pains'
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        threshold = float(user.threshold)/100.0
        items = user.items_per_page
        order = "id"
        if kw:
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    order = v
        if dsc:
            pains = pains.order_by(desc(order).nullslast())
        else:
            pains = pains.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(pains, page, url=page_url, items_per_page=items)
        pains = pains.all()

        return dict(length=len(pains), pains=currentPage.items, currentPage=currentPage, tmpl=tmpl, page='pains3', pname=pname)
        
    @expose('molgears.templates.users.pains.details_p3')
    def details(self, id, **kw):
        id = int(id)
        pains = DBSession.query(PAINS3).get(id)
        return dict(pains=pains, page='pains3', pname = 'pains')
        
class PainsController(BaseController):
    pains1 = Pains1Controller()
    pains2 = Pains2Controller()
    pains3 = Pains3Controller()
    
    @expose('molgears.templates.users.pains.index')
    def index(self, page=1, *args, **kw):
        from sqlalchemy import or_
        tmpl = ''
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        items = user.items_per_page
        pname = 'pains'
        pains = DBSession.query(Compound).filter(or_(Compound.pains1.has(), Compound.pains2.has(), Compound.pains3.has())).order_by(desc('gid'))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(pains, page, url=page_url, items_per_page=items)
        return dict(page='pains', pname=pname, pains=currentPage.items, currentPage=currentPage, tmpl=tmpl)
        
    @expose()
    def check(self):
        compounds = DBSession.query(Compound).all()
        pains1 = DBSession.query(PAINS1).all()
        pains2 = DBSession.query(PAINS2).all()
        pains3 = DBSession.query(PAINS3).all()
        ID = ''
        for compound in compounds:
            m = Chem.MolFromSmiles(str(compound.structure))
            mol = Chem.AddHs(m)
            for p1 in pains1:
                patt = Chem.MolFromSmarts(str(p1.structure))
                if patt:
                    if mol.HasSubstructMatch(patt):
                        compound.pains1 = p1
                else:
                    flash(l_(u'Pattern error'), 'error')
                    redirect(request.headers['Referer'])
            for p2 in pains2:
                patt = Chem.MolFromSmarts(str(p2.structure))
                if patt:
                    if mol.HasSubstructMatch(patt):
                        compound.pains2 = p2
                else:
                    flash(l_(u'Pattern error'), 'error')
                    redirect(request.headers['Referer'])
            for p3 in pains3:
                patt = Chem.MolFromSmarts(str(p3.structure))
                if patt:
                    if mol.HasSubstructMatch(patt):
                        compound.pains3 = p3
                else:
                    flash(l_(u'Pattern error'), 'error')
                    redirect(request.headers['Referer'])
        flash(l_(u'Task completed successfully'))
        redirect(request.headers['Referer'])
