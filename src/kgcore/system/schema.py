"""
System Graph Schema - Constants for system graph labels and properties.
"""

# System graph labels (entity types)
class SysLabels:
    """System graph entity type labels."""
    CodeObject = "http://kgcore.org/system/CodeObject"
    Class = "http://kgcore.org/system/Class"
    Function = "http://kgcore.org/system/Function"
    Instance = "http://kgcore.org/system/Instance"
    Run = "http://kgcore.org/system/Run"
    PydanticModel = "http://kgcore.org/system/PydanticModel"
    PydanticInstance = "http://kgcore.org/system/PydanticInstance"
    Object = "http://kgcore.org/system/Object"
    Attribute = "http://kgcore.org/system/Attribute"
    
    # Relations
    CALLS = "http://kgcore.org/system/calls"
    HAS_ATTRIBUTE = "http://kgcore.org/system/hasAttribute"
    IS_INSTANCE_OF = "http://kgcore.org/system/isInstanceOf"


# System graph properties
class SysProperties:
    """System graph property keys."""
    QUALNAME = "http://kgcore.org/system/qualname"
    NAME = "http://kgcore.org/system/name"
    MODULE = "http://kgcore.org/system/module"
    DESCRIPTION = "http://kgcore.org/system/description"
    INSTANCE_ID = "http://kgcore.org/system/instanceId"
    TIMESTAMP = "http://kgcore.org/system/timestamp"
    STATUS = "http://kgcore.org/system/status"
    ERROR = "http://kgcore.org/system/error"
    RESULT = "http://kgcore.org/system/result"
    FIELD_NAME = "http://kgcore.org/system/fieldName"
    FIELD_TYPE = "http://kgcore.org/system/fieldType"
    FIELD_DESCRIPTION = "http://kgcore.org/system/fieldDescription"
    OBJECT_ID = "http://kgcore.org/system/objectId"
    SERIALIZED_DATA = "http://kgcore.org/system/serializedData"

