# NEX Language Specification v1.1

## Overview
NEX is a lightweight scripting language designed for simplicity and Python interoperability. It features a clean, minimal syntax inspired by Lua and Python.

## File Extensions
- `.N` - Primary extension (recommended)
- `.nex` - Legacy extension (still supported)

## Comments
```N
-- This is a single-line comment
-- NEX does not support multi-line comments yet
```

## Data Types
| Type | Example | Description |
|------|---------|-------------|
| Number | `42`, `3.14` | Integer or float |
| String | `"hello"`, `'world'` | Text enclosed in quotes |
| Boolean | `true`, `false` | Logical values |
| Null | `null` | Empty value |
| List | `[1, 2, 3]` | Ordered collection |

## Operators
### Arithmetic
`+` `-` `*` `/` `%`

### Comparison
`==` `!=` `<` `>` `<=` `>=`

### Logical
`and` `or` `not`

### Assignment
`=`

## Keywords
`fn` `end` `if` `elif` `else` `loop` `in` `as` `true` `false` `null` `and` `or` `not`

## Special Syntax
| Syntax | Meaning | Example |
|--------|---------|---------|
| `[>= expr]` | Output/Print | `[>= "Hello"]` |
| `[<= prompt]` | Input | `name = [<= "Name: "]` |
| `=> module` | Import | `=> math` |
| `-> expr` | Return | `-> a + b` |
| `? condition` | If | `? x > 5` |
| `:? condition` | Else If | `:? x > 3` |
| `:` | Else | `:` |
| `@ count` | Repeat | `@ 5` |
| `@ var in list` | For Each | `@ i in items` |
| `<เปิด "file">> "content" end:` | File Write | `<เปิด "out.txt">> "hi" end:` |

## Built-in Functions
- `len(obj)` - Length of string or list
- `type(obj)` - Return type name
- `str(obj)` - Convert to string
- `num(obj)` - Convert to number
- `int(obj)` - Convert to integer
- `float(obj)` - Convert to float
- `range(start, end)` - Generate number list
- `append(list, item)` - Add item to list
- `split(string, delim)` - Split string
- `join(list, delim)` - Join list elements
- `upper(string)` - Uppercase
- `lower(string)` - Lowercase
- `contains(obj, value)` - Check containment

## Examples
See `examples/` directory for complete working examples.
