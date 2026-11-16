
import re
from typing import Dict, List, Any


class QueryAnalysisService:

    STOPWORDS = {
        "là", "của", "và", "có", "những", "ai", "nào", "thế",
        "bao", "nhiêu", "gì", "đâu", "sao", "chứ", "nhỉ", "ạ",
        "vậy", "hả", "kia", "này", "đấy", "đó", "nhé", "nha",
        "cho", "biết", "hãy", "kể", "về", "nói", "hỏi", "xin",
        "hướng", "dẫn", "tìm", "kiếm", "xem", "liệt", "kê",
        "mô", "tả", "giúp", "thử", "làm", "đọc", "so", "sánh",
        "phân", "tích", "định", "nghĩa", "trình", "bày", "tóm",
        "tắt", "tra", "cứu", "giải", "thích", "gồm", "trong",
        "ngoài", "trên", "dưới", "từ", "đến", "đang", "đã",
        "sẽ", "được", "bị", "với", "để", "như", "thì", "mà",
        "hoặc", "hay", "nhưng", "cũng", "đều", "rồi", "vẫn",
        "còn", "lại", "chỉ", "ngay", "luôn", "từng", "vừa",
        "mới", "sắp", "tới", "cả", "hết", "nữa", "rất",
        "khi", "lúc", "buổi", "ôi", "chao", "à", "ừm", "ờ", "vua"
    }

    # Dấu hiệu hỏi về nhân vật
    CHARACTER_KEYWORDS = {
        "là ai", "tiểu sử", "thân thế", "quê quán",
        "sinh ra", "mất năm", "qua đời", "nhân vật",
        "cuộc đời"
    }

    # Dấu hiệu hỏi về quan hệ giữa các thực thể
    RELATIONSHIP_KEYWORDS = {
        "quan hệ", "mối quan hệ", "liên hệ",
        "có quan hệ gì", "có quan hệ như thế nào",
        "là gì của", "là con của", "là cha của",
        "là mẹ của", "là vợ của", "là chồng của",
        "là anh của", "là em của", "là thầy của",
        "là học trò của", "có quan hệ gia đình",
        "quan hệ gia đình", "quan hệ huyết thống",
        "con trai", "con gái", "con nuôi",
        "vợ", "chồng", "cha", "mẹ", "bố",
        "anh em", "chị em", "anh trai", "em trai",
        "chị gái", "em gái", "gia đình",
        "họ hàng", "dòng họ", "gia phả",
        "huyết thống", "nhạc phụ", "nhạc mẫu",
        "con rể", "con dâu", "sư phụ", "đệ tử"
    }

    # Dấu hiệu hỏi về sự kiện lịch sử
    EVENT_KEYWORDS = {
        "trận", "chiến thắng", "đại phá",
        "khởi nghĩa", "đánh", "tiến quân",
        "xuất quân", "bao vây", "tấn công",
        "phản công", "phòng thủ", "tử trận",
        "bắt sống", "đầu hàng", "thất thủ",
        "dẹp loạn", "bình định", "chiến dịch",
        "cuộc chiến", "chiến tranh", "giao tranh",
        "đụng độ", "lên ngôi", "thoái vị",
        "lập quốc", "đăng quang", "hội nghị",
        "ký kết", "hòa ước", "sắc phong",
        "cải cách", "đảo chính", "truất phế",
        "dời đô", "bùng nổ", "diễn ra",
        "nổ ra", "kết thúc"
    }

    # Dấu hiệu hỏi nguyên nhân, ý nghĩa, tác động
    REASONING_KEYWORDS = {
        "vì sao", "tại sao", "nguyên nhân",
        "lý do", "do đâu", "vì điều gì",
        "nhân tố", "căn nguyên", "nguồn gốc",
        "bắt nguồn từ", "ảnh hưởng", "ý nghĩa",
        "hậu quả", "tác động", "hệ lụy",
        "đóng góp", "vai trò", "giá trị",
        "mục đích", "giải thích"
    }

    # Câu hỏi thời gian và địa điểm
    TIME_LOCATION_PATTERNS = {
        "năm nào", "khi nào", "vào lúc nào",
        "thời gian nào", "mấy giờ", "ở đâu",
        "tại đâu", "nơi nào", "quốc gia nào",
        "tỉnh nào", "nơi diễn ra"
    }

    # Câu hỏi tổng quan
    GENERAL_PATTERNS = {
        "tổng quan", "khái quát", "toàn cảnh",
        "những thông tin", "các thông tin",
        "lịch sử tây sơn", "phong trào tây sơn",
        "thông tin về"
    }

    def normalize_query(self, query: str) -> str:
        """Chuẩn hóa khoảng trắng và chữ hoa/thường."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query không được để trống")

        return re.sub(r"\s+", " ", query.strip().lower())

    def tokenize(self, query: str) -> List[str]:
        """Tách token, giữ nguyên dấu tiếng Việt."""

        return re.findall(r"\w+", query, flags=re.UNICODE)

    @staticmethod
    def _contains_phrase(query: str, phrase: str) -> bool:
        """Kiểm tra cụm từ theo ranh giới từ, bỏ qua dấu câu."""

        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        return re.search(pattern, query) is not None

    def _matches_any(
        self,
        query: str,
        keywords: set
    ) -> bool:
        """Kiểm tra query có chứa một trong các từ khóa."""

        return any(
            self._contains_phrase(query, keyword)
            for keyword in keywords
        )

    def extract_keywords(self, query: str) -> List[str]:
        """
        Trích xuất từ khóa đơn và cụm từ liên tiếp.
        - Chuẩn hóa từ khóa thành chữ thường.
        - Không ghép token qua stopword.
        - Loại bỏ từ khóa trùng lặp.
        """

        query = query.strip().lower()
        tokens = self.tokenize(query)

        keywords = []
        seen = set()

        # 1. Trích xuất từ khóa đơn
        for token in tokens:
            if token not in self.STOPWORDS and len(token) > 1:
                if token not in seen:
                    keywords.append(token)
                    seen.add(token)

        # 2. Trích xuất cụm từ gồm 3 từ và 2 từ
        for size in (3, 2):
            for i in range(len(tokens) - size + 1):

                original_tokens = tokens[i:i + size]

                # Không tạo cụm có chứa stopword
                if any(
                    token in self.STOPWORDS
                    for token in original_tokens
                ):
                    continue

                phrase = " ".join(original_tokens)

                if phrase not in seen:
                    keywords.insert(0, phrase)
                    seen.add(phrase)

        return keywords

    def classify_intent(self, query: str) -> str:
        """Phân loại ý định câu hỏi."""

        query = self.normalize_query(query)

        # 1. Quan hệ giữa nhân vật/thực thể
        if self._matches_any(
            query,
            self.RELATIONSHIP_KEYWORDS
        ):
            return "relationship_query"

        # 2. Nguyên nhân, ý nghĩa, vai trò
        if self._matches_any(
            query,
            self.REASONING_KEYWORDS
        ):
            return "reasoning_query"

        # 3. Sự kiện lịch sử
        if self._matches_any(
            query,
            self.EVENT_KEYWORDS
        ):
            return "event_query"

        # 4. Câu hỏi thời gian và địa điểm
        if self._matches_any(
            query,
            self.TIME_LOCATION_PATTERNS
        ):
            return "event_query"

        # 5. Câu hỏi về nhân vật
        if self._matches_any(
            query,
            self.CHARACTER_KEYWORDS
        ):
            return "character_query"

        # 6. Câu hỏi tổng quan
        if self._matches_any(
            query,
            self.GENERAL_PATTERNS
        ):
            return "general_query"

        return "general_query"

    def get_strategy(self, intent: str) -> Dict[str, bool]:
        """Xác định chiến lược truy xuất dữ liệu."""

        return {
            "vector_search": True,
            "graph_search": True,
            "relationship_expansion": intent in {
                "relationship_query",
                "event_query",
                "reasoning_query"
            }
        }

    def analyze(self, query: str) -> Dict[str, Any]:
        """Phân tích toàn bộ câu hỏi."""

        normalized = self.normalize_query(query)

        intent = self.classify_intent(normalized)
        keywords = self.extract_keywords(normalized)

        return {
            "original_query": query.strip(),
            "normalized_query": normalized,
            "tokens": self.tokenize(normalized),
            "keywords": keywords,
            "intent": intent,
            "retrieval_strategy": self.get_strategy(intent)
        }


query_analysis_service = QueryAnalysisService()
