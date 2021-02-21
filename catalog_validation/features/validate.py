from .utils import retrieve_features
from .validate_features import FEATURE_MAPPING


def validate_feature(question_data, schema, verrors, all_features=None):
    schema_data = question_data['schema']
    if '$ref' not in schema_data:
        return

    refs = schema_data['$ref']
    if type(refs) != list or not refs:
        # This has already been validated
        return

    if all_features is None:
        all_features = retrieve_features()

    # If all_features is none which is possible if the machine in question does not
    # have internet access let's just validate what we can
    for index, ref in enumerate(refs):
        if all_features:
            if ref not in all_features:
                verrors.add(
                    f'{schema}.{index}', 'Please specify a valid feature.'
                )

        if ref in FEATURE_MAPPING:
            FEATURE_MAPPING[ref](question_data, f'{schema}.{index}', verrors)
