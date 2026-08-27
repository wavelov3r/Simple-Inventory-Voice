"""Inventory Voice integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


DOMAIN = "simple_inventory_voice"
INVENTORY_DOMAIN = "simple_inventory"


def inventory_id_from_entity(
    hass: HomeAssistant,
    entity_id: str | None,
) -> str | None:
    """Return the Simple Inventory ID exposed by an inventory entity."""

    if not entity_id:
        return None

    state = hass.states.get(entity_id)
    if state is None:
        return None

    inventory_id = state.attributes.get("inventory_id")
    return inventory_id if isinstance(inventory_id, str) else None


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Set up Inventory Voice."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Inventory Voice config entry."""
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload Inventory Voice config entry."""
    return True