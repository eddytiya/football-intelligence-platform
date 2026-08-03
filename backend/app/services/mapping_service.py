from sqlalchemy.orm import Session

from app.models.external_id import ExternalID


class MappingService:
    """
    Service responsible for managing mappings between
    internal database IDs and external provider IDs.
    """

    @staticmethod
    def get_internal_id(
        db: Session,
        entity_type: str,
        provider: str,
        external_id: int | str,
    ) -> int | None:
        """
        Return the internal entity ID for an external ID.
        """

        external_id = str(external_id)

        mapping = (
            db.query(ExternalID)
            .filter(
                ExternalID.entity_type == entity_type,
                ExternalID.provider == provider,
                ExternalID.external_id == external_id,
            )
            .first()
        )

        return mapping.entity_id if mapping else None

    @staticmethod
    def get_external_id(
        db: Session,
        entity_type: str,
        provider: str,
        entity_id: int,
    ) -> int | str | None:
        """
        Return the external ID for an internal entity.
        """

        mapping = (
            db.query(ExternalID)
            .filter(
                ExternalID.entity_type == entity_type,
                ExternalID.provider == provider,
                ExternalID.entity_id == entity_id,
            )
            .first()
        )

        return mapping.external_id if mapping else None

    @staticmethod
    def mapping_exists(
        db: Session,
        entity_type: str,
        provider: str,
        external_id: int | str,
    ) -> bool:
        """
        Check whether a mapping exists.
        """

        external_id = str(external_id)

        return (
            db.query(ExternalID)
            .filter(
                ExternalID.entity_type == entity_type,
                ExternalID.provider == provider,
                ExternalID.external_id == external_id,
            )
            .first()
            is not None
        )

    @staticmethod
    def save_mapping(
        db: Session,
        entity_type: str,
        provider: str,
        entity_id: int,
        external_id: int | str,
        existing_mappings: dict[int, ExternalID] | None = None,
    ) -> ExternalID:
        """
        Create or update a mapping.

        If a mapping cache is provided, use it to avoid
        unnecessary database queries.

        NOTE:
        This method DOES NOT commit.
        """

        external_id = str(external_id)

        if existing_mappings is not None:
            mapping = existing_mappings.get(entity_id)
        else:
            mapping = None

        if mapping is None:

            mapping = (
                db.query(ExternalID)
                .filter(
                    ExternalID.entity_type == entity_type,
                    ExternalID.provider == provider,
                    ExternalID.entity_id == entity_id,
                )
                .first()
            )

        if mapping is None:

            mapping = ExternalID(
                entity_type=entity_type,
                provider=provider,
                entity_id=entity_id,
                external_id=external_id,
            )

            db.add(mapping)

            if existing_mappings is not None:
                existing_mappings[entity_id] = mapping

        else:

            mapping.external_id = external_id

        db.flush()

        return mapping

    @staticmethod
    def delete_mapping(
        db: Session,
        entity_type: str,
        provider: str,
        entity_id: int,
    ) -> None:
        """
        Delete a mapping.

        NOTE:
        This method DOES NOT commit.
        """

        mapping = (
            db.query(ExternalID)
            .filter(
                ExternalID.entity_type == entity_type,
                ExternalID.provider == provider,
                ExternalID.entity_id == entity_id,
            )
            .first()
        )

        if mapping:
            db.delete(mapping)

    @staticmethod
    def require_internal_id(
        db: Session,
        entity_type: str,
        provider: str,
        external_id: int | str,
    ) -> int:
        """
        Return an internal ID or raise an error if
        the mapping does not exist.
        """

        entity_id = MappingService.get_internal_id(
            db=db,
            entity_type=entity_type,
            provider=provider,
            external_id=external_id,
        )

        if entity_id is None:
            raise ValueError(
                f"No mapping found for "
                f"{entity_type} "
                f"({provider}:{external_id})"
            )

        return entity_id