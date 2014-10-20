# -*- coding: utf-8 -*-
from tg import expose, flash, require, url, lurl, request, redirect
from tg.predicates import has_permission
from tg.i18n import ugettext as _, lazy_ugettext as l_
from molgears import model
from molgears.controllers.secure import SecureController
from molgears.model import DBSession, Projects, User, Group, ProjectTests
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController
from molgears.lib.base import BaseController
from molgears.controllers.error import ErrorController
from molgears.controllers.molecules import MoleculesController
from molgears.controllers.select import SelectController
from molgears.controllers.synthesis import SynthesisController
from molgears.controllers.library import LibraryController
from molgears.controllers.results import ResultsController
from molgears.controllers.pains import PainsController
from molgears.controllers.myaccount import AccountController

__all__ = ['RootController']
class RootController(BaseController):
    """
The main controller for webpage.
It contains subcontrolers:

1. admin - for administration staff
2. error - handling error web pages
3. reagents - controler for managing reagents 
4. pains - controler for PAINS
5. myaccont - user accout settings controler
6. _lookup - iterative handlig project instance. Permission only for logged users it contains subcontrolers for subsites viewd as **/project_name/subsite_name**:
    
    * molecules - MoleculesController
    * select - SelectController
    * synthesis - SynthesisController
    * library - LibraryController
    * results - ResultsController
    """
    admin = AdminController(model, DBSession, config_type=TGAdminConfig)
    error = ErrorController()
    pains = PainsController()
    myaccount = AccountController()
    @expose('molgears.templates.index')
    def index(self):
        """
        Home page for not authorized users.
        """
        from tg.predicates import not_anonymous
        if not_anonymous():
            redirect('/start')
        return dict(page='index', pname=None)
        
    @expose('molgears.templates.start')
    def start(self):
        """
        Home page for authorized users.
        """
        from tg.predicates import not_anonymous
        if not not_anonymous():
            flash(l_(u'Permission is not sufficient for this user'), 'error')
            redirect('/')
        userid = request.identity['repoze.who.userid']
        projects = DBSession.query(Projects).order_by('id').all()
        user = DBSession.query(User).filter_by(user_name=userid).first()
        perms = list(user.permissions)
        perms = [p.permission_name for p in perms]
        flash(l_(u'Alpha version. Please send error reporting to: adrian.jasisnki@adamed.com.pl. \t\t :)'), 'warning')
        return dict(page='start', projects=projects, perms=perms, pname=None)

    @expose('chemdb.templates.login')
    def login(self, came_from=lurl('/start')):
        """Start the user login."""
        login_counter = request.environ.get('repoze.who.logins', 0)
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)

    @expose()
    def post_login(self, came_from=lurl('/start')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',
                params=dict(came_from=came_from, __logins=login_counter))
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose('molgears.templates.index')
    def post_logout(self, came_from):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.
        """
        came_from=lurl('/')
        flash(_('We hope to see you soon!'))
        return dict(page='index', pname=None, came_from=came_from)

    @expose('molgears.templates.jme_window')
    def jme_window(self, *args, **kw):
        """
        It servs JME Editor page for user.
        """
        try:
            smiles = str(args[0])
            mol = Chem.MolFromSmiles(smiles)
            from rdkit.Chem import AllChem
            AllChem.EmbedMolecule(mol)
            AllChem.UFFOptimizeMolecule(mol)
            AllChem.Compute2DCoords(mol)
            mol = Chem.MolToMolBlock(mol)
        except Exception:
            mol = None
            smiles = None
        return dict(mol = mol, smiles = smiles, page='molecules')
        
    @expose('molgears.templates.jsme')
    def jsme(self, *args, **kw):
        """
        It servs JSME Editor page for user.
        """
        try:
            from rdkit import Chem
            smiles = str(args[0])
            mol = Chem.MolFromSmiles(smiles)
            from rdkit.Chem import AllChem
            AllChem.EmbedMolecule(mol)
            AllChem.UFFOptimizeMolecule(mol)
            AllChem.Compute2DCoords(mol)
            mol = Chem.MolToMolBlock(mol)
        except Exception:
            mol = None
            smiles = None
        return dict(mol = mol, smiles = smiles, page='molecules')        
        
    @expose()
    def _lookup(self, project_name, *remainder):
        """
        Project instance lookup.
        """
        from tg.predicates import not_anonymous
        try:
            came_from = request.headers['Referer']
        except Exception:
            came_from = request.path_url
        if not not_anonymous():
            flash(l_('Permission is not sufficient for this user.'), 'error')
            redirect('/login?came_from=%s' % came_from)
        else:
            userid = request.identity['repoze.who.userid']
        if DBSession.query(Projects).filter(Projects.name==project_name).first():
            class UsersController(BaseController):
                """Subcontrollers for lookup.
                MAIN SITE FOR PROJECT INSTANCE.
                Parmission allowed only for logged user with added permision named as a project.
                """
                # The predicate that must be met for all the actions in this controller:
                allow_only = has_permission(project_name,
                                            msg=l_('Permission is not sufficient for this user.'))
                molecules = MoleculesController()
                select = SelectController()
                synthesis = SynthesisController()
                library = LibraryController()
                results = ResultsController()
                
                @expose('molgears.templates.users.index')
                def index(self):
                    """Main site for project."""
                    userid = request.identity['repoze.who.userid']    
                    projects = DBSession.query(Projects).all()
                    user = DBSession.query(User).filter_by(user_name=userid).first()
                    perms = [p.permission_name for p in list(user.permissions)]
                    return dict(page='index', userid=userid, projects=projects, perms=perms, pname=project_name)
            users = UsersController()
        else:
            users = ErrorController()
        return users, remainder
        
    @expose('molgears.templates.create_project')
    def create_project(self, *args, **kw):
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
            if kw.has_key('name') and kw['name'] != u'':
                #create new project:
                project = Projects()
                project.name = kw['name']
                #add group named as a project:
                gr = Group()
                gr.group_name = kw['name']
                gr.display_name = kw['name']
                gr.users.append(user)
                
                #add permission named as a project and assign it to group:
                from molgears.model import Permission
                perm = Permission()
                perm.permission_name = kw['name']
                perm.groups += [gr]
                #add description:
                if kw.has_key('description') and kw['description'] != u'':
                    project.description = kw['description']
                #add test and cell lines
                ptest = ProjectTests()
                ptest.name = 'CT'
                project.tests = [ptest]
                check_cell = True
                cell_lines = []
                for k, v in kw.iteritems():
                    if 'Cell_Line_' in str(k) and str(v) != '':
                        check_cell = False
                        cell_lines.append(str(v))

                if check_cell:
                    flash(l_(u'At least 1 Cell_Line is required'), 'error')
                    redirect(come_from)
                else:
                    if cell_lines:
                        import pickle
                        pickle_dump1 = pickle.dumps(cell_lines)
                        ptest.cell_line = pickle_dump1
                    else:
                        flash(l_(u'Cell Lines error'), 'error')
                        redirect(come_from)
                DBSession.add(perm)
                DBSession.add(gr)
                DBSession.add(ptest)
                DBSession.add(project)
                DBSession.flush()
                flash(l_(u'Task completed successfully'))
            else:
                flash(l_(u'Name and structure are required'), 'error')
                redirect(come_from)
        return dict(page='index', userid=userid)
        
    @expose('molgears.templates.create_tags')
    def create_tags(self, *args, **kw):
        """
        Create new project & group with correct permissions asigned.
        If you wish to allow users acces to the project- add them to group named as a project.
        """
        userid = request.identity['repoze.who.userid']
        from molgears.model import Tags
        try:
            come_from = request.headers['Referer']
        except Exception:
            come_from = request.path_url
        if kw:
            for k, v in kw.iteritems():
                if 'Tag_Name_' in str(k) and str(v) != '':
                    tag = Tags()
                    tag.name = str(v)
                    
                    DBSession.add(tag)
            DBSession.flush()
            flash(l_(u'Task completed successfully'))
            
        return dict(page='index', userid=userid)
