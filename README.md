# Sloperator

A tree-walking interpreter for SlopLang, built while working through
[Boot.dev's Learn AI Coding](https://www.boot.dev/courses/learn-ai-coding) course.

Sloperator lexes, parses, and evaluates `.slop` programs with a hand-written
scanner and recursive-descent parser, then walks the resulting AST. It ships with a
full `pytest` suite covering the lexer, parser, evaluator, CLI, and every example
program in `examples/`.

```bash
uv run sloperator.py examples/fizzbuzz.slop   # run a program
uv run pytest -q                              # run the test suite
uv run ruff check                             # lint
uv run ruff format --check                    # formatting check
```

## Language Reference

Files use the `.slop` extension and run with:

```bash
uv run sloperator.py path/to/program.slop
```

### Example

```slop
— Comments start with an em dash. Statements end with sparkles.
clanker describe(count) {
    vibe count > 1 {
        ship “big slop”✨
    } nah {
        ship “small slop”✨
    }
}

slop MAX = 3✨
slop count = 0✨

ralph count < MAX {
    hallucinate(describe(count))✨
    count = count + 1✨
}
```

Prints `small slop` twice, then `big slop`.

### The Slop Words

| SlopLang      | Conventional | Meaning                                                 |
| ------------- | ------------ | ------------------------------------------------------- |
| `slop`        | `let`        | Declare a mutable variable                              |
| `clanker`     | `fn`         | Define a function                                       |
| `vibe`        | `if`         | Conditional                                             |
| `nah`         | `else`       | Else branch                                             |
| `ralph`       | `while`      | Loop while a condition is `✅`                          |
| `hallucinate` | `print`      | Print one value, then a newline                         |
| `ship`        | `return`     | Return one value from a function                        |
| `✨`          | `;`          | Statement terminator (required)                         |
| `—`           | `//`         | Start a line comment                                    |
| `“ ”`         | `" "`        | String delimiters (straight quotes are a lexical error) |
| `✅`          | `true`       | Boolean true literal                                    |
| `❌`          | `false`      | Boolean false literal                                   |

There are no other reserved words, and no `break`, `continue`, `for`, or `else if`.

### Source Text

UTF-8, case-sensitive. Identifiers match `[A-Za-z_][A-Za-z0-9_]*`. Spaces, tabs, and newlines are whitespace; newlines do not end statements.

Emoji tokens are `✨` (U+2728), `✅` (U+2705), and `❌` (U+274C), each optionally followed by the variation selector U+FE0F, which some keyboards emit. `✨` must follow variable declarations, assignments, `ship`, and expression statements. It never follows a block's closing brace. `—` (U+2014) starts a comment that runs to end of line.

Strings open with `“` (U+201C), close with `”` (U+201D), and support escapes `\n`, `\t`, `\”`, and `\\`. A string cannot contain a raw newline. Unknown escapes and unterminated strings are lexical errors.

### Values

| Type     | Examples                            | Notes                        |
| -------- | ----------------------------------- | ---------------------------- |
| Number   | `0`, `42`, `9001`                   | Arbitrary-precision integers |
| String   | `“hello”`                           | Immutable Unicode text       |
| Boolean  | `✅`, `❌`                          | Required by conditions       |
| Nil      | Result of a function with no `ship` | No source literal            |
| Function | `hallucinate`, `describe`           | Built-in or user-defined     |

No implicit conversions.

### Variables

`slop` declares a mutable variable and requires an initializer. A scope cannot declare a name twice, but an inner block may shadow an outer name.

```slop
slop score = 10✨
slop LIMIT = 100✨
score = score + 5✨
score = score + 1✨
```

Assignment is a statement, not an expression: `name = expression✨`. It updates the nearest existing `slop` variable. Reading or assigning an undefined name is a runtime error.

Every brace block is a lexical scope. Assignment searches the current scope, then each enclosing scope.

### Control Flow

Conditions take no parentheses and must be booleans; there is no truthiness.

```slop
vibe score >= 10 {
    hallucinate(“ship it”)✨
} nah {
    hallucinate(“keep working”)✨
}

ralph score > 0 {
    score = score - 1✨
}
```

`nah` must be followed by a block; nest a `vibe` for another condition. `ralph` checks its condition before each iteration.

A tree-walking interpreter for [SlopLang](docs/spec.md), written in Python.

```bash
uv run sloperator.py examples/fib.slop
```

## Layout

| Path                    | What it is                                             |
| ----------------------- | ------------------------------------------------------ |
| `sloperator.py`         | Command-line entrypoint                                |
| `sloperator/lexer/`     | Source text to tokens                                  |
| `sloperator/parser/`    | Tokens to AST (`ast.py` holds the node definitions)    |
| `sloperator/evaluator/` | Walks the AST: values, environments, the interpreter   |
| `sloperator/runner.py`  | Runs source through all three stages                   |
| `docs/spec.md`          | The language specification                             |
| `examples/`             | Example programs                                       |
| `tests/`                | Pytest suite                                           |
| `playground/`           | A tiny web server and editor page for running programs |

## Validation

```bash
uv run pytest              # tests
uv run ruff format --check # formatting
uv run ruff check          # linting
uv run ty check            # type checking
```

## Playground

```bash
uv run playground/server.py
```

Then open <http://localhost:8080>.
