from odf.element import Element
from odf.text import H, P, Span

from kwiddle import is_odf_element


def test_factory_based_odf_nodes_are_detected():
    assert is_odf_element(P(text="hello"), P, H)
    assert is_odf_element(H(text="title"), H)
    assert is_odf_element(Span(text="em"), Span)
    assert not is_odf_element(Element(qname=("urn:oasis:names:tc:opendocument:xmlns:text:1.0", "p")), H)
