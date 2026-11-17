# SlopLang Specification

Files use the `.slop` extension and run with:

```bash
uv run sloperator.py path/to/program.slop
```

To check a file's syntax without executing it:

```bash
uv run sloperator.py --check path/to/program.slop
```

## Example

```slop
— Comments start with an em dash. Statements end with sparkles.
clanker describe(count) {
    vibe count > 1 {
        ship “big slop”✨
    } nah {
        ship “small slop”✨
    }
}

loadbearing MAX = 3✨
slop count = 0✨

ralph count < MAX {
    hallucinate(describe(count))✨
    count = count + 1✨
}
```

Prints `small slop` twice, then `big slop`.

## The Slop Words

| SlopLang      | Conventional | Meaning                                                 |
| ------------- | ------------ | ------------------------------------------------------- |
| `slop`        | `let`        | Declare a mutable variable                              |
| `loadbearing` | `const`      | Declare an immutable variable                           |
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

## Source Text

UTF-8, case-sensitive. Identifiers match `[A-Za-z_][A-Za-z0-9_]*`. Spaces, tabs, and newlines are whitespace; newlines do not end statements.

Emoji tokens are `✨` (U+2728), `✅` (U+2705), and `❌` (U+274C), each optionally followed by the variation selector U+FE0F, which some keyboards emit. `✨` must follow variable declarations, assignments, `ship`, and expression statements. It never follows a block's closing brace. `—` (U+2014) starts a comment that runs to end of line.

Strings open with `“` (U+201C), close with `”` (U+201D), and support escapes `\n`, `\t`, `\”`, and `\\`. A string cannot contain a raw newline. Unknown escapes and unterminated strings are lexical errors.

## Values

| Type     | Examples                            | Notes                        |
| -------- | ----------------------------------- | ---------------------------- |
| Number   | `0`, `42`, `9001`                   | Arbitrary-precision integers |
| String   | `“hello”`                           | Immutable Unicode text       |
| Boolean  | `✅`, `❌`                          | Required by conditions       |
| Nil      | Result of a function with no `ship` | No source literal            |
| Function | `hallucinate`, `describe`           | Built-in or user-defined     |

No implicit conversions.

## Variables

`slop` declares a mutable variable, and `loadbearing` declares an immutable one. Both require an initializer, which may be any expression and is evaluated once when the declaration runs. A scope cannot declare a name twice, but an inner block may shadow an outer name.

```slop
loadbearing LIMIT = 100✨
slop score = 10✨
score = score + 5✨
score = score + 1✨
```

Assignment is a statement, not an expression: `name = expression✨`. It updates the nearest existing binding. Assigning to a `loadbearing` variable is a runtime error.

```slop
LIMIT = 200✨ — runtime error: cannot assign to loadbearing 'LIMIT'
```

Reading or assigning an undefined name is a runtime error.

Every brace block is a lexical scope. Assignment searches the current scope, then each enclosing scope. An inner `slop` may shadow an outer `loadbearing` name.

## Control Flow

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

## Functions

`clanker` declares a named function at the top level. Calls require exactly the declared number of arguments. Parameters and locals belong to the call's scope.

```slop
clanker add(left, right) {
    ship left + right✨
}
hallucinate(add(20, 22))✨
```

`ship` returns one value; reaching the end of the body returns `nil`. `ship` outside a function and duplicate parameter names are syntax errors.

A `clanker` name is an immutable binding in the global scope: it cannot be redeclared or assigned, and it is a value, so `slop f = add✨` followed by `f(1, 2)✨` works. Calling a non-function is a runtime error. Functions must be declared before they are called; mutual recursion works when both are declared before the first call. No nested or anonymous functions.

Call depth is capped at 500 nested calls. Exceeding it is a runtime error (`stack overflow`), never a Python traceback.

## Built-Ins

`hallucinate(value)` is the only built-in. It accepts exactly one argument, prints it followed by a newline, and returns `nil`. Numbers print as base-10 digits, strings without quotes, booleans as `✅`/`❌`, nil as `nil`, and functions as `<clanker name>`.

```slop
hallucinate(3)✨   — 3
```

## Operators

`+` adds numbers or concatenates strings. `-`, `*`, `/` accept only numbers; division truncates toward zero (`-7 / 2` is `-3`, not floor division's `-4`) and division by zero is a runtime error. `<`, `<=`, `>`, `>=` compare numbers. `==`, `!=` compare any values; different types are unequal, and functions are equal only to themselves. `&&` and `||` require booleans and short-circuit. Unary `-` negates a number.

Precedence, lowest to highest:

1. `||`
2. `&&`
3. `==`, `!=`
4. `<`, `<=`, `>`, `>=`
5. `+`, `-`
6. `*`, `/`
7. Unary `-`
8. Calls
9. Literals, names, `( )`

## Grammar

```text
program        -> topLevel* EOF ;
topLevel       -> functionDecl | declaration ;

functionDecl   -> "clanker" IDENTIFIER "(" parameters? ")" block ;
parameters     -> IDENTIFIER ( "," IDENTIFIER )* ;

declaration    -> variableDecl | statement ;
variableDecl   -> ( "slop" | "loadbearing" ) IDENTIFIER "=" expression "✨" ;

statement      -> assignStmt | ifStmt | loopStmt | returnStmt
                | block | expressionStmt ;
assignStmt     -> IDENTIFIER "=" expression "✨" ;
ifStmt         -> "vibe" expression block ( "nah" block )? ;
loopStmt       -> "ralph" expression block ;
returnStmt     -> "ship" expression "✨" ;
block          -> "{" declaration* "}" ;
expressionStmt -> expression "✨" ;

expression     -> logicOr ;
logicOr        -> logicAnd ( "||" logicAnd )* ;
logicAnd       -> equality ( "&&" equality )* ;
equality       -> comparison ( ( "==" | "!=" ) comparison )* ;
comparison     -> term ( ( "<" | "<=" | ">" | ">=" ) term )* ;
term           -> factor ( ( "+" | "-" ) factor )* ;
factor         -> unary ( ( "*" | "/" ) unary )* ;
unary          -> "-" unary | call ;
call           -> primary ( "(" arguments? ")" )* ;
arguments      -> expression ( "," expression )* ;
primary        -> NUMBER | STRING | "✅" | "❌"
                | IDENTIFIER | "(" expression ")" ;
```

## Errors

The interpreter stops at the first lexical, syntax, or runtime error, writes the diagnostic to stderr, exits with status `1`, and never shows a Python traceback. Output produced before a runtime error stays on stdout.

```text
SlopLang lexical error at line 1: straight quotes are not supported, use “ and ” for strings
SlopLang syntax error at line 2: expected ✨ after variable declaration, found 'slop'
SlopLang runtime error at line 3: division by zero
```

## Typing SlopLang

The smart quotes, em dash, and emoji are part of the language, so you will type them a lot.

| Character  | macOS                | Windows      | Linux (GTK)                                     |
| ---------- | -------------------- | ------------ | ----------------------------------------------- |
| `“`        | `Option + [`         | `Alt + 0147` | `Ctrl+Shift+U 201C`                             |
| `”`        | `Option + Shift + [` | `Alt + 0148` | `Ctrl+Shift+U 201D`                             |
| `—`        | `Option + Shift + -` | `Alt + 0151` | `Ctrl+Shift+U 2014`                             |
| `✨ ✅ ❌` | `Ctrl + Cmd + Space` | `Win + .`    | `Ctrl + .` or `Ctrl+Shift+U 2728 / 2705 / 274C` |

The interpreter recognizes the common mistakes (`"`, `;`, `//`, and the en dash `–`) and tells you what to use instead. If an emoji shows up blank in your editor, the file is fine; the editor's font is missing the glyph. In Zed, set an explicit `buffer_font_family` (the bundled default has no `❌`) and add `"buffer_font_fallbacks": ["Apple Color Emoji"]` or your platform's emoji font.

## Non-Goals

No floats, arrays, maps, indexing, nested functions, classes, modules, imports, file access, user input, exceptions, or built-ins beyond `hallucinate`.
