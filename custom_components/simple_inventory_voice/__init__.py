"""Inventory Voice integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


DOMAIN = "simple_inventory_voice"


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
