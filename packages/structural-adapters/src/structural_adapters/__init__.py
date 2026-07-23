"""Owned, audited ports of the KOMPOSOS-derived methods audit procedures use.

The prototype reached these through runtime sys.path mutation into a vendored
KOMPOSOS-V checkout (unshippable, P1). Only the code the procedures actually
require is ported here — a composition-reachability index and Dempster-Shafer
evidence fusion — with semantics kept operation-for-operation identical so
receipts stay bit-compatible.
"""
