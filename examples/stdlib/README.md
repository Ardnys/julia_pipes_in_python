# Standard library examples

```sh
uv run python -m examples.stdlib.word_frequency
uv run python -m examples.stdlib.log_report
uv run python -m examples.stdlib.slugify
```

## Word frequency ([`word_frequency.py`](word_frequency.py))

Lowercase a text, split it into words, drop stopwords, count, and keep the top three.

### Without pipes: unreadable

```python
top_three(count(drop_stopwords(words(lowercase(TEXT)))))
```

To follow it you start at `TEXT` in the middle, read outward to the left, and count
parentheses. The step that happens *first*, `lowercase`, sits right next to the step that
happens *last*.

### With paipu™: beautiful

```python
TEXT | lowercase | words | drop_stopwords | count | top_three
```

Read it left to right, exactly in the order it happens.

## Log report ([`log_report.py`](log_report.py))

Raw log text → lines → parsed entries → errors only → error count per service → report.

### Without pipes: unreadable

```python
format_report(count_by_service(errors_only(parse(lines(LOG)))))
```

### With paipu™: beautiful

```python
LOG | lines | parse | errors_only | count_by_service | format_report
```

`parse` is declared with `@broadcast`, so it parses every line, like Julia's `.|>`:

```python
@broadcast
def parse(line: str) -> Entry: ...
```

Adding or removing a step means adding or removing one `| step`. In the nested version you
have to find the right pair of parentheses.

## Slugify ([`slugify.py`](slugify.py))

`"Crème Brûlée: A Love Story!"` → `"creme-brulee-a-love-story"`.

### Without pipes: unreadable

```python
def slugify_without_pipes(title: str) -> str:
    return "-".join(
        re.sub(
            r"[^\w\s-]",
            "",
            unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii"),
        )
        .lower()
        .split()
    )
```

The very last step, `"-".join`, is the first thing you read. Function calls and method chains
take turns, so the eye jumps back and forth.

### With paipu™: beautiful

```python
slugify = strip_accents | drop_punctuation | str.lower | str.split | "-".join

TITLES | broadcast(slugify)
```

Composing pipes gives you a new, named function (no `def`, no `lambda`), and plain callables
like `str.lower` and `"-".join` slot straight in.
