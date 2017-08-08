
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


# FIXME this file needs a refactoring
observer_disabled = False

def EnableObserver(x):
    """ used for manage.py --noobserver """
    global observer_disabled
    observer_disabled = not x

print_once = True

def notify_observer(model=None, delete=False, pk=None, model_dict={}):
    if (observer_disabled):
        global print_once
        if (print_once):
            print "The observer is disabled"
            print_once = False
        return

    try:
        from .event_manager import EventSender
        if (model and delete):
            if hasattr(model,"__name__"):
                modelName = model.__name__
            else:
                modelName = model.__class__.__name__
            EventSender().fire(delete_flag = delete, model = modelName, pk = pk, model_dict=model_dict)
        else:
            EventSender().fire()
    except Exception,e:
        print "Exception in Observer. This should not disrupt the front end. %s"%str(e)


