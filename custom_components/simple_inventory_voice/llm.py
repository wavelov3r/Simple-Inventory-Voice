"""LLM tools for Inventory Voice."""

from __future__ import annotations

import difflib
from typing import Any

import voluptuous as vol

from homeassistant.components import llm
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.llm import LLMContext, ToolInput
from homeassistant.util.json import JsonObjectType

from . import DOMAIN, inventory_id_from_entity


INVENTORY_DOMAIN = "simple_inventory"


DEFAULT_REQUIRED_OPTIONS = {
    "require_quantity": True,
    "require_unit": True,
    "require_category": True,
    "require_location": True,
    "require_expiry": True,
}


DEFAULT_LANGUAGE = "ita"


MESSAGES = {
    "ita": {
        "no_inventory": "Nessun inventario Simple Inventory configurato.",
        "item_missing_after_update": "L'elemento non è stato trovato dopo l'aggiornamento.",
        "invalid_returned_quantity": "La quantità restituita dall'inventario non è valida.",
        "quantity_not_verified": "Quantità non verificata: l'inventario riporta {quantity:g}.",
        "invalid_value": "{field} '{value}' non valida. Usa una delle {field} esistenti.",
        "missing_required": "Mancano informazioni obbligatorie: {fields}.",
        "add_failed": "Inserimento non riuscito: {error}",
        "item_missing_after_add": "L'elemento non risulta presente dopo l'inserimento.",
        "item_added": "{name} aggiunto all'inventario.",
        "negative_quantity": "La quantità non può essere negativa.",
        "item_not_found": "Non trovo '{name}' nell'inventario.",
        "quantity_not_updated": "Quantità non aggiornata.",
        "quantity_set": "Quantità di '{name}' impostata a {quantity:g}.",
        "positive_add_quantity": "La quantità da aggiungere deve essere positiva.",
        "invalid_current_quantity": "La quantità attuale dell'elemento non è valida.",
        "quantity_added": "Aggiunti {quantity:g} a '{name}'.",
        "positive_remove_quantity": "La quantità da rimuovere deve essere positiva.",
        "insufficient_quantity": "Quantità insufficiente: disponibili {quantity:g}.",
        "quantity_remaining": "Rimangono {quantity:g} nell'inventario.",
        "read_failed": "Impossibile leggere l'inventario: {error}",
        "delete_failed": "Eliminazione non riuscita: {error}",
        "item_still_present": "L'elemento risulta ancora presente nell'inventario.",
        "item_deleted": "'{name}' eliminato dall'inventario.",
        "delete_confirmation_required": "Vuoi eliminare definitivamente '{name}' dal database, inclusa la sua cronologia? Questa azione non può essere annullata. Rispondi confermando esplicitamente, ad esempio 'sì, elimina dal database', per procedere.",
        "barcode_lookup_failed": "Ricerca del codice a barre non riuscita: {error}",
        "barcode_not_found": "Nessun elemento trovato per il codice '{barcode}'.",
        "positive_quantity": "La quantità deve essere positiva.",
        "barcode_scan_failed": "Scansione del codice a barre non riuscita: {error}",
        "barcode_invalid_response": "La scansione non ha restituito un risultato valido.",
        "consumption_failed": "Analisi dei consumi non riuscita: {error}",
        "consumption_invalid_response": "L'analisi non ha restituito dati validi.",
        "read_all_failed": "Impossibile leggere tutti gli inventari: {error}",
        "read_all_invalid_response": "La lettura non ha restituito dati validi.",
        "item_missing_after_delete": "L'elemento non risulta presente dopo l'aggiornamento.",
        "update_failed": "Aggiornamento non riuscito: {error}",
        "item_missing_after_update_action": "L'elemento non risulta presente dopo l'aggiornamento.",
        "item_updated": "'{name}' aggiornato.",
        "expiry_alert_not_verified": "I giorni di avviso scadenza non sono stati verificati: l'inventario riporta {days}.",
        "expiry_current": "L'elemento '{name}' ha attualmente scadenza {expiry}. Quale deve essere la nuova scadenza?",
        "expiry_missing": "L'elemento '{name}' non ha una scadenza impostata. Quale scadenza vuoi impostare?",
        "similar_item_found": "Non trovo '{name}' nell'inventario. Ti riferisci a '{candidate}'?",
        "similar_items_found": "Non trovo '{name}' nell'inventario. Forse intendi uno di questi: {candidates}?",
        "item_found_other_location": "Non trovo '{name}' in questa posizione. Forse intendi '{candidate}' in '{location}'?",
    },
    "eng": {
        "no_inventory": "No Simple Inventory inventory is configured.",
        "item_missing_after_update": "The item was not found after the update.",
        "invalid_returned_quantity": "The quantity returned by the inventory is invalid.",
        "quantity_not_verified": "Quantity could not be verified: the inventory reports {quantity:g}.",
        "invalid_value": "{field} '{value}' is invalid. Use one of the existing {field} values.",
        "missing_required": "Required information is missing: {fields}.",
        "add_failed": "Could not add the item: {error}",
        "item_missing_after_add": "The item is not present after it was added.",
        "item_added": "{name} was added to the inventory.",
        "negative_quantity": "The quantity cannot be negative.",
        "item_not_found": "I cannot find '{name}' in the inventory.",
        "quantity_not_updated": "The quantity was not updated.",
        "quantity_set": "Quantity for '{name}' was set to {quantity:g}.",
        "positive_add_quantity": "The quantity to add must be positive.",
        "invalid_current_quantity": "The item's current quantity is invalid.",
        "quantity_added": "Added {quantity:g} to '{name}'.",
        "positive_remove_quantity": "The quantity to remove must be positive.",
        "insufficient_quantity": "Insufficient quantity: {quantity:g} available.",
        "quantity_remaining": "{quantity:g} remain in the inventory.",
        "read_failed": "Could not read the inventory: {error}",
        "delete_failed": "Could not delete the item: {error}",
        "item_still_present": "The item is still present in the inventory.",
        "item_deleted": "'{name}' was deleted from the inventory.",
        "delete_confirmation_required": "Do you want to permanently delete '{name}' from the database, including its history? This cannot be undone. Reply with an explicit confirmation, e.g. 'yes, delete from the database', to proceed.",
        "barcode_lookup_failed": "Barcode lookup failed: {error}",
        "barcode_not_found": "No item was found for barcode '{barcode}'.",
        "positive_quantity": "The quantity must be positive.",
        "barcode_scan_failed": "Barcode scan failed: {error}",
        "barcode_invalid_response": "The barcode scan returned an invalid result.",
        "consumption_failed": "Consumption analysis failed: {error}",
        "consumption_invalid_response": "Consumption analysis returned invalid data.",
        "read_all_failed": "Could not read all inventories: {error}",
        "read_all_invalid_response": "Reading all inventories returned invalid data.",
        "item_missing_after_delete": "The item was not found after the update.",
        "update_failed": "Update failed: {error}",
        "item_missing_after_update_action": "The item is not present after the update.",
        "item_updated": "'{name}' was updated.",
        "expiry_alert_not_verified": "Expiry alert days could not be verified: the inventory reports {days}.",
        "expiry_current": "'{name}' currently expires on {expiry}. What should the new expiration date be?",
        "expiry_missing": "'{name}' has no expiration date set. What expiration date would you like to set?",
        "similar_item_found": "I cannot find '{name}' in the inventory. Did you mean '{candidate}'?",
        "similar_items_found": "I cannot find '{name}' in the inventory. Did you mean one of these: {candidates}?",
        "item_found_other_location": "I cannot find '{name}' in that location. Did you mean '{candidate}' in '{location}'?",
    },
}


FIELD_LABELS = {
    "ita": {
        "quantity": "quantità",
        "unit": "unità",
        "category": "categoria",
        "location": "posizione",
        "expiry_date": "scadenza",
    },
    "eng": {
        "quantity": "quantity",
        "unit": "unit",
        "category": "category",
        "location": "location",
        "expiry_date": "expiration date",
    },
}


def _loaded_entry(hass: HomeAssistant) -> ConfigEntry | None:
    """Return the loaded Inventory Voice entry when exactly one exists."""

    entries = hass.config_entries.async_entries(DOMAIN)

    loaded_entries = [
        entry
        for entry in entries
        if entry.state is ConfigEntryState.LOADED
    ]

    if len(loaded_entries) == 1:
        return loaded_entries[0]

    return None


def _entry_options(hass: HomeAssistant) -> dict[str, Any]:
    """Return options for the single loaded Inventory Voice entry."""

    entry = _loaded_entry(hass)
    if entry is None:
        return {}

    return dict(entry.options)


def _language(hass: HomeAssistant) -> str:
    """Return the configured response language."""

    language = _entry_options(hass).get("language", DEFAULT_LANGUAGE)
    return language if language in MESSAGES else DEFAULT_LANGUAGE


def _message(hass: HomeAssistant, key: str, **values: Any) -> str:
    """Return a localized LLM response message."""

    return MESSAGES[_language(hass)][key].format(**values)


def _parse_alias_config(raw: str) -> dict[str, str]:
    """Parse multiline alias config into alias->canonical map."""

    alias_map: dict[str, str] = {}

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

        alias_map[canonical.lower()] = canonical

        for alias in aliases_raw.split(","):
            cleaned_alias = alias.strip()
            if cleaned_alias:
                alias_map[cleaned_alias.lower()] = canonical

    return alias_map


def _collect_existing_values(
    items: list[dict[str, Any]],
    field: str,
) -> set[str]:
    """Collect distinct non-empty string values from inventory items."""

    values: set[str] = set()

    for item in items:
        value = item.get(field)
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                values.add(cleaned)

    return values


def _match_existing_case(
    value: str,
    existing_values: set[str],
) -> str | None:
    """Return existing value preserving its stored casing."""

    value_lower = value.lower()
    for existing in existing_values:
        if existing.lower() == value_lower:
            return existing

    return None


def _is_missing_field(
    args: dict[str, Any],
    key: str,
) -> bool:
    """Treat None/empty strings as missing while allowing numeric zero."""

    if key not in args:
        return True

    value = args[key]
    if value is None:
        return True

    if isinstance(value, str) and not value.strip():
        return True

    return False


def _required_options(options: dict[str, Any]) -> dict[str, bool]:
    """Return required flags using entry options with defaults."""

    return {
        key: bool(options.get(key, default_value))
        for key, default_value in DEFAULT_REQUIRED_OPTIONS.items()
    }


def _normalize_mapped_value(
    raw_value: str,
    alias_map: dict[str, str],
    existing_values: set[str],
    field: str,
    hass: HomeAssistant,
    allow_new: bool = False,
) -> tuple[str | None, JsonObjectType | None]:
    """Normalize a mapped value and validate against existing inventory values."""

    value = raw_value.strip()
    if not value:
        return None, None

    canonical = alias_map.get(value.lower(), value)

    if not existing_values:
        # Empty inventory: allow configured canonical values.
        return canonical, None

    matched = _match_existing_case(canonical, existing_values)
    if matched is not None:
        return matched, None

    if allow_new:
        # User opted in to create new categories/locations by voice.
        return canonical, None

    available_values = sorted(existing_values, key=str.lower)
    field_label = FIELD_LABELS[_language(hass)][field]
    return None, {
        "success": False,
        "action": "invalid_value",
        "field": field_label,
        "value": raw_value,
        "message": _message(
            hass,
            "invalid_value",
            field=field_label.capitalize(),
            value=raw_value,
        ),
        "available": available_values,
    }


def _allow_new_categories_locations(options: dict[str, Any]) -> bool:
    """Return whether new categories/locations may be created by voice."""

    return bool(options.get("allow_new_categories_locations", False))


def _item_search_names(item: dict[str, Any]) -> list[str]:
    """Return all searchable names (name + aliases) for an item."""

    names = [str(item.get("name", "")).strip()]
    aliases = item.get("aliases", [])
    if isinstance(aliases, str):
        aliases = aliases.split(",")
    if isinstance(aliases, list):
        names.extend(str(alias).strip() for alias in aliases)
    return [name for name in names if name]


def _is_similar_name(query: str, candidate: str) -> bool:
    """Return whether candidate is a fuzzy/partial match for query."""

    query_lower = query.strip().lower()
    candidate_lower = candidate.strip().lower()
    if not query_lower or not candidate_lower:
        return False

    if query_lower in candidate_lower or candidate_lower in query_lower:
        return True

    return (
        difflib.SequenceMatcher(None, query_lower, candidate_lower).ratio()
        >= 0.6
    )


def _find_similar_items(
    items: list[dict[str, Any]],
    name: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Find items with a name/alias similar to the given name."""

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in items:
        stored_name = str(item.get("name", "")).strip()
        if not stored_name or stored_name.lower() in seen:
            continue

        if any(
            _is_similar_name(name, candidate)
            for candidate in _item_search_names(item)
        ):
            seen.add(stored_name.lower())
            candidates.append(item)

        if len(candidates) >= limit:
            break

    return candidates


def _build_not_found_response(
    hass: HomeAssistant,
    items: list[dict[str, Any]],
    name: str,
    location: str | None = None,
) -> JsonObjectType:
    """Build a not-found response, suggesting similar items when possible."""

    if location:
        other_location_item = _find_inventory_item(items, name)
        if other_location_item is not None:
            actual_location = str(
                other_location_item.get("location", "")
            ).strip()
            return {
                "success": False,
                "action": "confirmation_required",
                "confirmation_required": True,
                "candidates": [_format_item(other_location_item)],
                "message": _message(
                    hass,
                    "item_found_other_location",
                    name=name,
                    candidate=other_location_item.get("name", name),
                    location=actual_location,
                ),
            }

    similar_items = _find_similar_items(items, name)
    if similar_items:
        candidate_names = [
            str(item.get("name", "")) for item in similar_items
        ]
        if len(candidate_names) == 1:
            message = _message(
                hass,
                "similar_item_found",
                name=name,
                candidate=candidate_names[0],
            )
        else:
            message = _message(
                hass,
                "similar_items_found",
                name=name,
                candidates=", ".join(
                    f"'{candidate}'" for candidate in candidate_names
                ),
            )
        return {
            "success": False,
            "action": "confirmation_required",
            "confirmation_required": True,
            "candidates": [_format_item(item) for item in similar_items],
            "message": message,
        }

    return {
        "success": False,
        "action": "not_found",
        "message": _message(hass, "item_not_found", name=name),
    }


def _inventory_id_from_context(
    hass: HomeAssistant,
    llm_context: LLMContext,
) -> str | None:
    """Return the configured inventory ID.

    If there is exactly one Inventory Voice config entry, use it.
    """

    entry = _loaded_entry(hass)
    if entry is not None:
        return inventory_id_from_entity(
            hass,
            entry.data.get("inventory_entity"),
        ) or entry.data.get("inventory_id")

    return None


def _extract_items(response: Any) -> list[dict[str, Any]]:
    """Normalize Simple Inventory get_items response."""

    if not response:
        return []

    if isinstance(response, dict):
        if isinstance(response.get("items"), list):
            return response["items"]

        # Some service responses may be wrapped by inventory ID.
        for value in response.values():
            if isinstance(value, dict):
                items = value.get("items")
                if isinstance(items, list):
                    return items

    return []


async def _get_inventory_items(
    hass: HomeAssistant,
    inventory_id: str,
    llm_context: LLMContext,
) -> list[dict[str, Any]]:
    """Read items from the configured inventory."""

    response = await hass.services.async_call(
        INVENTORY_DOMAIN,
        "get_items",
        {
            "inventory_id": inventory_id,
        },
        blocking=True,
        return_response=True,
        context=llm_context.context,
    )
    return _extract_items(response)


def _normalize_lookup_value(
    value: str | None,
    alias_map: dict[str, str] | None = None,
) -> str:
    """Normalize a lookup value using configured aliases when available."""

    if value is None:
        return ""

    normalized = str(value).strip()
    if not normalized:
        return ""

    normalized_lower = normalized.lower()
    if alias_map is not None:
        normalized = alias_map.get(normalized_lower, normalized)

    return str(normalized).strip().lower()


def _find_inventory_item(
    items: list[dict[str, Any]],
    name: str,
    location: str | None = None,
    location_aliases: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Find an item by name or alias and, when supplied, location."""

    name_lower = name.strip().lower()
    location_lower = _normalize_lookup_value(location, location_aliases)

    for item in items:
        item_names = [str(item.get("name", "")).strip().lower()]
        aliases = item.get("aliases", [])
        if isinstance(aliases, str):
            aliases = aliases.split(",")
        if isinstance(aliases, list):
            item_names.extend(
                str(alias).strip().lower()
                for alias in aliases
                if str(alias).strip()
            )

        if name_lower not in item_names:
            continue
        if location_lower and _normalize_lookup_value(
            item.get("location", ""),
            location_aliases,
        ) != location_lower:
            continue
        return item

    return None


async def _set_item_quantity(
    hass: HomeAssistant,
    inventory_id: str,
    item_name: str,
    quantity: float,
    llm_context: LLMContext,
    location: str | None = None,
) -> tuple[bool, str | None]:
    """Set quantity through the existing Simple Inventory update service."""

    try:
        await hass.services.async_call(
            INVENTORY_DOMAIN,
            "update_item",
            {
                "inventory_id": inventory_id,
                "old_name": item_name,
                "name": item_name,
                "quantity": quantity,
            },
            blocking=True,
            context=llm_context.context,
        )
        updated_items = await _get_inventory_items(
            hass,
            inventory_id,
            llm_context,
        )
    except Exception as err:
        return False, str(err)

    updated_item = _find_inventory_item(
        updated_items,
        item_name,
        location,
    )
    if updated_item is None:
        return False, _message(hass, "item_missing_after_update")

    try:
        actual_quantity = float(updated_item.get("quantity"))
    except (TypeError, ValueError):
        return False, _message(hass, "invalid_returned_quantity")

    if actual_quantity != quantity:
        return False, _message(
            hass,
            "quantity_not_verified",
            quantity=actual_quantity,
        )

    return True, None


async def _adjust_item_quantity(
    hass: HomeAssistant,
    inventory_id: str,
    item_name: str,
    amount: float,
    direction: str,
    expected_quantity: float,
    llm_context: LLMContext,
    location: str | None = None,
    price: float | None = None,
) -> tuple[bool, str | None]:
    """Adjust quantity through Simple Inventory and verify the result."""

    service_data: dict[str, Any] = {
        "inventory_id": inventory_id,
        "name": item_name,
        "amount": amount,
    }
    if price is not None:
        service_data["price"] = price

    try:
        await hass.services.async_call(
            INVENTORY_DOMAIN,
            f"{direction}_item",
            service_data,
            blocking=True,
            context=llm_context.context,
        )
        updated_items = await _get_inventory_items(
            hass,
            inventory_id,
            llm_context,
        )
    except Exception as err:
        return False, str(err)

    updated_item = _find_inventory_item(
        updated_items,
        item_name,
        location,
    )
    if updated_item is None:
        return False, _message(hass, "item_missing_after_update")

    try:
        actual_quantity = float(updated_item.get("quantity"))
    except (TypeError, ValueError):
        return False, _message(hass, "invalid_returned_quantity")

    if actual_quantity != expected_quantity:
        return False, _message(
            hass,
            "quantity_not_verified",
            quantity=actual_quantity,
        )

    return True, None


def _format_item(item: dict[str, Any]) -> dict[str, Any]:
    """Return only useful fields from an inventory item."""

    fields = (
        "name",
        "quantity",
        "unit",
        "category",
        "categories",
        "location",
        "locations",
        "expiry_date",
        "expiry_alert_days",
        "description",
        "barcode",
        "barcodes",
        "aliases",
        "price",
        "auto_add_enabled",
        "auto_add_to_list_quantity",
        "desired_quantity",
        "todo_list",
        "todo_quantity_placement",
    )

    return {
        key: item[key]
        for key in fields
        if key in item and item[key] is not None
    }


class InventoryAddItemTool(llm.Tool):
    """Add an item to Simple Inventory."""

    name = "inventory_add_item"

    description = """
Add a new item to the user's Simple Inventory.

Use this tool when the user says they bought, acquired, added, received,
or wants to put something into their inventory.

Required information:
- name
- quantity
- unit
- category
- location
- expiry_date

Optional information:
- description
- barcode
- aliases
- price
- expiry_alert_days
- auto_add_enabled
- auto_add_to_list_quantity
- desired_quantity
- todo_list
- todo_quantity_placement

The user may provide these values in any order.

If required information is missing, DO NOT invent it.
Return the missing fields so the assistant can ask the user.

expiry_date must be ISO format YYYY-MM-DD.
If the user gives only a month and year, use the first day of that month.

If the item already exists in the inventory, its stored category and
location are always used, ignoring any category/location passed here.
Do not use this tool to modify an existing item. Use inventory_update_item
for modifications.
"""

    parameters = vol.Schema(
        {
            vol.Required("name"): str,
            vol.Optional("quantity"): vol.Coerce(float),
            vol.Optional("unit"): str,
            vol.Optional("category"): str,
            vol.Optional("location"): str,
            vol.Optional("expiry_date"): str,
            vol.Optional("description"): str,
            vol.Optional("barcode"): str,
            vol.Optional("aliases"): str,
            vol.Optional("price"): vol.Coerce(float),
            vol.Optional("expiry_alert_days"): vol.Coerce(int),
            vol.Optional("auto_add_enabled"): bool,
            vol.Optional("auto_add_to_list_quantity"): vol.Coerce(float),
            vol.Optional("desired_quantity"): vol.Coerce(float),
            vol.Optional("todo_list"): str,
            vol.Optional("todo_quantity_placement"): vol.In(
                ("name", "description", "none")
            ),
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Add item."""

        inventory_id = _inventory_id_from_context(
            hass,
            llm_context,
        )

        if not inventory_id:
            raise HomeAssistantError(
                _message(hass, "no_inventory")
            )

        args = dict(tool_input.tool_args)
        options = _entry_options(hass)
        required_options = _required_options(options)

        items = await _get_inventory_items(hass, inventory_id, llm_context)

        existing_item = _find_inventory_item(items, args["name"])
        if existing_item is not None:
            # Adding to an already-known item: reuse its stored unit/expiry
            # only when not supplied, but always keep its stored
            # category/location, since changing them should go through
            # inventory_update_item rather than being silently overridden here.
            for key in ("unit", "expiry_date"):
                if _is_missing_field(args, key) and not _is_missing_field(
                    existing_item, key
                ):
                    args[key] = existing_item[key]

            for key in ("category", "location"):
                if not _is_missing_field(existing_item, key):
                    args[key] = existing_item[key]

        required_by_options = {
            "quantity": required_options["require_quantity"],
            "unit": required_options["require_unit"],
            "category": required_options["require_category"],
            "location": required_options["require_location"],
            "expiry_date": required_options["require_expiry"],
        }

        required_fields = {
            key: FIELD_LABELS[_language(hass)][key]
            for key in required_by_options
        }

        missing = [
            label
            for key, label in required_fields.items()
            if required_by_options[key]
            and _is_missing_field(args, key)
        ]

        if missing:
            return {
                "success": False,
                "missing": missing,
                "message": (
                    _message(
                        hass,
                        "missing_required",
                        fields=", ".join(missing),
                    )
                ),
            }

        category_aliases = _parse_alias_config(
            str(options.get("categories", ""))
        )
        location_aliases = _parse_alias_config(
            str(options.get("locations", ""))
        )

        existing_categories = _collect_existing_values(items, "category")
        existing_locations = _collect_existing_values(items, "location")
        allow_new = _allow_new_categories_locations(options)

        normalized_category = args.get("category")
        if isinstance(normalized_category, str):
            normalized_category, category_error = _normalize_mapped_value(
                normalized_category,
                category_aliases,
                existing_categories,
                "category",
                hass,
                allow_new,
            )
            if category_error is not None:
                return category_error

        normalized_location = args.get("location")
        if isinstance(normalized_location, str):
            normalized_location, location_error = _normalize_mapped_value(
                normalized_location,
                location_aliases,
                existing_locations,
                "location",
                hass,
                allow_new,
            )
            if location_error is not None:
                return location_error

        service_data: dict[str, Any] = {
            "inventory_id": inventory_id,
            "name": args["name"],
        }

        if not _is_missing_field(args, "quantity"):
            service_data["quantity"] = args["quantity"]

        if not _is_missing_field(args, "unit"):
            service_data["unit"] = args["unit"]

        if normalized_category:
            service_data["category"] = normalized_category

        if normalized_location:
            service_data["location"] = normalized_location

        if not _is_missing_field(args, "expiry_date"):
            service_data["expiry_date"] = args["expiry_date"]

        for field in (
            "description",
            "barcode",
            "aliases",
            "price",
            "expiry_alert_days",
            "auto_add_enabled",
            "auto_add_to_list_quantity",
            "desired_quantity",
            "todo_list",
            "todo_quantity_placement",
        ):
            if not _is_missing_field(args, field):
                service_data[field] = args[field]

        try:
            await hass.services.async_call(
                INVENTORY_DOMAIN,
                "add_item",
                service_data,
                blocking=True,
                context=llm_context.context,
            )
            created_items = await _get_inventory_items(
                hass,
                inventory_id,
                llm_context,
            )
        except Exception as err:
            return {
                "success": False,
                "action": "add_failed",
                "message": _message(hass, "add_failed", error=err),
            }

        if _find_inventory_item(created_items, args["name"]) is None:
            return {
                "success": False,
                "action": "add_failed",
                "message": _message(hass, "item_missing_after_add"),
            }

        return {
            "success": True,
            "action": "added",
            "item": {
                "name": args["name"],
                "quantity": service_data.get("quantity"),
                "unit": service_data.get("unit"),
                "category": service_data.get("category"),
                "location": service_data.get("location"),
                "expiry_date": service_data.get("expiry_date"),
                "description": service_data.get("description"),
                "barcode": service_data.get("barcode"),
                "price": service_data.get("price"),
                "expiry_alert_days": service_data.get("expiry_alert_days"),
                "auto_add_enabled": service_data.get("auto_add_enabled"),
                "auto_add_to_list_quantity": service_data.get(
                    "auto_add_to_list_quantity"
                ),
                "desired_quantity": service_data.get("desired_quantity"),
                "todo_list": service_data.get("todo_list"),
                "todo_quantity_placement": service_data.get(
                    "todo_quantity_placement"
                ),
            },
            "message": _message(hass, "item_added", name=args["name"]),
        }


class InventorySetQuantityTool(llm.Tool):
    """Set an existing inventory item's quantity."""

    name = "inventory_set_quantity"

    description = """
Set the exact quantity of an existing inventory item.

Use the configured inventory automatically. The location is optional and is
only used to distinguish items with the same name in different locations.
Never report success unless the resulting quantity is verified in inventory.
"""

    parameters = vol.Schema(
        {
            vol.Required("name"): str,
            vol.Required("quantity"): vol.Coerce(float),
            vol.Optional("location"): str,
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Set item quantity."""

        inventory_id = _inventory_id_from_context(
            hass,
            llm_context,
        )
        if not inventory_id:
            raise HomeAssistantError(
                _message(hass, "no_inventory")
            )

        args = tool_input.tool_args
        quantity = args["quantity"]
        if quantity < 0:
            return {
                "success": False,
                "action": "invalid_quantity",
                "message": _message(hass, "negative_quantity"),
            }

        items = await _get_inventory_items(
            hass,
            inventory_id,
            llm_context,
        )
        location = args.get("location")
        location_aliases = None
        if isinstance(location, str) and location.strip():
            options = _entry_options(hass)
            location_aliases = _parse_alias_config(
                str(options.get("locations", ""))
            )
            normalized_location, location_error = _normalize_mapped_value(
                location,
                location_aliases,
                _collect_existing_values(items, "location"),
                "location",
                hass,
                _allow_new_categories_locations(options),
            )
            if location_error is not None:
                return location_error
            location = normalized_location

        item = _find_inventory_item(
            items,
            args["name"],
            location,
            location_aliases,
        )
        if item is None:
            return _build_not_found_response(
                hass, items, args["name"], location
            )

        success, error = await _set_item_quantity(
            hass,
            inventory_id,
            str(item.get("name", args["name"])),
            quantity,
            llm_context,
            location,
        )
        if not success:
            return {
                "success": False,
                "action": "update_failed",
                "message": error or _message(hass, "quantity_not_updated"),
            }

        return {
            "success": True,
            "action": "quantity_set",
            "item": args["name"],
            "quantity": quantity,
            "message": _message(
                hass, "quantity_set", name=args["name"], quantity=quantity
            ),
        }


class InventoryIncrementQuantityTool(llm.Tool):
    """Increase an existing inventory item's quantity."""

    name = "inventory_increment_quantity"

    description = """
Increase the quantity of an existing inventory item.

Use this when the user restocks an item. Optionally include the unit price paid;
it updates the stored price and records the price on the restock event. Never
report success unless the resulting quantity is verified in inventory.
"""

    parameters = vol.Schema(
        {
            vol.Required("name"): str,
            vol.Required("quantity"): vol.Coerce(float),
            vol.Optional("location"): str,
            vol.Optional("price"): vol.Coerce(float),
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Increment item quantity."""

        inventory_id = _inventory_id_from_context(hass, llm_context)
        if not inventory_id:
            raise HomeAssistantError(
                _message(hass, "no_inventory")
            )

        args = tool_input.tool_args
        amount = args["quantity"]
        if amount <= 0:
            return {
                "success": False,
                "action": "invalid_quantity",
                "message": _message(hass, "positive_add_quantity"),
            }

        items = await _get_inventory_items(hass, inventory_id, llm_context)
        location = args.get("location")
        location_aliases = None
        if isinstance(location, str) and location.strip():
            options = _entry_options(hass)
            location_aliases = _parse_alias_config(
                str(options.get("locations", ""))
            )
            normalized_location, location_error = _normalize_mapped_value(
                location,
                location_aliases,
                _collect_existing_values(items, "location"),
                "location",
                hass,
                _allow_new_categories_locations(options),
            )
            if location_error is not None:
                return location_error
            location = normalized_location

        item = _find_inventory_item(
            items,
            args["name"],
            location,
            location_aliases,
        )
        if item is None:
            return _build_not_found_response(
                hass, items, args["name"], location
            )

        try:
            current_quantity = float(item.get("quantity"))
        except (TypeError, ValueError):
            return {
                "success": False,
                "action": "invalid_current_quantity",
                "message": _message(hass, "invalid_current_quantity"),
            }

        success, error = await _adjust_item_quantity(
            hass,
            inventory_id,
            str(item.get("name", args["name"])),
            amount,
            "increment",
            current_quantity + amount,
            llm_context,
            args.get("location"),
            args.get("price"),
        )
        if not success:
            return {
                "success": False,
                "action": "increment_failed",
                "message": error or _message(hass, "quantity_not_updated"),
            }

        return {
            "success": True,
            "action": "quantity_incremented",
            "item": str(item.get("name", args["name"])),
            "added_quantity": amount,
            "quantity": current_quantity + amount,
            "message": _message(
                hass, "quantity_added", name=args["name"], quantity=amount
            ),
        }


class InventoryRemoveQuantityTool(llm.Tool):
    """Remove a quantity from an existing inventory item."""

    name = "inventory_remove_quantity"

    description = """
Remove a quantity from an existing inventory item, e.g. when the user says
they consumed, used, ate, drank, or finished some amount ("ho consumato",
"ho finito", "ho usato").

Use the configured inventory automatically. The location is optional and is
only used to distinguish items with the same name in different locations.
Do not remove more than the current quantity. It is normal and expected for
the resulting quantity to reach 0 (item fully consumed): this tool never
deletes the item or its history, it only sets the quantity to 0. Do not use
inventory_delete_item for this case. Never report success unless the
resulting quantity is verified in inventory.
"""

    parameters = vol.Schema(
        {
            vol.Required("name"): str,
            vol.Required("quantity"): vol.Coerce(float),
            vol.Optional("location"): str,
            vol.Optional("price"): vol.Coerce(float),
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Remove item quantity."""

        inventory_id = _inventory_id_from_context(
            hass,
            llm_context,
        )
        if not inventory_id:
            raise HomeAssistantError(
                _message(hass, "no_inventory")
            )

        args = tool_input.tool_args
        amount = args["quantity"]
        if amount <= 0:
            return {
                "success": False,
                "action": "invalid_quantity",
                "message": _message(hass, "positive_remove_quantity"),
            }

        items = await _get_inventory_items(
            hass,
            inventory_id,
            llm_context,
        )
        location = args.get("location")
        location_aliases = None
        if isinstance(location, str) and location.strip():
            options = _entry_options(hass)
            location_aliases = _parse_alias_config(
                str(options.get("locations", ""))
            )
            normalized_location, location_error = _normalize_mapped_value(
                location,
                location_aliases,
                _collect_existing_values(items, "location"),
                "location",
                hass,
                _allow_new_categories_locations(options),
            )
            if location_error is not None:
                return location_error
            location = normalized_location

        item = _find_inventory_item(
            items,
            args["name"],
            location,
            location_aliases,
        )
        if item is None:
            return _build_not_found_response(
                hass, items, args["name"], location
            )

        try:
            current_quantity = float(item.get("quantity"))
        except (TypeError, ValueError):
            return {
                "success": False,
                "action": "invalid_current_quantity",
                "message": _message(hass, "invalid_current_quantity"),
            }

        new_quantity = current_quantity - amount
        if new_quantity < 0:
            return {
                "success": False,
                "action": "insufficient_quantity",
                "current_quantity": current_quantity,
                "message": _message(
                    hass,
                    "insufficient_quantity",
                    quantity=current_quantity,
                ),
            }

        success, error = await _adjust_item_quantity(
            hass,
            inventory_id,
            str(item.get("name", args["name"])),
            amount,
            "decrement",
            new_quantity,
            llm_context,
            location,
            args.get("price"),
        )
        if not success:
            return {
                "success": False,
                "action": "decrement_failed",
                "message": error or _message(hass, "quantity_not_updated"),
            }

        return {
            "success": True,
            "action": "quantity_removed",
            "item": args["name"],
            "removed_quantity": amount,
            "quantity": new_quantity,
            "message": _message(
                hass, "quantity_remaining", quantity=new_quantity
            ),
        }


class InventoryDeleteItemTool(llm.Tool):
    """Delete an item from Simple Inventory."""

    name = "inventory_delete_item"

    description = """
Permanently remove an item, including its history, from the configured
Simple Inventory database.

Only use this when the user explicitly asks to delete/erase the item from
the database (e.g. "elimina dal database", "cancella dal database", "delete
it from the database"). Running out of stock, consuming the last unit, or
the quantity reaching zero is NEVER a reason to call this tool: use
inventory_remove_quantity for that instead, which keeps the item (with its
history) at quantity 0.

Confirmation flow: call this tool without confirm=true first. It responds
with action="confirmation_required" and a confirmation message instead of
deleting anything. Read that message to the user and only call this tool
again with confirm=true after the user explicitly confirms. Never pass
confirm=true on the first call.

Never report success unless the item is no longer present after the service
call.
"""

    parameters = vol.Schema(
        {
            vol.Required("name"): str,
            vol.Optional("confirm", default=False): bool,
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Delete item and verify it no longer exists."""

        inventory_id = _inventory_id_from_context(hass, llm_context)
        if not inventory_id:
            raise HomeAssistantError(
                _message(hass, "no_inventory")
            )

        args = tool_input.tool_args
        item_name = args["name"]
        confirm = bool(args.get("confirm", False))
        try:
            items = await _get_inventory_items(hass, inventory_id, llm_context)
        except Exception as err:
            return {
                "success": False,
                "action": "read_failed",
                "message": _message(hass, "read_failed", error=err),
            }

        item = _find_inventory_item(items, item_name)
        if item is None:
            return _build_not_found_response(hass, items, item_name)

        stored_name = str(item.get("name", item_name))

        if not confirm:
            return {
                "success": False,
                "action": "confirmation_required",
                "confirmation_required": True,
                "item": stored_name,
                "message": _message(
                    hass, "delete_confirmation_required", name=stored_name
                ),
            }

        try:
            await hass.services.async_call(
                INVENTORY_DOMAIN,
                "remove_item",
                {"inventory_id": inventory_id, "name": stored_name},
                blocking=True,
                context=llm_context.context,
            )
            remaining_items = await _get_inventory_items(
                hass, inventory_id, llm_context
            )
        except Exception as err:
            return {
                "success": False,
                "action": "delete_failed",
                "message": _message(hass, "delete_failed", error=err),
            }

        if _find_inventory_item(remaining_items, stored_name) is not None:
            return {
                "success": False,
                "action": "delete_failed",
                "message": _message(hass, "item_still_present"),
            }

        return {
            "success": True,
            "action": "deleted",
            "item": stored_name,
            "message": _message(hass, "item_deleted", name=stored_name),
        }


class InventoryLookupBarcodeTool(llm.Tool):
    """Look up a barcode across all Simple Inventory inventories."""

    name = "inventory_lookup_barcode"

    description = """Find items by barcode across all Simple Inventory inventories."""

    parameters = vol.Schema({vol.Required("barcode"): str})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Look up barcode."""

        barcode = tool_input.tool_args["barcode"]
        try:
            response = await hass.services.async_call(
                INVENTORY_DOMAIN,
                "lookup_by_barcode",
                {"barcode": barcode},
                blocking=True,
                return_response=True,
                context=llm_context.context,
            )
        except Exception as err:
            return {
                "success": False,
                "action": "barcode_lookup_failed",
                "message": _message(
                    hass, "barcode_lookup_failed", error=err
                ),
            }

        items = _extract_items(response)
        if not items:
            return {
                "success": False,
                "action": "not_found",
                "message": _message(
                    hass, "barcode_not_found", barcode=barcode
                ),
            }

        return {
            "success": True,
            "count": len(items),
            "items": [_format_item(item) for item in items],
        }


class InventoryScanBarcodeTool(llm.Tool):
    """Act on an item identified by barcode."""

    name = "inventory_scan_barcode"

    description = """
Scan a barcode to increment, decrement, or look up an item. The inventory ID
is optional; omit it to let Simple Inventory resolve an unambiguous barcode.
"""

    parameters = vol.Schema(
        {
            vol.Required("barcode"): str,
            vol.Required("action"): vol.In(("increment", "decrement", "lookup")),
            vol.Optional("quantity", default=1): vol.Coerce(float),
            vol.Optional("price"): vol.Coerce(float),
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Scan barcode and return the service response."""

        args = tool_input.tool_args
        service_data: dict[str, Any] = {
            "barcode": args["barcode"],
            "action": args["action"],
        }
        if args["action"] != "lookup":
            if args["quantity"] <= 0:
                return {
                    "success": False,
                    "action": "invalid_quantity",
                    "message": _message(hass, "positive_quantity"),
                }
            service_data["amount"] = args["quantity"]
        if args.get("price") is not None:
            service_data["price"] = args["price"]

        try:
            response = await hass.services.async_call(
                INVENTORY_DOMAIN,
                "scan_barcode",
                service_data,
                blocking=True,
                return_response=True,
                context=llm_context.context,
            )
        except Exception as err:
            return {
                "success": False,
                "action": "barcode_scan_failed",
                "message": _message(hass, "barcode_scan_failed", error=err),
            }

        if not isinstance(response, dict) or response.get("success") is False:
            return {
                "success": False,
                "action": "barcode_scan_failed",
                "message": _message(hass, "barcode_invalid_response"),
                "response": response if isinstance(response, dict) else {},
            }

        return {"success": True, "result": response}


class InventoryConsumptionRatesTool(llm.Tool):
    """Retrieve consumption analytics for an inventory item."""

    name = "inventory_get_consumption_rates"

    description = """
Get consumption and spending analytics for an item, including daily and weekly
usage, estimated days until depletion, restock interval, and spending rates.
"""

    parameters = vol.Schema(
        {
            vol.Required("name"): str,
            vol.Optional("window_days"): vol.All(vol.Coerce(int), vol.Range(min=1)),
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Get consumption rates for an item."""

        inventory_id = _inventory_id_from_context(hass, llm_context)
        if not inventory_id:
            raise HomeAssistantError(
                _message(hass, "no_inventory")
            )

        args = tool_input.tool_args
        service_data: dict[str, Any] = {
            "inventory_id": inventory_id,
            "name": args["name"],
        }
        if args.get("window_days") is not None:
            service_data["window_days"] = args["window_days"]

        try:
            response = await hass.services.async_call(
                INVENTORY_DOMAIN,
                "get_item_consumption_rates",
                service_data,
                blocking=True,
                return_response=True,
                context=llm_context.context,
            )
        except Exception as err:
            return {
                "success": False,
                "action": "consumption_rates_failed",
                "message": _message(hass, "consumption_failed", error=err),
            }

        if not isinstance(response, dict):
            return {
                "success": False,
                "action": "consumption_rates_failed",
                "message": _message(hass, "consumption_invalid_response"),
            }

        return {"success": True, "rates": response}


class InventoryFindAllItemsTool(llm.Tool):
    """Retrieve Simple Inventory items across all inventories."""

    name = "inventory_find_all_items"

    description = """
Retrieve inventory items from every Simple Inventory inventory.

Use this only when the user explicitly asks about all inventories. Use
inventory_find_items for the configured inventory.
"""

    parameters = vol.Schema({})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Retrieve all inventory items."""

        try:
            response = await hass.services.async_call(
                INVENTORY_DOMAIN,
                "get_items_from_all_inventories",
                {},
                blocking=True,
                return_response=True,
                context=llm_context.context,
            )
        except Exception as err:
            return {
                "success": False,
                "action": "read_all_failed",
                "message": _message(hass, "read_all_failed", error=err),
            }

        if not isinstance(response, dict) or not isinstance(
            response.get("inventories"), list
        ):
            return {
                "success": False,
                "action": "read_all_failed",
                "message": _message(hass, "read_all_invalid_response"),
            }

        inventories = []
        for inventory in response["inventories"]:
            if not isinstance(inventory, dict):
                continue
            inventories.append(
                {
                    "inventory_id": inventory.get("inventory_id"),
                    "inventory_name": inventory.get("inventory_name"),
                    "items": [
                        _format_item(item)
                        for item in inventory.get("items", [])
                        if isinstance(item, dict)
                    ],
                }
            )

        return {"success": True, "inventories": inventories}


class InventoryFindItemsTool(llm.Tool):
    """Find items in Simple Inventory."""

    name = "inventory_find_items"

    description = """
Search the user's Simple Inventory.

Use this when the user asks:
- what they have
- whether they have an item
- what hardware they have
- what filaments they have
- what food they have
- which items are in a location
- which items belong to a category
- what ingredients are available

Always query the inventory rather than guessing.

Optional filters:
- query: item name or free text
- category
- location

Return the matching inventory items.
"""

    parameters = vol.Schema(
        {
            vol.Optional("query"): str,
            vol.Optional("category"): str,
            vol.Optional("location"): str,
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Search inventory."""

        inventory_id = _inventory_id_from_context(
            hass,
            llm_context,
        )

        if not inventory_id:
            raise HomeAssistantError(
                _message(hass, "no_inventory")
            )

        response = await hass.services.async_call(
            INVENTORY_DOMAIN,
            "get_items",
            {
                "inventory_id": inventory_id,
            },
            blocking=True,
            return_response=True,
            context=llm_context.context,
        )

        items = _extract_items(response)
        options = _entry_options(hass)

        category_aliases = _parse_alias_config(
            str(options.get("categories", ""))
        )
        location_aliases = _parse_alias_config(
            str(options.get("locations", ""))
        )

        existing_categories = _collect_existing_values(items, "category")
        existing_locations = _collect_existing_values(items, "location")

        args = tool_input.tool_args

        query = args.get("query", "").strip().lower()
        category = args.get("category", "").strip()
        location = args.get("location", "").strip()

        if category:
            normalized_category, _ = _normalize_mapped_value(
                category,
                category_aliases,
                existing_categories,
                "category",
                hass,
            )
            if normalized_category is not None:
                category = normalized_category

        if location:
            normalized_location, _ = _normalize_mapped_value(
                location,
                location_aliases,
                existing_locations,
                "location",
                hass,
            )
            if normalized_location is not None:
                location = normalized_location

        category = category.lower()
        location = location.lower()

        filtered: list[dict[str, Any]] = []

        for raw_item in items:
            item = _format_item(raw_item)

            if query:
                searchable = " ".join(
                    str(item.get(key, ""))
                    for key in (
                        "name",
                        "category",
                        "location",
                        "description",
                    )
                ).lower()

                if query not in searchable:
                    continue

            if category:
                if str(
                    item.get("category", "")
                ).lower() != category:
                    continue

            if location:
                if str(
                    item.get("location", "")
                ).lower() != location:
                    continue

            filtered.append(item)

        return {
            "success": True,
            "count": len(filtered),
            "items": filtered,
        }


class InventoryUpdateItemTool(llm.Tool):
    """Update an existing inventory item."""

    name = "inventory_update_item"

    description = """
Update an existing item in Simple Inventory.

Use this when the user explicitly wants to change an existing inventory item.

The item is identified by name.

Supported fields:
- name
- quantity
- unit
- category
- location
- expiry_date
- description
- barcode
- price
- aliases
- expiry_alert_days
- auto_add_enabled
- auto_add_to_list_quantity
- desired_quantity
- todo_list
- todo_quantity_placement

IMPORTANT EXPIRY RULE:
If the user asks to update the expiration date but does NOT provide the
new expiration date, DO NOT modify anything.

Instead:
1. Find the item first with inventory_find_items.
2. Tell the user its CURRENT expiration date.
3. Ask what the NEW expiration date should be.
4. Only call inventory_update_item after the user gives the new date.

If the user explicitly provides the new expiration date in the same request,
you may update it immediately.

EXPIRY ALERT RULE:
Use expiry_alert_days when the user asks to be alerted a number of days before
an item expires. This value is the number of days before expiry, and does not
change expiry_date. For example, "avvisami 4 giorni prima che scade" or
"alert me 4 days before it expires" requires expiry_alert_days=4.

Do not invent values.
"""

    parameters = vol.Schema(
        {
            vol.Required("name"): str,
            vol.Optional("new_name"): str,
            vol.Optional("quantity"): vol.Coerce(float),
            vol.Optional("unit"): str,
            vol.Optional("category"): str,
            vol.Optional("location"): str,
            vol.Optional("expiry_date"): str,
            vol.Optional("description"): str,
            vol.Optional("barcode"): str,
            vol.Optional("aliases"): str,
            vol.Optional("price"): vol.Coerce(float),
            vol.Optional("expiry_alert_days"): vol.Coerce(int),
            vol.Optional("auto_add_enabled"): bool,
            vol.Optional("auto_add_to_list_quantity"): vol.Coerce(float),
            vol.Optional("desired_quantity"): vol.Coerce(float),
            vol.Optional("todo_list"): str,
            vol.Optional("todo_quantity_placement"): vol.In(
                ("name", "description", "none")
            ),
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Update inventory item."""

        inventory_id = _inventory_id_from_context(
            hass,
            llm_context,
        )

        if not inventory_id:
            raise HomeAssistantError(
                _message(hass, "no_inventory")
            )

        args = tool_input.tool_args
        options = _entry_options(hass)

        old_name = args["name"]

        # ---------------------------------------------------------
        # Get current item first.
        # ---------------------------------------------------------

        response = await hass.services.async_call(
            INVENTORY_DOMAIN,
            "get_items",
            {
                "inventory_id": inventory_id,
            },
            blocking=True,
            return_response=True,
            context=llm_context.context,
        )

        items = _extract_items(response)

        matching_item = _find_inventory_item(items, old_name)

        if matching_item is None:
            return _build_not_found_response(hass, items, old_name)

        category_aliases = _parse_alias_config(
            str(options.get("categories", ""))
        )
        location_aliases = _parse_alias_config(
            str(options.get("locations", ""))
        )

        existing_categories = _collect_existing_values(items, "category")
        existing_locations = _collect_existing_values(items, "location")
        allow_new = _allow_new_categories_locations(options)

        normalized_category = args.get("category")
        if isinstance(normalized_category, str):
            normalized_category, category_error = _normalize_mapped_value(
                normalized_category,
                category_aliases,
                existing_categories,
                "category",
                hass,
                allow_new,
            )
            if category_error is not None:
                return category_error

        normalized_location = args.get("location")
        if isinstance(normalized_location, str):
            normalized_location, location_error = _normalize_mapped_value(
                normalized_location,
                location_aliases,
                existing_locations,
                "location",
                hass,
                allow_new,
            )
            if location_error is not None:
                return location_error

        # ---------------------------------------------------------
        # Expiry requested without a new expiry.
        #
        # Never modify anything in this case.
        # ---------------------------------------------------------

        editable_fields = {
            "new_name",
            "quantity",
            "unit",
            "category",
            "location",
            "expiry_date",
            "description",
            "barcode",
            "aliases",
            "price",
            "expiry_alert_days",
            "auto_add_enabled",
            "auto_add_to_list_quantity",
            "desired_quantity",
            "todo_list",
            "todo_quantity_placement",
        }

        provided_fields = [
            field
            for field in editable_fields
            if field in args
            and args[field] is not None
        ]

        if not provided_fields:
            current_expiry = matching_item.get(
                "expiry_date"
            )

            if current_expiry:
                message = _message(
                    hass,
                    "expiry_current",
                    name=old_name,
                    expiry=current_expiry,
                )
            else:
                message = _message(
                    hass,
                    "expiry_missing",
                    name=old_name,
                )

            return {
                "success": False,
                "action": "confirmation_required",
                "confirmation_required": True,
                "current_item": _format_item(
                    matching_item
                ),
                "message": message,
            }

        # ---------------------------------------------------------
        # Perform update.
        # ---------------------------------------------------------

        service_data: dict[str, Any] = {
            "inventory_id": inventory_id,
            "old_name": old_name,
            "name": old_name,
        }

        if args.get("new_name") is not None:
            service_data["name"] = args["new_name"]

        for field in (
            "quantity",
            "unit",
            "expiry_date",
            "description",
            "barcode",
            "aliases",
            "price",
            "expiry_alert_days",
            "auto_add_enabled",
            "auto_add_to_list_quantity",
            "desired_quantity",
            "todo_list",
            "todo_quantity_placement",
        ):
            if args.get(field) is not None:
                service_data[field] = args[field]

        if normalized_category is not None:
            service_data["category"] = normalized_category

        if normalized_location is not None:
            service_data["location"] = normalized_location

        try:
            await hass.services.async_call(
                INVENTORY_DOMAIN,
                "update_item",
                service_data,
                blocking=True,
                context=llm_context.context,
            )
            updated_items = await _get_inventory_items(
                hass,
                inventory_id,
                llm_context,
            )
        except Exception as err:
            return {
                "success": False,
                "action": "update_failed",
                "message": _message(hass, "update_failed", error=err),
            }

        updated_name = str(service_data["name"])
        updated_item = _find_inventory_item(updated_items, updated_name)
        if updated_item is None:
            return {
                "success": False,
                "action": "update_failed",
                "message": _message(hass, "item_missing_after_update_action"),
            }

        if "expiry_alert_days" in service_data:
            actual_alert_days = updated_item.get("expiry_alert_days")
            if actual_alert_days != service_data["expiry_alert_days"]:
                return {
                    "success": False,
                    "action": "update_failed",
                    "message": _message(
                        hass,
                        "expiry_alert_not_verified",
                        days=actual_alert_days,
                    ),
                }

        return {
            "success": True,
            "action": "updated",
            "item": old_name,
            "updated_fields": [
                key
                for key in service_data
                if key not in {
                    "inventory_id",
                    "old_name",
                }
            ],
            "message": _message(hass, "item_updated", name=old_name),
        }


def async_get_tools(
    hass: HomeAssistant,
    llm_context: LLMContext,
    api_id: str,
) -> llm.LLMTools | None:
    """Return Inventory Voice tools."""

    if not hass.config_entries.async_entries(DOMAIN):
        return None

    return llm.LLMTools(
        tools=[
            InventoryAddItemTool(),
            InventorySetQuantityTool(),
            InventoryIncrementQuantityTool(),
            InventoryRemoveQuantityTool(),
            InventoryDeleteItemTool(),
            InventoryFindItemsTool(),
            InventoryFindAllItemsTool(),
            InventoryUpdateItemTool(),
            InventoryLookupBarcodeTool(),
            InventoryScanBarcodeTool(),
            InventoryConsumptionRatesTool(),
        ],
        prompt="""
Inventory Voice gives you access to the user's Simple Inventory.

Use inventory tools whenever the user asks about inventory contents,
adding something, updating something, quantities, prices, categories,
locations, expiration dates, expiry alerts, barcodes, shopping-list settings,
consumption analytics, hardware, filaments, food, or cleaning products.

For restocking use inventory_increment_quantity; for consuming a quantity use
inventory_remove_quantity; for setting an exact quantity use
inventory_set_quantity. To delete an entire item use inventory_delete_item.
For barcode actions use inventory_lookup_barcode or inventory_scan_barcode.
Use inventory_get_consumption_rates for consumption or spending questions.
The configured inventory ID is used automatically except for barcode lookups
and requests explicitly about all inventories. A location such as "dispensa"
is an item location, never the inventory name.

When the user says they consumed, used, finished, or ran out of something
("ho consumato", "ho finito", "è finito"), always use
inventory_remove_quantity (or inventory_set_quantity to set it to 0). It is
normal for the quantity to reach 0; never call inventory_delete_item in this
case, since that would permanently erase the item and its whole history.

Only call inventory_delete_item when the user explicitly asks to delete or
erase the item from the database (e.g. "elimina dal database", "cancella dal
database", "elimina [l'oggetto] dal database"), never just because it ran
out. inventory_delete_item requires two steps: call it once to get a
confirmation message, read that message to the user, and only call it again
with confirm=true after the user has explicitly confirmed the deletion.
Never set confirm=true on the first call or without an explicit user
confirmation.

Never invent inventory information.

If a single message contains multiple instructions or mentions multiple
items (e.g. "rimuovi una birra e i cavoli", "setta a dopodomani la scadenza
di A e B"), you must handle EVERY item/instruction mentioned, not just the
first one. Call the appropriate tool separately once per item/instruction,
one at a time, and wait for each tool result before moving to the next call.
Do not stop after the first tool call and do not summarize the remaining
items as done without actually calling the tool for each of them.

For additions, collect all required information before calling
inventory_add_item:
- item
- quantity
- unit
- category
- location
- expiry date

The user may provide these values in any order and across multiple turns.

For updates, first identify the existing item. Never silently change an
expiration date when the user has not specified the new date. In that case,
tell the user the current expiration date and ask for the new one.

When the user asks for an expiry reminder or alert a number of days before an
item expires, call inventory_update_item with expiry_alert_days set to that
number. Examples: "avvisami 4 giorni prima che scade" and "alert me 4 days
before it expires" both require expiry_alert_days=4. Do not say that expiry
alerts are unsupported.

When searching inventory, actually call inventory_find_items rather than
assuming what the user owns.

Only confirm an operation when its tool returns success=true. If it returns
success=false or an error, report the failure and do not claim that anything
changed. When a message covers multiple items, report the outcome of each
item individually (some may succeed while others fail): never report an item
as done unless its own tool call actually returned success=true.

If a tool returns action="confirmation_required" with candidates, it means
the exact item was not found but a similar item (e.g. a different name,
alias, or location) was. Ask the user to confirm which item they meant using
the suggestion in the message, and only retry the operation with the
confirmed item name once the user agrees. Do not repeat a plain "not found"
answer when candidates are present.

After a successful tool call, give the user a short natural-language
confirmation in Italian.
""",
    )
