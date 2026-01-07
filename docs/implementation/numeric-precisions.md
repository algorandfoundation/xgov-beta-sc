# Numeric Precisions

## Percentages

All the percentages **MUST** have a precision of two decimals and be expressed as
[basis-points](https://en.wikipedia.org/wiki/Basis_point) (bps) scaled as Algorand
Virtual Machine (AVM) `uint64`.

{{#include ../_include/styles.md:example}}
> The AVM works with `uint64`, therefore
> \\( 100.00 \\% = 10{,}000 \mathrm{bps} \\).
> So, \\( 12.5 \\% \\) of \\( X \\) is calculated on the AVM as:
>
> $$
> \frac{1{,}250 \mathrm{bps} \times X}{10{,}000 \mathrm{bps}}.
> $$
