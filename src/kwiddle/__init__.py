"""Kwiddle desktop document reader."""
__version__ = "0.3.0"


def is_odf_element(node, *factories):
    """Return whether an odfpy node matches one of the supplied factories."""
    qname = getattr(node, "qname", None)
    if qname is None:
        return False
    for factory in factories:
        try:
            if factory(check_grammar=False).qname == qname:
                return True
        except Exception:
            try:
                if factory().qname == qname:
                    return True
            except Exception:
                continue
    return False


def main():
    from .maincode import run
    run()


if __name__ == "__main__":
    main()
