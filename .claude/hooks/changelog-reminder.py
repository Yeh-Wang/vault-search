"""PostToolUse hook: trigger changelog skill when source code is modified."""
import json
import sys
import re


def main():
    data = json.load(sys.stdin)
    file_path = (
        data.get("tool_input", {}).get("file_path")
        or data.get("tool_response", {}).get("filePath")
        or ""
    )

    if re.search(r"[\\/]vault_search[\\/].*\.py$", file_path):
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        "Source code in src/vault_search/ was modified. "
                        "Before finishing this task, invoke the /changelog skill "
                        "to generate a changelog entry in docs/changelog/."
                    ),
                }
            },
            sys.stdout,
        )
    else:
        sys.stdout.write("{}")


if __name__ == "__main__":
    main()
