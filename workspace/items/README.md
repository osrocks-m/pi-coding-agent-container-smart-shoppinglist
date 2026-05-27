# Items Directory

This directory contains shared item lists used by the receipt processing system.

## Files

### `shoppinglist.txt`

The current, up-to-date shopping list. Contains items that need to be purchased.

### `normalized-items.txt`

A master list of normalized item names used for matching and standardization.

**Purpose:** When processing receipts, item names often appear abbreviated or shortened (e.g., "BAUERNBROETCH." → "
bauernbrötchen", "HIMB. -HEIDELB. MX" → "gefrorene Beeren"). This file provides the canonical, colloquial names for
comparison before merging items into store-specific lists.

**Format:** One item per line, using common grocery terms:

- Colloquial spellings (e.g., "Aufbackbrötchen" not "Aufbackbrötchen 5er Pack")
- Complete words, not abbreviations
- Capitalized nouns following language conventions

**Example mappings:**
| Receipt Text | Normalized Name |
|--------------|-----------------|
| BAUERNBROETCH. | Bauernbrötchen |
| HIMB. -HEIDELB. MX | gefrorene Beeren |
| STAPELCHIPS PAPR | Chips |
| 5ER FRUEHSTUEKSB | Aufbackbrötchen |
| RUEPPURRER MSCHG | Kaffee |
| TOIPA FEUCHT | Feuchttücher |

## Workflow

Unclear items are matched against `normalized-items.txt`
If a match is found, the normalized name is used
New items are added to both the target list and `normalized-items.txt`

## Related

- Store-specific items: `../stores/<store-name>/items.txt`
- `./shoppinglist.txt`
- Skill documentation: `../.pi/skills/receipt-to-items/SKILL.md`
