# Contribution Guidelines

The xGov Architecture source code is released on the official [GitHub repository](https://github.com/algorandfoundation/xgov-beta-sc/).

Issues can be submitted on the [GitHub issues page](https://github.com/algorandfoundation/xgov-beta-sc/issues).

External contributions to _tests_ and _documentation_ are welcome. If you would like
to contribute, please read these guidelines and consider submitting a [Pull Request](https://github.com/algorandfoundation/xgov-beta-sc/pulls).

> ⚠️ Commits must be signed!

## Docs Guidelines

By clicking on the _“Suggest an edit”_ icon in the top-right corner, while reading
this book, you will be redirected to the relevant documentation source code file
to be referenced in an Issue or edited in a Pull Request.

The xGov Architecture Specifications book is built with [mdBook](https://rust-lang.github.io/mdBook/index.html).

The book is written in [CommonMark](https://commonmark.org/).

The CI pipeline enforces Markdown linting, formatting, and style checking with
[`markdownlint`](https://github.com/DavidAnson/markdownlint).

### Numbered Lists

Numbered lists **MUST** be defined with `1`-only style.

{{#include ./_include/styles.md:example}}
> ```text
> 1. First item
> 1. Second item
> 1. Third item
> ```
>
> Result:
> 1. First item
> 1. Second item
> 1. Third item

### Tables

Table rows **MUST** use the same column widths.

{{#include ./_include/styles.md:example}}
> ✅ Correct table format
> ```text
> | Month    | Savings |
> |----------|---------|
> | January  | €250    |
> | February | €80     |
> | March    | €420    |
> ```
>
> ❌ Wrong table format
> ```text
> | Month | Savings |
> |----------|---------|
> | January | €250 |
> | February | €80 |
> | March | €420 |
> ```
>
> Result:
>
> | Month    | Savings |
> |----------|---------|
> | January  | €250    |
> | February | €80     |
> | March    | €420    |

Consider aligning text in the columns to the left, right, or center by adding a
colon `:` to the left, right, or on both sides of the dashes `---` within the header
row.

{{#include ./_include/styles.md:example}}
> ```text
> | Name   | Quantity | Size |
> |:-------|:--------:|-----:|
> | Item A |    1     |    S |
> | Item B |    5     |    M |
> | Item C |    10    |   XL |
> ```
>
> Result:
>
> | Name   | Quantity | Size |
> |:-------|:--------:|-----:|
> | Item A |    1     |    S |
> | Item B |    5     |    M |
> | Item C |    10    |   XL |

### MathJax

Mathematical formulas are defined with [MathJax](https://www.mathjax.org/).

> mdBook MathJax [documentation](https://rust-lang.github.io/mdBook/format/mathjax.html).

### Block Styles

Block styles are defined in the `./docs/_include/styles.md` file using the mdBook
[include feature](https://rust-lang.github.io/mdBook/format/mdbook.html#including-files).

Block styles (e.g., examples, implementation notes, etc.) are “styled quote” blocks
included in the book.

{{#include ./_include/styles.md:example}}
> This example block has been included with the following syntax:
> ```text
> \{{#include ./_include/styles.md:example}}
> > This example block has been included with the following syntax:
> ```
