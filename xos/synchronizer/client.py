
# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import urlparse

try:
    from keystoneauth1.identity import v2 as keystoneauth_v2
    from keystoneauth1 import session as keystone_session
    from keystoneclient.v2_0 import client as keystone_client
    # from glance import client as glance_client
    import glanceclient
    from novaclient.v2 import client as nova_client
    from neutronclient.v2_0 import client as neutron_client

    has_openstack = True
except:
    has_openstack = False

from xosconfig import Config


def require_enabled(callable):
    def wrapper(*args, **kwds):
        if has_openstack:
            return callable(*args, **kwds)
        else:
            return None

    return wrapper


def parse_novarc(filename):
    opts = {}
    f = open(filename, 'r')
    for line in f:
        try:
            line = line.replace('export', '').strip()
            parts = line.split('=')
            if len(parts) > 1:
                value = parts[1].replace("\'", "")
                value = value.replace('\"', '')
                opts[parts[0]] = value
        except:
            pass
    f.close()
    return opts


class Client:
    def __init__(self, username=None, password=None, tenant=None, url=None, token=None, endpoint=None, controller=None,
                 cacert=None, admin=True, *args, **kwds):

        self.has_openstack = has_openstack
        self.url = controller.auth_url
        if admin:
            self.username = controller.admin_user
            self.password = controller.admin_password
            self.tenant = controller.admin_tenant
        else:
            self.username = None
            self.password = None
            self.tenant = None

        if username:
            self.username = username
        if password:
            self.password = password
        if tenant:
            self.tenant = tenant
        if url:
            self.url = url
        if token:
            self.token = token
        if endpoint:
            self.endpoint = endpoint

        if cacert:
            self.cacert = cacert
        else:
            self.cacert = Config.get("nova.ca_ssl_cert")


class KeystoneClient(Client):
    def __init__(self, *args, **kwds):
        Client.__init__(self, *args, **kwds)
        if has_openstack:
            auth = keystoneauth_v2.Password(username=self.username,
                                            password=self.password,
                                            tenant_name=self.tenant,
                                            auth_url=self.url,
                                            )
            sess = keystone_session.Session(auth=auth, verify=self.cacert, )
            self.client = keystone_client.Client(session=sess)

    @require_enabled
    def connect(self, *args, **kwds):
        self.__init__(*args, **kwds)

    @require_enabled
    def __getattr__(self, name):
        return getattr(self.client, name)


class Glance(Client):
    def __init__(self, *args, **kwds):
        Client.__init__(self, *args, **kwds)
        if has_openstack:
            self.client = glanceclient.get_client(host='0.0.0.0',
                                                  username=self.username,
                                                  password=self.password,
                                                  tenant=self.tenant,
                                                  auth_url=self.url,
                                                  cacert=self.cacert
                                                  )

    @require_enabled
    def __getattr__(self, name):
        return getattr(self.client, name)


class GlanceClient(Client):
    def __init__(self, version, endpoint, token, cacert=None, *args, **kwds):
        Client.__init__(self, *args, **kwds)
        if has_openstack:
            self.client = glanceclient.Client(version,
                                              endpoint=endpoint,
                                              token=token,
                                              cacert=cacert
                                              )

    @require_enabled
    def __getattr__(self, name):
        return getattr(self.client, name)


class NovaClient(Client):
    def __init__(self, *args, **kwds):
        Client.__init__(self, *args, **kwds)
        if has_openstack:
            self.client = nova_client.client.Client(
                "2",
                username=self.username,
                api_key=self.password,
                project_id=self.tenant,
                auth_url=self.url,
                region_name='',
                extensions=[],
                service_type='compute',
                service_name='',
                cacert=self.cacert
            )

    @require_enabled
    def connect(self, *args, **kwds):
        self.__init__(*args, **kwds)

    @require_enabled
    def __getattr__(self, name):
        return getattr(self.client, name)


class NovaDB(Client):
    def __init__(self, *args, **kwds):
        Client.__init__(self, *args, **kwds)
        if has_openstack:
            self.ctx = get_admin_context()
            nova_db_api.FLAGS(default_config_files=['/etc/nova/nova.conf'])
            self.client = nova_db_api

    @require_enabled
    def connect(self, *args, **kwds):
        self.__init__(*args, **kwds)

    @require_enabled
    def __getattr__(self, name):
        return getattr(self.client, name)


class NeutronClient(Client):
    def __init__(self, *args, **kwds):
        Client.__init__(self, *args, **kwds)
        if has_openstack:
            self.client = neutron_client.Client(username=self.username,
                                                password=self.password,
                                                tenant_name=self.tenant,
                                                auth_url=self.url,
                                                ca_cert=self.cacert
                                                )

    @require_enabled
    def connect(self, *args, **kwds):
        self.__init__(*args, **kwds)

    @require_enabled
    def __getattr__(self, name):
        return getattr(self.client, name)


class OpenStackClient:
    """
    A simple native shell to the openstack backend services.
    This class can receive all nova calls to the underlying testbed
    """

    def __init__(self, *args, **kwds):
        # instantiate managers
        self.keystone = KeystoneClient(*args, **kwds)
        url_parsed = urlparse.urlparse(self.keystone.url)
        hostname = url_parsed.netloc.split(':')[0]
        token = self.keystone.client.tokens.authenticate(username=self.keystone.username,
                                                         password=self.keystone.password,
                                                         tenant_name=self.keystone.tenant)
        #        glance_endpoint = self.keystone.client.service_catalog.url_for(service_type='image', endpoint_type='publicURL')
        #        self.glanceclient = GlanceClient('1', endpoint=glance_endpoint, token=token.id, **kwds)
        self.nova = NovaClient(*args, **kwds)
        # self.nova_db = NovaDB(*args, **kwds)
        self.neutron = NeutronClient(*args, **kwds)

    @require_enabled
    def connect(self, *args, **kwds):
        self.__init__(*args, **kwds)

    @require_enabled
    def authenticate(self):
        return self.keystone.authenticate()
