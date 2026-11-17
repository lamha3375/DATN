
from app.core.config import settings


def main():
    print("APP:", settings.APP_NAME)
    print("GEMINI MODEL:", settings.GEMINI_MODEL)
    print("GEMINI TIMEOUT:", settings.GEMINI_TIMEOUT)

    print(
        "GEMINI API KEY:",
        "Configured" if settings.GEMINI_API_KEY else "Missing"
    )


if __name__ == "__main__":
    main()
