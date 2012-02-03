# coding: utf-8
#
# Copyright (c) 2010, Logica
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright 
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <ORGANIZATION> nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
# Created on 17 May 2011
# @author parthiban ramasamy
import re
from datetime import datetime
from genshi.filters.transform import Transformer
from genshi.template.loader import TemplateLoader
from pkg_resources import resource_filename
from trac.util.datefmt import to_utimestamp, utc
from trac.config import Option
from trac.perm import PermissionSystem
from trac.admin import *
from trac.core import *
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.main import IRequestFilter
from trac.env import IEnvironmentSetupParticipant
from trac.db.api import DatabaseManager
from trac.web.chrome import ITemplateProvider, add_javascript, add_stylesheet, Chrome
from trac.util.translation import _
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import Chrome, add_notice, add_warning
from model import DisclaimerModel, UserDisclaimerModel
from trac.util.compat import sha1

__all__ = ['Disclaimer']

class Disclaimer(Component):
    implements(ITemplateStreamFilter, IRequestHandler, IAdminPanelProvider,
               IEnvironmentSetupParticipant, ITemplateProvider)

    c_version = Option("disclaimer", "version", default='0',
                doc="default version of disclaimer to be used")
    c_name = Option("disclaimer", "name", default='',
                doc="default name of disclaimer to be used")

   # IAdminPanelProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('access', _('Access Controls'), 'disclaimer', _('Disclaimer'))

    def render_admin_panel(self, req, cat, page, disclaimer_name):
        # Detail view?
        data = {}
        obj = DisclaimerModel(self.env)
        if disclaimer_name:
            name = disclaimer_name
            if req.method == 'POST':
                if req.args.get('save'):
                    new_name = req.args.get('name').strip()
                    if disclaimer_name != new_name:
                        obj.update(new_name, disclaimer_name)
                        name = new_name
                        add_notice(req, _('Disclaimer name renamed successfully.'))
                elif req.args.get('cancel'):
                    pass #just skip
                req.redirect(req.href.admin(cat, page))
            data = {'view': 'detail', 'name':name }
        else:
            if req.method == 'POST':
                if req.args.get('add') :
                    name = req.args.get('name').strip()
                    body = req.args.get('body').strip()
                    author = req.args.get('author').strip()
                    obj.insert(name, body, author)
                elif req.args.get('remove'):
                    sel = req.args.get('sel')
                    if not sel:
                        raise TracError(_('No disclaimer selected'))
                    if not isinstance(sel, list):
                        sel = [sel]
                    for id in sel:
                        name, version = obj.get_by_id(id)
                        if name == self.c_name and version == int(self.c_version):
                            add_warning(req, _('You cannot delete disclaimer "%s"  with version:%s' %(name,version)))
                            continue
                        obj.delete(id)
                        add_notice(req, _('Disclaimer "%s" with version:%s deleted succesfully' %(name, version)))
                elif req.args.get('apply'):
                    id = req.args.get('default')
                    if id:
                        name, version = obj.get_by_id(id)
                        self.config.set('disclaimer', 'name', name)
                        self.config.set('disclaimer', 'version', version)
                        self.config.save()
                        add_notice(req, _('Disclaimer "%s" with version:%s saved succesfully' %(name, version)))
                req.redirect(req.href.admin(cat, page))
            data['disclaimers'] = obj.getall()
            row = obj.get_by_name_version(self.c_name,self.c_version)
            if row:
                data['default'] = row[0]
            else: 
               data['default'] = None
        perm = PermissionSystem(self.env)
        def valid_author(username):
            return perm.get_user_permissions(username).get('TRAC_ADMIN')
        data['authors'] = [username for username, name, email
                          in self.env.get_known_users()
                          if valid_author(username)]
        data['authors'].insert(0, '')
        data['authors'].sort()
        Chrome(self.env).add_wiki_toolbars(req)
        return 'admin-disclaimer.html', data
    
    def match_request(self, req):
        if req.authname == 'anonymous' or not req.method == 'POST':
            return False
        return req.path_info == '/ajax/disclaimer'
  
    def process_request(self, req):
        if req.authname == 'anonymous':
            return
        dis_obj = DisclaimerModel(self.env)
        user_dis_obj = UserDisclaimerModel(self.env)
        if req.method == 'POST':
            name = req.args.get('name').strip()
            body = req.args.get('body').strip()
            version = req.args.get('version').strip()
            user = req.authname
            try:
                accepted = sha1(body).hexdigest()
            except Exception, why:
                self.log.debug(why)
                accepted = body
            user_dis_obj.insert(user, name, version, accepted)
            req.send('{"message":"success"}', 'text/json')
        else:
            req.send('{"message":"Invalid call"}', 'text/json')
    
    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        if req.authname == 'anonymous':
            return stream
        if not self.c_name or not int(self.c_version):
            return stream
        obj = DisclaimerModel(self.env)
        disclaimer = obj.get_by_name_version(self.c_name,self.c_version)
        if not disclaimer:
            return stream
        (id, author, body) = disclaimer
        user_dis_obj = UserDisclaimerModel(self.env)
        valid = user_dis_obj.validate(req.authname, self.c_name, self.c_version)
        if valid:
            return stream
        add_stylesheet(req, 'disclaimer/css/disclaimer.css')
        add_javascript(req, 'disclaimer/js/disclaimer.js')
        tmpl = TemplateLoader(self.get_templates_dirs()).load('disclaimer.html')
        disclaimerbox = tmpl.generate(req=req, name=self.c_name, version=self.c_version, body=body, href=req.href)
        stream |= Transformer('//div[@id="footer"]').append(disclaimerbox)
        return stream

     # IEnvironmentSetupParticipant
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("select count(*) from disclaimer")
            cursor.fetchone()
            return False
        except:
            db.rollback()
            return True

    def upgrade_environment(self, db):
        self.log.debug("Upgrading schema for disclaimer plugin")
        db_backend, _ = DatabaseManager(self.env).get_connector()
        cursor = db.cursor()
        for table in DisclaimerModel.disclaimer_schema:
            for stmt in db_backend.to_sql(table):
                self.log.debug(stmt)
                cursor.execute(stmt)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('disclaimer', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

