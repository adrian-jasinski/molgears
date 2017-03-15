# -*- coding: utf-8 -*-\
from tg import expose, request, flash, redirect, require
from tg.predicates import Any, is_user, has_permission
from tg.i18n import lazy_ugettext as l_
#from tg.predicates import has_permission
from molgears.model import DBSession, User, Projects, Tags, Group, Permission, ProjectTests
from molgears.lib.base import BaseController
try:
    from webhelpers import paginate
except ImportError:
    from tg.decorators import paginate
from sqlalchemy import desc
from tgext.admin.tgadminconfig import BootstrapTGAdminConfig as TGAdminConfig
from tgext.admin.controller import AdminController
from tgext.crud import EasyCrudRestController

from molgears import model

try:
    from tg.predicates import in_group
except ImportError:
    from repoze.what.predicates import in_group


class TagsController(EasyCrudRestController):
    model = Tags
    title = "Tags"

    __form_options__ = {
        '__hide_fields__':['id'],
        '__field_order__':['id', 'name'], 
    }


class MyAdminController(BaseController):
    admin = AdminController(model, DBSession, config_type=TGAdminConfig)
    allow_only = in_group('managers')
    tags = TagsController(DBSession)

    @expose('molgears.templates.myadmin.index')
    def index(self):
        """
        Main page for admin controller
        """
#        userid = request.identity['repoze.who.userid']
        return dict(page='index', pname=None)

    @expose('molgears.templates.myadmin.users')
    def users(self, page=1, *args, **kw):
        """
        Users Managment.
        """
        users = DBSession.query(User)
        page_url = paginate.PageURL_WebOb(request)
        tmpl = ''
        dsc = True
        order = 'user_id'
        if kw:
            if 'desc' in kw and kw['desc'] != u'':
                if kw['desc'] != u'1':
                    dsc = False
            if 'order_by' in kw and kw['order_by'] != u'':
                order = kw['order_by']
        if dsc:
            users = users.order_by(desc(order).nullslast())
        else:
            users = users.order_by((order))
            
        currentPage = paginate.Page(users, page, url=page_url, items_per_page=30)
        return dict(page='index', currentPage=currentPage, tmpl=tmpl, pname=None)
        
    @require(Any(is_user('manager'), has_permission('manage'), msg='Permission denied'))
    @expose('molgears.templates.myadmin.new_user')
    def new_user(self, *args, **kw):
        """
        Add new User.
        """
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        groups = DBSession.query(Group).all()
        if kw:
            if 'come_from' in kw and kw['come_from'] != u'':
                come_from = kw['come_from']
            if 'password' in kw and kw['password'] != u'':                        
                new = kw['password']
                if 'verification' in kw and kw['verification'] != u'' and new != kw['verification']:
                    flash(l_(u'Password not match'), 'error')
                    redirect(come_from)
                else:
                    flash(l_('Verification error'), 'error')
            else:
                flash(l_(u'Password is required'), 'error')
                redirect(come_from)
            if 'email' in kw and kw['email'] != u'':
                email = kw['email']
            else:
                flash(l_('Email is required'), 'error')
                redirect(come_from)
            if 'items_per_page' in kw and kw['items_per_page'] !=u'':
                try:
                    items_per_page = int(kw['items_per_page'])
                except Exception:
                    flash(l_('Compounds per page should be a number'), 'error')
            else:
                flash(l_('Compounds per page required'), 'error')
                redirect(come_from)                    
            if 'user_name' in kw and kw['user_name'] !=u'':
                user = User()
                user.user_name = kw['user_name'].strip().replace(' ', '.')
            else:
                flash(l_('User name is required'), 'error')
                redirect(come_from)
            if 'display_name' in kw and kw['display_name'] !=u'':
                user.display_name = kw['display_name']
            if 'groups' in kw and kw['groups'] != u'':
                if isinstance(kw['groups'], basestring):
                    groups = [DBSession.query(Group).get(kw['groups'])]
                else:
                    groups = [DBSession.query(Group).get(group_id) for group_id in kw['groups']]
            else:
                flash(l_('Group is required'), 'error')
                redirect(come_from)
            if items_per_page:
                if items_per_page > 10 and items_per_page < 150:
                    user.items_per_page = items_per_page
                else:
                    flash(l_(u'Number of Compound per page should be between 10 and 150'), 'error')
                    redirect(come_from)
            if email:
                import re
                if len(email) >= 6:
                    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
                        user.email_address = email
                    else:
                        flash(l_(u'Email error'), 'warning')
                        redirect(come_from)
                else:
                    flash(l_(u'Email error'), 'warning')
                    redirect(come_from)
            else:
                flash(l_(u'Email not changed'), 'warning')
            if new:
                if len(new)>=6:
                    user._set_password(new)
                else:
                    flash(l_(u'Password error'), 'error')
                    redirect(come_from)
            else:
                flash(l_('Password is required'), 'error')
                redirect(come_from)
            if groups:
                for group in groups:
                    group.users.append(user)
            else:
                flash(l_('Gropus error'), 'error')
                redirect(come_from)
            DBSession.add(user)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        return dict(page='index', come_from=come_from, groups=groups, pname=None)
        
    @require(Any(is_user('manager'), has_permission('manage'), msg='Permission denied'))
    @expose('molgears.templates.myadmin.edit_user')
    def edit_user(self, *args, **kw):
        """
        Edit User record.
        """
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        groups = DBSession.query(Group).order_by('group_id').all()
        try:
            user_id = args[0]
        except Exception:
            redirect("/error")
        user = DBSession.query(User).get(user_id)
        if kw:
            if 'come_from' in kw and kw['come_from'] != u'':
                come_from = kw['come_from']
            if 'password' in kw and kw['password'] != u'':                        
                new = kw['password']
                if 'verification' in kw and kw['verification'] != u'' and new != kw['verification']:
                    flash(l_(u'Password not match'), 'error')
                    redirect(come_from)
            else:
                new = None
            if 'email' in kw and kw['email'] != u'':
                email = kw['email']
            else:
                flash(l_('Email is required'), 'error')
                redirect(come_from)
            if 'items_per_page' in kw and kw['items_per_page'] !=u'':
                try:
                    items_per_page = int(kw['items_per_page'])
                except Exception:
                    flash(l_('Compounds per page should be a number'), 'error')
            else:
                flash(l_('Compounds per page required'), 'error')
                redirect(come_from)                    
            if 'user_name' in kw and kw['user_name'] !=u'':
                if kw['user_name'] != user.user_name:
                    user.user_name = kw['user_name']
            else:
                flash(l_('User name is required'), 'error')
                redirect(come_from)
            if 'display_name' in kw and kw['display_name'] !=u'' and kw['display_name'] != user.display_name:
                user.display_name = kw['display_name']
            if 'groups' in kw and kw['groups'] != u'':
                if isinstance(kw['groups'], basestring):
                    groups = [DBSession.query(Group).get(kw['groups'])]
                else:
                    groups = [DBSession.query(Group).get(group_id) for group_id in kw['groups']]
            else:
                flash(l_('Group is required'), 'error')
                redirect(come_from)
            if items_per_page:
                if items_per_page > 10 and items_per_page < 150:
                    if user.items_per_page != items_per_page:
                        user.items_per_page = items_per_page
                else:
                    flash(l_(u'Number of Compound per page should be between 10 and 150'), 'error')
                    redirect(come_from)
            if email:
                import re
                if len(email) >= 6:
                    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
                        if email != user.email_address:
                            user.email_address = email
                    else:
                        flash(l_(u'Email error'), 'warning')
                        redirect(come_from)
                else:
                    flash(l_(u'Email error'), 'warning')
                    redirect(come_from)
            if new:
                if len(new)>=6:
                    user._set_password(new)
                else:
                    flash(l_(u'Password error'), 'error')
                    redirect(come_from)
            if groups:
                for group in groups:
                    if user not in group.users:
                        group.users.append(user)
                for ugroup in user.groups:
                    if ugroup not in groups:
                        ugroup.users.remove(user)
            else:
                flash(l_('Gropus error'), 'error')
                redirect(come_from)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            redirect(come_from)
        return dict(page='index', come_from=come_from, groups=groups, user=user, pname=None)
        
    @require(Any(is_user('manager'), has_permission('manage'), msg='Permission denied'))
    @expose('')
    def delete_user(self, *args, **kw):
        try:
            user_id = args[0]
        except Exception:
            redirect("/error")
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        user = DBSession.query(User).get(user_id)
        if user:
            for group in user.groups:
                group.users.remove(user)
            DBSession.delete(user)
        else:
            flash(l_(u'User error'), 'error')
            redirect(come_from)
            
        flash(l_(u'Task completed successfully'))
        redirect(come_from)
        

    @expose('molgears.templates.myadmin.projects')
    def projects(self, page=1, *args, **kw):
        """
        Projects Managment.
        """
        projects = DBSession.query(Projects)
        page_url = paginate.PageURL_WebOb(request)
        tmpl = ''
        dsc = True
        order = 'id'
        if kw:
            if 'desc' in kw and kw['desc'] != u'':
                if kw['desc'] != u'1':
                    dsc = False
            if 'order_by' in kw and kw['order_by'] != u'':
                order = kw['order_by']
        if dsc:
            projects = projects.order_by(desc(order).nullslast())
        else:
            projects = projects.order_by((order))
            
        currentPage = paginate.Page(projects, page, url=page_url, items_per_page=30)
        return dict(page='index', currentPage=currentPage, tmpl=tmpl, pname=None)
        
    @expose('molgears.templates.myadmin.new_project')
    @require(Any(is_user('manager'), has_permission('manage'),
                 msg='Permission denied'))
    def new_project(self, *args, **kw):
        """
        Create new project & group with correct permissions asigned.
        If you wish to allow users acces to the project- add them to group named as a project.
        """
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter_by(user_name=userid).first()
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if kw:
            if 'come_from' in kw and kw['come_from'] != u'':
                come_from = kw['come_from']
            if 'name' in kw and kw['name'] != u'':
                cell_lines = []
                fp_lines = []
                htrf_lines = []
                for k, v in kw.iteritems():
                    if 'Cell_Line_' in str(k) and v != u'':
                        cell_lines.append(v.strip().replace(' ', '_'))
                    if 'FP_Line_' in str(k) and v != u'':
                        fp_lines.append(v.strip().replace(' ', '_'))
                    if 'HTRF_Line_' in str(k) and v != u'':
                        htrf_lines.append(v.strip().replace(' ', '_'))
                    
                if not cell_lines:
                    flash(l_(u'At least 1 Cell_Line is required'), 'error')
                    redirect(come_from)
                if not fp_lines:
                    flash(l_(u'At least 1 FP_Line is required'), 'error')
                    redirect(come_from)
                if not htrf_lines:
                    flash(l_(u'At least 1 HTRF_Line is required'), 'error')
                    redirect(come_from)
                #create new project:
                project = Projects()
                project.name = kw['name'].strip().replace(' ', '_')
                #add group named as a project:
                gr = Group()
                gr.group_name = kw['name'].strip().replace(' ', '_')
                gr.display_name = kw['name']
                gr.users.append(user)
                
                #add permission named as a project and assign it to group:
                from molgears.model import Permission
                perm = Permission()
                perm.permission_name = kw['name'].strip().replace(' ', '_')
                perm.groups += [gr]
                #add description:
                if 'description' in kw and kw['description'] != u'':
                    project.description = kw['description']
                #add test and cell lines
                ptest = ProjectTests()
                ptest.name = 'CT'
                
                fp_ptest = ProjectTests()
                fp_ptest.name = 'FP'
                htrf_ptest = ProjectTests()
                htrf_ptest.name = 'HTRF'
                project.tests = [fp_ptest, ptest, htrf_ptest]
                import pickle
                if cell_lines:
                    pickle_dump1 = pickle.dumps(cell_lines)
                    ptest.cell_line = pickle_dump1
                if fp_lines:
                    pickle_dump2 = pickle.dumps(fp_lines)
                    fp_ptest.cell_line = pickle_dump2
                if htrf_lines:
                    pickle_dump3 = pickle.dumps(htrf_lines)
                    htrf_ptest.cell_line = pickle_dump3
                DBSession.add(perm)
                DBSession.add(gr)
                DBSession.add(ptest)
                DBSession.add(fp_ptest)
                DBSession.add(project)
                DBSession.flush()
                flash(l_(u'Task completed successfully'))
                redirect(come_from)
            else:
                flash(l_(u'Name is required'), 'error')
                redirect(come_from)
        return dict(page='index', userid=userid, come_from=come_from)
        
    @expose('molgears.templates.myadmin.edit_project')
    @require(Any(is_user('manager'), has_permission('manage'),
                 msg='Permission denied'))
    def edit_project(self, *args, **kw):
        """
        Edit Project.
        If you wish to allow users acces to the project- add them to group named as a project.
        """
        try:
            project_id = args[0]
        except:
            redirect("error")
        userid = request.identity['repoze.who.userid']
#        user = DBSession.query(User).filter_by(user_name=userid).first()
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        try:
            project = DBSession.query(Projects).get(project_id)
        except:
            flash("Project not exist", "error")
            redirect(come_from)
        if kw:
            if 'come_from' in kw and kw['come_from'] != u'':
                come_from = kw['come_from']
            if 'name' in kw and kw['name'] != u'':
                fp_lines = []
                ct_lines = []
                htrf_lines = []
                for k, v in kw.iteritems():
                    if 'FP_Line_' in str(k) and v != u'':
                        fp_lines.append(v)
                    if 'CT_Line_' in str(k) and v != u'':
                        ct_lines.append(v)
                    if 'HTRF_Line_' in str(k) and v != u'':
                        htrf_lines.append(v)
                if 'CT_Old_Line' in kw and kw['CT_Old_Line'] != u'':
                    if isinstance(kw['CT_Old_Line'], basestring):
                        if kw['CT_Old_Line'] != u'':
                            ct_lines.append(kw['CT_Old_Line'])
                    else:
                        ct_lines += [cell for cell in kw['CT_Old_Line'] if cell != u'']
                if 'FP_Old_Line' in kw and kw['FP_Old_Line'] != u'':
                    if isinstance(kw['FP_Old_Line'], basestring):
                        if kw['FP_Old_Line'] != u'':
                            fp_lines.append(kw['FP_Old_Line'])
                    else:
                        fp_lines += [cell for cell in kw['FP_Old_Line'] if cell != u'']
                if 'HTRF_Old_Line' in kw and kw['HTRF_Old_Line'] != u'':
                    if isinstance(kw['HTRF_Old_Line'], basestring):
                        if kw['HTRF_Old_Line'] != u'':
                            htrf_lines.append(kw['HTRF_Old_Line'])
                    else:
                        htrf_lines += [cell for cell in kw['HTRF_Old_Line'] if cell != u'']
                if not ct_lines:
                    flash(l_(u'At least 1 CT_Line is required'), 'error')
                    redirect(come_from)
                if not fp_lines:
                    flash(l_(u'At least 1 FP_Line is required'), 'error')
                    redirect(come_from)
                if not htrf_lines:
                    flash(l_(u'At least 1 HTRF_Line is required'), 'error')
                    redirect(come_from)
                #edit project name:
                if project.name != kw['name']:

                    #change group name:
                    gr = DBSession.query(Group).filter_by(group_name=project.name).first()
                    gr.group_name = kw['name']
                    gr.display_name = kw['name']
                    
                    #change permission name:
                    perm = DBSession.query(Permission).filter(Permission.permission_name==project.name).first()
                    perm.permission_name = kw['name']
                    
                    project.name = kw['name']
                #add description:
                if 'description' in kw and kw['description'] != u'' and kw['description'] != project.description:
                    project.description = kw['description']
                #add cell lines
                import pickle
                if ct_lines:
                    pickle_dump1 = pickle.dumps(ct_lines)
                    ct_test = [test for test in project.tests if test.name == 'CT'][0]
                    ct_test.cell_line = pickle_dump1
                if fp_lines:
                    pickle_dump2 = pickle.dumps(fp_lines)
                    fp_test = [test for test in project.tests if test.name == 'FP'][0]
                    fp_test.cell_line = pickle_dump2
                if htrf_lines:
                    pickle_dump3 = pickle.dumps(htrf_lines)
                    htrf_test = [test for test in project.tests if test.name == 'HTRF'][0]
                    htrf_test.cell_line = pickle_dump3

                DBSession.flush()
                flash(l_(u'Task completed successfully'))
                redirect(come_from)
            else:
                flash(l_(u'Name is required'), 'error')
                redirect(come_from)
        return dict(page='index', userid=userid, project=project, come_from=come_from)
        
    @require(Any(is_user('manager'), has_permission('manage'), msg='Permission denied'))
    @expose('')
    def delete_project(self, *args, **kw):
        try:
            project_id = args[0]
        except Exception:
            redirect("/error")
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        project = DBSession.query(Projects).get(project_id)
        if project:
            DBSession.delete(project)
        else:
            flash(l_(u'Project error'), 'error')
            redirect(come_from)
            
        flash(l_(u'Task completed successfully'))
        redirect(come_from)
        
