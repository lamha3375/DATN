document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const API = window.ApiClient;
    const $ = id => document.getElementById(id);

    const el = {
        network: $("knowledge-network"),
        loading: $("graph-loading"),
        error: $("graph-error"),
        errorMessage: $("graph-error-message"),
        empty: $("graph-empty"),

        totalNodes: $("total-node-count"),
        totalEdges: $("total-edge-count"),
        visibleNodes: $("visible-node-count"),
        visibleEdges: $("visible-edge-count"),
        status: $("graph-status-text"),

        searchInput: $("graph-search-input"),
        searchType: $("graph-search-type"),
        searchButton: $("graph-search-btn"),
        nodeControls: $("graph-node-controls"),
        zoomIn: $("graph-zoom-in"),
        zoomOut: $("graph-zoom-out"),
        zoomLevel: $("graph-zoom-level"),
        searchResults: $("search-results"),

        filter: $("entity-filter"),
        fit: $("fit-graph-btn"),
        reset: $("reset-graph-btn"),
        retry: $("graph-retry-btn"),
        clearFocus: $("clear-focus-btn"),

        placeholder: $("detail-placeholder"),
        content: $("detail-content"),
        type: $("detail-type"),
        name: $("detail-name"),
        businessId: $("detail-business-id"),
        properties: $("detail-properties-list"),
        relations: $("detail-relations-list"),
        relationCount: $("relation-count"),
        expand: $("expand-node-btn")
    };

    const CONFIG = {
        INITIAL_LIMIT: 40,
        INITIAL_NODE_COUNT: 1,
        EXPANSION_LIMIT: 8,
        SEARCH_LIMIT: 20,
        MAX_PROPERTY_LENGTH: 1200
    };

    const LABELS = {
        Person: "Nhân vật",
        Event: "Sự kiện",
        Location: "Địa điểm",
        Faction: "Phe phái",
        Policy: "Chính sách",
        Document: "Văn kiện",
        Unit: "Đơn vị",
        Tactics: "Chiến thuật",
        Source: "Nguồn tư liệu",
        NhanVat: "Nhân vật",
        SuKien: "Sự kiện",
        DiaDiem: "Địa điểm",
        TheLuc: "Phe phái",
        NguonTaiLieu: "Nguồn tư liệu",
        Unknown: "Thực thể"
    };

    const TYPE_ALIASES = {
        NhanVat: "Person", SuKien: "Event", DiaDiem: "Location",
        TheLuc: "Faction", NguonTaiLieu: "Source"
    };

    const RELATION_GROUPS = {
        family: { label: "Gia đình – Huyết thống" },
        allies: { label: "Đồng minh – Thân cận" },
        hierarchy: { label: "Cấp trên – Cấp dưới" },
        teachers: { label: "Thầy – Trò" },
        opponents: { label: "Đối thủ – Kẻ thù" },
        other: { label: "Quan hệ khác" }
    };

    const RELATION_PRIORITY = ["family", "allies", "hierarchy", "teachers", "opponents", "other"];

    const PROPERTY_LABELS = {
        name: "Tên",
        title: "Tiêu đề",
        entity: "Thực thể",
        ten: "Tên",
        alias: "Tên gọi khác",
        aliases: "Tên gọi khác",

        role: "Vai trò",
        position: "Chức vụ",
        occupation: "Nghề nghiệp",
        dynasty: "Triều đại",
        period: "Thời kỳ",
        bio: "Tiểu sử",
        biography: "Tiểu sử",
        birthDate: "Ngày sinh",
        deathDate: "Ngày mất",
        birthYear: "Năm sinh",
        deathYear: "Năm mất",
        hometown: "Quê quán",

        description: "Mô tả",
        summary: "Tóm tắt",
        content: "Nội dung",
        context: "Bối cảnh",
        result: "Kết quả",
        significance: "Ý nghĩa lịch sử",
        historicalSignificance: "Ý nghĩa lịch sử",

        startDate: "Thời gian bắt đầu",
        endDate: "Thời gian kết thúc",
        date: "Thời gian",
        year: "Năm",
        eventType: "Loại sự kiện",

        location: "Địa điểm",
        locationName: "Tên địa điểm",
        historicalName: "Tên lịch sử",
        modernName: "Tên hiện nay",
        region: "Khu vực",
        country: "Quốc gia",

        leader: "Người lãnh đạo",
        members: "Thành viên",
        faction: "Phe phái",
        unit: "Đơn vị",
        tactics: "Chiến thuật",
        policy: "Chính sách",

        author: "Tác giả",
        source: "Nguồn tư liệu",
        sourceName: "Tên nguồn",
        publisher: "Nhà xuất bản",
        publicationDate: "Ngày xuất bản",
        documentType: "Loại tài liệu",
        url: "Đường dẫn",

        tags: "Từ khóa",
        note: "Ghi chú",
        notes: "Ghi chú",
        rank: "Cấp bậc",
        militaryRank: "Cấp bậc quân sự",
        achievements: "Thành tựu",
        weapons: "Vũ khí",
        forces: "Lực lượng",
        participants: "Người tham gia",
        commander: "Người chỉ huy",
        cause: "Nguyên nhân",
        consequences: "Hệ quả",
        duration: "Thời gian diễn ra"
    };

    const HIDDEN_PROPERTIES = new Set([
        "id",
        "module",
        "rag_text",
        "embedding",
        "embeddings",
        "vector",
        "raw_data",
        "created_at",
        "updated_at",
        "createdAt",
        "updatedAt",
        "person_id",
        "event_id",
        "location_id",
        "source_id",
        "element_id",
        "node_id"
    ]);

    const WIDE_PROPERTIES = new Set([
        "description",
        "summary",
        "bio",
        "biography",
        "content",
        "context",
        "result",
        "significance",
        "historicalSignificance",
        "achievements",
        "consequences",
        "notes",
        "note"
    ]);

    const RELATION_LABELS = {
        DIEN_RA_TAI: "Diễn ra tại",
        THAM_GIA_SU_KIEN: "Tham gia sự kiện",
        CHI_HUY_SU_KIEN: "Chỉ huy sự kiện",
        TRICH_DAN_TU_NGUON: "Trích dẫn từ nguồn",
        THUOC_VE_PHE_PHAI: "Thuộc về phe phái",
        ANH_EM_CUA: "Anh em của",
        CHA_ME_CUA: "Cha mẹ của",
        VO_CHONG_CUA: "Vợ chồng với",
        HA_SAT_XU_TU: "Hạ sát, xử tử",
        PHUNG_SU_TRIEU_INH: "Phụng sự triều đình",
        LIEN_MINH_VOI: "Liên minh với",
        THAY_HOC_CUA: "Thầy học của",
        BAN_HANH: "Ban hành",
        SOAN_THAO: "Soạn thảo",
        CHU_TRI_THUC_HIEN: "Chủ trì thực hiện",
        CHI_HUY_DON_VI: "Chỉ huy đơn vị",
        CHI_HUY_ON_VI: "Chỉ huy đơn vị",
        SANG_TAO_CHIEN_THUAT: "Sáng tạo chiến thuật",
        AP_DUNG_TRONG: "Áp dụng trong",
        BAN_HANH_TRONG_SU_KIEN: "Ban hành trong sự kiện",
        SU_DUNG_TRONG_SU_KIEN: "Sử dụng trong sự kiện",
        SU_DUNG_TRONG: "Sử dụng trong",
        TIEN_DE_CUA: "Là tiền đề của",
        TIEN_E_CUA: "Là tiền đề của",
        DAN_DEN: "Dẫn đến",
        CHU_TRI_SU_KIEN: "Chủ trì sự kiện",
        ANH_BAI: "Chịu ảnh hưởng bởi",
        CUU_MANG: "Cưu mang",
        CUU_MANG_CUU_MANG: "Cưu mang",
        TUYEN_DOC_TAI_SU_KIEN: "Tuyển mộ tại sự kiện",
        TUYEN_OC_TAI_SU_KIEN: "Tuyển mộ tại sự kiện",
        TAC_DONG_DEN: "Tác động đến",
        TAC_ONG_EN: "Tác động đến",
        TAC_DONG_QUYEN_LUC: "Tác động đến quyền lực",
        TAC_ONG_QUYEN_LUC: "Tác động đến quyền lực",
        DONG_CO_KHOI_NGHIA: "Khởi nghĩa",
        ONG_CO_KHOI_NGHIA: "Khởi nghĩa"
    };

    const COLORS = {
        Person: { background: "#e7c49b", border: "#a87948" },
        Event: { background: "#c8d5b7", border: "#788b68" },
        Location: { background: "#c3d7e0", border: "#708b9c" },
        Faction: { background: "#e0c5ce", border: "#a8798c" },
        Policy: { background: "#ead5ae", border: "#b58b50" },
        Document: { background: "#d9d5cb", border: "#999080" },
        Unit: { background: "#d4c8e2", border: "#8974a5" },
        Tactics: { background: "#d4d1ae", border: "#92905f" },
        Source: { background: "#d5d5d5", border: "#858585" }
    };

    const state = {
        network: null,
        nodes: null,
        edges: null,

        nodeMap: new Map(),
        edgeMap: new Map(),

        selectedId: null,
        rootId: null,
        expandedIds: new Set(),
        expansionHistory: new Map(),

        loading: false,
        expanding: false,
        searchRequest: 0,
        searchDebounce: null,
        overlayFrame: null,
        zoomClamping: false
    };

    // ================================================
    // HELPERS
    // ================================================

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[char]);
    }

    function normalizeId(id) {
        return String(id ?? "");
    }

    function getNodeType(node) {
        const labels = node?.labels;

        const raw = Array.isArray(labels)
            ? (labels.find(label => LABELS[label]) || labels[0])
            : labels;
        return TYPE_ALIASES[raw] || raw || "Unknown";
    }

    function getNodeName(node) {
        const p = node?.properties || {};

        return (
            p.name ||
            p.event_name ||
            p.location_name ||
            p.source_name ||
            p.fullName ||
            p.full_name ||
            p.title ||
            p.entity ||
            p.ten ||
            node?.name ||
            "Chưa có tên"
        );
    }

    function getNodeColor(type) {
        return COLORS[type] || {
            background: "#ded2bd",
            border: "#9a8263"
        };
    }

    function getRelationshipName(edge) {
        const type = String(edge?.type || "QUAN_HE").toUpperCase();

        return (
            RELATION_LABELS[type] ||
            edge?.display_type ||
            type.replace(/_/g, " ").toLowerCase()
        );
    }

    function getPropertyLabel(key) {
        if (PROPERTY_LABELS[key]) {
            return PROPERTY_LABELS[key];
        }

        const readable = String(key)
            .replace(/([a-z])([A-Z])/g, "$1 $2")
            .replace(/[_-]/g, " ")
            .trim();

        return readable
            ? readable.charAt(0).toUpperCase() + readable.slice(1)
            : "Thông tin khác";
    }

    function formatValue(value) {
        if (value === null || value === undefined || value === "") {
            return "";
        }

        if (Array.isArray(value)) {
            return value.map(item => {
                if (item === null || item === undefined) return "";
                if (typeof item === "object") {
                    return Object.values(item).join(" – ");
                }
                return String(item);
            }).filter(Boolean).join(", ");
        }

        if (typeof value === "object") {
            return Object.entries(value)
                .map(([key, item]) => `${getPropertyLabel(key)}: ${formatValue(item)}`)
                .join("\n");
        }

        return String(value);
    }

    function setLoading(value) {
        el.loading.hidden = !value;
    }

    function showError(message) {
        el.errorMessage.textContent = message;
        el.error.hidden = false;
        el.empty.hidden = true;
    }

    function hideError() {
        el.error.hidden = true;
    }

    function updateStatus(message) {
        el.status.textContent = message;
    }

    function getEnabledRelationGroups() {
        if (!el.filter) return new Set();
        return new Set(Array.from(el.filter.querySelectorAll('input[data-relation-type]:checked'))
            .map(input => input.dataset.relationType));
    }

    function getEnabledRelationTypes() {
        return getEnabledRelationGroups();
    }

    function normalizeRelationType(value) {
        return String(value || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toUpperCase()
            .replace(/[\s-]+/g, "_");
    }

    function getRelationGroup(edge) {
        const type = normalizeRelationType(edge?.type || edge?.display_type);

        if (/CHA_ME|CHA_CUA|ME_CUA|ANH_EM|VO_CHONG|VO_CUA|CHONG_CUA|CON_CUA|HUYET_THONG|GIA_DINH/.test(type)) return "family";
        if (/DONG_MINH|LIEN_MINH|BAN_BE|THAN_CAN|UNG_HO|HO_TRO|CUU_MANG|CUU_GIUP|CUNG_CHI_HUONG|THAM_GIA|CHU_TRI|THAM_DU|THAM_CHIEN/.test(type)) return "allies";
        if (/CHI_HUY|CHU_TUONG|CAP_TREN|CAP_DUOI|LANH_DAO|PHUC_VU|THUOC_QUYEN|THUOC_DUOI|TUONG_LINH/.test(type)) return "hierarchy";
        if (/THAY_HOC|THAY_DAY|DAY_DO|TRUYEN_DAY|HOC_TRO|MON_DE|KE_THUA/.test(type)) return "teachers";
        if (/DOI_THU|DOI_DAU|CHONG_DOI|KE_THU|PHAN_BOI|DANH_BAI|TIEU_DIET|HA_SAT|XU_TU|TRANH_GIANH/.test(type)) return "opponents";

        return "other";
    }

    function isEdgeAllowed(edge) {
        const enabled = getEnabledRelationTypes();
        return enabled.has(normalizeRelationType(edge?.type || edge?.display_type));
    }

    function renderRelationFilters(nodeId) {
        if (!el.filter) return;
        const types = new Map();
        state.edgeMap.forEach(edge => {
            if (normalizeId(edge.source) !== nodeId && normalizeId(edge.target) !== nodeId) return;
            const raw = String(edge.type || edge.display_type || "QUAN_HE_KHAC");
            const key = normalizeRelationType(raw);
            if (!types.has(key)) types.set(key, { raw, label: getRelationshipName(edge), group: getRelationGroup(edge) });
        });
        const ordered = [...types.entries()].sort((a, b) => {
            const pa = RELATION_PRIORITY.indexOf(a[1].group);
            const pb = RELATION_PRIORITY.indexOf(b[1].group);
            return (pa < 0 ? 99 : pa) - (pb < 0 ? 99 : pb) || a[1].label.localeCompare(b[1].label, "vi");
        });
        const primary = ordered.filter(([, item]) => item.group !== "other");
        const extended = ordered.filter(([, item]) => item.group === "other");
        const checkbox = ([key, item], checked) => `
            <label class="kg-relation-filter-item">
                <input type="checkbox" data-relation-type="${escapeHTML(key)}" ${checked ? "checked" : ""}>
                <span>${escapeHTML(item.label)}</span>
            </label>`;
        el.filter.innerHTML = primary.length
            ? primary.map(item => checkbox(item, true)).join("")
            : '<p class="kg-filter-empty">Nhân vật/nút này chưa có quan hệ thuộc nhóm chính.</p>';
        if (extended.length) {
            el.filter.innerHTML += `
                <details class="kg-filter-extended">
                    <summary>Quan hệ mở rộng (${extended.length})</summary>
                    ${extended.map(item => checkbox(item, false)).join("")}
                </details>`;
        }
    }

    function isNodeAllowed(node) {
        const nodeId = normalizeId(node.id);
        if (nodeId === state.rootId || nodeId === state.selectedId) return true;

        return Array.from(state.edgeMap.values()).some(edge => {
            if (!isEdgeAllowed(edge)) return false;
            const source = normalizeId(edge.source);
            const target = normalizeId(edge.target);
            return (source === nodeId || target === nodeId) &&
                state.nodeMap.has(source) && state.nodeMap.has(target);
        });
    }

    function wrapNodeLabel(name, maxLength = 19) {
        const words = String(name || "").trim().split(/\s+/);
        const lines = [];
        let current = "";

        words.forEach(word => {
            const candidate = current ? `${current} ${word}` : word;
            if (candidate.length > maxLength && current) {
                lines.push(current);
                current = word;
            } else {
                current = candidate;
            }
        });
        if (current) lines.push(current);
        if (lines.length > 2) {
            lines.length = 2;
            lines[1] = lines[1].slice(0, Math.max(1, maxLength - 3)) + "...";
        }
        return lines.join("\n");
    }

    function getNeighborIds(nodeId) {
        const neighbors = new Set();
        if (!nodeId) return neighbors;
        state.edgeMap.forEach(edge => {
            const source = normalizeId(edge.source);
            const target = normalizeId(edge.target);
            if (source === nodeId) neighbors.add(target);
            if (target === nodeId) neighbors.add(source);
        });
        return neighbors;
    }

    function getNodeIconData(type) {
        const paths = {
            Person: '<circle cx="32" cy="23" r="11"/><path d="M12 57c2-12 9-18 20-18s18 6 20 18"/>',
            Event: '<rect x="12" y="15" width="40" height="38" rx="5"/><path d="M21 9v12M43 9v12M12 27h40M22 37h7M35 37h7M22 45h7"/>',
            Location: '<path d="M32 58s19-20 19-34a19 19 0 1 0-38 0c0 14 19 34 19 34Z"/><circle cx="32" cy="24" r="6"/>',
            Faction: '<path d="M15 58V9M17 12h34L42 25l9 13H17"/>',
            Policy: '<path d="M15 10h34v48H15zM22 22h20M22 32h20M22 42h14"/>',
            Document: '<path d="M18 8h23l11 11v37H18zM41 8v12h11M25 31h19M25 40h19M25 49h13"/>',
            Unit: '<path d="M32 8 53 19v17c0 13-9 21-21 26C20 57 11 49 11 36V19zM22 33l7 7 14-15"/>',
            Tactics: '<path d="M12 50 27 35l9 8 17-22M42 21h11v11"/>',
            Source: '<path d="M13 14h39v42H13zM21 24h23M21 33h23M21 42h17"/>',
            Unknown: '<circle cx="32" cy="32" r="22"/><path d="M25 25a7 7 0 1 1 12 5c-4 3-5 4-5 9M32 47h.1"/>'
        };
        const body = paths[type] || paths.Unknown;
        const palette = getNodeColor(type);
        const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 72 72"><circle cx="36" cy="36" r="27" fill="${palette.background}" stroke="#ffffff" stroke-width="2.2"/><g transform="translate(4 4)" fill="none" stroke="#ffffff" stroke-width="2.35" stroke-linecap="round" stroke-linejoin="round">${body}</g></svg>`;
        return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
    }

    // ================================================
    // NODE / EDGE CONVERSION
    // ================================================

    function convertNode(node) {
        const type = getNodeType(node);
        const color = getNodeColor(type);
        const name = getNodeName(node);
        const id = normalizeId(node.id);
        const selected = state.selectedId === id;
        const neighbors = getNeighborIds(state.selectedId);
        const related = neighbors.has(id);
        const emphasized = !state.selectedId || selected || related;
        const expanded = state.expandedIds.has(id);
        const nodeLabel = wrapNodeLabel(name, selected ? 24 : 19);

        return {
            id,
            label: emphasized ? nodeLabel : "",
            title: escapeHTML(name),
            group: type,
            shape: "image",
            image: getNodeIconData(type),
            size: selected ? 30 : related ? 23 : 19,
            color: {
                background: emphasized ? color.background : "#e9e4db",
                border: selected ? "#805a2b" : emphasized ? color.border : "#d5cdbf",
                highlight: { background: color.background, border: "#805a2b" },
                hover: { background: color.background, border: "#805a2b" }
            },
            borderWidth: selected ? 4 : related ? 2.5 : 1.5,
            font: {
                face: "Be Vietnam Pro",
                size: selected ? 14 : 11,
                color: emphasized ? "#35291f" : "#aaa194",
                strokeWidth: 4,
                strokeColor: "#fffdf8"
            },
            hidden: !isNodeAllowed(node)
        };
    }

    function convertEdge(edge) {
        const relationship = getRelationshipName(edge);
        const source = normalizeId(edge.source);
        const target = normalizeId(edge.target);
        const focused = !state.selectedId || source === state.selectedId || target === state.selectedId;
        const shortLabel = relationship.length > 22
            ? relationship.slice(0, 19) + "..."
            : relationship;

        return {
            id: normalizeId(edge.id),
            from: source,
            to: target,
            label: state.selectedId && focused ? shortLabel : "",
            title: escapeHTML(relationship),
            font: {
                face: "Be Vietnam Pro",
                size: 10,
                color: "#80613e",
                background: "#fffdf8",
                strokeWidth: 0,
                align: "middle"
            },
            arrows: { to: { enabled: true, scaleFactor: 0.45 } },
            color: {
                color: focused ? "#b49a75" : "#e6e0d6",
                highlight: "#a87948",
                hover: "#a87948"
            },
            width: focused ? 1.8 : 1,
            smooth: { enabled: true, type: "continuous", roundness: 0.25 },
            hidden: !focused
        };
    }

    function refreshGraphAppearance() {
        if (!state.nodes || !state.edges) return;
        state.nodes.update(Array.from(state.nodeMap.values()).map(convertNode));
        state.edges.update(Array.from(state.edgeMap.values()).map(convertEdge));
        applyFilter();
        updateGraphLegend();
    }

    function updateGraphLegend() {
        const container = $("graph-legend-items");
        if (!container) return;

        const typeOrder = ["Person", "Event", "Location", "Faction", "Policy", "Document", "Unit", "Tactics", "Source", "Unknown"];
        const presentTypes = new Set();
        state.nodeMap.forEach(node => {
            if (isNodeAllowed(node)) presentTypes.add(getNodeType(node));
        });

        const items = typeOrder.filter(type => presentTypes.has(type));
        if (!items.length) {
            container.innerHTML = '<span class="legend-empty">Chưa có nút nào được hiển thị.</span>';
            return;
        }

        container.innerHTML = items.map(type => {
            const palette = getNodeColor(type);
            const label = LABELS[type] || "Thực thể";
            return `<span class="canvas-legend-item"><i class="canvas-legend-dot" style="background:${palette.background}"></i>${escapeHTML(label)}</span>`;
        }).join("");
    }

    // ================================================
    // COUNTERS
    // ================================================

    function updateCounters() {
        let visibleNodes = 0;
        let visibleEdges = 0;

        state.nodeMap.forEach(node => {
            if (isNodeAllowed(node)) visibleNodes++;
        });

        state.edgeMap.forEach(edge => {
            const source = state.nodeMap.get(normalizeId(edge.source));
            const target = state.nodeMap.get(normalizeId(edge.target));

            if (source && target && isEdgeAllowed(edge) &&
                (normalizeId(edge.source) === state.selectedId ||
                 normalizeId(edge.target) === state.selectedId ||
                 normalizeId(edge.source) === state.rootId ||
                 normalizeId(edge.target) === state.rootId)) visibleEdges++;
        });

        el.totalNodes.textContent = state.nodeMap.size;
        el.totalEdges.textContent = state.edgeMap.size;

        el.visibleNodes.textContent = visibleNodes;
        el.visibleEdges.textContent = visibleEdges;
    }

    // ================================================
    // DATA MANAGEMENT
    // ================================================

    function mergeData(data) {
        const incomingNodes = Array.isArray(data.nodes) ? data.nodes : [];
        const incomingEdges = Array.isArray(data.edges) ? data.edges : [];

        incomingNodes.forEach(node => {
            if (!node || node.id === undefined || node.id === null) return;

            const normalized = {
                ...node,
                id: normalizeId(node.id)
            };

            state.nodeMap.set(normalized.id, normalized);
            state.nodes.update(convertNode(normalized));
        });

        incomingEdges.forEach(edge => {
            if (
                !edge ||
                edge.id === undefined ||
                edge.source === undefined ||
                edge.target === undefined
            ) {
                return;
            }

            const normalized = {
                ...edge,
                id: normalizeId(edge.id),
                source: normalizeId(edge.source),
                target: normalizeId(edge.target)
            };

            if (
                !state.nodeMap.has(normalized.source) ||
                !state.nodeMap.has(normalized.target)
            ) {
                return;
            }

            state.edgeMap.set(normalized.id, normalized);
            state.edges.update(convertEdge(normalized));
        });

        applyFilter();
        updateCounters();
        updateGraphLegend();
    }

    function updateZoomLevel() {
        if (!state.network || !el.zoomLevel) return;
        el.zoomLevel.textContent = `${Math.round(state.network.getScale() * 100)}%`;
    }

    function changeZoom(factor) {
        if (!state.network) return;
        const current = state.network.getScale();
        const next = Math.max(0.38, Math.min(1.25, current * factor));
        state.network.moveTo({ scale: next, animation: { duration: 180, easingFunction: "easeInOutQuad" } });
        updateZoomLevel();
    }

    function renderNodeControls() {
        if (!el.nodeControls || !state.network) return;
        const visible = [];
        state.nodeMap.forEach((node, id) => {
            if (!isNodeAllowed(node)) return;
            const isExpanded = state.expandedIds.has(id);
            const pos = state.network.getPositions([id])[id];
            if (!pos) return;
            const dom = state.network.canvasToDOM(pos);
            visible.push({ id, x: dom.x, y: dom.y, expanded: isExpanded });
        });
        el.nodeControls.innerHTML = visible.map(item => `
            <button type="button" class="kg-node-toggle ${item.expanded ? 'is-expanded' : ''}"
                data-node-id="${escapeHTML(item.id)}"
                style="left:${item.x + 15}px;top:${item.y - 25}px"
                title="${item.expanded ? 'Thu gọn nhánh' : 'Mở rộng quan hệ'}"
                aria-label="${item.expanded ? 'Thu gọn' : 'Mở rộng'} quan hệ">
                ${item.expanded ? '−' : '+'}
            </button>`).join('');
        el.nodeControls.querySelectorAll('.kg-node-toggle').forEach(button => {
            button.addEventListener('click', async event => {
                event.preventDefault(); event.stopPropagation();
                const id = normalizeId(button.dataset.nodeId);
                button.disabled = true;
                try {
                    if (state.expandedIds.has(id)) collapseNode(id);
                    else await expandNode(id);
                } catch (error) {
                    console.error('Node toggle error:', error);
                    showError('Không thể cập nhật nhánh quan hệ: ' + error.message);
                } finally {
                    renderNodeControls();
                }
            });
        });
    }

    function scheduleNodeControls() {
        if (state.overlayFrame) cancelAnimationFrame(state.overlayFrame);
        state.overlayFrame = requestAnimationFrame(renderNodeControls);
    }

    // ================================================
    // NETWORK
    // ================================================

    function initializeNetwork() {
        if (typeof vis === "undefined") {
            throw new Error("Không tải được thư viện vis-network.");
        }

        state.nodes = new vis.DataSet();
        state.edges = new vis.DataSet();

        state.network = new vis.Network(
            el.network,
            {
                nodes: state.nodes,
                edges: state.edges
            },
            {
                autoResize: true,

                interaction: {
                    hover: true,
                    tooltipDelay: 150,
                    hideEdgesOnDrag: true,
                    navigationButtons: false,
                    keyboard: { enabled: true }
                },

                physics: {
                    enabled: true,
                    solver: "forceAtlas2Based",

                    forceAtlas2Based: {
                        gravitationalConstant: -125,
                        centralGravity: 0.008,
                        springLength: 190,
                        springConstant: 0.035,
                        damping: 0.72,
                        avoidOverlap: 1.05
                    },

                    stabilization: {
                        enabled: true,
                        iterations: 160,
                        updateInterval: 25
                    }
                },

                nodes: {
                    chosen: true
                },

                edges: {
                    selectionWidth: 2,
                    hoverWidth: 2
                }
            }
        );

        state.network.on("click", params => {
            if (params.nodes.length) {
                focusNode(params.nodes[0]);
            }
        });

        // Mở rộng/thu gọn được thực hiện bằng nút +/- nổi trên từng nút.
        // Nhấp đúp không còn là thao tác bắt buộc để tránh thao tác khó phát hiện.
        state.network.on("afterDrawing", scheduleNodeControls);
        state.network.on("zoom", () => {
            if (!state.zoomClamping) {
                const scale = state.network.getScale();
                const bounded = Math.max(0.38, Math.min(1.25, scale));
                if (bounded !== scale) {
                    state.zoomClamping = true;
                    state.network.moveTo({ scale: bounded });
                    state.zoomClamping = false;
                }
            }
            scheduleNodeControls();
            updateZoomLevel();
        });
        state.network.on("dragEnd", scheduleNodeControls);
        state.network.on("selectNode", scheduleNodeControls);
        state.network.on("deselectNode", scheduleNodeControls);

        state.network.once("stabilizationIterationsDone", () => {
            state.network.setOptions({
                physics: { enabled: false }
            });
        });
    }

    // ================================================
    // FILTER
    // ================================================

    function applyFilter() {
        if (!state.nodes || !state.edges) return;

        state.nodeMap.forEach(node => {
            state.nodes.update({
                id: normalizeId(node.id),
                hidden: !isNodeAllowed(node)
            });
        });

        state.edgeMap.forEach(edge => {
            const source = state.nodeMap.get(normalizeId(edge.source));
            const target = state.nodeMap.get(normalizeId(edge.target));

            const visible =
                source && target && isEdgeAllowed(edge) &&
                (normalizeId(edge.source) === state.selectedId ||
                 normalizeId(edge.target) === state.selectedId ||
                 normalizeId(edge.source) === state.rootId ||
                 normalizeId(edge.target) === state.rootId);

            state.edges.update({
                id: normalizeId(edge.id),
                hidden: !visible
            });
        });

        if (state.selectedId) {
            const selected = state.nodeMap.get(state.selectedId);

            if (selected && !isNodeAllowed(selected)) {
                clearDetails();
            }
        }

        updateCounters();

        const hasVisibleNodes = Array.from(state.nodeMap.values()).some(isNodeAllowed);
        el.empty.hidden = hasVisibleNodes;
        updateGraphLegend();
    }

    // ================================================
    // DETAIL PANEL
    // ================================================

    function clearDetails() {
        state.selectedId = null;
        el.placeholder.hidden = false;
        el.content.hidden = true;
        if (el.clearFocus) el.clearFocus.hidden = true;
        refreshGraphAppearance();
    }

    function getRelations(nodeId) {
        const relations = [];

        state.edgeMap.forEach(edge => {
            const source = normalizeId(edge.source);
            const target = normalizeId(edge.target);

            if (source !== nodeId && target !== nodeId) return;
            if (!isEdgeAllowed(edge)) return;

            const isSource = source === nodeId;
            const relatedId = isSource ? target : source;
            const relatedNode = state.nodeMap.get(relatedId);

            if (!relatedNode) return;

            relations.push({
                edge,
                relatedId,
                relatedNode,
                direction: isSource ? "out" : "in"
            });
        });

        relations.sort((a, b) => {
            const pa = RELATION_PRIORITY.indexOf(getRelationGroup(a.edge));
            const pb = RELATION_PRIORITY.indexOf(getRelationGroup(b.edge));
            return pa - pb || getNodeName(a.relatedNode).localeCompare(getNodeName(b.relatedNode), "vi");
        });
        return relations;
    }

    function updateExpandButton(nodeId) {
        if (!el.expand) return;
        const expanded = state.expandedIds.has(normalizeId(nodeId));
        el.expand.disabled = false;
        el.expand.innerHTML = expanded
            ? '<i class="bi bi-dash-circle"></i> Thu gọn nhánh này'
            : '<i class="bi bi-plus-circle"></i> Mở rộng các mối quan hệ';
        el.expand.dataset.action = expanded ? "collapse" : "expand";
    }

    function showDetails(nodeId) {
        nodeId = normalizeId(nodeId);

        const node = state.nodeMap.get(nodeId);
        if (!node) return;

        state.selectedId = nodeId;

        el.placeholder.hidden = true;
        el.content.hidden = false;

        const type = getNodeType(node);

        el.type.textContent = LABELS[type] || "Thực thể";
        el.name.textContent = getNodeName(node);

        el.businessId.textContent = node.business_id
            ? `Mã thực thể: ${node.business_id}`
            : "";

        renderProperties(node.properties || {});
        renderRelationFilters(nodeId);
        renderRelations(nodeId);

        refreshGraphAppearance();
        if (el.clearFocus) el.clearFocus.hidden = false;
        updateExpandButton(nodeId);
    }

    function renderProperties(properties) {
        const entries = Object.entries(properties || {})
            .filter(([key, value]) => {
                return (
                    !HIDDEN_PROPERTIES.has(key) &&
                    value !== null &&
                    value !== undefined &&
                    value !== ""
                );
            })
            .map(([key, value]) => ({
                key,
                label: getPropertyLabel(key),
                value: formatValue(value)
            }))
            .filter(item => item.value !== "")
            .slice(0, 20);

        if (!entries.length) {
            el.properties.innerHTML = `
                <p class="detail-empty">
                    Chưa có thông tin chi tiết cho thực thể này.
                </p>
            `;
            return;
        }

        el.properties.innerHTML = entries.map(item => {
            const isWide =
                WIDE_PROPERTIES.has(item.key) ||
                item.value.length > 150;

            const value = item.value.length > CONFIG.MAX_PROPERTY_LENGTH
                ? `${item.value.slice(0, CONFIG.MAX_PROPERTY_LENGTH)}…`
                : item.value;

            return `
                <article class="property-item ${isWide ? "property-item-wide" : ""}">
                    <span class="property-label">
                        ${escapeHTML(item.label)}
                    </span>

                    <span class="property-value">
                        ${escapeHTML(value)}
                    </span>
                </article>
            `;
        }).join("");
    }

    function renderRelations(nodeId) {
        const relations = getRelations(nodeId);

        el.relationCount.textContent = relations.length;

        if (!relations.length) {
            el.relations.innerHTML = `
                <p class="detail-empty">
                    Chưa có kết nối được tải. Hãy chọn “Khám phá các kết nối”
                    để tìm hiểu thêm về thực thể này.
                </p>
            `;
            return;
        }

        el.relations.innerHTML = relations.map(relation => {
            const name = getNodeName(relation.relatedNode);
            const type = getRelationshipName(relation.edge);

            const direction = relation.direction === "out"
                ? "Thực thể này →"
                : "← Thực thể này";

            return `
                <button
                    type="button"
                    class="relation-item"
                    data-related-id="${escapeHTML(relation.relatedId)}">

                    <span class="relation-direction">
                        ${escapeHTML(direction)}
                    </span>

                    <span class="relation-name">
                        ${escapeHTML(type)}
                    </span>

                    <span class="relation-target">
                        ${escapeHTML(name)}
                    </span>

                    <i class="bi bi-arrow-up-right"></i>
                </button>
            `;
        }).join("");

        el.relations.querySelectorAll(".relation-item").forEach(button => {
            button.addEventListener("click", () => {
                focusNode(button.dataset.relatedId);
            });
        });
    }

    // ================================================
    // FOCUS
    // ================================================

    function focusNode(nodeId) {
        nodeId = normalizeId(nodeId);

        const node = state.nodeMap.get(nodeId);
        if (!node || !state.network) return;

        state.rootId = nodeId;
        showDetails(nodeId);
        state.network.selectNodes([nodeId]);

        state.network.focus(nodeId, {
            scale: 1.15,
            animation: {
                duration: 500,
                easingFunction: "easeInOutQuad"
            }
        });
    }

    // ================================================
    // INITIAL GRAPH
    // ================================================

    function selectInitialNodes(nodes, edges) {
        const filter = getFilter();
        const candidates = nodes.filter(node => {
            const labels = Array.isArray(node.labels) ? node.labels : [node.labels];
            return filter === "all" || labels.includes(filter);
        });
        const degree = new Map(candidates.map(node => [normalizeId(node.id), 0]));
        edges.forEach(edge => {
            const source = normalizeId(edge.source);
            const target = normalizeId(edge.target);
            if (degree.has(source)) degree.set(source, degree.get(source) + 1);
            if (degree.has(target)) degree.set(target, degree.get(target) + 1);
        });
        const priority = ["Person", "Event", "Location", "Faction", "Policy", "Document", "Unit", "Tactics", "Source"];
        const groups = new Map(priority.map(type => [
            type,
            candidates.filter(node => getNodeType(node) === type)
                .sort((a, b) => (degree.get(normalizeId(b.id)) || 0) - (degree.get(normalizeId(a.id)) || 0))
        ]));
        const selected = [];
        while (selected.length < CONFIG.INITIAL_NODE_COUNT) {
            let added = false;
            priority.forEach(type => {
                const group = groups.get(type);
                if (group.length && selected.length < CONFIG.INITIAL_NODE_COUNT) {
                    selected.push(group.shift());
                    added = true;
                }
            });
            if (!added) break;
        }
        return selected;
    }

    function buildInitialGraph(nodes, edges) {
        const selectedNodes = selectInitialNodes(nodes, edges);

        const selectedIds = new Set(
            selectedNodes.map(node => normalizeId(node.id))
        );

        const selectedEdges = edges.filter(edge =>
            selectedIds.has(normalizeId(edge.source)) &&
            selectedIds.has(normalizeId(edge.target))
        );

        mergeData({
            nodes: selectedNodes,
            edges: selectedEdges
        });

        if (!selectedNodes.length) {
            el.empty.hidden = false;
            updateStatus("Chưa có dữ liệu");
            return;
        }

        el.empty.hidden = true;

        state.network.fit({
            animation: {
                duration: 600,
                easingFunction: "easeInOutQuad"
            }
        });

        updateStatus("Sẵn sàng khám phá");
    }

    async function loadGraph() {
        if (state.loading) return;

        state.loading = true;

        setLoading(true);
        hideError();
        el.empty.hidden = true;

        updateStatus("Đang tải dữ liệu");

        try {
            if (!API) {
                throw new Error("Không tìm thấy ApiClient.");
            }

            const params = new URLSearchParams(window.location.search);
            const requestedName = params.get("personName") || params.get("character") ||
                params.get("person") || params.get("name") || "Nguyễn Huệ";
            const requestedNodeId = params.get("nodeId") || params.get("personId") ||
                params.get("characterId");

            let response;
            if (requestedNodeId) {
                const detail = await API.get(
                    `/api/graph/node/${encodeURIComponent(requestedNodeId)}`,
                    { limit: CONFIG.EXPANSION_LIMIT }
                );
                const center = detail?.center ||
                    (Array.isArray(detail?.nodes)
                        ? detail.nodes.find(item => normalizeId(item.id) === normalizeId(requestedNodeId))
                        : null);
                if (!center) throw new Error("Không tìm thấy nhân vật theo mã định danh trên trang.");
                response = { results: [{
                    ...center,
                    node_id: center.id,
                    name: center.name || center.properties?.name
                }] };
            } else {
                response = await API.get("/api/graph/search", {
                    keyword: requestedName,
                    limit: CONFIG.SEARCH_LIMIT,
                    entity_type: "Person"
                });
            }
            const results = Array.isArray(response?.results) ? response.results : [];
            const normalizedQuery = requestedName.toLocaleLowerCase("vi");
            const root = results.find(item => {
                const labels = Array.isArray(item.labels) ? item.labels : [item.labels];
                const name = String(item.name || item.properties?.name || item.properties?.full_name || "").toLocaleLowerCase("vi");
                return labels.includes("Person") && name === normalizedQuery;
            }) || results.find(item => {
                const labels = Array.isArray(item.labels) ? item.labels : [item.labels];
                return labels.includes("Person");
            });

            if (!root) throw new Error(`Không tìm thấy nhân vật "${requestedName}" trong dữ liệu.`);

            if (!state.network) initializeNetwork();
            state.nodeMap.clear(); state.edgeMap.clear();
            state.nodes.clear(); state.edges.clear();
            state.expandedIds.clear();
            state.expansionHistory.clear();
            state.selectedId = null;
            state.rootId = normalizeId(root.node_id || root.id);
            clearDetails();

            const rootNode = {
                id: normalizeId(root.node_id || root.id),
                business_id: root.business_id,
                labels: root.labels || ["Person"],
                display_labels: root.display_labels || [],
                properties: root.properties || { name: root.name }
            };
            mergeData({ nodes: [rootNode], edges: [] });
            focusNode(rootNode.id);
            await expandNode(rootNode.id);
            updateStatus(`Đang khám phá từ ${getNodeName(rootNode)}`);
            updateCounters();

        } catch (error) {
            console.error("Load graph error:", error);

            updateStatus("Không thể tải dữ liệu");
            showError(error.message || "Không thể tải đồ thị.");

        } finally {
            state.loading = false;
            setLoading(false);
        }
    }

    function reflowNetwork() {
        if (!state.network) return;
        state.network.setOptions({
            physics: {
                enabled: true,
                solver: "forceAtlas2Based",
                forceAtlas2Based: {
                    gravitationalConstant: -120,
                    centralGravity: 0.008,
                    springLength: 190,
                    springConstant: 0.035,
                    damping: 0.75,
                    avoidOverlap: 1
                },
                stabilization: { enabled: true, iterations: 180, updateInterval: 25 }
            }
        });
        state.network.once("stabilizationIterationsDone", () => {
            state.network.setOptions({ physics: { enabled: false } });
        });
        state.network.stabilize(180);
    }

    // ================================================
    // EXPANSION
    // ================================================

    async function expandNode(nodeId) {
        nodeId = normalizeId(nodeId);
        if (state.expanding) return;
        if (state.expandedIds.has(nodeId)) {
            showDetails(nodeId);
            return;
        }
        if (!API) throw new Error("Không tìm thấy ApiClient.");

        state.expanding = true;
        el.expand.disabled = true;
        el.expand.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Đang tải...';

        // Nút được mở rộng trở thành tâm khám phá hiện tại.
        state.rootId = nodeId;

        try {
            const response = await API.get(
                `/api/graph/node/${encodeURIComponent(nodeId)}`,
                { limit: CONFIG.EXPANSION_LIMIT }
            );
            if (!response || !Array.isArray(response.nodes) || !Array.isArray(response.edges)) {
                throw new Error("Dữ liệu kết nối không hợp lệ.");
            }

            const nodes = [...response.nodes];
            if (response.center?.id !== undefined &&
                !nodes.some(node => normalizeId(node.id) === normalizeId(response.center.id))) {
                nodes.push(response.center);
            }

            mergeData({ nodes, edges: response.edges });

            // Lưu toàn bộ nội dung API trả về, không chỉ phần mới thêm vào DataSet.
            // Nhờ vậy một nút/cạnh được nhiều nhánh cùng sử dụng sẽ không bị xóa nhầm.
            const ownedNodeIds = nodes.map(item => normalizeId(item.id)).filter(Boolean);
            const ownedEdgeIds = response.edges.map(item => normalizeId(item.id)).filter(Boolean);
            state.expansionHistory.set(nodeId, { nodeIds: ownedNodeIds, edgeIds: ownedEdgeIds });
            state.expandedIds.add(nodeId);

            refreshGraphAppearance();
            reflowNetwork();
            showDetails(nodeId);
            state.network.selectNodes([nodeId]);
            state.network.focus(nodeId, {
                scale: 1.05,
                animation: { duration: 450, easingFunction: "easeInOutQuad" }
            });
            updateStatus("Đã mở rộng các mối quan hệ");
            scheduleNodeControls();
        } finally {
            state.expanding = false;
            updateExpandButton(state.selectedId || nodeId);
        }
    }

    function collapseNode(nodeId) {
        nodeId = normalizeId(nodeId);
        const snapshot = state.expansionHistory.get(nodeId);
        state.expandedIds.delete(nodeId);
        state.expansionHistory.delete(nodeId);

        if (snapshot) {
            // Chỉ gỡ cạnh nếu không còn nhánh đang mở nào sở hữu cạnh đó.
            snapshot.edgeIds.forEach(edgeId => {
                const ownedElsewhere = [...state.expansionHistory.values()].some(item => item.edgeIds.includes(edgeId));
                if (!ownedElsewhere) {
                    state.edgeMap.delete(edgeId);
                    state.edges.remove(edgeId);
                }
            });

            // Giữ nút trung tâm/đang chọn và mọi nút còn được nhánh khác tham chiếu.
            snapshot.nodeIds.forEach(ownedId => {
                if (ownedId === state.rootId || ownedId === state.selectedId) return;
                const ownedElsewhere = [...state.expansionHistory.values()].some(item => item.nodeIds.includes(ownedId));
                const stillConnected = [...state.edgeMap.values()].some(edge =>
                    normalizeId(edge.source) === ownedId || normalizeId(edge.target) === ownedId
                );
                if (!ownedElsewhere && !stillConnected) {
                    state.nodeMap.delete(ownedId);
                    state.nodes.remove(ownedId);
                }
            });
        }

        refreshGraphAppearance();
        updateCounters();
        if (state.selectedId === nodeId && state.nodeMap.has(nodeId)) showDetails(nodeId);
        updateStatus("Đã thu gọn các kết nối do nút này mở");
        scheduleNodeControls();
    }

    // ================================================
    // SEARCH
    // ================================================

    function renderSearchResults(results) {
        el.searchResults.hidden = false;

        if (!results.length) {
            el.searchResults.innerHTML = `
                <div class="search-no-result">
                    Không tìm thấy thực thể phù hợp.
                </div>
            `;
            return;
        }

        el.searchResults.innerHTML = results.map((item, index) => {
            const labels = Array.isArray(item.labels)
                ? item.labels
                : [item.labels];

            const rawType = labels.find(Boolean) || "Unknown";
            const type = TYPE_ALIASES[rawType] || rawType;
            const icon = ({ Person: "bi-person", Location: "bi-geo-alt", Event: "bi-calendar-event", Faction: "bi-flag", Source: "bi-journal-text" })[type] || "bi-diagram-3";
            return `
                <button type="button" class="search-result-item" data-index="${index}">
                    <span class="search-result-type-icon"><i class="bi ${icon}"></i></span>
                    <span class="search-result-name">${escapeHTML(getNodeName(item))}</span>
                    <i class="bi bi-arrow-up-right"></i>
                </button>`;
        }).join("");

        el.searchResults.querySelectorAll(".search-result-item").forEach(button => {
            button.addEventListener("click", () => {
                selectSearchResult(results[Number(button.dataset.index)]);
            });
        });
    }

    function matchesSearchType(item, selectedType) {
        if (!selectedType || selectedType === "all") return true;
        const labels = Array.isArray(item.labels) ? item.labels : [item.labels || item.entity_type || item.node_type];
        if (item.display_labels) labels.push(...(Array.isArray(item.display_labels) ? item.display_labels : [item.display_labels]));
        const aliases = {
            NhanVat: ["NhanVat", "Person"], Person: ["NhanVat", "Person"],
            SuKien: ["SuKien", "Event"], Event: ["SuKien", "Event"],
            DiaDiem: ["DiaDiem", "Location"], Location: ["DiaDiem", "Location"],
            TheLuc: ["TheLuc", "Faction"], Faction: ["TheLuc", "Faction"],
            NguonTaiLieu: ["NguonTaiLieu", "Source"], Source: ["NguonTaiLieu", "Source"]
        };
        return (aliases[selectedType] || [selectedType]).some(label => labels.includes(label));
    }

    async function searchEntities() {
        const keyword = el.searchInput.value.trim();
        if (!keyword) { el.searchInput.focus(); return; }
        if (!API) { showError("Không tìm thấy ApiClient."); return; }

        const requestId = ++state.searchRequest;
        const selectedType = el.searchType?.value || "";
        el.searchButton.disabled = true;
        el.searchButton.textContent = "Đang tìm...";
        try {
            // Ưu tiên lọc ở backend; nếu backend chưa hỗ trợ nhãn tiếng Việt thì fallback lọc phía client.
            let response = await API.get("/api/graph/search", {
                keyword, limit: CONFIG.SEARCH_LIMIT,
                ...(selectedType ? { entity_type: selectedType } : {})
            });
            let results = Array.isArray(response?.results) ? response.results : [];
            if (selectedType) {
                results = results.filter(item => matchesSearchType(item, selectedType));
                if (!results.length) {
                    const fallback = await API.get("/api/graph/search", { keyword, limit: CONFIG.SEARCH_LIMIT * 3 });
                    if (requestId !== state.searchRequest) return;
                    results = (fallback?.results || []).filter(item => matchesSearchType(item, selectedType));
                }
            }
            if (requestId !== state.searchRequest) return;
            renderSearchResults(results);
        } catch (error) {
            console.error("Search error:", error);
            el.searchResults.hidden = false;
            el.searchResults.innerHTML = `<div class="search-no-result">${escapeHTML(error.message || "Không thể tìm kiếm.")}</div>`;
        } finally {
            if (requestId === state.searchRequest) {
                el.searchButton.disabled = false;
                el.searchButton.textContent = "Tìm kiếm";
            }
        }
    }

    async function selectSearchResult(result) {
        if (!result) return;

        el.searchResults.hidden = true;

        const nodeId = normalizeId(result.node_id || result.id);

        if (!nodeId) {
            showError("Thực thể không có mã định danh hợp lệ.");
            return;
        }

        if (state.nodeMap.has(nodeId)) {
            focusNode(nodeId);

            if (!state.expandedIds.has(nodeId)) {
                await expandNode(nodeId);
            }

            return;
        }

        // Khi chọn một nhân vật mới từ ô tìm kiếm, dựng lại đồ thị quanh nhân vật đó.
        state.nodeMap.clear();
        state.edgeMap.clear();
        state.nodes.clear();
        state.edges.clear();
        state.expandedIds.clear();
        state.expansionHistory.clear();
        state.rootId = nodeId;
        state.selectedId = null;

        const node = {
            id: nodeId,
            business_id: result.business_id,
            labels: result.labels || [],
            display_labels: result.display_labels || [],
            properties: result.properties || {}
        };

        state.nodeMap.set(nodeId, node);
        state.nodes.update(convertNode(node));

        applyFilter();
        focusNode(nodeId);

        await expandNode(nodeId);
    }

    // ================================================
    // EVENTS
    // ================================================

    if (el.zoomIn) el.zoomIn.addEventListener("click", () => changeZoom(1.12));
    if (el.zoomOut) el.zoomOut.addEventListener("click", () => changeZoom(1 / 1.12));

    if (el.clearFocus) {
        el.clearFocus.addEventListener("click", () => {
            clearDetails();
            if (state.network) {
                state.network.unselectAll();
                state.network.fit({ animation: { duration: 450, easingFunction: "easeInOutQuad" } });
            }
            updateStatus("Đang xem toàn bộ mạng lưới");
        });
    }


    el.searchButton.addEventListener("click", searchEntities);

    el.searchInput.addEventListener("keydown", event => {
        if (event.key === "Enter") searchEntities();

        if (event.key === "Escape") {
            el.searchResults.hidden = true;
        }
    });

    el.searchInput.addEventListener("input", () => {
        const value = el.searchInput.value.trim();
        if (!value) {
            el.searchResults.hidden = true;
            return;
        }
        if (value.length >= 2) {
            clearTimeout(state.searchDebounce);
            state.searchDebounce = setTimeout(() => searchEntities(), 380);
        }
    });

    if (el.searchType) el.searchType.addEventListener("change", () => {
        if (el.searchInput.value.trim().length >= 2) searchEntities();
    });

    el.filter.addEventListener("change", () => {
        applyFilter();
        if (state.selectedId) renderRelations(state.selectedId);
        el.searchResults.hidden = true;
        scheduleNodeControls();
    });

    el.fit.addEventListener("click", () => {
        if (!state.network) return;

        state.network.fit({
            nodes: state.nodes.getIds(),
            minZoomLevel: 0.35,
            maxZoomLevel: 1.5,
            animation: { duration: 500, easingFunction: "easeInOutQuad" }
        });
        scheduleNodeControls();
    });

    el.reset.addEventListener("click", () => {
        el.filter.querySelectorAll('input[type="checkbox"]').forEach(input => input.checked = true);
        state.rootId = null;
        el.searchInput.value = "";
        el.searchResults.hidden = true;

        state.searchRequest++;
        loadGraph();
    });

    el.retry.addEventListener("click", loadGraph);

    el.expand.addEventListener("click", async () => {
        if (!state.selectedId) return;
        const nodeId = state.selectedId;
        try {
            if (state.expandedIds.has(nodeId)) collapseNode(nodeId);
            else await expandNode(nodeId);
        } catch (error) {
            console.error("Graph expansion error:", error);
            showError("Không thể cập nhật nhánh quan hệ: " + error.message);
            updateExpandButton(nodeId);
        }
    });

    document.addEventListener("click", event => {
        if (!event.target.closest(".graph-search")) {
            el.searchResults.hidden = true;
        }
    });

    // ================================================
    // START
    // ================================================

    loadGraph();
});