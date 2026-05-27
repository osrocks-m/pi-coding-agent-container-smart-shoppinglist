---
name: receipt-to-items
description: Extracts grocery items from receipt PDFs and images, normalizes item names, and organizes them by store in structured text files. Use when processing shopping receipts to build store-specific item inventories.
---

# Receipt to Items

Extract items from a receipt (PDF or image) and add them to the appropriate store's items list.

## How it works

- Uses the `pdf-to-markdown` skill for OCR extraction. The result of that is a .md file.
- Reads the .md file contents. 
- Extracts the store and item names from the receipt lines
- Creates/updates `stores/<store>/items.txt` with normalized item names

## Directory Structure

```
stores/
├── <store-name>/
│   └── items.txt             # One item per line, lowercase, normalized
items/
├── shoppinglist.txt          # The up-to date current shopping list 
├── normalized-items.txt      # A list of normalized item names for comparision before merging into other lists.
├── README.md                 # Information how to use normalized-items.txt and shoppinglist.txt

```

## Output

- Creates the store directory if it doesn't exist
- Appends new items to `stores/<store>/items.txt` (deduplicated)
- Prints extracted store and items to stdout

## Example

Input: `Scan 2026-05-26 17.33.48.md` containing:
```
nahkauf
...
6  BAUERNBROETCH.
5ER  FRUEHSTUEKSB
HIMB. -HEIDELB. MX
STAPELCHIPS PAPR
...
```

Output: `stores/nahkauf/items.txt`
```
bauernbroetchen
Himbeer Heidelbeer Mix
stapelchips paprika
```

# Procedure

For unclear stores, 
  - try to match it to already existing stores based on name similarity, respecting abbreviations. 
  - If still unclear, ask the user where the receipt comes from. Wait for an answer before proceeding.
Merge all items that are clear enough into that store's items.txt. 
Then ask the user for the unclear items if they want to label it. Give them suggestions from the existing list. Wait for an answer before proceeding. 
  - Match the users answer against normalized-items.txt. If you find a fitting name there, use that. 
    - If there's no similar name in the normalized-items.txt, use a correctly spelled variant to add to the normalized-items.txt. 
  - Merge the normalized name to the items.txt.

### Merge rules
- For the new items name, find a good general name. Use names from the normalized-items.txt list when fitting.
- If there's a similar item in the list already, use the more general but still concise name.
- Add new items to the end of the list

# Cleaning up

When you're done, move the original receipt PDF and the Markdown version to /workspace/receipts/. Delete the ocr.pdf version. 