# -*- coding: utf-8 -*-
"""Setup the molgears application"""
from __future__ import print_function

import logging
from tg import config
from molgears import model
import transaction

def bootstrap(command, conf, vars):
    """Place any commands to setup molgears here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        u = model.User()
        u.user_name = 'manager'
        u.display_name = 'Example manager'
        u.email_address = 'manager@somedomain.com'
        u.password = 'managepass'
    
        model.DBSession.add(u)
    
        g = model.Group()
        g.group_name = 'managers'
        g.display_name = 'Managers Group'
    
        g.users.append(u)
    
        model.DBSession.add(g)
        
        g1 = model.Group()
        g1.group_name = 'users'
        g1.display_name = 'Users Group'
    
        g1.users.append(u)
    
        model.DBSession.add(g1)
        
        g2 = model.Group()
        g2.group_name = 'principals'
        g2.display_name = 'Principals Group'
    
        g2.users.append(u)
    
        model.DBSession.add(g2)
    
        p = model.Permission()
        p.permission_name = 'manage'
        p.description = 'This permission give an administrative right to the bearer'
        p.groups.append(g)
    
        model.DBSession.add(p)
    
        u1 = model.User()
        u1.user_name = 'editor'
        u1.display_name = 'Example editor'
        u1.email_address = 'editor@somedomain.com'
        u1.password = 'editpass'
        
        model.DBSession.add(u1)
        
        pstatus1 = model.PStatus()
        pstatus1.name = 'proposed'
        
        model.DBSession.add(pstatus1)
        
        pstatus2 = model.PStatus()
        pstatus2.name = 'accepted'
        
        model.DBSession.add(pstatus2)
        
        pstatus3 = model.PStatus()
        pstatus3.name = 'rejected'
        
        model.DBSession.add(pstatus3)
        
        sstatus1 = model.SStatus()
        sstatus1.name = 'pending'
        
        model.DBSession.add(sstatus1)
        
        sstatus2 = model.SStatus()
        sstatus2.name = 'synthesis'
        
        model.DBSession.add(sstatus2)
        
        sstatus3 = model.SStatus()
        sstatus3.name = 'finished'
        
        model.DBSession.add(sstatus3)
        
        sstatus4 = model.SStatus()
        sstatus4.name = 'received'
        
        model.DBSession.add(sstatus4)
        
        sstatus5 = model.SStatus()
        sstatus5.name = 'rejected'
        
        model.DBSession.add(sstatus5)
        
        sstatus6 = model.SStatus()
        sstatus6.name = 'discontinued'
        
        model.DBSession.add(sstatus6)
        
        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:
        print('Warning, there was a problem adding your auth data, it may have already been added:')
        import traceback
        print(traceback.format_exc())
        transaction.abort()
        print('Continuing with bootstrapping...')

    # <websetup.bootstrap.after.auth>
