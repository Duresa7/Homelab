#!/usr/bin/env python3
"""key-rotation: the rotation state machine for one identity (restyle of the
2026-07-20 Excalidraw diagram, content kept). Facts: Platforms/Ansible/Documentation/
Architecture.md (Rotation State Machine) and Platforms/Ansible/Source/ssh-key-automation/
README.md (Rotation Workflow)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "key-rotation.svg")
d = Diagram("key-rotation", "Key rotation state machine (one identity)",
            "Five states of one identities/<id>.yml file; the removal gate opens only when every condition below holds",
            source="Platforms/Ansible/Documentation/Architecture.md, Platforms/Ansible/Source/ssh-key-automation/README.md",
            width=1640, gap=96, card_w=200)

d.group("states", "Rotation of one identity", badge="identities/<id>.yml", family="Internal")
d.card("states", "s1", "Current key only", sub1="current_public_key, fingerprint", sub2="no replacement configured", logo="glyph:1")
d.card("states", "s2", "Replacement configured", sub1="replacement_public_key set", sub2="made on the owner device", logo="glyph:2")
d.card("states", "s3", "Both keys present", sub1="ssh-key-stage.yml, additive", sub2="old and new on every target", logo="glyph:3")
d.card("states", "s4", "Verified", sub1="verify play, then a login test", sub2="operator_verified: true", logo="glyph:4")
d.card("states", "s5", "Old key removed", sub1="ssh-key-retire.yml", sub2="phrase RETIRE <identity-id>", logo="glyph:5")

d.group("gate", "Removal gate: all five must hold", family="Dmz", notes=[
    (None, "a distinct replacement public key is configured"),
    (None, "both old and replacement keys are present on every selected target"),
    (None, "the replacement was tested from the owner device and operator_verified is true"),
    (None, "the exact phrase RETIRE <identity-id> is supplied"),
    (None, "every selected target is reachable; one offline host blocks the whole removal"),
])
d.group("after", "After retirement, in the identity file", family="External", notes=[
    (None, "promote the replacement to current_public_key"),
    (None, "update fingerprint"),
    (None, "clear replacement_public_key"),
    (None, "reset operator_verified to false"),
    (None, "rerun the validator and the audit"),
])

d.row("states")
d.row("gate", "after")

d.edge("s1", "s2", "supply new key", color="blue")
d.edge("s2", "s3", "stage", color="blue")
d.edge("s3", "s4", "verify + test", color="blue")
d.edge("s4", "s5", "RETIRE confirm", color="orange")
d.edge("s5", "s1", "promote replacement in the identity file", color="purple", from_side="bottom", to_side="bottom", y="gap:0", label_seg=1)

d.legend_family("Internal", "state of the identity file"); d.legend_family("Dmz", "gate"); d.legend_family("External", "bookkeeping")
d.legend_edge("forward transition", "solid", "blue"); d.legend_edge("guarded removal", "solid", "orange"); d.legend_edge("back to the start", "solid", "purple")
d.footnote("A failed stage leaves the old key installed. A partial retirement is recovered by reinstalling the recorded old key through a surviving credential, then rerunning the audit.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
