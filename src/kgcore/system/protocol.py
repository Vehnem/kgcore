from typing import Protocol, Mapping, Any, Optional

class KGAnnotatable(Protocol):
    def kg_definition(self) -> Mapping[str, Any]:
        ...
    def kg_call(self, *args, **kwargs) -> Mapping[str, Any]:
        ...
    def kg_id(self) -> Optional[str]:
        """
        Optional deterministic instance identifier.
        If provided, the same instance data will map to the same KG ID across runs.
        """
        ...