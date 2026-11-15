from kwloader import ImageAsset, TextBlock, TextRun, TextStyle


def test_legacy_text_block_api_still_works():
    block = TextBlock("paragraph", [TextRun("hello", TextStyle(bold=True))])
    assert block.text == "hello"
    assert block.runs[0].style.bold


def test_nested_table_text_is_available():
    cell = TextBlock("table_cell", children=[TextBlock("paragraph", [TextRun("inside")])])
    row = TextBlock("table_row", children=[cell])
    table = TextBlock("table", children=[row])
    assert "inside" in table.text


def test_image_asset_model():
    asset = ImageAsset("a.png", "image/png", b"image")
    run = TextRun("", image=asset)
    block = TextBlock("paragraph", [run])
    assert block.runs[0].image.name == "a.png"
