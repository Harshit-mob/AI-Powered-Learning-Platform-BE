from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelBaseModel(BaseModel):
    """
    Base model that converts Python snake_case properties 
    into JSON JS/React Native friendly camelCase.
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
