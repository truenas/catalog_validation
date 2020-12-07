import os
import yaml

from semantic_version import Version

from .exceptions import CatalogDoesNotExist, ValidationErrors
from .utils import SCHEMA_MAPPING, validate_key_value_types, WANTED_FILES_IN_ITEM_VERSION


def validate_catalog(catalog_path):
    if not os.path.exists(catalog_path):
        raise CatalogDoesNotExist(catalog_path)

    verrors = ValidationErrors()

    for file_dir in os.listdir(catalog_path):
        complete_path = os.path.join(catalog_path, file_dir)
        if file_dir.startswith('.') or not os.path.isdir(complete_path):
            continue

        try:
            validate_train(complete_path)
        except ValidationErrors as e:
            verrors.extend(e)

    verrors.check()


def validate_train(train_path):
    train = os.path.basename(train_path)
    verrors = ValidationErrors()
    for catalog_item in os.listdir(train_path):
        try:
            validate_catalog_item(os.path.join(train_path, catalog_item), f'{train}.{catalog_item}')
        except ValidationErrors as e:
            verrors.extend(e)

    verrors.check()


def validate_catalog_item(catalog_item_path, schema):
    # We should ensure that each catalog item has at least 1 version available
    # Also that we have item.yaml present
    verrors = ValidationErrors()
    item_name = os.path.join(catalog_item_path)
    files = []
    versions = []
    for file_dir in os.listdir(catalog_item_path):
        complete_path = os.path.join(catalog_item_path, file_dir)
        if os.path.isdir(complete_path):
            versions.append(complete_path)
        else:
            files.append(file_dir)

    if not versions:
        verrors.add(f'{schema}.versions', f'No versions found for {item_name} item.')

    if 'item.yaml' not in files:
        verrors.add(f'{schema}.item', 'Item configuration (item.yaml) not found')
    else:
        with open(os.path.join(catalog_item_path, 'item.yaml'), 'r') as f:
            item_config = yaml.safe_load(f.read())

        validate_key_value_types(item_config, (('categories', list),), verrors, f'{schema}.item_config')

    for version_path in versions:
        try:
            validate_catalog_item_version(version_path, f'{schema}.versions.{os.path.basename(version_path)}')
        except ValidationErrors as e:
            verrors.extend(e)

    verrors.check()


def validate_catalog_item_version(version_path, schema):
    verrors = ValidationErrors()
    version_name = os.path.basename(version_path)
    item_name = version_path.split('/')[-2]
    try:
        Version(version_name)
    except ValueError:
        verrors.add(f'{schema}.name', f'{version_name!r} is not a valid version name.')

    files_diff = WANTED_FILES_IN_ITEM_VERSION ^ set(
        f for f in os.listdir(version_path) if f in WANTED_FILES_IN_ITEM_VERSION
    )
    if files_diff:
        verrors.add(f'{schema}.required_files', f'Missing {", ".join(files_diff)} required configuration files.')

    chart_version_path = os.path.join(version_path, 'Chart.yaml')
    if os.path.exists(chart_version_path):
        with open(chart_version_path, 'r') as f:
            chart_config = yaml.safe_load(f.read())

        if chart_config.get('name') != item_name:
            verrors.add(f'{schema}.item_name', 'Item name not correctly set in "Chart.yaml".')

        if chart_config.get('version') != version_name:
            verrors.add(
                f'{schema}.version', 'Configured version in "Chart.yaml" does not match version directory name.'
            )

    questions_path = os.path.join(version_path, 'questions.yaml')
    if os.path.exists(questions_path):
        try:
            validate_questions_yaml(questions_path, f'{schema}.questions_configuration')
        except ValidationErrors as v:
            verrors.extend(v)

    verrors.check()


def validate_questions_yaml(questions_yaml_path, schema):
    with open(questions_yaml_path, 'r') as f:
        questions_config = yaml.safe_load(f.read())

    verrors = ValidationErrors()

    validate_key_value_types(
        questions_config, (('groups', list), ('questions', list), ('portals', list, False)), verrors, schema
    )

    groups = []
    if type(questions_config.get('groups')) == list:
        for index, group in enumerate(questions_config['groups']):
            if type(group) != dict:
                verrors.add(f'{schema}.group.{index}', 'Type of group should be a dictionary.')
                continue

            if group.get('name'):
                groups.append(group['name'])

            validate_key_value_types(group, (('name', str), ('description', str)), verrors, f'{schema}.group.{index}')

    if type(questions_config.get('questions')) != list:
        # We only want to raise verrors here if questions is not a list as otherwise we can raise them at the end
        # after validating the questions
        verrors.check()

    for index, question in enumerate(questions_config['questions']):
        validate_question(question, f'{schema}.questions.{index}', verrors, (('group', str),))
        if question.get('group') and question['group'] not in groups:
            verrors.add(f'{schema}.questions.{index}.group', f'Please specify a group declared in "{schema}.groups"')

    verrors.check()


def validate_question(question_data, schema, verrors, validate_top_level_attrs=None):
    if type(question_data) != dict:
        verrors.add(schema, 'Question must be a valid dictionary.')
        return

    validate_top_level_attrs = validate_top_level_attrs or tuple()
    validate_key_value_types(
        question_data, (('variable', str), ('label', str), ('schema', dict)) + validate_top_level_attrs, verrors, schema
    )
    if type(question_data.get('schema')) != dict:
        return

    schema_data = question_data['schema']
    validate_key_value_types(schema_data, (('type', str),), verrors, f'{schema}.schema')

    if type(schema_data.get('type')) != str:
        return

    variable_type = schema_data['type']
    if variable_type not in SCHEMA_MAPPING:
        verrors.add(f'{schema}.schema.type', 'Invalid schema type specified.')
        return

    mapping = SCHEMA_MAPPING[variable_type]
    for key, value in schema_data.items():
        if key not in mapping:
            verrors.add(f'{schema}.schema', f'{key!r} not allowed with {variable_type!r} variable schema.')
            continue
        if value is None:
            continue
        if not isinstance(value, mapping[key]):
            verrors.add(f'{schema}.schema.{key}', f'Expected {mapping[key].__name__!r} value type.')

    for condition, key, schema_str in (
        (variable_type != 'list', 'subquestions', f'{schema}.schema.subquestions'),
        (variable_type == 'list', 'items', f'{schema}.schema.items'),
        (variable_type == 'dict', 'attrs', f'{schema}.schema.attrs'),
    ):
        if not (condition and type(schema_data.get(key)) == list):
            continue

        for index, item in enumerate(schema_data[key]):
            validate_question(item, f'{schema_str}.{index}', verrors)
