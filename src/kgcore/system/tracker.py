class KGTracker:
    """
    Small helper that can enable/disable KG tracking per object.
    It just flips attributes on the decorated class/function.
    """

    # --- per-object switches -----------------------------------------

    @staticmethod
    def disable(obj, *, calls=True, definition=False):
        """
        Disable tracking for a specific class or function.

        calls=True        -> stop logging calls/inits
        definition=True   -> stop (or skip) publishing the definition
        """
        if calls:
            setattr(obj, "__kg_track_calls__", False)
        if definition:
            setattr(obj, "__kg_track_definition__", False)

    @staticmethod
    def enable(obj, *, calls=True, definition=False):
        """
        Re-enable tracking for a specific class or function.
        """
        if calls:
            setattr(obj, "__kg_track_calls__", True)
        if definition:
            setattr(obj, "__kg_track_definition__", True)

    @staticmethod
    def calls_enabled(obj) -> bool:
        return getattr(obj, "__kg_track_calls__", True)

    @staticmethod
    def definition_enabled(obj) -> bool:
        return getattr(obj, "__kg_track_definition__", True)
