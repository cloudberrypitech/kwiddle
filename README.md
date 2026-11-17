# Kwiddle

Kwiddle is a Tkinter desktop reader that uses `kwloader` to read ODT/FODT/OTT/ODM/ODF and DOCX/DOTX documents.

## Install from source

Install `kwloader` first (or install both projects in editable mode):

```bash
python -m pip install -e ../kwloader
python -m pip install --no-deps -e .
python -m pip install "Pillow>=10,<13" "CairoSVG>=2.7.1,<3" "pyfiglet>=1.0.4,<2"
```

## Update

For a source checkout, pull the latest Kwiddle and kwloader changes. When kwloader is installed from Git rather than a local sibling checkout, update it with:

```bash
python -m pip install --upgrade "kwloader @ git+https://github.com/cloudberrypitech/kwloader@main"
python -m pip install --no-deps -e .
```

When using a separate local kwloader checkout, update that checkout and reinstall it in editable mode instead.

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

The reading view keeps a centred, comfortable text column when the window is resized
or switched to full screen. Use **F11** or the **Full screen** button to toggle full
screen; **Esc** exits it. The toolbar provides text-size, search, contents, font, and
reading-theme controls. Left/Right arrow keys move between reader pages.

## Adding books

Place complete supported book files in `src/kwiddle/books/` (subfolders are scanned
too). Kwiddle detects additions, replacements, and removals automatically while the
library is open. Supported formats are provided by `kwloader`; use ODT/FODT for
portable, self-contained books with embedded images and formatting.


## PDF reading

Kwiddle can open PDF files placed in the same books folder as ODT documents
(`src/kwiddle/books/`). The desktop reader renders PDF pages locally and
provides previous/next navigation, page selection, fit-to-width, zoom, and
fullscreen controls.

PDF rendering uses PyMuPDF. It is included in the normal Kwiddle installation;
after upgrading an existing environment, run:

```bash
python -m pip install --upgrade kwiddle
```

The online reader also has an **Open PDF** control for opening a PDF from the
device. Browser PDF files are rendered locally and are not uploaded to a server.
