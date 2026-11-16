# Kwiddle

Kwiddle is a Tkinter desktop reader that uses `kwloader` to read ODT/FODT/OTT/ODM/ODF and DOCX/DOTX documents.

## Install from source

Install `kwloader` first (or install both projects in editable mode):

```bash
python -m pip install -e ../kwloader
python -m pip install --no-deps -e .
python -m pip install "Pillow>=10,<13" "CairoSVG>=2.7.1,<3" "pyfiglet>=1.0.4,<2"
```

## Run

```bash
python -m kwiddle
```

Place supported documents in `src/kwiddle/books/`. Kwiddle scans that directory recursively and refreshes the library automatically. The offline reader renders embedded raster images and SVGs, common inherited and direct font styling, paragraph alignment/spacing/indentation, hyperlinks, notes, numbered and bulleted lists, styled table cells, and available page dimensions/margins and master-page headers/footers.

For best image support, install the declared Pillow and CairoSVG dependencies. External linked images are not downloaded. Complex OLE objects, charts, formulas, text wrapping around floating objects, fields and exact paginated layout still depend on the source document and may display as simplified content.


## Reader features

The reader includes adaptive reading-column margins, document font inspection, a
document outline for headings, in-page text search, zoom controls, Light/Dark/Sepia
reading themes, keyboard navigation, and per-document page-position restoration.
The existing renderer continues to display embedded images, styled text, hyperlinks,
lists, and tables using the format-neutral model supplied by `kwloader`.

Reader progress is stored under `~/.local/share/kwiddle/reading-progress.json`
and is optional: if the location is unavailable, reading continues without saving.
Use the **Fonts** control to inspect font families declared in the source document.
