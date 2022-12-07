from typing import Any, Callable

import dataclasses


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

    @staticmethod
    def serialize_from_type(field_instance: Any) -> Any:
        """
        :return: A JSON compatible serialized value provided the instance of a field
        """
        try:
            val = field_instance.serialize()
        except AttributeError:
            # if the field_instance doesn't have the serialize function
            val = field_instance

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
        init_kwargs = {}

        dataclass_fields = dataclasses.fields(cls)

        for field_representation in dataclass_fields:
            input_val = json_kwargs.pop(field_representation.name)
            kwarg_val = cls.deserialize_as_type(field_representation.type, input_val)

            init_kwargs[field_representation.name] = kwarg_val

        if len(json_kwargs) > 0 or len(init_kwargs) != len(dataclass_fields):
            clean_fields = {f.name: f.type for f in dataclass_fields}
            received_fields = {**init_kwargs, **json_kwargs}
            raise ValueError(f"Expected fields {clean_fields} and received {received_fields}")

        return cls(**init_kwargs)

    @staticmethod
    def deserialize_as_type(obj_class: Callable, json_val: Any):
        """
        :return: The deserialized value provided a class builder and a json value
        """
        try:
            built_val = obj_class.deserialize(**json_val)
        except AttributeError:
            # if the obj_class doesn't have the deserialize function
            built_val = json_val if obj_class == Any else obj_class(json_val)

        return built_val


def IncrementallyDeserialize(*options):
    """
    Decorator for a Deserializable field type
    """
    def nested_func(value: Any):
        """
        Iterate through all the field types provided by the parent function
        and check whether the provided value can be deserialized into any of them
        :return: The first appropriate deserialized value
        """
        for class_option in options:
            try:
                deserialized_value = Deserializable.deserialize_as_type(class_option, value)
            except Exception as e:
                # doesn't matter what the problem is, just go to the next one
                continue

            return deserialized_value
        raise TypeError(f"Could not deserialize {value} with {options}")

    return nested_func

