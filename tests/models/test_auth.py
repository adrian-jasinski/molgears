# -*- coding: utf-8 -*-
"""Test suite for the TG app's models"""
from __future__ import unicode_literals
from nose.tools import eq_

from molgears import model
from molgears.tests.models import ModelTest

class TestGroup(ModelTest):
    """Unit test case for the ``Group`` model."""
    klass = model.Group
    attrs = dict(
        group_name = "test_group",
        display_name = "Test Group"
        )

    def test_obj_creation_group(self):
        """The obj constructor must set the user name right"""
        eq_(self.obj.group_name, "test_group")
        eq_(self.obj.display_name, "Test Group")
        
    def test_no_users_by_default(self):
        """User objects should have no permission by default."""
        eq_(len(self.obj.users), 0)
        
class TestUser(ModelTest):
    """Unit test case for the ``User`` model."""
    
    klass = model.User
    attrs = dict(
        user_name = "ignucius",
        email_address = "ignucius@example.org", 
        display_name  = "Ignucius"
        )

    def test_obj_creation_username(self):
        """The obj constructor must set the user name right"""
        eq_(self.obj.user_name, "ignucius")
        eq_(self.obj.display_name, "Ignucius")

    def test_default_values_set_in_user(self):
        """The obj constructor must set the user name right"""
        eq_(self.obj.items_per_page, 30)
        eq_(self.obj.limit_sim, 30)
        eq_(self.obj.threshold, 35)
        eq_(self.obj.lists, []) #empty list by default

    def test_obj_creation_email(self):
        """The obj constructor must set the email right"""
        eq_(self.obj.email_address, "ignucius@example.org")

    def test_no_permissions_by_default(self):
        """User objects should have no permission by default."""
        eq_(len(self.obj.permissions), 0)

    def test_getting_by_email(self):
        """Users should be fetcheable by their email addresses"""
        him = model.User.by_email_address("ignucius@example.org")
        eq_(him, self.obj)
        
    def test_getting_by_user_name(self):
        """Users should be fetcheable by their email addresses"""
        him = model.User.by_user_name("ignucius")
        eq_(him, self.obj)


class TestPermission(ModelTest):
    """Unit test case for the ``Permission`` model."""
    
    klass = model.Permission
    attrs = dict(
        permission_name = "test_permission",
        description = "This is a test Description"
        )

    def test_obj_creation_permission(self):
        """The obj constructor must set the user name right"""
        eq_(self.obj.permission_name, "test_permission")
        eq_(self.obj.description, "This is a test Description")
        
    def test_no_groups_by_default(self):
        """User objects should have no permission by default."""
        eq_(len(self.obj.groups), 0)
        
        
