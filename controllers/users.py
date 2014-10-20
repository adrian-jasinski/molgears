# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
import tg
from tg import expose, flash, redirect, request, url, lurl
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission
from molgears import model
from molgears.model import DBSession
from molgears.model import User
from molgears.lib.base import BaseController
import transaction
from molgears import model

from molgears.controllers.molecules import MoleculesController
from molgears.controllers.select import SelectController
from molgears.controllers.synthesis import SynthesisController
from molgears.controllers.library import LibraryController

__all__ = ['UsersController']

test = 'test'

# ----------- MAIN CONTROLLER ----------------------------------------------------------------------------------------------------------------------------------

class UsersController(BaseController):
    """Sample controller-wide authorization"""
    # The predicate that must be met for all the actions in this controller:
    allow_only = has_permission('user',
                                msg=l_('Permission is not sufficient for this user'))
    molecules = MoleculesController()
    select = SelectController()
    synthesis = SynthesisController()
    library = LibraryController()
    #select = SelectController(DBSession)
    
    @expose('molgears.templates.users.index')
    def index(self):
        """Let the user know that's visiting a protected controller."""
        #flash(_("Only for Users"))
        userid = request.identity['repoze.who.userid']
        return dict(page='index', userid=userid)
        
    @expose('molgears.templates.users.myaccount')
    def myaccount(self):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
        user = DBSession.query(User).filter(User.user_name == userid).first()
#        flash(u'Zapisanie zmian wymaga podania obecnego hasła.', 'warning')
        return dict(user=user, page='index')
        
    @expose()
    def save(self, *args, **kw):
        """Let the user know that's visiting a protected controller."""
        userid = request.identity['repoze.who.userid']
#        if not(userid == kw['name']):
#            flash(u'Zła nazwa użytkownika', 'error')
#            redirect(request.headers['Referer'])
        user = DBSession.query(User).filter(User.user_name == userid).first()
#        flash(kw)
        try:
            old = kw['old_password']
        except Exception:
            old = None
        try:
            new = kw['password']
            if not(new == kw['veryfie']):
                flash(l_(u'Password error'), 'error')
                redirect(request.headers['Referer'])
        except Exception:
            new = None
            flash(l_(u'Password error'), 'error')
            redirect(request.headers['Referer'])
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
                        redirect(request.headers['Referer'])
                if limit_sim and limit_sim != user.limit_sim:
                    if limit_sim >10 and limit_sim <50:
                        user.limit_sim = limit_sim
                    else:
                        flash(l_(u'Number of Compound per page should be between 10 and 150'), 'error')
                        redirect(request.headers['Referer'])
                if threshold and threshold != user.threshold:
                    if threshold >10 and threshold <50:
                        user.threshold = threshold
                    else:
                        flash(l_(u'Smililarity value should be between 10 and 50'), 'error')
                        redirect(request.headers['Referer'])
                if email and user.email_address != email:
                    import re
                    if len(email) > 7:
                        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
                            user.email_address = email
                        else:
                            flash(l_(u'Email error'), 'warning')
                            redirect(request.headers['Referer'])
                    else:
                        flash(l_(u'Email error'), 'warning')
                        redirect(request.headers['Referer'])
                else:
                    flash(l_(u'Email not changed'), 'warning')
                if new:
                    if len(new)>6:
                        user._set_password(new)
                    else:
                        flash(l_(u'Password error'), 'error')
                        redirect(request.headers['Referer'])
            else:
                flash(l_(u'Password verification error'), 'error')
                redirect(request.headers['Referer'])
        else:
            flash(l_(u'Current password required'), 'warning')
            redirect(request.headers['Referer'])
        flash(l_(u'Task completed successfully'))
        redirect(request.headers['Referer'])
