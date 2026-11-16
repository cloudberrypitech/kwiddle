from types import SimpleNamespace

from kwiddle.reader_features import document_headings, font_inventory, table_to_rows


def test_heading_outline_and_levels():
    doc = SimpleNamespace(blocks=[
        SimpleNamespace(kind="heading", text="Chapter", attributes={"outline_level": "1"}),
        SimpleNamespace(kind="paragraph", text="Body", attributes={}),
    ])
    assert document_headings(doc) == [("Chapter", 1)]


def test_font_inventory_reads_run_styles():
    run = SimpleNamespace(style=SimpleNamespace(font="Liberation Serif"))
    block = SimpleNamespace(style=SimpleNamespace(font=None), runs=[run], children=[])
    assert font_inventory(SimpleNamespace(blocks=[block])) == ["Liberation Serif"]


def test_table_to_rows_preserves_cell_content():
    p1 = SimpleNamespace(text="A")
    p2 = SimpleNamespace(text="B")
    cell1 = SimpleNamespace(children=[p1])
    cell2 = SimpleNamespace(children=[p2])
    row = SimpleNamespace(children=[cell1, cell2])
    assert table_to_rows(SimpleNamespace(children=[row])) == [["A", "B"]]
