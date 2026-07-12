"""Legacy compatibility shim.

V5.2 removed the aggregated diagnostics provider. Each source now has its own
module under pios.providers.health. This file intentionally registers nothing,
so uploading V5.2 over V5.1 also neutralizes the old implementation.
"""
