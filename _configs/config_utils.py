from pydantic import BaseModel

def list_model_paths(model: BaseModel, prefix: str = "") -> list[str]:
    paths = []
    for field_name, value in model:
        full_key = f"{prefix}{field_name}"
        if isinstance(value, BaseModel):
            paths.extend(list_model_paths(value, f"{full_key} "))
        else:
            paths.append(f"{full_key} = {value!r}")
    return paths


def set_config_value(model: BaseModel, path: list[str], raw_value: str) -> None:
    *prefix, field = path
    target = model
    for key in prefix:
        target = getattr(target, key)

    expected_type = target.__annotations__[field]
    parsed_value = expected_type(raw_value)
    setattr(target, field, parsed_value)