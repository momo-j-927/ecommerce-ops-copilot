import argparse
import json

from .workflow import run_query


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    print(json.dumps(run_query(args.query).model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
