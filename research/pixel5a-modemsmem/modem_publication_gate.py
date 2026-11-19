"""Pure host-only Pixel 5a modem publication gate model.

This models a proposed fail-closed policy. It does not read device trees,
write SMEM, invoke firmware, use ADB, or operate any kernel or hardware API.
No event here is evidence that a corresponding hardware condition is met.
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Gate:
    provider_ready: bool = False
    item_existing: bool | None = None
    owner_cleared: bool = False
    existing_item_preserved: bool = False
    payload_valid: bool = False
    visible: bool = False
    acknowledged: bool = False
    manual_authorized: bool = False
    recovery_blocked: bool = False

    @property
    def may_start(self) -> bool:
        return all((
            self.provider_ready,
            self.item_existing is not None,
            self.owner_cleared,
            self.existing_item_preserved,
            self.payload_valid,
            self.visible,
            self.acknowledged,
            self.manual_authorized,
            not self.recovery_blocked,
        ))


def transition(state: Gate, event: str) -> Gate:
    """Advance a *fictional* policy state; never start firmware."""
    if event == "provider_lost":
        return Gate(recovery_blocked=True)
    if event == "crash":
        return Gate(provider_ready=state.provider_ready, recovery_blocked=True)
    if event == "recovery_reviewed":
        if not state.provider_ready or not state.recovery_blocked:
            raise ValueError("recovery review requires provider and prior block")
        return Gate(provider_ready=True)
    if state.recovery_blocked:
        raise ValueError("recovery is blocked pending fresh review")
    if event == "provider_ready":
        return replace(state, provider_ready=True)
    if not state.provider_ready:
        raise ValueError("provider unavailable: simulated EPROBE_DEFER")
    if event in ("existing_item", "new_item"):
        if state.item_existing is not None:
            raise ValueError("item discovery already performed")
        return replace(state, item_existing=(event == "existing_item"))
    if state.item_existing is None:
        raise ValueError("item ownership unknown")
    if event == "owner_cleared":
        return replace(state, owner_cleared=True)
    if not state.owner_cleared:
        raise ValueError("cannot proceed without explicit owner clearance")
    if event == "preservation_verified":
        return replace(state, existing_item_preserved=True)
    if not state.existing_item_preserved:
        raise ValueError("existing/new item policy not verified")
    if event == "payload_validated":
        return replace(state, payload_valid=True)
    if not state.payload_valid:
        raise ValueError("invalid or incomplete payload")
    if event == "visibility_confirmed":
        return replace(state, visible=True)
    if not state.visible:
        raise ValueError("visibility not confirmed")
    if event == "acknowledged":
        return replace(state, acknowledged=True)
    if not state.acknowledged:
        raise ValueError("no publication acknowledgement")
    if event == "manual_authorized":
        return replace(state, manual_authorized=True)
    raise ValueError("unrecognized or out-of-order gate event")
