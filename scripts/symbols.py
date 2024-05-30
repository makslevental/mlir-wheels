import re


class TooComplexName(Exception):
    pass


def skip_itanium_template(arg):
    # A template argument list starts with I
    assert arg.startswith("I"), arg
    tmp = arg[1:]
    while tmp:
        # Check for names
        match = re.match("(\d+)(.+)", tmp)
        if match:
            n = int(match.group(1))
            tmp = match.group(2)[n:]
            continue
        # Check for substitutions
        match = re.match("S[A-Z0-9]*_(.+)", tmp)
        if match:
            tmp = match.group(1)
        # Start of a template
        elif tmp.startswith("I"):
            tmp = skip_itanium_template(tmp)
        # Start of a nested name
        elif tmp.startswith("N"):
            _, tmp = parse_itanium_nested_name(tmp)
        # Start of an expression: assume that it's too complicated
        elif tmp.startswith("L") or tmp.startswith("X"):
            raise TooComplexName
        # End of the template
        elif tmp.startswith("E"):
            return tmp[1:]
        # Something else: probably a type, skip it
        else:
            tmp = tmp[1:]
    return None


def parse_itanium_name(arg):
    # Check for a normal name
    match = re.match("(\d+)(.+)", arg)
    if match:
        n = int(match.group(1))
        name = match.group(1) + match.group(2)[:n]
        rest = match.group(2)[n:]
        return name, rest
    # Check for constructor/destructor names
    match = re.match("([CD][123])(.+)", arg)
    if match:
        return match.group(1), match.group(2)
    # Assume that a sequence of characters that doesn't end a nesting is an
    # operator (this is very imprecise, but appears to be good enough)
    match = re.match("([^E]+)(.+)", arg)
    if match:
        return match.group(1), match.group(2)
    # Anything else: we can't handle it
    return None, arg


def parse_itanium_nested_name(arg):
    # A nested name starts with N
    assert arg.startswith("N"), arg
    ret = []

    # Skip past the N, and possibly a substitution
    match = re.match("NS[A-Z0-9]*_(.+)", arg)
    if match:
        tmp = match.group(1)
    else:
        tmp = arg[1:]

    # Skip past CV-qualifiers and ref qualifiers
    match = re.match("[rVKRO]*(.+)", tmp)
    if match:
        tmp = match.group(1)

    # Repeatedly parse names from the string until we reach the end of the
    # nested name
    while tmp:
        # An E ends the nested name
        if tmp.startswith("E"):
            return ret, tmp[1:]
        # Parse a name
        name_part, tmp = parse_itanium_name(tmp)
        if not name_part:
            # If we failed then we don't know how to demangle this
            return None, None
        is_template = False
        # If this name is a template record that, then skip the template
        # arguments
        if tmp.startswith("I"):
            tmp = skip_itanium_template(tmp)
            is_template = True
        # Add the name to the list
        ret.append((name_part, is_template))

    # If we get here then something went wrong
    return None, None


def should_keep_itanium_symbol(symbol, calling_convention_decoration=False):
    # Start by removing any calling convention decoration (which we expect to
    # see on all symbols, even mangled C++ symbols)
    if calling_convention_decoration and symbol.startswith("_"):
        symbol = symbol[1:]
    # Keep unmangled names
    if not symbol.startswith("_") and not symbol.startswith("."):
        return symbol
    # Discard manglings that aren't nested names
    match = re.match("_Z(T[VTIS])?(N.+)", symbol)
    if not match:
        return None
    # Demangle the name. If the name is too complex then we don't need to keep
    # it, but it the demangling fails then keep the symbol just in case.
    try:
        names, _ = parse_itanium_nested_name(match.group(2))
    except TooComplexName:
        return None
    if not names:
        return symbol
    # Keep llvm:: and clang:: names
    elif names[0][0] == "4llvm" or names[0][0] == "5clang":
        return symbol
    # Discard everything else
    else:
        return None


if __name__ == "__main__":
    keep_symbols = []
    with open("symbols.txt") as sf:
        symbols = sf.readlines()
    for s in symbols:
        s = s.strip()
        if should_keep_itanium_symbol(s, calling_convention_decoration=True):
            keep_symbols.append(s)
    print(",".join(keep_symbols[:1000]))

# target_link_options(mlir-opt PUBLIC -Wl,--export-all)
# target_link_options(mlir-opt PUBLIC -Wl,--unresolved-symbols=ignore-all)