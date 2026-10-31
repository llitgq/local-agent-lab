# Copy Table Structure with Formulas (跨表复制字段结构)

## When to use

You need to replicate a table's complete field structure (including formula fields) to another table, typically when creating a new table that mirrors an existing one.

## Why it's complex

Feishu formulas reference fields by their internal IDs (`$field[fldxxxxx]`, `$column[fldxxxxx]`, `CurrentValue.$column[fldxxxxx]`) and the table by its table ID (`bitable::$table[tbl_xxxxx]`). These are auto-generated when fields are created and are unique across the entire bitable. Copying formulas verbatim will point them at the old table — they will not work in the new table.

## Two-pass algorithm

### Pass 1 — Create non-formula fields

1. Read all fields from source table: `GET .../tables/{src_table_id}/fields`
2. For each field where `ui_type != "Formula"`:
   - Call `POST .../tables/{tgt_table_id}/fields` with `{"field_name": "...", "type": <numeric>, "property": {...}}`
   - Capture the returned new `field_id`
3. Build a mapping `old_field_id → new_field_id`

### Pass 2 — Create formula fields

1. Read formula expressions from source fields
2. For each formula expression, rewrite it by string replacement:
   - Replace table ID: `bitable::$table[src_tbl_id]` → `bitable::$table[tgt_tbl_id]`
   - Replace field references: `$field[old_id]` → `$field[new_id]`, `$column[old_id]` → `$column[new_id]`, `CurrentValue.$column[old_id]` → `CurrentValue.$column[new_id]`
3. Call `POST .../tables/{tgt_table_id}/fields` with `{"field_name": "...", "type": 20, "property": {"formula_expression": "rewritten_expr", "formatter": "...", "type": {...}}}`

### Handling inter-formula dependencies

If formula A references formula B's field ID:
- Create formula B first (it depends only on non-formula fields)
- Add B's new ID to the mapping
- Then create formula A

In practice, two passes are usually sufficient since most formulas reference non-formula fields (raw input data) rather than other formula results.

## Critical gotchas

1. **`type` must be numeric** — The create-field API rejects string types. Use `20` for Formula, `1005` for AutoNumber, `5` for DateTime, `2` for Number, `1` for Text.

2. **Bracket-anchored replacement** — Always replace within brackets: `$field[old_id]` → `$field[new_id]`. Never do bare `old_id` → `new_id` on the whole formula string, because field IDs can be substrings of other IDs.

3. **Sleep between batches** — Feishu API has rate limits. When creating 40+ fields in a loop, insert `time.sleep(1)` between batches of 5 to avoid 429 errors.

4. **Formula expression format** — The `formula_expression` value contains `\n` literal characters (newlines) in the formula body. When constructing the JSON body programmatically, ensure `\n` in the expression is properly escaped as `\\n` in Python string literals, or the JSON will be malformed.

5. **Property.type for percentage formulas** — Some formulas have an additional `type` property nested inside `property`:
   ```json
   "type": {"data_type": 2, "ui_property": {"formatter": "0.00%"}}
   ```
   This is separate from the top-level `type: 20` (Formula). When copying, preserve this nested `type` object if present.
