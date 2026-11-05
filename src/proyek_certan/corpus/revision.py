"""Conservative, versioned corrections; original corpus artifacts are immutable.

Only the reviewed source-specific layout patterns below are changed. This is
not a general PDF reflow algorithm: UCF's tables and diagrams remain untouched.
"""

from __future__ import annotations

import re


VERSION = "m3-reviewed-v2"


def revise_text(document_id: str, text: str) -> tuple[str, dict]:
    before = text
    changes: dict[str, int] = {}
    if document_id == "DOC06":
        # The official <pre> itself contains two '$' prompts on the first line.
        # Split only the reviewed example, preserving every non-whitespace token.
        replacements = (
            ("mode in VLAN 9: $ ovs-vsctl", "mode in VLAN 9:\n$ ovs-vsctl"),
            ("$ ovs-vsctl add-br br0 $ ovs-vsctl add-port br0 eth0 tag=9 vlan_mode=native-tagged In this situation,",
             "$ ovs-vsctl add-br br0\n$ ovs-vsctl add-port br0 eth0 tag=9 vlan_mode=native-tagged\nIn this situation,"),
        )
        for old, new in replacements:
            if text.count(old) != 1:
                raise ValueError("DOC06 reviewed command anchor changed; audit source again")
            text = text.replace(old, new)
        if text.split() != before.split():
            raise ValueError("DOC06 correction changed source tokens")
        changes["command_example_line_breaks"] = 3
    elif document_id == "DOC11":
        # Verified against pypdf page boundaries: these are printed folios 1..16.
        folios = re.findall(r"(?m)^\d{1,2}$", text)
        if folios != [str(i) for i in range(1, 17)]:
            raise ValueError("DOC11 page-number anchors changed; audit PDF again")
        text = re.sub(r"(?m)^\d{1,2}\n", "", text)
        changes["page_folios_removed"] = len(folios)
        # Hard wraps / TOC / figure tables deliberately retained: ambiguous layout.
    elif document_id == "DOC13":
        header = "University Policy 08-010 University Network Administration\n"
        if text.count(header) != 4:
            raise ValueError("DOC13 running header count changed; audit PDF again")
        text = text.replace(header, "")
        changes["repeated_running_headers_removed"] = 4
        # Policy prose only: preserve numbered clauses, lettered items, headings,
        # front matter and contact lines. Join known continuation lines in clauses.
        lines = text.splitlines()
        output: list[str] = []
        in_clause = False
        joins = 0
        for line in lines:
            stripped = line.strip()
            if re.match(r"^(?:\d+(?:\.\d+)+\.|[a-d]\.) ", stripped):
                output.append(stripped)
                in_clause = True
            elif not stripped or re.match(r"^(?:#|\d+\. |History$|Contacts$|Next scheduled|6\. Related)", stripped):
                output.append(line)
                in_clause = False
            elif in_clause:
                output[-1] += " " + stripped
                joins += 1
            else:
                output.append(line)
        text = "\n".join(output) + "\n"
        if text.split() != before.replace(header, "").split():
            raise ValueError("DOC13 reflow changed source tokens")
        changes["prose_line_breaks_joined"] = joins
    return text, {"changed": text != before, "operations": changes}


def document_kind(title: str) -> str:
    """Source-title classification, independent of queries or relevance labels."""
    title = title.casefold()
    if any(term in title for term in ("troubleshoot", "diagnose", "faq")):
        return "diagnostic"
    if any(term in title for term in ("incident", "insiden", "service desk")):
        return "incident_procedure"
    return "network_policy"
