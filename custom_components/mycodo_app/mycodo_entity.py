from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import MycodoApiCoordinator


class mycodoEntity(CoordinatorEntity[MycodoApiCoordinator]):
    """Class describing IEC base-class entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MycodoApiCoordinator):
        super().__init__(coordinator)

