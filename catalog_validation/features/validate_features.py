from jsonschema import validate, ValidationError


def validate_interface_configuration(question_data, schema, verrors):
    schema_data = question_data['schema']
    if schema_data['type'] != 'dict':
        verrors.add(schema, 'Schema type must be "dict"')
        return

    attrs = schema_data.get('attrs') or []
    if len(attrs) != 2 or not all(v['variable'] in ('hostInterface', 'ipam') for v in attrs):
        verrors.add(schema, 'Only "hostInterface" and "ipam" variables are expected.')
        return


def validate_ix_volume(question_data, schema, verrors):
    {
        'type': ['object', 'string'],
        'properties': {
            'properties': {
                'type': 'object',
                'properties': {
                    'recordsize': {
                        'type': 'string',
                        'enum': [
                            '512', '1K', '2K', '4K', '8K', '16K', '32K', '64K', '128K', '256K', '512K', '1024K'
                        ],
                    },
                },
                'additionalProperties': False,
            },
            'datasetName': {
                'type': 'string',
            }
        },
        'required': ['datasetName'],
    }
    schema_data = question_data['schema']
    if schema['type'] not in ('dict', 'string'):
        verrors.add(schema, 'Schema type must be dict or string for ix Volume.')
        return

    if schema['type'] == 'dict':
        found_dataset_name = False
        for index, attr in enumerate(schema['attrs']):
            if attr['variable'] == 'datasetName':
                found_dataset_name = True
                if attr['schema']['type'] != 'string':
                    verrors.add(f'{schema}.attrs.{index}', 'Variable "datasetName" must be of string type.')
            elif attr['variable'] == 'properties':
                if attr['schema']['type'] != 'dict':
                    verrors.add(f'{schema}.attrs.{index}', 'Variable "properties" must be of dict type.')
                else:
                    supported_props = {
                        'recordsize': {
                            'type': 'object',
                            'properties': {
                                'type': {
                                    'type': 'string',
                                },
                                'enum': {
                                    'type': 'array',
                                    'enum': []  # TODO: 
                                }
                            }
                        },
                    }
                    props_schema = attr['schema']['attrs']
                    if len(props_schema) != len(supported_props):
                        verrors.add(
                            f'{schema}.attrs.{index}',
                            f'Only {", ".join(supported_props)} properties are supported for ix volumes.'
                        )
                    for p_index, prop in enumerate(props_schema):
                        if prop['variable'] not in supported_props:
                            verrors.add(
                                f'{schema}.attrs.{index}.schema.attrs.{p_index}',
                                f'Only {", ".join(supported_props)} properties are supported for ix volumes.'
                            )
                            continue


        if not found_dataset_name:
            verrors.add(
                f'{schema}.schema.type', 'Variable "datasetName" must be provided when ixVolume is of type "dict".'
            )

    try:
        validate(
            question_data['schema'], {
                'type': 'object',
                'properties': {
                    'type': {
                        'type': 'string',
                        'enum': ['string', 'dict'],
                    },
                    'attrs': {
                        'type': 'object',

                    }
                }
            }
        )
    except ValidationError as e:
        verrors.add(schema, f'Provided ixVolume $ref is invalid: {e}')


def validate_definition_interface(question_data, schema, verrors):
    try:
        validate(
            question_data['schema'], {
                'type': ''
            }
        )
    except ValidationError as e:
        verrors.add(schema, f'Provided definition for interface $ref is invalid: {e}')


def validate_gpu_configuration(question_data, schema, verrors):
    pass


def validate_timezone(question_data, schema, verrors):
    pass


def validate_node_ip(question_data, schema, verrors):
    pass


def validate_node_port(question_data, schema, verrors):
    pass


FEATURE_MAPPING = {
    'normalize/interfaceConfiguration': validate_interface_configuration,
    'normalize/ixVolume': validate_ix_volume,
    'definitions/interface': validate_definition_interface,
    'definitions/gpuConfiguration': validate_gpu_configuration,
    'definitions/timezone': validate_timezone,
    'definitions/nodeIP': validate_node_ip,
    'validations/nodePort': validate_node_port,
}
