# Simple Inventory Voice

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
![Custom integration](https://img.shields.io/badge/Home%20Assistant-Custom%20integration-41BDF5)
![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)
![Language](https://img.shields.io/badge/Responses-Italian%20%7C%20English-009688)

Simple Inventory Voice is a Home Assistant custom integration that adds LLM tools to Home Assistant Assist. It manages a [Simple Inventory](https://github.com/blaineventurine/simple_inventory) database through natural language. It can add, update, restock, consume, delete, search, and inspect inventory items, including prices, expiration alerts, barcodes, shopping-list settings, and consumption analytics.

Both Simple Inventory Voice and its Simple Inventory dependency are Home Assistant custom integrations.

## Installation

1. Copy this folder to:

   ```text
   config/custom_components/simple_inventory_voice
   ```

2. Install [Simple Inventory](https://github.com/blaineventurine/simple_inventory), the Home Assistant inventory custom integration, and restart Home Assistant.
3. Create an inventory item in the Simple Inventory Home Assistant integration with one or more categories.
4. In Home Assistant, open **Settings > Devices & services > Add integration** and add **Simple Inventory Voice**.
5. Enter the Simple Inventory database ID (in developer tools, inventory ID attribute from sensor.databasename_inventory) . Optionally configure category aliases and location aliases, select the response language, and choose which item fields are required.
6. Expose the Simple Inventory entities for the selected database to Assist.
7. In the conversation agent settings, allow the LLM-based conversation agent to control Assist.
8. Open Assist with that conversation agent and start populating or querying the database.

## Settings

- **Inventory ID**: The ID of the Simple Inventory database to manage.
- **Response language**: Choose Italian (`ita`) or English (`eng`) for LLM tool responses.
- **Categories**: Optional canonical category names and aliases, one per line. Example:

  ```text
  food: groceries, meals
  cleaning: detergents
  ```

- **Locations**: Optional canonical location names and aliases, one per line. Example:

  ```text
  pantry: cupboard, kitchen pantry
  garage: box
  ```

- **Required fields**: Choose whether quantity, unit, category, location, and expiration date must be collected before adding an item.

When you open the integration options, Simple Inventory Voice reads the categories and locations already stored in the selected inventory database. It keeps configured aliases only for values that still exist in that database, helping Assist use the current inventory data.

## Example requests

- "Add three bottles of olive oil to the pantry, price 8.50."
- "Set an expiry alert for milk seven days before it expires."
- "How many batteries do I have?"
- "Restock coffee by two packs and set the price to 6.99."
- "What is expiring soon?"
