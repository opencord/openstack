
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


from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))


class ErrorMapper:
    def __init__(self, error_map_file):
        self.error_map = {}
        try:
            error_map_lines = open(error_map_file).read().splitlines()
            for l in error_map_lines:
                if (not l.startswith('#')):
                    splits = l.split('->')
                    k, v = map(lambda i: i.rstrip(), splits)
                    self.error_map[k] = v
        except:
            log.info('Could not read error map')

    def map(self, error):
        return self.error_map[error]
