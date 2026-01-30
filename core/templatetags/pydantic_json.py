from django import template
from django.utils.html import json_script

register = template.Library()

try:
    from pydantic import BaseModel
except Exception:
    BaseModel = ()


def _pydantic_to_jsonable(value):
    if BaseModel and isinstance(value, BaseModel):
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if hasattr(value, "dict"):
            return value.dict()

    if isinstance(value, dict):
        return {key: _pydantic_to_jsonable(val) for key, val in value.items()}

    if isinstance(value, (list, tuple)):
        return [_pydantic_to_jsonable(item) for item in value]

    return value


@register.filter
def pydantic_json_script(value, element_id):
    return json_script(_pydantic_to_jsonable(value), element_id)
