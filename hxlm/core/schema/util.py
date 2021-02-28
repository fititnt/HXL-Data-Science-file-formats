"""hxlm.core.schema allow load schemas from YAML without coding
# @see https://pyyaml.org/wiki/PyYAMLDocumentation
"""

import yaml
import json


def export_schema_yaml(schema):
    # return yaml.dump(schema, indent=4)
    # @see https://github.com/yaml/pyyaml/issues/234

    return yaml.dump(schema, Dumper=Dumper)


def export_schema_json(schema):
    return json.dumps(schema)


def get_schema(file):
    # Funciona Ok, exceto com a Noruega https://noyaml.com/

    with open(file) as f:

        data = yaml.safe_load(f)
        # data = yaml.safe_load_all(f)
        # print(data)
        return data


class Dumper(yaml.Dumper):
    """Force identation on pylint, https://github.com/yaml/pyyaml/issues/234
    TODO: check on future if this still need (Emerson Rocha, 2021-02-28 10:56 UTC)
    """

    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)
