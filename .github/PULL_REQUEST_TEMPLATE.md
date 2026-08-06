## Summary

<!-- Brief description of what this PR changes and why -->

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New extractor or format support
- [ ] Breaking change (existing behavior changes)
- [ ] Documentation update
- [ ] Test improvement

## Changes made

<!-- List the specific changes. If adding an extractor, name it and where it sits in the chain. -->

## Testing

- [ ] Tests pass (`cd src && pytest`)
- [ ] Linter passes (`ruff check .`)
- [ ] Tested manually with a real file (describe below)

<!-- What file(s) did you test with? What engine was selected? Did the output look correct? -->

## Checklist

- [ ] New extractors raise `ExtractorUnavailable` when their tool is missing
- [ ] New extractors are wired into the appropriate chain in `router.py`
- [ ] README.md updated if formats or engines changed
- [ ] No hardcoded paths, secrets, or personal info in the code