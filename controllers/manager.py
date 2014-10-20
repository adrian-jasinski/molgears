# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
import tg
from tg import expose, flash, tmpl_context, redirect, request, url, lurl
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission
from molgears import model
from molgears.model import DBSession, metadata, PCompound, PHistory, PStatus, Tags, SCompound, SStatus, SFiles, SHistory, SPurity, LCompound, LPurity, LHistory, Group, RHistory, Reagents
from molgears.model import Compound, Names, History, User, Projects
import transaction, os
from pkg_resources import resource_filename
from sqlalchemy import desc, asc
from molgears.lib.base import BaseController
from rdkit import Chem
from molgears.widgets.structure import create_image, addsmi, checksmi
from datetime import datetime

from tg.decorators import paginate, with_trailing_slash
from webhelpers import paginate

__all__ = ['ManagerController']

public_dirname = os.path.join(os.path.abspath(resource_filename('molgears', 'public')))
#img_dir = os.path.join(public_dirname, 'img')
files_dir = os.path.join(public_dirname, 'files')

# -------- SCompound controller ----------------------------------------------------------------------------------------------------------------------------------

class ManagerController(BaseController):
    allow_only = has_permission('kierownik',
                                msg=l_('Permission is not sufficient for this user'))

    @expose('molgears.templates.users.kierownik.index')
    def index(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        from datetime import timedelta
        now=datetime.now()
        one_day=timedelta(days=1)
        history = DBSession.query( History).filter(History.project.any(Projects.name==pname)).order_by(desc('History.id')).limit(20).all()
        phistory = DBSession.query( PHistory).filter(PHistory.project.any(Projects.name==pname)).order_by(desc('PHistory.id')).limit(20).all()
        shistory= DBSession.query( SHistory).filter(SHistory.project.any(Projects.name==pname)).order_by(desc('SHistory.id')).limit(20).all()
        lhistory= DBSession.query( LHistory).filter(LHistory.project.any(Projects.name==pname)).order_by(desc('LHistory.id')).limit(20).all()
        
        hist = history +phistory + shistory + lhistory
        hist = sorted(hist, key=lambda hist: hist.date, reverse=True)[0:30]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        items = user.items_per_page
        tmpl = ''
        dsc = True
        return dict(history=hist, tmpl=tmpl, one_day=one_day, now=now, page='kierownik', pname=pname)
        
    @expose('molgears.templates.users.kierownik.index')
    def index2(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        from datetime import timedelta
        now=datetime.now()
        one_day=timedelta(days=1)
        history = DBSession.query( History).order_by(desc('History.id')).limit(20).all()
        phistory = DBSession.query( PHistory).order_by(desc('PHistory.id')).limit(20).all()
        shistory= DBSession.query( SHistory).order_by(desc('SHistory.id')).limit(20).all()
        lhistory= DBSession.query( LHistory).order_by(desc('LHistory.id')).limit(20).all()
        rhistory= DBSession.query( RHistory).order_by(desc('RHistory.id')).limit(20).all()
        
        hist = history +phistory + shistory + lhistory + rhistory
        hist = sorted(hist, key=lambda hist: hist.date, reverse=True)[0:30]
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        items = user.items_per_page
        tmpl = ''
        dsc = True
        return dict(history=hist, tmpl=tmpl, one_day=one_day, now=now, page='kierownik', pname=pname)



#        return dict(page='kierownik', pname=pname)
        
#    @expose('molgears.templates.users.kierownik.details')
#    def details(self, id, **kw):
#        sid = int(id)
#        if sid != 0:
#            scompound = DBSession.query( SCompound ).get(sid)
#            if scompound:
#                return dict(scompound=scompound, page='kierownik')
#            else:
#                flash('Zwiazek nie istnieje.', 'warning')
#                redirect(request.headers['Referer'])
#        else:
#            flash('Zwiazek nie posiada pochodnej z tabeli syntezy. Dodano go recznie do biblioteki.', 'warning')
#            redirect(request.headers['Referer'])
#            
    @expose('molgears.templates.users.kierownik.edit')
    def edit(self, id):
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        id = int(id)
        scompound = DBSession.query( SCompound ).get(id)
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        etap_max = scompound.effort[-1].etap_max
        etap = scompound.effort[-1].etap
        principals = DBSession.query (Group).get(3)
        owners = DBSession.query (Group).get(2)
        come_from = request.headers['Referer']
        try:
            tags = [tag for tag in scompound.mol.tags]
        except Exception as msg:
            tags = [scompound.mol.tags]
            pass
        try:
            files = scompound.filename
        except Exception:
            files = None
            pass
        return dict(scompound=scompound, tags=tags, alltags=alltags, files=files, etap=etap, etap_max=etap_max, users=principals.users, owners=owners.users, come_from=come_from, page='kierownik', pname=pname)

    @expose()
    def put(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        sid = int(args[0])
        userid = request.identity['repoze.who.userid']
        scompound = DBSession.query(SCompound).get(sid)

        try:
            if isinstance(kw['text_tags'], basestring):
                tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
            else:
                tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
        except Exception as msg:
            flash(l_(u'Tags error: %s' %msg))
            redirect(request.headers['Referer'])
        
        shistory = SHistory()
        shistory.gid = scompound.mol.gid
        shistory.user = userid
        shistory.status = u'Edycja'
        schanges = u''
        try:
            reason = kw['reason']
        except Exception:
            reason = None
            pass
        if reason and reason != u'':
            schanges += u'UWAGA! niestandardowa zmiana z powodu:' + reason
            etap = int(kw['etap']) 
            etap_max = int(kw['etap_max'])
            if etap < etap_max:
                scompound.effort[-1].etap = etap
                scompound.effort[-1].etap_max = etap_max
                scompound.status = DBSession.query( SStatus ).get(2)
                schanges += u'; Bieżący etap: ' + str(etap)
                schanges += u'; Liczba etapow: ' + str(etap_max)
            else:
                flash(l_(u'Completed step must be smaller by 2 than the number of stages'), 'error')
                redirect(request.headers['Referer'])
#        scompound.status_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if kw.has_key('lso') and kw['lso'] != scompound.lso:
            scompound.lso = kw['lso']
            schanges += u'; LSO: ' + kw['lso']
        if kw.has_key('notes') and kw['notes'] != scompound.notes:
            scompound.notes = kw['notes']
            schanges += u';Notes: ' + kw['notes']
        try:
            filename = kw['loadfile'].filename
            import os
            filename = os.path.basename(filename)
        except Exception as msg:
            filename = None
            pass
        try:
            reaction_file = kw['reaction'].filename
            import os
            reaction_file = os.path.basename(reaction_file)
        except Exception as msg:
            reaction_file = None
            pass
        
        if kw['owner'] != scompound.owner:
            scompound.owner = kw['owner']
            schanges += u'; Wlasciciel:' + kw['owner']
        if kw['principal'] != scompound.principal:
            scompound.principal = kw['principal']
            schanges += u'; Odbiorca:' + kw['principal']
        if kw.has_key('priority') and kw['priority'] != u'':
            scompound.priority = int(kw['priority'])
            schanges += u'; Priorytet:' + kw['priority']
            pcompound = DBSession.query(PCompound).get(scompound.pid)
            if pcompound:
                pcompound.priority = int(kw['priority'])
                phistory = PHistory()
                phistory.project = pname
                phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                phistory.user = userid
                phistory.status = 'Priorytet'
                phistory.changes = u'Priority: ' + kw['priority']
                pcompound.history += [phistory]
                DBSession.add(phistory)

        if filename or reaction_file:
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
                schanges += u'; Plik: ' + filename + u' ( ' + newfilename + u' )'
                DBSession.add(sfile)
            if reaction_file:
                number2 = DBSession.query(SFiles).count() + 1
                newfilename2 = str(number2) + '_' + userid + '_' + str(sid) + '_' + reaction_file
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
                schanges += u'; Sciezka reakcji: ' + reaction_file + u' ( ' + newfilename2 + u' )'
                DBSession.add(reaction_sfile)
            shistory.changes = schanges
            scompound.history += [shistory]
    
            DBSession.add(shistory)
            DBSession.flush()
            #transaction.commit()
            scompound2 = DBSession.query(SCompound).get(sid)
            if filename:
                sfile2 = [sfile]
                sfile2 += scompound2.filename
                scompound2.filename = sfile2
            if reaction_file:
                reaction_sfile = [reaction_sfile]
#                reaction_sfile += scompound2.reaction
                scompound2.reaction = reaction_sfile
        else:
            shistory.changes = schanges
            scompound.history += [shistory]
            DBSession.add(shistory)
            DBSession.flush()
        
            flash(l_(u'Task completed successfully'))
        if kw and kw.has_key('come_from'):
            come_from = kw['come_from']
        else:
            come_from = request.headers['Referer']
        redirect(come_from)
    
    @expose('molgears.templates.users.kierownik.molecules')
    def molecules(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        history = DBSession.query( History ).filter(History.project.any(Projects.name==pname))
        order='id'
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
                        order = History.compound_id
                    elif v == 'user':
                        order = History.user
                    elif v == 'date':
                        order = History.date
                    else:
                        order = v
                if str(k) != 'remove':
                    tmpl += str(k) + '=' + str(v) + '&'
            if search_clicked:
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_gid'])
                        history = history.filter_by(gid = gid )
                    except Exception as msg:
                        flash(l_(u'GID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_user') and kw['text_user'] !=u'':
                    history = history.filter(History.user.like(kw['text_user'].replace('*', '%')))
                if kw.has_key('text_status') and kw['text_status'] !=u'':
                    history = history.filter(History.status.like(kw['text_status'].replace('*', '%')))
                if kw.has_key('text_changes') and kw['text_changes'] !=u'':
                    history = history.filter(History.changes.like(kw['text_changes'].replace('*', '%')))
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    history = history.filter(History.date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            history = history.filter(History.date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        history = history.filter(History.date < date_to)
        if dsc:
            history = history.order_by(desc(order).nullslast())
        else:
            history = history.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(history, page, url=page_url, items_per_page=items)
        return dict(history=currentPage.items, currentPage=currentPage, tmpl=tmpl, one_day=one_day, now=now, page='kierownik', pname=pname)
        
    @expose('molgears.templates.users.kierownik.select')
    def select(self, page=1, *args, **kw):
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
        return dict(history=currentPage.items, currentPage=currentPage, one_day=one_day, now=now, tmpl=tmpl, page='kierownik', pname=pname)
        
    @expose('molgears.templates.users.kierownik.synthesis')
    def synthesis(self, page=1, *args, **kw):
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
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
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
        return dict(history=currentPage.items, currentPage=currentPage, tmpl=tmpl, one_day=one_day, now=now, page='kierownik', pname=pname)

    @expose('molgears.templates.users.kierownik.library')
    def library(self, page=1, *args, **kw):
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
        return dict(history=currentPage.items, currentPage=currentPage, tmpl=tmpl, one_day=one_day, now=now, page='kierownik', pname=pname)
        
    @expose('molgears.templates.users.kierownik.reagents')
    def reagents(self, page=1, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        history = DBSession.query( RHistory ).filter(RHistory.project.any(Projects.name==pname))
        order='RHistory.id'
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
                        order = RHistory.reagents_id
                    elif v == 'user':
                        order = RHistory.user
                    elif v == 'date':
                        order = RHistory.date
                    else:
                        order = v
                if str(k) != 'remove':
                    tmpl += str(k) + '=' + str(v) + '&'
            if search_clicked:
                if kw.has_key('text_GID') and kw['text_GID'] !=u'':
                    try:
                        gid = int(kw['text_gid'])
                        history = history.filter(Reagents.rid == gid )
                    except Exception as msg:
                        flash(l_(u'ID should be a number: %s' % msg), 'error')
                        redirect(request.headers['Referer'])
                if kw.has_key('text_user') and kw['text_user'] !=u'':
                    history = history.filter(RHistory.user.like(kw['text_user'].replace('*', '%')))
                if kw.has_key('text_status') and kw['text_status'] !=u'':
                    history = history.filter(RHistory.status.like(kw['text_status'].replace('*', '%')))
                if kw.has_key('text_changes') and kw['text_changes'] !=u'':
                    history = history.filter(RHistory.changes.like(kw['text_changes'].replace('*', '%')))
                if kw.has_key('date_from') and kw['date_from'] !=u'':
                    date_from = datetime.strptime(str(kw['date_from']), '%Y-%m-%d')
                    history = history.filter(RHistory.date > date_from)
                else:
                    date_from = None
                if kw.has_key('date_to') and kw['date_to'] !=u'':
                    date_to = datetime.strptime(str(kw['date_to']), '%Y-%m-%d')
                    if date_from:
                        if date_to>date_from:
                            history = history.filter(RHistory.date < date_to)
                        else:
                            flash(l_(u'The End date must be later than the initial'), 'error')
                            redirect(request.headers['Referer'])
                    else:
                        history = history.filter(RHistory.date < date_to)
        if dsc:
            history = history.order_by(desc(order).nullslast())
        else:
            history = history.order_by((order))
        page_url = paginate.PageURL_WebOb(request)
        currentPage = paginate.Page(history, page, url=page_url, items_per_page=items)
        return dict(history=currentPage.items, currentPage=currentPage, tmpl=tmpl, one_day=one_day, now=now, page='kierownik', pname=pname)

    @expose('molgears.templates.users.kierownik.tags')
    def tags(self, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        userid = request.identity['repoze.who.userid']
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        if kw:
            try:
                usun = kw['button1']
            except Exception:
                usun = None
            if usun:
                try:
                    if isinstance(kw['deltags'], basestring):
                        tagi = [DBSession.query( Tags ).get(int(kw['deltags']))]
                    else:
                        tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['deltags']]
                except Exception as msg:
                    tagi = None
                if tagi:
                    for tag in tagi:
                        for compound in DBSession.query(Compound).all():
                            if tag in compound.tags:
                                compound.tags.remove(tag)
                                history = History()
                                history.user = userid
                                history.status = u'Usuwanie tagu'
                                history.changes = u'Usunieto tag %s ' % tag.name
                                compound.history += [history]
                                DBSession.add(history)
                        DBSession.delete(tag)
                        DBSession.flush()
                    flash(l_(u'Task completed successfully'))
                    alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
            else:
                try:
                    if kw['addtag'] != '':
                        tagname = kw['addtag']
                    else:
                        tagname = None
                except Exception:
                    tagname = None
                if tagname:
                    tag = Tags()
                    tag.name = tagname
                    flash(l_(u'Task completed successfully'))
                    DBSession.add(tag)
                    DBSession.flush()
                    alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
                else:
                    flash(l_(u'Name required'), 'warning')
        return dict(alltags=alltags, page='kierownik', pname=pname)

    @expose('molgears.templates.users.kierownik.multiedit')
    def multiedit(self, *args, **kw):
        pname = request.environ['PATH_INFO'].split('/')[1]
        project = DBSession.query(Projects).filter(Projects.name==pname).first()
        alltags =[tag for tag in DBSession.query(Tags).order_by('name').all() ]
        principals = DBSession.query (Group).get(3)
        owners = DBSession.query (Group).get(2)
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
            try:
                priority = int(kw['priority'])
            except Exception:
                priority = None
            if argv:
                userid = request.identity['repoze.who.userid']
                for arg in argv:
                    try:
                        if isinstance(kw['text_tags'], basestring):
                            tagi = [DBSession.query( Tags ).get(int(kw['text_tags']))]
                        else:
                            tagi = [DBSession.query( Tags ).get(int(id)) for id in kw['text_tags']]
                    except Exception as msg:
                        tagi = None
                    scompound = DBSession.query(SCompound).get(int(arg))
                    shistory = SHistory()
                    shistory.gid = scompound.mol.gid
                    shistory.user = userid
                    shistory.status = u'Multi - edit'
                    shistory.changes = u''
                    if kw.has_key('owner') and kw['owner'] != u'None' and kw['owner'] != scompound.owner:
                        scompound.owner = kw['owner']
                        shistory.changes += u' Właściciel: ' + kw['owner'] + ';'
                    if kw.has_key('principal') and kw['principal'] != u'None' and kw['principal'] != scompound.principal:
                        scompound.principal = kw['principal']
                        shistory.changes += u' Odbiorca: ' + kw['principal'] + ';'
                    if priority and priority != scompound.priority:
                        scompound.priority = int(kw['priority'])
                        shistory.changes += u'; Priorytet: ' + kw['priority'] + ';'
                        pcompound = DBSession.query(PCompound).get(scompound.pid)
                        if pcompound:
                            pcompound.priority = int(kw['priority'])
                            phistory = PHistory()
                            phistory.project = pname
                            phistory.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            phistory.user = userid
                            phistory.status = 'Priorytet'
                            phistory.changes = u'Priority: ' + kw['priority']
                            pcompound.history += [phistory]
                            DBSession.add(phistory)
                    if tagi and scompound.mol.tags != tagi:
                        scompound.mol.tags = tagi
                        shistory.changes += u' Tags: '
                        for tag in tagi:
                            shistory.changes += str(tag.name) + ';'
                    if notes and notes != scompound.notes:
                        scompound.notes = notes
                        shistory.changes += u' Notes: ' + notes
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
                
        return dict(alltags=alltags, args=args, users=principals.users, owners=owners.users, come_from=come_from, page='kierownik', pname=pname)
                    
#    @expose()
#    def test(self, page=1, *args, **kw):
#        pname = request.environ['PATH_INFO'].split('/')[1]
#        history = DBSession.query( LHistory ).all()
#        for h in history:
#            if h.lcompound_id:
#                lcompound = DBSession.query(LCompound).get(h.lcompound_id)
#                h.gid = lcompound.mol.gid
#        flash('ok')
#        redirect(request.headers['Referer'])
        
#    @expose()
#    def test2(self, page=1, *args, **kw):
#        pname = request.environ['PATH_INFO'].split('/')[1]
#        history = DBSession.query( RHistory ).all()
#        project = DBSession.query(Projects).filter(Projects.name==pname).first()
#        project1 = DBSession.query(Projects).filter(Projects.name=='MDM').first()
#        for h in history:
#            if not h.project:
#                r = DBSession.query(Reagents).filter_by(rid=h.reagents_id).first()
#                if r:
#                    h.project = r.project
#                else:
#                    if h.user == 'marcin.kolaczkowski':
#                        h.project = [project]
#                    else:
#                        h.project = [project1]
#        flash('ok')
#        redirect(request.headers['Referer'])
