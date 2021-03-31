# Copyright 2020 The FedLearner Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# coding: utf-8
from string import Template
from flatten_dict import flatten
from fedlearner_webconsole.proto.workflow_definition_pb2 import Slot


class _YamlTemplate(Template):
    delimiter = '$'
    # Which placeholders in the template should be interpreted
    idpattern = r'Slot_[a-z0-9_]*'

    # overwrite this func to escape the invalid placeholder such as
    # ${project.variables.namespace}
    def substitute(self, mapping):
        # Helper function for .sub()
        def convert(mo):
            # Check the most common path first.
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                return str(mapping[named])
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                # overwrite to escape invalid placeholder
                return mo.group()
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)


def format_yaml(yaml, **kwargs):
    """Formats a yaml template.

    Example usage:
        format_yaml('{"abc": ${x.y}}', x={'y': 123})
    output should be  '{"abc": 123}'
    """
    template = _YamlTemplate(yaml)
    try:
        return template.substitute(flatten(kwargs or {},
                                           reducer='dot'))
    except KeyError as e:
        raise RuntimeError(
            'Unknown placeholder: {}'.format(e.args[0])) from e


def generate_yaml_template(base_yaml, slots_proto):
    """
    Args:
        base_yaml: A string representation of one type job's base yaml.
        slots_proto: A proto map object representation of modification
        template's operable smallest units.
    Returns:
        string: A yaml_template
    """
    slots = {}
    for key in slots_proto:
        if slots_proto[key].reference_type == Slot.ReferenceType.DEFAULT:
            slots[key] = slots_proto[key].default
        else:
            slots[key] = f'${{{slots_proto[key].reference}}}'
    return format_yaml(base_yaml, **slots)
