## StrongerFox Fonts

Contains selected fonts, as well as logic to build
their optimized variants for web.

Selected fonts are placed in separate directories, exactly as they were downloaded and as-is.


### Building

Run `make` and that's it.

`make clean` will tidy build results.

`make clean all` is a handy shortcut to rebuild everything.

Everything else is in the [`Makefile`](Makefile)

> [!NOTE]
> To run builds you need:
> - `python3`
> - `poetry` python package installed
> - `make` and core linux (LSB) utilities
