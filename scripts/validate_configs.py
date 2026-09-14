"""Validate PhotoScpec YAML configuration files."""
import argparse

from photoscpec.config import load_specs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_dir", nargs="?", default="configs")
    args = parser.parse_args()
    result = load_specs(args.config_dir)
    for error in result.errors:
        print(f"ERROR: {error}")
    print(f"Loaded {len(result.specs)} valid specification(s).")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
