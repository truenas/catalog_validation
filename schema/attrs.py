import collections.abc

from jsonschema import validate as json_schema_validate, ValidationError as JsonValidationError

from catalog_validation.exceptions import ValidationErrors
from catalog_validation.features import validate_features


class Feature:

    NAME = NotImplementedError

    def validate(self, schema):
        raise NotImplementedError

    def __eq__(self, other):
        return self.NAME == other.NAME


class IXVolumeFeature(Feature):

    NAME = 'normalize/ixVolume'

    def validate(self, schema):
        verrors = ValidationErrors()
        if not isinstance(schema, (StringSchema, DictSchema)):
            verrors.add(f'{schema}.type', 'Schema must be of string/dictionary type')

        verrors.check()

        if isinstance(schema, StringSchema):
            return

        attrs = schema.attrs
        if 'datasetName' not in attrs:
            verrors.add(f'{schema}.attrs', 'Variable "datasetName" must be specified.')
        elif not isinstance(attrs[attrs.index('datasetName')].schema, StringSchema):
            verrors.add(f'{schema}.attrs', 'Variable "datasetName" must be of string type.')

        if 'properties' in attrs:
            index = attrs.index('properties')
            properties = attrs[index]
            try:
                json_schema_validate(
                    properties.schema._schema_data, {
                        'type': 'object',
                        'properties': {
                            'recordsize': {
                                'type': 'string',
                                'enum': [
                                    '512', '1K', '2K', '4K', '8K', '16K', '32K', '64K', '128K', '256K', '512K', '1024K'
                                ]
                            }
                        },
                        'additionalProperties': False,
                    }
                )
            except JsonValidationError as e:
                verrors.add(f'{schema}.attrs.{index}.properties', f'Error validating properties: {e}')

        verrors.check()


class Schema:

    DEFAULT_TYPE = NotImplementedError

    def __init__(self, include_subquestions_attrs=True, data=None):
        self.required = self.null = self.show_if = self.ref = self.ui_ref = self.type =\
            self.editable = self.hidden = self.default = self._schema_data = None
        self._skip_data_values = []
        if include_subquestions_attrs:
            self.subquestions = self.show_subquestions_if = None
        if data:
            self.initialize_values(data)

    def initialize_values(self, data):
        self._schema_data = data
        for key, value in filter(
            lambda k, v: hasattr(self, k) and k not in self._skip_data_values, data.items()
        ):
            setattr(self, key, value)

    def get_schema_str(self, schema):
        if schema:
            return f'{schema}.'
        return ''

    def validate(self, schema, data=None):
        if data:
            self.initialize_values(data)

        if not self._schema_data:
            raise Exception('Schema data must be initialized before validating schema')

        verrors = ValidationErrors()
        try:
            json_schema_validate(self._schema_data, self.json_schema())
        except JsonValidationError as e:
            verrors.add(schema, f'Failed to validate schema: {e}')

        verrors.check()

        if '$ref' in self._schema_data:
            pass

    def json_schema(self):
        schema = {
            'type': 'object',
            'properties': {
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
                },
                'editable': {
                    'type': 'boolean',
                },
                'hidden': {
                    'type': 'boolean',
                },
            },
            'required': ['type'],
        }
        if self.DEFAULT_TYPE:
            schema['properties']['default'] = {
                'type': [self.DEFAULT_TYPE] + (['null'] if self.null else [])
            }
        if hasattr(self, 'enum'):
            schema['properties']['enum'] = {
                'type': 'array',
                'items': [{
                    'type': 'object',
                    'properties': {
                        'value': {'type': [self.DEFAULT_TYPE] + (['null'] if self.null else [])},
                        'description': {'type': ['string', 'null']},
                    },
                    'required': ['value', 'description']
                }]
            }
        return schema


class Variable:
    def __init__(self, data):
        self.name = self.label = self.description = self.group = None
        self.schema = None
        self.update_from_data(data)

    def update_from_data(self, data):
        self.name = data.get('variable')
        self.label = data.get('label')
        self.description = data.get('description')
        schema = data.get('schema')
        if isinstance(schema, dict):
            s_type = schema.get('type')
            if s_type == 'boolean':
                self.schema = BooleanSchema(data=schema)

    def validate(self, schema):
        verrors = ValidationErrors()
        if not self.name:
            verrors.add(f'{schema}.variable', 'Variable value must be specified')

        if not self.schema:
            verrors.add(f'{schema}.schema', 'Schema must be specified for variable')
        else:
            self.schema.validate(f'{schema}.schema')

    def __eq__(self, other):
        return (other if isinstance(other, str) else other.name) == self.name


class BooleanSchema(Schema):
    DEFAULT_TYPE = 'boolean'


class StringSchema(Schema):
    DEFAULT_TYPE = 'string'

    def __init__(self, data):
        self.min_length = self.max_length = self.enum = self.private = self.valid_chars = None
        super().__init__(data=data)

    def json_schema(self):
        schema = super().json_schema()
        schema['properties'].update({
            'min_length': {
                'type': 'integer',
            },
            'max_length': {
                'type': 'integer',
            },
            'private': {
                'type': 'boolean',
            },
            'valid_chars': {
                'type': 'string',
            },
        })
        return schema


class IntegerSchema(Schema):
    DEFAULT_TYPE = 'integer'

    def __init__(self, data):
        self.min = self.max = self.enum = None
        super().__init__(data=data)

    def json_schema(self):
        schema = super().json_schema()
        schema['properties'].update({
            'min': {
                'type': 'integer',
            },
            'max': {
                'type': 'integer',
            },
        })
        return schema


class PathSchema(Schema):
    DEFAULT_TYPE = 'string'


class HostPathSchema(Schema):
    DEFAULT_TYPE = 'string'


class IPAddrSchema(Schema):
    DEFAULT_TYPE = 'string'

    def __init__(self, data):
        self.ipv4 = self.ipv6 = self.cidr = None
        super().__init__(data=data)

    def json_schema(self):
        schema = super().json_schema()
        schema['properties'].update({
            'ipv4': {'type': 'boolean'},
            'ipv6': {'type': 'boolean'},
            'cidr': {'type': 'boolean'},
        })
        return schema


class CronSchema(Schema):
    DEFAULT_TYPE = 'object'


class DictSchema(Schema):
    DEFAULT_TYPE = 'object'

    def __init__(self, data):
        self.attrs = []
        self.additional_attrs = None
        super().__init__(data=data)
        self._skip_data_values = ['attrs']

    def initialize_values(self, data):
        super().initialize_values(data)
        self.attrs = [Variable(d) for d in (data.get('attrs') or [])]

    def json_schema(self):
        schema = super().json_schema()
        schema['additionalProperties'] = bool(self.additional_attrs)
        schema['properties']['attrs'] = {'type': 'array'}
        schema['required'].append('attrs')
        # We do not validate nested children and hence do not add it in the
        # json schema as it makes it very complex to handle all the possibilities
        return schema


class ListSchema(Schema):

    DEFAULT_TYPE = 'array'

    def __init__(self, data):
        self.items = []
        super().__init__(False, data=data)
        self._skip_data_values = ['items']

    def initialize_values(self, data):
        super().initialize_values(data)
        self.items = [Variable(d) for d in (data.get('items') or [])]

    def json_schema(self):
        schema = super().json_schema()
        schema['properties']['items'] = {'type': 'array'}
        schema['required'].append('items')
        return schema
