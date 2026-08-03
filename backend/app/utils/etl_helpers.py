from typing import Iterable


def update_if_changed(existing, new_data, fields: Iterable[str]) -> bool:
    """
    Compare the specified fields between two SQLAlchemy ORM objects.

    Parameters
    ----------
    existing : SQLAlchemy Model
        Existing object from the database.

    new_data : SQLAlchemy Model
        Newly created object containing the latest data.

    fields : Iterable[str]
        List of field names to compare.

    Returns
    -------
    bool
        True  -> At least one field was updated.
        False -> No fields changed.
    """

    changed = False

    for field in fields:

        existing_value = getattr(existing, field)
        new_value = getattr(new_data, field)

        if existing_value != new_value:
            setattr(existing, field, new_value)
            changed = True

    return changed