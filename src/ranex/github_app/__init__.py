"""The GitHub acceptance loop: bind a PR head, publish its check, receive events.

Host-side only, like `deps fetch`: nothing in this package may run inside
governed execution, where the network is refused by construction. The signed
surface is unchanged — this package projects the verdicts `gate evaluate`
already publishes; it never judges and never signs.
"""
