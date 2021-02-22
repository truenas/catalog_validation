from jsonschema import validate as json_schema_validate, ValidationError as JsonValidationError

from catalog_validation.exceptions import ValidationErrors

from .schema_gen import DictSchema, IntegerSchema, StringSchema


class Feature:

    NAME = NotImplementedError
    VALID_SCHEMAS = []

    def __str__(self):
        return self.NAME

    def validate(self, schema_obj, schema_str):
        verrors = ValidationErrors()
        if not isinstance(schema_obj, tuple(self.VALID_SCHEMAS)):
            verrors.add(
                f'{schema_str}.type',
                f'Schema must be one of {", ".join(str(v) for v in self.VALID_SCHEMAS)} schema types'
            )

        if not verrors:
            self._validate(verrors, schema_obj, schema_str)
        verrors.check()

    def _validate(self, verrors, schema_obj, schema_str):
        pass

    def __eq__(self, other):
        return self.NAME == (other if isinstance(other, str) else other.NAME)


class IXVolumeFeature(Feature):

    NAME = 'normalize/ixVolume'
    VALID_SCHEMAS = [DictSchema, StringSchema]

    def _validate(self, verrors, schema_obj, schema_str):
        if isinstance(schema_obj, StringSchema):
            return

        attrs = schema_obj.attrs
        if 'datasetName' not in attrs:
            verrors.add(f'{schema_str}.attrs', 'Variable "datasetName" must be specified.')
        elif not isinstance(attrs[attrs.index('datasetName')].schema, StringSchema):
            verrors.add(f'{schema_str}.attrs', 'Variable "datasetName" must be of string type.')

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
                verrors.add(f'{schema_str}.attrs.{index}.properties', f'Error validating properties: {e}')


class DefinitionInterfaceFeature(Feature):

    NAME = 'definitions/interface'
    VALID_SCHEMAS = [StringSchema]


class DefinitionGPUConfigurationFeature(Feature):

    NAME = 'definitions/gpuConfiguration'
    VALID_SCHEMAS = [DictSchema]


class DefinitionTimezoneFeature(Feature):

    NAME = 'definitions/timezone'
    VALID_SCHEMAS = [StringSchema]


class DefinitionNodeIPFeature(Feature):

    NAME = 'definitions/nodeIP'
    VALID_SCHEMAS = [StringSchema]


class ValidationNodePortFeature(Feature):

    NAME = 'validations/nodePort'
    VALID_SCHEMAS = [IntegerSchema]


class CertificateFeature(Feature):

    NAME = 'definitions/certificate'
    VALID_SCHEMAS = [IntegerSchema]


class CertificateAuthorityFeature(Feature):

    NAME = 'definitions/certificateAuthority'
    VALID_SCHEMAS = [IntegerSchema]


FEATURES = [
    IXVolumeFeature(),
    DefinitionInterfaceFeature(),
    DefinitionGPUConfigurationFeature(),
    DefinitionTimezoneFeature(),
    DefinitionNodeIPFeature(),
    ValidationNodePortFeature(),
    CertificateFeature(),
    CertificateAuthorityFeature(),
]
