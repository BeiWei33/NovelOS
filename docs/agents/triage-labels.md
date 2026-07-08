# Triage labels

The five canonical triage roles, all using default names:

| Role | Label string | Meaning |
|------|-------------|---------|
| needs-triage | `needs-triage` | Maintainer needs to evaluate |
| needs-info | `needs-info` | Waiting on reporter for more info |
| ready-for-agent | `ready-for-agent` | Fully specified, AFK-ready |
| ready-for-human | `ready-for-human` | Needs human implementation |
| wontfix | `wontfix` | Will not be actioned |

These are stored in the `labels` field of issue frontmatter. No mapping
overrides are configured — the label string equals the role name.