"""Find honest test targets for RFC 4518 §2.4, rather than guessing code points from memory.

Two things matter for the prohibited step and cannot be recalled reliably:

1. **Table version drift.** RFC 4518 prohibits "all unassigned code points", pointing at Table A.1
   of RFC 3454, which is pinned to Unicode 3.2. Python's `stringprep` module carries those same
   3.2-era tables, while `unicodedata` follows Unicode 16. Any code point assigned between 3.2 and
   today is therefore prohibited by the profile as written and not prohibited by current data - so
   the profile must be implemented against the pinned tables, and the drift must be documented with
   a real example rather than a hypothetical one.

2. **Which C.8 members are reachable at all.** §2.2 maps every Cc and Cf code point to nothing, so a
   deprecated character in those categories never survives to the prohibit step. Only a C.8 member
   outside them can actually trigger the rule.
"""

from __future__ import annotations

import stringprep
import unicodedata

MAP_TO_NOTHING_CATEGORIES = {"Cc", "Cf"}


def describe(cp: int) -> str:
    char = chr(cp)
    return (
        f"U+{cp:04X} {unicodedata.name(char, '<unnamed>')!r} "
        f"category={unicodedata.category(char)} "
        f"a1={stringprep.in_table_a1(char)} c8={stringprep.in_table_c8(char)} "
        f"cn={unicodedata.category(char) == 'Cn'}"
    )


drift = [
    cp
    for cp in range(0x110000)
    if stringprep.in_table_a1(chr(cp)) and unicodedata.category(chr(cp)) != "Cn"
]
print(f"code points prohibited by Table A.1 but assigned in this Unicode: {len(drift)}")
for cp in drift[:6]:
    print(" ", describe(cp))

still_unassigned = [
    cp for cp in range(0x0300, 0x0400) if unicodedata.category(chr(cp)) == "Cn"
]
print(f"\nstill unassigned today, first few: {[f'U+{c:04X}' for c in still_unassigned[:6]]}")

c8 = [
    cp
    for cp in range(0x110000)
    if stringprep.in_table_c8(chr(cp))
    and unicodedata.category(chr(cp)) not in MAP_TO_NOTHING_CATEGORIES
]
print(f"\nC.8 members that survive the §2.2 map step: {len(c8)}")
for cp in c8[:6]:
    print(" ", describe(cp))

for name, cp in (
    ("private use C.3", 0xE000),
    ("non-character C.4", 0xFDD0),
    ("non-character C.4 (FFFE)", 0xFFFE),
    ("surrogate C.5", 0xD800),
    ("replacement char", 0xFFFD),
):
    char = chr(cp)
    print(
        f"\n{name}: U+{cp:04X} c3={stringprep.in_table_c3(char)} c4={stringprep.in_table_c4(char)} "
        f"c5={stringprep.in_table_c5(char)} category={unicodedata.category(char)}"
    )

print("\nZs members added after Unicode 4.1, which RFC 4518's pinned list omits:")
for cp in range(0x110000):
    char = chr(cp)
    if unicodedata.category(char) == "Zs" and ord(char) not in {
        0x0020, 0x00A0, 0x1680, 0x202F, 0x205F, 0x3000,
    } and not (0x2000 <= ord(char) <= 0x200A):
        print(" ", describe(cp))

print("\nfullwidth forms the printed 'FF00-FE0F' would have deleted (erratum 860):")
for cp in (0xFF00, 0xFF21, 0xFF41, 0x3000):
    print(" ", describe(cp), "in_a1=", stringprep.in_table_a1(chr(cp)))
