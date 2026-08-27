# Simple Inventory Voice

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
![Custom integration](https://img.shields.io/badge/Home%20Assistant-Custom%20integration-41BDF5)
![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)
![Language](https://img.shields.io/badge/Responses-Italian%20%7C%20English-009688)

Simple Inventory Voice is a Home Assistant custom integration that adds LLM tools to Home Assistant Assist. It lets you manage a [Simple Inventory](https://github.com/blaineventurine/simple_inventory) database using natural language.

The integration can add, update, restock, consume, delete, search, and inspect inventory items. It also supports prices, expiration dates and alerts, barcodes, shopping-list settings, and consumption analytics.

Simple Inventory Voice is an add-on, not a standalone inventory system. The main integration, [Simple Inventory](https://github.com/blaineventurine/simple_inventory), must be installed and configured first.

## Features

- Add items with quantity, unit, category, location, expiration date, price, barcode, aliases, and shopping-list settings.
- Set an exact quantity, increase a quantity for restocking, or decrease it when an item is consumed.
- Update item details, including expiration dates and expiration-alert days.
- Search one inventory or inspect all configured inventories.
- Look up or scan barcodes when supported by the underlying Simple Inventory integration.
- Ask for consumption and spending statistics.
- Use Italian or English for the LLM tool responses.

## Requirements

- Home Assistant with Assist and an LLM-based conversation agent.
- The [Simple Inventory](https://github.com/blaineventurine/simple_inventory) custom integration.
- A configured Simple Inventory database with its inventory ID.

## Installation

### Option 1: HACS

Both repositories must be installed as custom integrations. Install the main Simple Inventory integration first:

1. Open **HACS > Integrations** and select the three-dot menu.
2. Choose **Custom repositories**.
3. Add `https://github.com/blaineventurine/simple_inventory` and choose **Integration**.
4. Install **Simple Inventory** and restart Home Assistant.
5. Repeat the same steps for `https://github.com/wavelov3r/Simple-Inventory-Voice`.
6. Install **Simple Inventory Voice**, restart Home Assistant, and add it from **Settings > Devices & services > Add integration**.

After installing the repository, HACS may initially show a commit hash. Create and publish a GitHub release tagged `v1.2` from the `main` branch, then use **Update information** in HACS. A release is required for HACS to display `1.2` instead of a commit hash.

### Option 2: Manual installation

1. Install [Simple Inventory](https://github.com/blaineventurine/simple_inventory) and restart Home Assistant.
2. Copy this repository's integration directory to:

   ```text
   config/custom_components/simple_inventory_voice
   ```

3. Restart Home Assistant again.
4. Add **Simple Inventory Voice** from **Settings > Devices & services > Add integration**.

The GitHub repository must keep this structure:

```text
Simple-Inventory-Voice/
  custom_components/
    simple_inventory_voice/
      __init__.py
      config_flow.py
      llm.py
      manifest.json
      strings.json
      brand/
        icon.png
  hacs.json
  README.md
```

## Initial setup

1. Create or select an inventory in Simple Inventory.
2. Find its inventory ID. It is available in Developer Tools in the `inventory_id` attribute of the corresponding `sensor.<database>_inventory` entity.
3. Add Simple Inventory Voice and enter that inventory ID.
4. Expose the Simple Inventory entities for the selected database to Assist.
5. In the conversation agent settings, allow the LLM-based agent to control Assist.
6. Open Assist using that conversation agent and make a request.

## Options

- **Inventory ID**: The Simple Inventory database used by default.
- **Response language**: `ita` for Italian or `eng` for English responses.
- **Categories**: Canonical category names and optional aliases, one per line.
- **Locations**: Canonical location names and optional aliases, one per line.
- **Required quantity**: Require a quantity when adding an item.
- **Required unit**: Require a unit when adding an item.
- **Required category**: Require a category when adding an item.
- **Required location**: Require a location when adding an item.
- **Required expiration date**: Require an expiration date when adding an item.
- **Allow new categories and locations**: Allow voice requests to create values that are not already present in the inventory.

Alias example:

```text
food: groceries, meals
cleaning: detergents
```

When options are opened, the integration reads the categories and locations already stored in the selected inventory. Existing aliases are retained only for values still present in that inventory.

## Assistant behavior and decisions

- The configured inventory ID is used automatically. Barcode lookups and requests about all inventories are handled separately.
- A location such as `pantry` is an item location, never the inventory name.
- For additions, the assistant collects every enabled required field before calling the add tool. It does not invent missing values.
- If an item already exists, its stored category and location are preserved when adding more information. Use an update request to change them.
- Categories and locations are normalized through the configured aliases and validated against existing values. New values are rejected unless **Allow new categories and locations** is enabled.
- If an exact item is not found but similar names, aliases, or locations exist, the assistant asks for confirmation before changing anything.
- An expiration date is never changed implicitly. If a new date was not provided, the assistant reports the current date and asks for the new one.
- Expiration reminders use the requested number of days through the item update operation.
- Restocking increases quantity; consuming decreases quantity; setting quantity replaces it with the exact value. Negative quantities are rejected.
- Every write operation is checked by reading the inventory again. The assistant reports success only when the requested result is verified.
- If one request contains multiple items or actions, each one is processed separately and its result is reported individually.
- Search and statistics requests always read the inventory rather than relying on previous conversation context.

## Example requests

- "Add three bottles of olive oil to the pantry, price 8.50."
- "Restock coffee by two packs and set the price to 6.99."
- "Set the expiry alert for milk to seven days before it expires."
- "How many batteries do I have?"
- "What is expiring soon?"
- "Remove one bottle of water and two cans of beans."
- "Find the item with barcode 123456789."

## Release

The current integration version is `1.2`. For HACS, publish a non-draft GitHub release with the tag `v1.2`. Future releases should update the version in `custom_components/simple_inventory_voice/manifest.json` and use a matching Git tag.
