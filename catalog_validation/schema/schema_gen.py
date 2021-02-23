from .attrs import (
    BooleanSchema, StringSchema, IntegerSchema, PathSchema, HostPathSchema, ListSchema, DictSchema,
    IPAddrSchema, CronSchema
)


def get_schema(schema_data):
    schema = None
    if not isinstance(schema_data, dict):
        return schema

    s_type = schema_data.get('type')
    if s_type == 'boolean':
        schema = BooleanSchema
    elif s_type == 'string':
        schema = StringSchema
    elif s_type == 'int':
        schema = IntegerSchema
    elif s_type == 'path':
        schema = PathSchema
    elif s_type == 'hostpath':
        schema = HostPathSchema
    elif s_type == 'list':
        schema = ListSchema
    elif s_type == 'dict':
        schema = DictSchema
    elif s_type == 'ipaddr':
        schema = IPAddrSchema
    elif s_type == 'cron':
        schema = CronSchema
    if schema:
        schema = schema(data=schema_data)

    return schema
