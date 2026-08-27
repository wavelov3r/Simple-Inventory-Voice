"""Config flow for Inventory Voice."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import DOMAIN, inventory_id_from_entity


INVENTORY_DOMAIN = "simple_inventory"


DEFAULT_CATEGORIES = """cibo: alimenti, mangiare
pulizia: detergenti, detersivi
hardware: elettronica, componenti
filamenti: filament, filamento"""


DEFAULT_LOCATIONS = """cucina: cucina
ripostiglio: sgabuzzino, dispensa
garage: box
ufficio: studio"""


DEFAULT_REQUIRED = {
    "require_quantity": True,
    "require_unit": True,
    "require_category": True,
    "require_location": True,
    "require_expiry": True,
}


DEFAULT_LANGUAGE = "ita"


def _extract_items(response: Any) -> list[dict[str, Any]]:
    """Normalize Simple Inventory get_items response."""

    if not response:
        return []

    if isinstance(response, dict):
        if isinstance(response.get("items"), list):
            return response["items"]

        for value in response.values():
            if isinstance(value, dict):
                items = value.get("items")
                if isinstance(items, list):
                    return items

    return []


def _parse_alias_lines(
    raw: str,
) -> tuple[list[str], dict[str, list[str]]]:
    """Parse multiline config and preserve order and aliases."""

    order: list[str] = []
    values: dict[str, list[str]] = {}

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if ":" in stripped:
            canonical, aliases_raw = stripped.split(":", 1)
        else:
            canonical, aliases_raw = stripped, ""

        canonical = canonical.strip()
        if not canonical:
            continue

        if canonical not in values:
            order.append(canonical)
            values[canonical] = []

        for alias in aliases_raw.split(","):
            cleaned = alias.strip()
            if (
                cleaned
                and cleaned.lower() != canonical.lower()
                and cleaned not in values[canonical]
            ):
                values[canonical].append(cleaned)

    return order, values


def _filter_to_discovered_values(
    order: list[str],
    values: dict[str, list[str]],
    discovered: set[str],
) -> str:
    """Keep discovered values and aliases for matching configured values."""

    configured_by_lower = {
        canonical.lower(): aliases
        for canonical, aliases in values.items()
    }
    filtered_order = sorted(discovered, key=str.lower)
    filtered_values = {
        canonical: configured_by_lower.get(
            canonical.lower(),
        ) or []
        for canonical in filtered_order
    }

    return _serialize_alias_lines(
        filtered_order,
        filtered_values,
    )


def _serialize_alias_lines(
    order: list[str],
    values: dict[str, list[str]],
) -> str:
    """Serialize canonical values and aliases into multiline text."""

    lines: list[str] = []

    for canonical in order:
        aliases = values.get(canonical, [])
        if aliases:
            lines.append(
                f"{canonical}: {', '.join(aliases)}"
            )
        else:
            lines.append(canonical)

    return "\n".join(lines)


def _collect_existing_values(
    items: list[dict[str, Any]],
    field: str,
) -> set[str]:
    """Collect distinct non-empty string field values from inventory items."""

    found: set[str] = set()

    for item in items:
        value = item.get(field)
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                found.add(cleaned)

    return found


class InventoryVoiceConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a config flow for Inventory Voice."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup."""

        if user_input is not None:
            return self.async_create_entry(
                title="Simple Inventory Voice",
                data={
                    "inventory_entity": user_input[
                        "inventory_entity"
                    ],
                },
                options={
                    "language": user_input.get(
                        "language",
                        DEFAULT_LANGUAGE,
                    ),
                    "categories": user_input.get(
                        "categories",
                        DEFAULT_CATEGORIES,
                    ),
                    "locations": user_input.get(
                        "locations",
                        DEFAULT_LOCATIONS,
                    ),
                    "require_quantity": user_input.get(
                        "require_quantity",
                        True,
                    ),
                    "require_unit": user_input.get(
                        "require_unit",
                        True,
                    ),
                    "require_category": user_input.get(
                        "require_category",
                        True,
                    ),
                    "require_location": user_input.get(
                        "require_location",
                        True,
                    ),
                    "require_expiry": user_input.get(
                        "require_expiry",
                        True,
                    ),
                    "allow_new_categories_locations": user_input.get(
                        "allow_new_categories_locations",
                        False,
                    ),
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "inventory_entity"
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            integration=INVENTORY_DOMAIN,
                        )
                    ),
                    vol.Optional(
                        "language",
                        default=DEFAULT_LANGUAGE,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["ita", "eng"],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        "categories",
                        default=DEFAULT_CATEGORIES,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiline=True
                        )
                    ),
                    vol.Optional(
                        "locations",
                        default=DEFAULT_LOCATIONS,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiline=True
                        )
                    ),
                    vol.Optional(
                        "require_quantity",
                        default=True,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "require_unit",
                        default=True,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "require_category",
                        default=True,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "require_location",
                        default=True,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "require_expiry",
                        default=True,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "allow_new_categories_locations",
                        default=False,
                    ): selector.BooleanSelector(),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""

        return InventoryVoiceOptionsFlow()


class InventoryVoiceOptionsFlow(
    config_entries.OptionsFlow
):
    """Handle Inventory Voice options."""

    async def _fetch_inventory_items(
        self,
    ) -> list[dict[str, Any]] | None:
        """Fetch current Simple Inventory items for this config entry."""

        inventory_id = inventory_id_from_entity(
            self.hass,
            self.config_entry.data.get("inventory_entity"),
        ) or self.config_entry.data.get("inventory_id")
        if not inventory_id:
            return None

        try:
            response = await self.hass.services.async_call(
                INVENTORY_DOMAIN,
                "get_items",
                {
                    "inventory_id": inventory_id,
                },
                blocking=True,
                return_response=True,
            )
        except Exception:
            return None

        return _extract_items(response)

    def _merged_alias_default(
        self,
        configured_value: str,
        discovered: set[str],
    ) -> str:
        """Filter configured aliases to existing canonical values."""

        order, values = _parse_alias_lines(
            configured_value
        )
        return _filter_to_discovered_values(
            order,
            values,
            discovered,
        )

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""

        if user_input is not None:
            # Keep the selected entity in data as the authoritative source.
            new_data = dict(self.config_entry.data)
            if "inventory_entity" in user_input:
                new_data["inventory_entity"] = user_input.pop(
                    "inventory_entity"
                )
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                )
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        options = self.config_entry.options
        items = await self._fetch_inventory_items()

        configured_categories = options.get(
            "categories",
            DEFAULT_CATEGORIES,
        )
        configured_locations = options.get(
            "locations",
            DEFAULT_LOCATIONS,
        )

        if items is None:
            merged_categories = str(configured_categories)
            merged_locations = str(configured_locations)
        else:
            existing_categories = _collect_existing_values(
                items,
                "category",
            )
            existing_locations = _collect_existing_values(
                items,
                "location",
            )

            merged_categories = self._merged_alias_default(
                str(configured_categories),
                existing_categories,
            )
            merged_locations = self._merged_alias_default(
                str(configured_locations),
                existing_locations,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "inventory_entity",
                        default=self.config_entry.data.get(
                            "inventory_entity", ""
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            integration=INVENTORY_DOMAIN,
                        )
                    ),
                    vol.Optional(
                        "language",
                        default=options.get(
                            "language",
                            DEFAULT_LANGUAGE,
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["ita", "eng"],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        "categories",
                        default=merged_categories,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiline=True
                        )
                    ),
                    vol.Optional(
                        "locations",
                        default=merged_locations,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiline=True
                        )
                    ),
                    vol.Optional(
                        "require_quantity",
                        default=options.get(
                            "require_quantity",
                            True,
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "require_unit",
                        default=options.get(
                            "require_unit",
                            True,
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "require_category",
                        default=options.get(
                            "require_category",
                            True,
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "require_location",
                        default=options.get(
                            "require_location",
                            True,
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "require_expiry",
                        default=options.get(
                            "require_expiry",
                            True,
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        "allow_new_categories_locations",
                        default=options.get(
                            "allow_new_categories_locations",
                            False,
                        ),
                    ): selector.BooleanSelector(),
                }
            ),
        )