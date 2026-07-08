# Issue tracker

Issues are tracked as local markdown files.

## Location

Each feature or workstream gets its own subdirectory under `.scratch/<feature>/`.
Issue files use `.md` extension with YAML frontmatter for metadata.

## Frontmatter schema

```yaml
---
title: <short title>
status: <open | closed>
labels:
  - needs-triage
created: <YYYY-MM-DD>
---
```

## Labels

The five canonical triage roles map to the `labels` field in frontmatter:
`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.

## CLI usage

Create a new issue:

```bash
mkdir -p .scratch/my-feature
cat > .scratch/my-feature/my-issue.md <<EOF
---
title: My issue title
status: open
labels:
  - needs-triage
created: $(date +%Y-%m-%d)
---
EOF
```