
import os
import re
import pandas as pd
import unicodedata

from neo4j import GraphDatabase
from dotenv import load_dotenv

# 1. CẤU HÌNH
ENV_PATH = r"D:\DATN\backend\.env"
load_dotenv(ENV_PATH)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "datn")

CSV_DIR = r"D:\DATN\CSV"

# 2. ÁNH XẠ THẾ LỰC
FACTION_NAME_TO_IDS = {
    "Tây Sơn": ["FAC_001"],
    "Chúa Trịnh": ["FAC_002"],
    "Nhà Hậu Lê": ["FAC_003"],
    "Chúa Nguyễn": ["FAC_004"],
    "Nhà Nguyễn": ["FAC_005"],
    "Chúa Nguyễn / Nhà Nguyễn": ["FAC_004", "FAC_005"],
    "Tây Sơn / Bắc Hà": ["FAC_001", "FAC_003"],
    "Tây Sơn / Chúa Nguyễn": ["FAC_001", "FAC_004"],
    "Mãn Thanh": ["FAC_006"],
    "Xiêm La": ["FAC_007"],
}

# 3. HÀM XỬ LÝ
def clean_str(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def get_value(row, column):
    return clean_str(row.get(column, ""))


def read_csv(filename):
    path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Không tìm thấy file: {path}")

    return pd.read_csv(path, encoding="utf-8-sig").fillna("")


def normalize_rel_type(rel_type):
    # Bỏ dấu tiếng Việt (Unicode Normalization Form KD)
    nfkd_form = unicodedata.normalize('NFKD', rel_type)
    text_no_accent = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # Thay khoảng trắng và ký tự đặc biệt thành dấu gạch dưới, giữ lại chữ cái/số
    clean_text = re.sub(r'[^A-Za-z0-9_]', '_', text_no_accent)
    clean_text = re.sub(r'_+', '_', clean_text).strip('_').upper()
    
    if not clean_text or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", clean_text):
        return "RELATED_TO"
    return clean_text


# 4. XÓA DATABASE CŨ
def clear_database(tx):
    print("Đang xóa dữ liệu cũ...")
    tx.run("MATCH (n) DETACH DELETE n").consume()
    print("Đã xóa dữ liệu cũ!")


# 5. TẠO CONSTRAINTS
def setup_constraints(tx):
    labels = [
        "Person", "Event", "Location", "Faction",
        "Policy", "Document", "Unit", "Tactics", "Source"
    ]

    for label in labels:
        tx.run(f"""
            CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS
            FOR (n:{label})
            REQUIRE n.id IS UNIQUE
        """).consume()

    print("Đã tạo Constraints!")


# 6. IMPORT NODES
def import_all_nodes(tx):
    total_nodes = 0

    # PERSON
    print("Đang import Person...")
    df = read_csv("Nodes_Person.csv")

    for _, r in df.iterrows():
        node_id = get_value(r, "Mã nhân vật (ID)")
        if not node_id:
            continue

        tx.run("""
            MERGE (n:Person {id: $id})
            SET n.name = $name,
                n.alias = $alias,
                n.role = $role,
                n.dynasty = $dynasty,
                n.bio = $bio,
                n.period = $period,
                n.module = $module
        """,
            id=node_id,
            name=get_value(r, "Họ và tên chuẩn"),
            alias=get_value(r, "Bí danh / Tên gọi khác"),
            role=get_value(r, "Chức vị / Vai trò"),
            dynasty=get_value(r, "Thế lực / Triều đại"),
            bio=get_value(r, "Tiểu sử & Ghi chú"),
            period=get_value(r, "Giai đoạn lịch sử"),
            module=get_value(r, "Phân hệ Module")
        ).consume()

        total_nodes += 1

    # EVENT
    print("Đang import Event...")
    df = read_csv("Nodes_Event.csv")

    for _, r in df.iterrows():
        node_id = get_value(r, "Mã sự kiện (ID)")
        if not node_id:
            continue

        tx.run("""
            MERGE (n:Event {id: $id})
            SET n.name = $name,
                n.startDate = $startDate,
                n.endDate = $endDate,
                n.eventType = $eventType,
                n.description = $description,
                n.result = $result,
                n.significance = $significance,
                n.period = $period,
                n.module = $module,
                n.tags = $tags,
                n.rag_text = $rag_text
        """,
            id=node_id,
            name=get_value(r, "Tên sự kiện"),
            startDate=get_value(r, "Bắt đầu (Dương lịch)"),
            endDate=get_value(r, "Kết thúc (Dương lịch)"),
            eventType=get_value(r, "Loại sự kiện"),
            description=get_value(r, "Mô tả sự kiện"),
            result=get_value(r, "Kết quả"),
            significance=get_value(r, "Ý nghĩa lịch sử"),
            period=get_value(r, "Giai đoạn lịch sử"),
            module=get_value(r, "Phân hệ Module"),
            tags=get_value(r, "Tags"),
            rag_text=get_value(r, "rag_document_text")
        ).consume()

        total_nodes += 1

    # LOCATION
    print("Đang import Location...")
    df = read_csv("Nodes_Location.csv")

    for _, r in df.iterrows():
        node_id = get_value(r, "Mã địa danh (ID)")
        if not node_id:
            continue

        tx.run("""
            MERGE (n:Location {id: $id})
            SET n.name = $name,
                n.historicalName = $histName,
                n.modernName = $modName,
                n.region = $region,
                n.context = $context
        """,
            id=node_id,
            name=get_value(r, "Tên địa danh chuẩn"),
            histName=get_value(r, "Tên lịch sử / Cổ sử"),
            modName=get_value(r, "Địa danh ngày nay"),
            region=get_value(r, "Vùng miền"),
            context=get_value(r, "Bối cảnh lịch sử")
        ).consume()

        total_nodes += 1

    # FACTION
    print("Đang import Faction...")
    df = read_csv("Nodes_Faction.csv")

    for _, r in df.iterrows():
        node_id = get_value(r, "Mã thế lực (ID)")
        if not node_id:
            continue

        tx.run("""
            MERGE (n:Faction {id: $id})
            SET n.name = $name,
                n.fullName = $fullName,
                n.leaders = $leaders,
                n.headquarters = $hq,
                n.era = $era,
                n.notes = $notes
        """,
            id=node_id,
            name=get_value(r, "Tên thế lực"),
            fullName=get_value(r, "Tên đầy đủ"),
            leaders=get_value(r, "Thủ lĩnh / Lãnh đạo"),
            hq=get_value(r, "Đại bản doanh"),
            era=get_value(r, "Thời kỳ"),
            notes=get_value(r, "Ghi chú lịch sử")
        ).consume()

        total_nodes += 1

    # POLICY
    print("Đang import Policy...")
    df = read_csv("Nodes_Policy.csv")

    for _, r in df.iterrows():
        node_id = get_value(r, "Mã chính sách (ID)")
        if not node_id:
            continue

        tx.run("""
            MERGE (n:Policy {id: $id})
            SET n.name = $name,
                n.field = $field,
                n.year = $year,
                n.issuer = $issuer,
                n.content = $content
        """,
            id=node_id,
            name=get_value(r, "Tên chính sách"),
            field=get_value(r, "Lĩnh vực"),
            year=get_value(r, "Năm ban hành"),
            issuer=get_value(r, "Người ban hành"),
            content=get_value(r, "Nội dung chính sách")
        ).consume()

        total_nodes += 1

    # DOCUMENT
    print("Đang import Document...")
    df = read_csv("Nodes_Document.csv")

    for _, r in df.iterrows():
        node_id = get_value(r, "Mã văn kiện (ID)")
        if not node_id:
            continue

        tx.run("""
            MERGE (n:Document {id: $id})
            SET n.name = $name,
                n.author = $author,
                n.year = $year,
                n.category = $category,
                n.content = $content
        """,
            id=node_id,
            name=get_value(r, "Tên văn kiện / Tấu biểu"),
            author=get_value(r, "Tác giả / Ngự soạn"),
            year=get_value(r, "Năm ban hành"),
            category=get_value(r, "Thể loại"),
            content=get_value(r, "Nội dung văn kiện")
        ).consume()

        total_nodes += 1

    # UNIT VÀ TACTICS
    print("Đang import Unit và Tactics...")
    df = read_csv("Nodes_Unit.csv")

    for _, r in df.iterrows():
        node_id = get_value(r, "Mã đơn vị (ID)")
        if not node_id:
            continue

        label = "Tactics" if node_id.startswith("TAC_") else "Unit"

        tx.run(f"""
            MERGE (n:{label} {{id: $id}})
            SET n.name = $name,
                n.commander = $cmd,
                n.category = $cat,
                n.characteristics = $char
        """,
            id=node_id,
            name=get_value(r, "Tên đơn vị / Chiến thuật"),
            cmd=get_value(r, "Chỉ huy"),
            cat=get_value(r, "Phân loại"),
            char=get_value(r, "Đặc điểm chiến thuật / Binh chủng")
        ).consume()

        total_nodes += 1

    # SOURCE
    print("Đang import Source...")
    df = read_csv("Event_Sources.csv")

    columns = ["Mã nguồn", "Tên tác phẩm", "Tác giả", "Tệp số hóa"]
    df_src = df[columns].drop_duplicates()

    for _, r in df_src.iterrows():
        node_id = get_value(r, "Mã nguồn")
        if not node_id:
            continue

        tx.run("""
            MERGE (n:Source {id: $id})
            SET n.name = $name,
                n.author = $author,
                n.file = $file
        """,
            id=node_id,
            name=get_value(r, "Tên tác phẩm"),
            author=get_value(r, "Tác giả"),
            file=get_value(r, "Tệp số hóa")
        ).consume()

        total_nodes += 1

    print(f"Tổng số Nodes đã xử lý: {total_nodes}")


# 7. IMPORT RELATIONSHIPS
def import_relationships(tx):
    print("An đang import Relationships...")

    df = read_csv("Relationships.csv")

    created_count = 0
    skipped_count = 0

    for _, r in df.iterrows():
        src = get_value(r, "Mã thực thể nguồn")
        raw_dst = get_value(r, "Mã thực thể đích")

        raw_rel_type = get_value(r, "Loại quan hệ (Tiếng Việt)")
        rel_type = normalize_rel_type(raw_rel_type)

        desc = get_value(r, "Mô tả quan hệ lịch sử")
        citation = get_value(r, "Trích dẫn nguồn")

        if not src or not raw_dst or not rel_type:
            skipped_count += 1
            continue

        target_ids = FACTION_NAME_TO_IDS.get(raw_dst, [raw_dst])

        for dst in target_ids:
            result = tx.run(f"""
                MATCH (a {{id: $src}})
                MATCH (b {{id: $dst}})
                MERGE (a)-[rel:`{rel_type}`]->(b)
                ON CREATE SET rel.description = $desc,
                              rel.citation = $citation
                RETURN count(rel) AS c
            """,
                src=src,
                dst=dst,
                desc=desc,
                citation=citation
            )

            record = result.single()

            if record and record["c"] > 0:
                created_count += 1
            else:
                skipped_count += 1

    print(f"Tổng Relationships đã xử lý: {created_count}")
    print(f"Số quan hệ bị bỏ qua: {skipped_count}")


# 8. KIỂM TRA DATABASE
def check_database(tx):
    print("\n========== THỐNG KÊ DATABASE ==========")

    result = tx.run("""
        MATCH (n)
        RETURN count(n) AS totalNodes
    """)
    print(f"Tổng Nodes: {result.single()['totalNodes']}")

    result = tx.run("""
        MATCH ()-[r]->()
        RETURN count(r) AS totalRelationships
    """)
    print(f"Tổng Relationships: {result.single()['totalRelationships']}")

    print("\n========== THỐNG KÊ THEO LABEL ==========")

    result = tx.run("""
        MATCH (n)
        UNWIND labels(n) AS label
        RETURN label, count(*) AS total
        ORDER BY label
    """)

    for record in result:
        print(f"{record['label']}: {record['total']}")

    print("========================================")


# 9. CHƯƠNG TRÌNH CHÍNH
def main():
    if not NEO4J_PASSWORD:
        raise ValueError("Chưa cấu hình NEO4J_PASSWORD trong file .env")

    if not os.path.isdir(CSV_DIR):
        raise FileNotFoundError(f"Không tìm thấy thư mục CSV: {CSV_DIR}")

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    try:
        driver.verify_connectivity()

        with driver.session(database=DATABASE) as session:
            print("========== NEO4J DATA IMPORT SYSTEM ==========")

            print("\n[1/5] Xóa dữ liệu cũ...")
            session.execute_write(clear_database)

            print("\n[2/5] Tạo Constraints...")
            session.execute_write(setup_constraints)

            print("\n[3/5] Import Nodes...")
            session.execute_write(import_all_nodes)

            print("\n[4/5] Import Relationships...")
            session.execute_write(import_relationships)

            print("\n[5/5] Kiểm tra dữ liệu...")
            session.execute_read(check_database)

            print("\n========== IMPORT HOÀN TẤT! ==========")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
