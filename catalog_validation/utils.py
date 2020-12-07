from collections import namedtuple

CatalogItem = namedtuple('CatalogItem', 'train item version')
common_mapping = {
    'required': bool,
    'null': bool,
    'show_if': list,
    '$ref': list,
    'subquestions': list,
    'show_subquestions_if': object,
    'type': str,
    'editable': bool,
}

SCHEMA_MAPPING = {
    'string': {
        'default': str,
        'min_length': int,
        'max_length': int,
        'enum': list,
        'private': bool,
        'valid_chars': str,
        **common_mapping,
    },
    'int': {
        'default': int,
        'min': int,
        'max': int,
        'enum': list,
        **common_mapping,
    },
    'boolean': {
        'default': bool,
        **common_mapping,
    },
    'path': {
        'default': str,
        **common_mapping,
    },
    'hostpath': {
        'default': str,
        **common_mapping,
    },
    'list': {
        'default': list,
        'items': list,
        **{k: v for k, v in common_mapping.items() if k not in ('subquestions', 'show_subquestions_if')},
    },
    'dict': {
        'default': dict,
        'attrs': list,
        'additional_attrs': bool,
        **common_mapping,
    },
    'ipaddr': {
        'default': str,
        'ipv4': bool,
        'ipv6': bool,
        'cidr': bool,
        **common_mapping,
    },
    'cron': {
        'default': dict,
        **common_mapping,
    }
}
WANTED_FILES_IN_ITEM_VERSION = {'questions.yaml', 'app-readme.md', 'values.yaml', 'Chart.yaml', 'README.md'}


def validate_key_value_types(data_to_check, mapping, verrors, schema):
    for key, value_type in mapping:
        if key not in data_to_check:
            verrors.add(f'{schema}.{key}', f'Missing required {key!r} key.')
        elif type(data_to_check[key]) != value_type:
            verrors.add(f'{schema}.{key}', f'{key!r} value should be a {value_type.__name__!r}')
