"""Extension point for application-specific configuration resolution.

No Global/Fab/Tool hierarchy, merge policy, or business configuration store is
installed. A product must define identifiers, precedence, conflict behavior,
versioning and authorization before implementing its resolver in this layer.
"""
