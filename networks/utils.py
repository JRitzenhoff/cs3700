from typing import Any, Type, Dict, List

import dataclasses

from enum import Enum


class ConnectionType(str, Enum):
    PEER = "peer"
    PROVIDER = "prov"
    CUSTOMER = "cust"


@dataclasses.dataclass(frozen=True)
class ConditionalField:
    var_name: str
    mapping: Dict[Any, Type[Any]]


class Replaceable:
    def replace(self, **kwargs) -> 'Replaceable':
        return dataclasses.replace(self, **kwargs)


class Serializable:
    def serialize(self) -> Any:
        """
        :return: JSON compatible equivalent of this Packet instance
        """
        return {
            f.name: self.serialize_from_type(getattr(self, f.name))
            for f in dataclasses.fields(self)
        }

    @classmethod
    def serialize_from_type(cls, field_instance: Any) -> Any:
        """
        :return: A JSON compatible serialized value provided the instance of a field
        """
        try:
            val = field_instance.serialize()
        except AttributeError:
            # if the field_instance doesn't have the serialize function
            val = field_instance if not isinstance(field_instance, list)\
                                 else [cls.serialize_from_type(elem) for elem in field_instance]

        return val


class Deserializable:
    """
    Parent for a dataclass that can be deserialized from a JSON object
    """

    @classmethod
    def deserialize(cls, **json_kwargs):
        """
        :return: An instance of the class after deserialization from a JSON object
        """
        # get the associated values of this class
        init_kwargs: Dict[str, Any] = {}
        dataclass_fields = dataclasses.fields(cls)

        for field_representation in dataclass_fields:
            input_val = json_kwargs.pop(field_representation.name)

            if field_representation.type == ConditionalField:
                kwarg_val = cls.deserialize_conditional_field(conditional_field=field_representation.default,
                                                              existing_fields=init_kwargs,
                                                              json_val=input_val)
            else:
                kwarg_val = cls.deserialize_as_type(field_representation.type, input_val)

            init_kwargs[field_representation.name] = kwarg_val

        cls.validate_deserialization(starting_args=json_kwargs, parsed_args=init_kwargs,
                                     class_fields=dataclass_fields)

        return cls(**init_kwargs)

    @staticmethod
    def validate_deserialization(starting_args: Dict[str, Any], parsed_args: Dict[str, Any],
                                 class_fields: List[dataclasses.Field]) -> None:
        """
        :raises: ValueError if the fields provided to deserialize don't match the underlying object
        """
        if len(starting_args) > 0 or len(parsed_args) != len(class_fields):
            clean_fields = {f.name: f.type for f in class_fields}
            received_fields = {**parsed_args, **starting_args}
            raise ValueError(f"Expected fields {clean_fields} and received {received_fields}")

    @classmethod
    def deserialize_as_type(cls, obj_class: Type, json_val: Any) -> Any:
        """
        :return: The deserialized value provided a class builder and a json value
        """

        try:
            built_val = obj_class.deserialize(**json_val)
        except AttributeError:
            if obj_class == Any:
                built_val = json_val
            elif getattr(obj_class, '__origin__', None) in (list, List):
                # this is very hacky
                nested_type, = obj_class.__args__
                built_val = [cls.deserialize_as_type(nested_type, element) for element in json_val]
            else:
                built_val = obj_class(json_val)

        return built_val

    @classmethod
    def deserialize_conditional_field(cls, conditional_field: ConditionalField, existing_fields: Dict[str, Any],
                                      json_val: Any) -> Any:
        """
        :return: Appropriate value from a defined ConditionalField
        """
        # get the name of the field that this one relies on
        associated_field = existing_fields[conditional_field.var_name]

        # get the class that this field should deserialize to
        associated_type = conditional_field.mapping[associated_field]

        return cls.deserialize_as_type(obj_class=associated_type, json_val=json_val)
