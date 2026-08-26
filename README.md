# Simple Inventory Voice

Simple Inventory Voice adds LLM tools to Home Assistant Assist for managing a [Simple Inventory](https://github.com/blaineventurine/simple_inventory) database using natural language. It can add, update, restock, consume, delete, search, and inspect inventory items, including prices, expiration alerts, barcodes, shopping-list settings, and consumption analytics.

## Installation

1. Copy this folder to:

   ```text
   config/custom_components/simple_inventory_voice
   ```

2. Install [Simple Inventory](https://github.com/blaineventurine/simple_inventory) and restart Home Assistant.
3. Create an inventory item in Simple Inventory with one or more categories.
4. In Home Assistant, open **Settings > Devices & services > Add integration** and add **Simple Inventory Voice**.
5. Enter the Simple Inventory database ID. Optionally configure category aliases and location aliases, select the response language, and choose which item fields are required.
6. Open Assist with an LLM-based conversation agent and start populating or querying the database.

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
