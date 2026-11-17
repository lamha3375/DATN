
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    if not api_key:
        raise ValueError("Thiếu GEMINI_API_KEY")

    print("1. Đang khởi tạo Gemini client...", flush=True)

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=60000
        )
    )

    print("2. Đang gửi yêu cầu đến Gemini...", flush=True)
    start = time.time()

    response = client.models.generate_content(
        model=model,
        contents="Trả lời bằng một câu: Nguyễn Huệ là ai?"
    )

    print(f"3. Hoàn thành sau {time.time() - start:.2f} giây")
    print("Kết quả:", response.text)


if __name__ == "__main__":
    main()
