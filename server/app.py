from app import app


def main() -> None:
    """Run the API server entry point expected by OpenEnv validators."""
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
