"""Standalone, sharded H3 bidirectional audio/video inference."""

from configs.loader import load_config


def main():
    config = load_config()
    if config["check_config"]:
        import json

        print(json.dumps(config, indent=2, ensure_ascii=False))
        return
    from pipelines.bidirection import run

    run(config)


if __name__ == "__main__":
    main()
