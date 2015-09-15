# -*- coding: utf-8 -*-\
from tg import expose, flash, request, redirect
#from tg.predicates import has_permission
from tg.i18n import lazy_ugettext as l_
from molgears.model import DBSession, Projects, User
from molgears.model.auth import UserLists
from molgears.lib.base import BaseController

__all__ = ['AccountController']


class AccountController(BaseController):
    from tg.predicates import not_anonymous
    allow_only = not_anonymous()
    
    @expose('molgears.templates.myaccount.index')
    def index(self):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
        return dict(user=user, page='index', pname=None)
    
    @expose('molgears.templates.myaccount.edit')
    def edit(self):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
        return dict(user=user, page='index', pname=None)
        
    @expose()
    def save(self, *args, **kw):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
        try:
            old = kw['old_password']
        except Exception:
            old = None
        try:
            new = kw['password']
            if not(new == kw['veryfie']):
                flash(l_(u'Password error'), 'error')
                redirect('/myaccount')
        except Exception:
            new = None
            flash(l_(u'Password error'), 'error')
            redirect('/myaccount')
        try:
            email = kw['email']
        except Exception:
            email = None
        try:
            items_per_page = int(kw['items_per_page'])
            limit_sim = int(kw['limit_sim'])
            threshold = int(kw['threshold'])
        except Exception:
            items_per_page = None
            limit_sim = None
            threshold = None
        if old:
            if user.validate_password(old):
                if items_per_page and items_per_page != user.items_per_page:
                    if items_per_page > 10 and items_per_page < 150:
                        user.items_per_page = items_per_page
                    else:
                        flash(l_(u'Number of Compound per page should be between 10 and 150'), 'error')
                        redirect('/myaccount')
                if limit_sim and limit_sim != user.limit_sim:
                    if limit_sim >10 and limit_sim <50:
                        user.limit_sim = limit_sim
                    else:
                        flash(l_(u'Number of Compound per page should be between 10 and 150'), 'error')
                        redirect('/myaccount')
                if threshold and threshold != user.threshold:
                    if threshold >10 and threshold <50:
                        user.threshold = threshold
                    else:
                        flash(l_(u'Similarity value should be between 10 and 50'), 'error')
                        redirect('/myaccount')
                if email and user.email_address != email:
                    import re
                    if len(email) > 7:
                        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
                            user.email_address = email
                        else:
                            flash(l_(u'Email error'), 'warning')
                            redirect('/myaccount')
                    else:
                        flash(l_(u'Email error'), 'warning')
                        redirect('/myaccount')
                else:
                    flash(l_(u'Email not changed'), 'warning')
                if new:
                    if len(new)>6:
                        user._set_password(new)
                    else:
                        flash(l_(u'Password error'), 'error')
                        redirect('/myaccount')
            else:
                flash(l_(u'Password verification error'), 'error')
                redirect('/myaccount')
        else:
            flash(l_(u'Current password required'), 'warning')
            redirect('/myaccount')
        flash(l_(u'Task completed successfully'))
        redirect('/myaccount')

    @expose('molgears.templates.myaccount.mylists')
    def mylists(self, page=1, *args, **kw):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
        mylists = user.lists
        import pickle as pcl
        dsc = True
        tmpl = ''
        selection = None
        order = "id"
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
        mylists = sorted(mylists, key=lambda list: list.__getattribute__(order))
        if dsc:
            mylists.reverse()
            
        if selection and not search_clicked:
            argv =''
            for arg in selection:
                argv += '/' + arg
            if kw['akcja'] == u'edit':
                if len(selection) == 1:
                    redirect('/myaccount/editlist%s' %argv)
                else:
                    flash(l_(u'Editing only one by one'), 'warning')
                    redirect(request.headers['Referer'])
            elif kw['akcja'] == u'delete':
                redirect('/myaccount/removelist%s' % argv)
            else:
                flash(l_(u'Action error'), 'error')
                redirect(request.headers['Referer'])

        return dict(mylists=mylists, pcl=pcl, page='index', tmpl=tmpl, pname=None)
        
    @expose('molgears.templates.myaccount.sharedlists')
    def sharedlists(self, page=1, *args, **kw):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        SharedLists = DBSession.query(UserLists).filter(UserLists.permitusers.any(User.user_name == userid)).all()
        import pickle as pcl
        dsc = True
        tmpl = ''
        selection = None
        order = "id"
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
        SharedLists = sorted(SharedLists, key=lambda list: list.__getattribute__(order))
        if dsc:
            SharedLists.reverse()
            
        if selection and not search_clicked:
            argv =''
            for arg in selection:
                argv += '/' + arg
            if kw['akcja'] == u'edit':
                if len(selection) == 1:
                    redirect('/myaccount/editlist%s' %argv)
                else:
                    flash(l_(u'Editing only one by one'), 'warning')
                    redirect(request.headers['Referer'])
            elif kw['akcja'] == u'delete':
                redirect('/myaccount/removelist%s' % argv)
            else:
                flash(l_(u'Action error'), 'error')
                redirect(request.headers['Referer'])
        return dict(SharedLists=SharedLists, tmpl=tmpl, pcl=pcl, page='index', pname=None)

    @expose('molgears.templates.myaccount.editlist')
    def editlist(self, *args, **kw):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
        users = DBSession.query(User).order_by(User.display_name).all()
        id = args[0]
        mylist = DBSession.query(UserLists).get(id)
        assert mylist.tg_user_id == user.user_id, u"Brak uprawnien edycji"
        if kw:
            if not (kw.has_key('name') and kw['name'] != u''):
                flash(l_(u'Name is required'), 'error')
            else:
                if kw.has_key('name') and kw['name'] != mylist.name:
                    mylist.name=kw['name']
#                if kw.has_key('table') and kw['table'] != mylist.table:
#                    mylist.table=kw['table']
                if kw.has_key('notes') and kw['notes'] != mylist.notes:
                    mylist.notes = kw['notes']
                if kw.has_key('permitusers') and kw['permitusers'] != u'':
                    if isinstance(kw['permitusers'], (list, tuple)):
                        permitusers = [usr for usr in users if usr.user_name in kw['permitusers']]
                    else:
                        permitusers = [usr for usr in users if usr.user_name == kw['permitusers']]
                    if permitusers != mylist.permitusers:
                        mylist.permitusers = permitusers
                DBSession.flush()
                flash(l_(u'Task completed successfully'))
                redirect(request.headers['Referer'])
        return dict(mylist=mylist, user=user, users=users, page='index', pname=None)
        
    @expose('molgears.templates.myaccount.addlist')
    def addlist(self, *args, **kw):        
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
        users = DBSession.query(User).order_by(User.display_name).all()
        allproj = DBSession.query(Projects).order_by('id').all()
        if args and len(args) >= 2:
            ntable = args[0]
            get_args = args[1:]
        else:
            ntable, get_args = [None, ()]
        if kw:
            if not (kw.has_key('name') and kw['name'] != u''):
                flash(l_(u'Name is required'), 'error')
                redirect(request.headers['Referer'])
            elif not (kw.has_key('table') and kw['table'] != u''):
                flash(l_(u'Table is required'), 'error')
                redirect(request.headers['Referer'])
            elif not (kw.has_key('project') and kw['project'] != u''):
                flash(l_(u'Project is required'), 'error')
                redirect(request.headers['Referer'])
            else:
                lista = UserLists()
                lista.name = kw['name']
                lista.table = kw['table']
                lista.pname = kw['project']
                if kw.has_key('notes') and kw['notes'] != u'':
                    lista.notes = kw['notes']
                if kw.has_key('permitusers') and kw['permitusers'] != u'':
                    if isinstance(kw['permitusers'], (list, tuple)):
                        permitusers = [usr for usr in users if usr.user_name in kw['permitusers']]
                    else:
                        permitusers = [usr for usr in users if usr.user_name == kw['permitusers']]
                    lista.permitusers = permitusers
                if kw.has_key('argv') and kw['argv'] != u'':
                    elements = []
                    for arg in kw['argv']:
                        elements.append(arg)
                    import pickle
                    lista.elements = pickle.dumps(elements)
                        
                user.lists.append(lista)
                DBSession.add(lista)
                DBSession.flush()
                flash(l_(u'Task completed successfully'))
                redirect(request.headers['Referer'])
        return dict(user=user, allproj=allproj, users=users, page='index', ntable=ntable, get_args=get_args, pname=None)

    @expose()
    def removelist(self, *args, **kw):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
        id = args[0]
        mylist = DBSession.query(UserLists).get(id)
        if mylist.tg_user_id != user.user_id:
            flash(l_(u'Permission denied'), 'error')
            redirect(request.headers['Referer'])
        assert mylist.tg_user_id == user.user_id, u"Brak uprawnien usuwania"
        if mylist:
            DBSession.delete(mylist)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(request.headers['Referer'])
        else:
            flash(l_(u'List is required'), 'warning')
            redirect(request.headers['Referer'])
        
    @expose()
    def add_to_list(self, *args, **kw):
        if args:
            listid = args[0]
#            table = args[1]
            ulist = DBSession.query(UserLists).get(listid)

            values = []
            if args[2:]:
                for arg in args[2:]:
                    values.append(arg)
            import pickle
            if ulist and ulist.elements and ulist.elements != u"":
                elements = pickle.loads(ulist.elements)
            else:
                elements = []
            new_elements = set(elements + values)
            ulist.elements = pickle.dumps(list(new_elements))
            flash(l_(u'Task completed successfully'))
            redirect(request.headers['Referer'])
        else:
            flash(l_(u'Args error'), 'error')
            redirect("/")
            
    @expose()
    def remove_from_list(self, *args, **kw):
        ulistid = args[0]
        ulist = DBSession.query(UserLists).get(ulistid)
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
        if (ulist in user.lists):
            if ulist.elements:
                import pickle
                elements = pickle.loads(ulist.elements)
                if args[1:]:
                    for arg in args[1:]:
                        elements.remove(arg)
                    ulist.elements = pickle.dumps(elements)
                    flash(l_(u'Task completed successfully'))
                    redirect(request.headers['Referer'])
                else:
                    flash(l_(u'Args error'), 'error')
                    redirect(request.headers['Referer'])
            else:
                flash(l_(u'List error'), 'error')
                redirect(request.headers['Referer'])
        else:
            flash(l_(u'Permission denied'), 'error')
            redirect(request.headers['Referer'])


