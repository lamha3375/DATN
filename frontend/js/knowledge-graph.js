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
        searchButton: $("graph-search-btn"),
        searchResults: $("search-results"),

        filter: $("entity-filter"),
        fit: $("fit-graph-btn"),
        reset: $("reset-graph-btn"),
        retry: $("graph-retry-btn"),

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
        INITIAL_NODE_COUNT: 18,
        EXPANSION_LIMIT: 30,
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
        Unknown: "Thực thể"
    };

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
        expandedIds: new Set(),

        loading: false,
        expanding: false,
        searchRequest: 0
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

        if (Array.isArray(labels)) {
            return labels.find(label => LABELS[label]) || labels[0] || "Unknown";
        }

        return labels || "Unknown";
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

    function getFilter() {
        return el.filter.value || "all";
    }

    function isNodeAllowed(node) {
        const filter = getFilter();
        const labels = Array.isArray(node.labels) ? node.labels : [node.labels];

        return filter === "all" || labels.includes(filter);
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

        return {
            id,
            label: name.length > 25 ? `${name.slice(0, 22)}...` : name,
            title: escapeHTML(name),
            group: type,
            shape: "dot",
            size: selected ? 25 : 18,

            color: {
                background: color.background,
                border: selected ? "#805a2b" : color.border,
                highlight: {
                    background: color.background,
                    border: "#805a2b"
                },
                hover: {
                    background: color.background,
                    border: "#805a2b"
                }
            },

            borderWidth: selected ? 4 : 2,

            font: {
                face: "Be Vietnam Pro",
                size: selected ? 14 : 12,
                color: "#35291f",
                strokeWidth: 4,
                strokeColor: "#fffdf8"
            },

            hidden: !isNodeAllowed(node)
        };
    }

    function convertEdge(edge) {
        const relationship = getRelationshipName(edge);

        return {
            id: normalizeId(edge.id),
            from: normalizeId(edge.source),
            to: normalizeId(edge.target),

            label: "",
            title: escapeHTML(relationship),

            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.55
                }
            },

            color: {
                color: "#cbbda8",
                highlight: "#a87948",
                hover: "#a87948"
            },

            width: 1.4,

            smooth: {
                enabled: true,
                type: "continuous",
                roundness: 0.22
            }
        };
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

            if (source && target && isNodeAllowed(source) && isNodeAllowed(target)) {
                visibleEdges++;
            }
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
                        gravitationalConstant: -85,
                        centralGravity: 0.012,
                        springLength: 155,
                        springConstant: 0.045,
                        damping: 0.58,
                        avoidOverlap: 0.9
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
                showDetails(params.nodes[0]);
            }
        });

        state.network.on("doubleClick", params => {
            if (params.nodes.length) {
                expandNode(params.nodes[0]).catch(console.error);
            }
        });

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
                source &&
                target &&
                isNodeAllowed(source) &&
                isNodeAllowed(target);

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
    }

    // ================================================
    // DETAIL PANEL
    // ================================================

    function clearDetails() {
        state.selectedId = null;

        el.placeholder.hidden = false;
        el.content.hidden = true;
    }

    function getRelations(nodeId) {
        const relations = [];

        state.edgeMap.forEach(edge => {
            const source = normalizeId(edge.source);
            const target = normalizeId(edge.target);

            if (source !== nodeId && target !== nodeId) return;

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

        return relations;
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
        renderRelations(nodeId);

        state.nodes.update(
            Array.from(state.nodeMap.values()).map(convertNode)
        );

        el.expand.disabled = false;
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

        if (!isNodeAllowed(node)) {
            el.filter.value = "all";
            applyFilter();
        }

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
            const labels = Array.isArray(node.labels)
                ? node.labels
                : [node.labels];

            return filter === "all" || labels.includes(filter);
        });

        const degree = new Map();

        candidates.forEach(node => degree.set(normalizeId(node.id), 0));

        edges.forEach(edge => {
            const source = normalizeId(edge.source);
            const target = normalizeId(edge.target);

            if (degree.has(source)) degree.set(source, degree.get(source) + 1);
            if (degree.has(target)) degree.set(target, degree.get(target) + 1);
        });

        const priority = [
            "Person",
            "Event",
            "Location",
            "Faction",
            "Policy",
            "Document",
            "Unit",
            "Tactics",
            "Source"
        ];

        candidates.sort((a, b) => {
            const degreeDifference =
                (degree.get(normalizeId(b.id)) || 0) -
                (degree.get(normalizeId(a.id)) || 0);

            if (degreeDifference !== 0) return degreeDifference;

            return priority.indexOf(getNodeType(a)) -
                priority.indexOf(getNodeType(b));
        });

        return candidates.slice(0, CONFIG.INITIAL_NODE_COUNT);
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

            const response = await API.get("/api/graph/", {
                limit: CONFIG.INITIAL_LIMIT
            });

            if (
                !response ||
                !Array.isArray(response.nodes) ||
                !Array.isArray(response.edges)
            ) {
                throw new Error("Dữ liệu đồ thị không hợp lệ.");
            }

            if (!state.network) {
                initializeNetwork();
            }

            state.nodeMap.clear();
            state.edgeMap.clear();
            state.nodes.clear();
            state.edges.clear();
            state.expandedIds.clear();
            state.selectedId = null;

            clearDetails();

            buildInitialGraph(response.nodes, response.edges);

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

        if (!API) {
            throw new Error("Không tìm thấy ApiClient.");
        }

        state.expanding = true;
        el.expand.disabled = true;

        el.expand.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Đang khám phá...
        `;

        try {
            const response = await API.get(
                `/api/graph/node/${encodeURIComponent(nodeId)}`,
                {
                    limit: CONFIG.EXPANSION_LIMIT
                }
            );

            if (
                !response ||
                !Array.isArray(response.nodes) ||
                !Array.isArray(response.edges)
            ) {
                throw new Error("Dữ liệu kết nối không hợp lệ.");
            }

            // Một số API trả thêm center riêng.
            const nodes = [...response.nodes];

            if (response.center?.id !== undefined) {
                const centerId = normalizeId(response.center.id);

                if (!nodes.some(node => normalizeId(node.id) === centerId)) {
                    nodes.push(response.center);
                }
            }

            mergeData({
                nodes,
                edges: response.edges
            });

            state.expandedIds.add(nodeId);

            showDetails(nodeId);

            state.network.selectNodes([nodeId]);

            state.network.focus(nodeId, {
                scale: 1.05,
                animation: {
                    duration: 500,
                    easingFunction: "easeInOutQuad"
                }
            });

            updateStatus("Đã mở rộng kết nối");

        } finally {
            state.expanding = false;
            el.expand.disabled = false;

            el.expand.innerHTML = `
                <i class="bi bi-plus-circle"></i>
                Khám phá các kết nối
            `;
        }
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

            const type = labels
                .filter(Boolean)
                .map(label => LABELS[label] || label)
                .join(", ") || "Thực thể";

            return `
                <button
                    type="button"
                    class="search-result-item"
                    data-index="${index}">

                    <span class="search-result-name">
                        ${escapeHTML(getNodeName(item))}
                    </span>

                    <span class="search-result-type">
                        ${escapeHTML(type)}
                    </span>

                    <i class="bi bi-arrow-up-right"></i>
                </button>
            `;
        }).join("");

        el.searchResults.querySelectorAll(".search-result-item").forEach(button => {
            button.addEventListener("click", () => {
                selectSearchResult(results[Number(button.dataset.index)]);
            });
        });
    }

    async function searchEntities() {
        const keyword = el.searchInput.value.trim();

        if (!keyword) {
            el.searchInput.focus();
            return;
        }

        if (!API) {
            showError("Không tìm thấy ApiClient.");
            return;
        }

        const requestId = ++state.searchRequest;

        el.searchButton.disabled = true;
        el.searchButton.textContent = "Đang tìm...";

        try {
            const params = {
                keyword,
                limit: CONFIG.SEARCH_LIMIT
            };

            if (getFilter() !== "all") {
                params.entity_type = getFilter();
            }

            const response = await API.get("/api/graph/search", params);

            if (requestId !== state.searchRequest) return;

            renderSearchResults(response.results || []);

        } catch (error) {
            console.error("Search error:", error);

            el.searchResults.hidden = false;
            el.searchResults.innerHTML = `
                <div class="search-no-result">
                    ${escapeHTML(error.message || "Không thể tìm kiếm.")}
                </div>
            `;

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

        const node = {
            id: nodeId,
            business_id: result.business_id,
            labels: result.labels || [],
            display_labels: result.display_labels || [],
            properties: result.properties || {}
        };

        state.nodeMap.set(nodeId, node);
        state.nodes.update(convertNode(node));

        if (!isNodeAllowed(node)) {
            el.filter.value = "all";
        }

        applyFilter();
        focusNode(nodeId);

        await expandNode(nodeId);
    }

    // ================================================
    // EVENTS
    // ================================================

    el.searchButton.addEventListener("click", searchEntities);

    el.searchInput.addEventListener("keydown", event => {
        if (event.key === "Enter") searchEntities();

        if (event.key === "Escape") {
            el.searchResults.hidden = true;
        }
    });

    el.searchInput.addEventListener("input", () => {
        if (!el.searchInput.value.trim()) {
            el.searchResults.hidden = true;
        }
    });

    el.filter.addEventListener("change", () => {
        applyFilter();
        el.searchResults.hidden = true;

        if (state.network) {
            state.network.fit({
                animation: {
                    duration: 400,
                    easingFunction: "easeInOutQuad"
                }
            });
        }
    });

    el.fit.addEventListener("click", () => {
        if (!state.network) return;

        state.network.fit({
            animation: {
                duration: 500,
                easingFunction: "easeInOutQuad"
            }
        });
    });

    el.reset.addEventListener("click", () => {
        el.filter.value = "all";
        el.searchInput.value = "";
        el.searchResults.hidden = true;

        state.searchRequest++;
        loadGraph();
    });

    el.retry.addEventListener("click", loadGraph);

    el.expand.addEventListener("click", async () => {
        if (!state.selectedId) return;

        try {
            await expandNode(state.selectedId);
        } catch (error) {
            console.error("Expand error:", error);
            showError("Không thể mở rộng kết nối: " + error.message);
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