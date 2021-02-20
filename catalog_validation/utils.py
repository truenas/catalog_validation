import re

from collections import namedtuple

CatalogItem = namedtuple('CatalogItem', 'train item version')

common_schema = {
    'required': {
        'type': 'boolean',
    },
    'null': {
        'type': 'boolean',
    },
    'show_if': {
        'type': 'array',
    },
    '$ref': {
        'type': 'array',
    },
    '$ui-ref': {
        'type': 'array',
    },
    'subquestions': {
        'type': 'array',
    },
    'show_subquestions_if': {
        'type': ['string', 'integer', 'boolean', 'object', 'array', 'null'],

    },
    'type': {
        'type': 'string',
        '_required_': True,
    },
    'editable': {
        'type': 'boolean',
    },
    'hidden': {
        'type': 'boolean',
    },
}

# TODO: Investigate using json if/else for updating default property type
SCHEMA_JSON_MAPPING = {
    'string': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['string', 'null'],
            },
            'min_length': {
                'type': 'integer',
            },
            'max_length': {
                'type': 'integer',
            },
            'enum': {
                'type': 'array',
                'items': [{
                    'type': 'object',
                    'properties': {
                        'value': {'type': ['string', 'integer', 'null'], '_required_': True},
                        'description': {'type': ['string', 'null'], '_required_': True},
                    },
                    'additionalProperties': False,
                }]
            },
            'private': {
                'type': 'boolean',
            },
            'valid_chars': {
                'type': 'string',
            },
            **common_schema
        },
        'additionalProperties': False,
    },
    'int': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['integer', 'null'],
            },
            'min': {
                'type': 'integer',
            },
            'max': {
                'type': 'integer',
            },
            'enum': {
                'type': 'array',
                'items': [{
                    'type': 'object',
                    'properties': {
                        'value': {'type': ['integer', 'null'], '_required_': True},
                        'description': {'type': ['string', 'null'], '_required_': True},
                    },
                    'additionalProperties': False,
                }]
            },
            **common_schema,
        },
        'additionalProperties': False,
    },
    'boolean': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['boolean', 'null'],
            },
            **common_schema,
        },
        'additionalProperties': False,
    },
    'path': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['string', 'null'],
            },
            **common_schema,
        },
        'additionalProperties': False,
    },
    'hostpath': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['string', 'null'],
            },
            **common_schema,
        },
        'additionalProperties': False,
    },
    'list': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['array', 'null'],
            },
            'items': {
                'type': 'array',
                '_required_': True,
            },
            **{k: v for k, v in common_schema.items() if k not in ('subquestions', 'show_subquestions_if')},
        },
        'additionalProperties': False,
    },
    'dict': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['object', 'null'],
            },
            'attrs': {
                'type': 'array',
                '_required_': True,
            },
            'additional_attrs': {
                'type': 'boolean',
            },
            **common_schema,
        },
        'additionalProperties': False,
    },
    'ipaddr': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['string', 'null'],
            },
            'ipv4': {
                'type': 'boolean',
            },
            'ipv6': {
                'type': 'boolean',
            },
            'cidr': {
                'type': 'boolean',
            },
            **common_schema,
        },
        'additionalProperties': False,
    },
    'cron': {
        'type': 'object',
        'properties': {
            'default': {
                'type': ['object', 'null'],
            },
            **common_schema,
        },
        'additionalProperties': False,
    },
}

VALID_TRAIN_REGEX = re.compile(r'^\w+[\w.-]*$')
WANTED_FILES_IN_ITEM_VERSION = {'questions.yaml', 'app-readme.md', 'Chart.yaml', 'README.md'}


def validate_key_value_types(data_to_check, mapping, verrors, schema):
    for key_mapping in mapping:
        if len(key_mapping) == 2:
            key, value_type, required = *key_mapping, True
        else:
            key, value_type, required = key_mapping

        if required and key not in data_to_check:
            verrors.add(f'{schema}.{key}', f'Missing required {key!r} key.')
        elif key in data_to_check and not isinstance(data_to_check[key], value_type):
            verrors.add(f'{schema}.{key}', f'{key!r} value should be a {value_type.__name__!r}')
