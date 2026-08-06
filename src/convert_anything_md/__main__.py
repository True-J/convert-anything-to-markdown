"""Allows `python -m convert_anything_md file1.pdf file2.docx` usage.

The `sys.exit(main())` is load-bearing - earlier revisions just called
`main()` and discarded the return code, so `python -m convert_anything_md
some-directory` exited 0 even when it printed an error to stderr.
"""

import sys

from convert_anything_md.cli import main

if __name__ == "__main__":
    sys.exit(main())
