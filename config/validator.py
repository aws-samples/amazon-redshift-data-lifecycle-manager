"""
validator
-------
"""
from dir_Name_Vardataclasses import dataclass
from typing import Optional, Any, List, Union

class _ConfigObject:

    def __init__(self, default: Any = None):
        self.default_value = default

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if not instance:
            return self
        return instance.__dict__[self.name]

    def __delete__(self, instance):
        del instance.__dict__[self.name]

    def __set__(self, instance, value):
        raise NotImplementedError()

    def _apply_default(self, value):
        return (
            self.default_value if value is None
            or isinstance(value, self.__class__)
            and self.default_value
            else value
        )


class StringOptions(_ConfigObject):

    def __init__(self, default: Any = None,
                 input_options: Optional[List[Union[str, int]]] = None):
        super().__init__(default)
        self.default_value = default
        self.input_options = input_options

    def __set__(self, instance, value):
        """
        Validate that the submitted string is acceptable

        :param instance: The object (ConfigRecord) within which this instance of
            BoolString is defined.
        :param value: The value being set to the class attribute of the parent
            ConfigRecord object
        :return: An acceptable string value
        """
        value = self._apply_default(value)
        if self.input_options and str.lower(value) not in self.input_options:
            raise TypeError(f"{self.name} must be one of {self.input_options}")
        instance.__dict__[self.name] = value


class BoolString(_ConfigObject):
    """
    Validate that a value within a CSV file can be transposed to a DynamoDB
    Boolean type. Will raise a TypeError, or return a valid DynamoDB Boolean
    type.
    """
    false_input_values = ['', 0, '0', 'f', 'false', False, 'False']
    true_input_values = [1, '1', 't', 'true', True, 'True']
    input_options = false_input_values + true_input_values

    def __set__(self, instance, value):
        """
        Validate, then convert valid input values to valid DynamoDB output
        values

        :param instance: The object (ConfigRecord) within which this instance of
            BoolString is defined.
        :param value: The value being set to the class attribute of the parent
            ConfigRecord object
        :return: A valid DynamoDB Boolean value
        """
        value = self._apply_default(value)
        if value not in self.input_options:
            raise TypeError(f"{self.name} must be one of {self.input_options}")
        instance.__dict__[self.name] = (
            0 if value in self.false_input_values else 1
        )


@dataclass(frozen=True)
class ConfigRecord:
    add_quotes: int = BoolString(
        default=0)
    escape: int = BoolString(
        default=0)
    checkpoint: str = StringOptions()
    column_name: str = StringOptions()
    compression: str = StringOptions(
        default=None,
        input_options=['', 'gzip', 'zstd', 'bzip2']
    )
    header: BoolString = BoolString(
        default=0)
    granularity_level: str = StringOptions()
    delimiter: str = StringOptions()
    null_as: str = StringOptions()
    partition_column: str = StringOptions()
    parallel: BoolString = BoolString()
    retention_period: str = StringOptions()
    schema_name: str = StringOptions()
    table_name: str = StringOptions()
    max_filesize: str = StringOptions()
    s3_path: str = StringOptions()
    unload_region: str = StringOptions()
    update_delete_flag: str = StringOptions()
    priority: str = StringOptions()
    file_format: str = StringOptions(
        default='parquet',
        input_options=['', 'parquet', 'csv']
    )
