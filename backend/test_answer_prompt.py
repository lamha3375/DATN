
from app.prompts.answer_prompt import AnswerPrompt


def main():

    query = "Nguyễn Huệ đại phá quân Thanh năm nào?"

    context = """
VECTOR CONTEXT:

Document: Hoàng Lê nhất thống chí
Page: 120

Nguyễn Huệ lên ngôi Hoàng đế tại Phú Xuân
vào cuối năm 1788 và tiến quân ra Bắc.

GRAPH CONTEXT:

Node: Nguyễn Huệ
Type: NhanVat

Node: Chiến thắng Ngọc Hồi - Đống Đa
Type: SuKien

Relationship:
Nguyễn Huệ -> chỉ huy -> Chiến thắng Ngọc Hồi - Đống Đa
"""

    prompt = AnswerPrompt.build_prompt(
        query=query,
        context=context
    )

    print("===== GENERATED PROMPT =====")
    print(prompt)

    assert query in prompt
    assert "VECTOR CONTEXT" in prompt
    assert "GRAPH CONTEXT" in prompt

    print("\nPROMPT TEST PASSED")


if __name__ == "__main__":
    main()
