
document.addEventListener("DOMContentLoaded", () => {
    const API = window.ApiClient;

    const elements = {
        network: document.getElementById("knowledge-network"),
        loading: document.getElementById("graph-loading"),
        error: document.getElementById("graph-error"),
        errorMessage: document.getElementById("graph-error-message"),
        empty: document.getElementById("graph-empty"),

        nodeCount: document.getElementById("node-count"),
        edgeCount: document.getElementById("edge-count"),

        searchInput: document.getElementById("graph-search-input"),
        searchButton: document.getElementById("graph-search-btn"),
        searchResults: document.getElementById("search-results"),

        entityFilter: document.getElementById("entity-filter"),
        fitButton: document.getElementById("fit-graph-btn"),
        resetButton: document.getElementById("reset-graph-btn"),
        retryButton: document.getElementById("graph-retry-btn"),

        detailPlaceholder: document.getElementById("detail-placeholder"),
        detailContent: document.getElementById("detail-content"),
        detailType: document.getElementById("detail-type"),
        detailName: document.getElementById("detail-name"),
        detailBusinessId: document.getElementById("detail-business-id"),
        detailProperties: document.getElementById("detail-properties-list"),
        detailRelations: document.getElementById("detail-relations-list"),
        relationCount: document.getElementById("relation-count"),
        expandButton: document.getElementById("expand-node-btn")
    };

    const state = {
        network: null,
        nodes: new Map(),
        edges: new Map(),
        selectedNodeId: null,
        isExpanding: false,
        isLoading: false
    };

    const NODE_COLORS = {
        NhanVat: {
            background: "#d8b58b",
            border: "#a87948",
            highlight: "#b88b5b"
        },
        SuKien: {
            background: "#b9c5a8",
            border: "#788b68",
            highlight: "#8b9d77"
        },
        DiaDiem: {
            background: "#b5c9d3",
            border: "#708b9c",
            highlight: "#849eac"
        },
        TheLuc: {
            background: "#d5b8c2",
            border: "#a8798c",
            highlight: "#b58c9b"
        },
        NguonTaiLieu: {
            background: "#d2cec3",
            border: "#999080",
            highlight: "#aaa394"
        },
        Default: {
            background: "#d8cbb5",
            border: "#9a8263",
            highlight: "#b18a4b"
        }
    };

    const LABEL_NAMES = {
        NhanVat: "Nhân vật",
        SuKien: "Sự kiện",
        DiaDiem: "Địa điểm",
        TheLuc: "Thế lực",
        NguonTaiLieu: "Nguồn tài liệu"
    };

    /* =====================================
       HELPERS
    ===================================== */

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[character]);
    }

    function getNodeName(node) {
        const properties = node.properties || {};

        return (
            properties.name ||
            properties.event_name ||
            properties.location_name ||
            properties.title ||
            properties.source_name ||
            node.name ||
            "Chưa có tên"
        );
    }

    function getNodeType(node) {
        const labels = node.labels || node.entity_type || [];

        if (!Array.isArray(labels)) {
            return labels || "Khác";
        }

        return labels.find(label => LABEL_NAMES[label]) || labels[0] || "Khác";
    }

    function getTypeName(type) {
        return LABEL_NAMES[type] || type || "Thực thể";
    }

    function getNodeColor(type) {
        return NODE_COLORS[type] || NODE_COLORS.Default;
    }

    function formatValue(value, maxLength = 500) {
        if (value === null || value === undefined || value === "") {
            return "Chưa có thông tin";
        }

        let result;

        if (Array.isArray(value)) {
            result = value.map(item =>
                typeof item === "object"
                    ? JSON.stringify(item)
                    : String(item)
            ).join(", ");
        } else if (typeof value === "object") {
            result = JSON.stringify(value);
        } else {
            result = String(value);
        }

        if (result.length > maxLength) {
            result = result.slice(0, maxLength) + "...";
        }

        return result;
    }

    function setLoading(isLoading) {
        elements.loading.hidden = !isLoading;
    }

    function showError(message) {
        elements.errorMessage.textContent = message;
        elements.error.hidden = false;
        elements.empty.hidden = true;
    }

    function hideError() {
        elements.error.hidden = true;
    }

    function getNodeLabel(node) {
        const name = getNodeName(node);
        return name.length > 25
            ? name.slice(0, 22) + "..."
            : name;
    }

    /* =====================================
       GRAPH DATA CONVERSION
    ===================================== */

    function convertNode(node) {
        const type = getNodeType(node);
        const colors = getNodeColor(type);

        return {
            id: String(node.id),
            label: getNodeLabel(node),
            title: escapeHTML(getNodeName(node)),
            group: type,
            shape: "dot",
            size: 17,
            color: {
                background: colors.background,
                border: colors.border,
                highlight: {
                    background: colors.highlight,
                    border: colors.border
                },
                hover: {
                    background: colors.highlight,
                    border: colors.border
                }
            },
            borderWidth: 2,
            font: {
                face: "Be Vietnam Pro",
                size: 11,
                color: "#4c3b2c",
                strokeWidth: 2,
                strokeColor: "#fffdf8"
            }
        };
    }

    function convertEdge(edge) {
        return {
            id: String(edge.id),
            from: String(edge.source),
            to: String(edge.target),
            label: edge.type || "",
            title: escapeHTML(edge.type || "Quan hệ"),
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.55
                }
            },
            color: {
                color: "#c4b59d",
                highlight: "#a87948",
                hover: "#a87948"
            },
            width: 1.3,
            font: {
                face: "Be Vietnam Pro",
                size: 8,
                color: "#897963",
                strokeWidth: 3,
                strokeColor: "#fffdf8",
                align: "middle"
            },
            smooth: {
                enabled: true,
                type: "dynamic"
            }
        };
    }

    /* =====================================
       GRAPH DATA MANAGEMENT
    ===================================== */

    function updateCounters() {
        elements.nodeCount.textContent = state.nodes.size;
        elements.edgeCount.textContent = state.edges.size;
    }

    function mergeGraphData(data) {
        const nodes = data.nodes || [];
        const edges = data.edges || [];

        nodes.forEach(node => {
            if (!node.id) return;

            const normalizedNode = {
                ...node,
                id: String(node.id)
            };

            state.nodes.set(normalizedNode.id, normalizedNode);

            if (state.network) {
                state.network.body.data.nodes.update(
                    convertNode(normalizedNode)
                );
            }
        });

        edges.forEach(edge => {
            if (!edge.id || !edge.source || !edge.target) return;

            const normalizedEdge = {
                ...edge,
                id: String(edge.id),
                source: String(edge.source),
                target: String(edge.target)
            };

            state.edges.set(normalizedEdge.id, normalizedEdge);

            if (state.network) {
                state.network.body.data.edges.update(
                    convertEdge(normalizedEdge)
                );
            }
        });

        updateCounters();
        applyNodeFilter();
    }

    function initializeNetwork() {
        if (typeof vis === "undefined") {
            throw new Error(
                "Không tải được thư viện vis-network. Hãy kiểm tra kết nối Internet."
            );
        }

        const nodeDataSet = new vis.DataSet();
        const edgeDataSet = new vis.DataSet();

        const options = {
            autoResize: true,

            interaction: {
                hover: true,
                tooltipDelay: 150,
                navigationButtons: true,
                keyboard: {
                    enabled: true,
                    speed: {
                        x: 10,
                        y: 10,
                        zoom: 0.05
                    }
                }
            },

            physics: {
                enabled: true,
                solver: "forceAtlas2Based",
                forceAtlas2Based: {
                    gravitationalConstant: -45,
                    centralGravity: 0.008,
                    springLength: 125,
                    springConstant: 0.07,
                    damping: 0.45,
                    avoidOverlap: 0.7
                },
                stabilization: {
                    enabled: true,
                    iterations: 250,
                    updateInterval: 25
                }
            },

            nodes: {
                chosen: true,
                scaling: {
                    min: 12,
                    max: 24
                }
            },

            edges: {
                selectionWidth: 2,
                hoverWidth: 2,
                smooth: {
                    enabled: true,
                    type: "dynamic"
                }
            }
        };

        state.network = new vis.Network(
            elements.network,
            {
                nodes: nodeDataSet,
                edges: edgeDataSet
            },
            options
        );

        state.network.on("click", params => {
            if (params.nodes.length > 0) {
                showNodeDetails(params.nodes[0]);
            }
        });

        state.network.on("deselectNode", () => {
            // Giữ thông tin đang xem khi click vùng trống.
        });

        state.network.once("stabilizationIterationsDone", () => {
            state.network.setOptions({
                physics: {
                    enabled: false
                }
            });
        });
    }

    /* =====================================
       FILTER
    ===================================== */

    function applyNodeFilter() {
        if (!state.network) return;

        const selectedType = elements.entityFilter.value;

        const visibleNodeIds = new Set();

        state.nodes.forEach(node => {
            const labels = node.labels || [];
            const isVisible =
                selectedType === "all" ||
                labels.includes(selectedType);

            if (isVisible) {
                visibleNodeIds.add(String(node.id));
            }

            state.network.body.data.nodes.update({
                id: String(node.id),
                hidden: !isVisible
            });
        });

        state.edges.forEach(edge => {
            const isVisible =
                visibleNodeIds.has(String(edge.source)) &&
                visibleNodeIds.has(String(edge.target));

            state.network.body.data.edges.update({
                id: String(edge.id),
                hidden: !isVisible
            });
        });

        if (state.selectedNodeId) {
            const selectedNode = state.nodes.get(state.selectedNodeId);

            if (
                selectedNode &&
                selectedType !== "all" &&
                !(selectedNode.labels || []).includes(selectedType)
            ) {
                clearNodeDetails();
            }
        }
    }

    /* =====================================
       NODE DETAILS
    ===================================== */

    function clearNodeDetails() {
        state.selectedNodeId = null;

        elements.detailPlaceholder.hidden = false;
        elements.detailContent.hidden = true;
    }

    function getNodeRelations(nodeId) {
        const relations = [];

        state.edges.forEach(edge => {
            if (
                String(edge.source) !== String(nodeId) &&
                String(edge.target) !== String(nodeId)
            ) {
                return;
            }

            const relatedId =
                String(edge.source) === String(nodeId)
                    ? String(edge.target)
                    : String(edge.source);

            const relatedNode = state.nodes.get(relatedId);

            if (!relatedNode) return;

            relations.push({
                type: edge.type,
                name: getNodeName(relatedNode),
                id: relatedId
            });
        });

        return relations;
    }

    function showNodeDetails(nodeId) {
        const node = state.nodes.get(String(nodeId));

        if (!node) return;

        state.selectedNodeId = String(nodeId);

        const properties = node.properties || {};
        const type = getNodeType(node);
        const name = getNodeName(node);

        elements.detailPlaceholder.hidden = true;
        elements.detailContent.hidden = false;

        elements.detailType.textContent = getTypeName(type);
        elements.detailName.textContent = name;
        elements.detailBusinessId.textContent =
            node.business_id
                ? `Mã thực thể: ${node.business_id}`
                : `Node ID: ${node.id}`;

        renderProperties(properties);
        renderRelations(nodeId);
    }

    function renderProperties(properties) {
        const ignoredFields = new Set([
            "person_id",
            "event_id",
            "location_id",
            "source_id",
            "id"
        ]);

        const entries = Object.entries(properties)
            .filter(([key, value]) =>
                value !== null &&
                value !== undefined &&
                value !== "" &&
                !ignoredFields.has(key)
            )
            .slice(0, 10);

        if (entries.length === 0) {
            elements.detailProperties.innerHTML = `
                <p class="relation-empty">
                    Chưa có thông tin chi tiết cho thực thể này.
                </p>
            `;
            return;
        }

        elements.detailProperties.innerHTML = entries.map(([key, value]) => `
            <div class="property-row">
                <span class="property-label">${escapeHTML(key)}</span>
                <span class="property-value">${escapeHTML(formatValue(value))}</span>
            </div>
        `).join("");
    }

    function renderRelations(nodeId) {
        const relations = getNodeRelations(nodeId);

        elements.relationCount.textContent = relations.length;

        if (relations.length === 0) {
            elements.detailRelations.innerHTML = `
                <p class="relation-empty">
                    Chưa có mối quan hệ được tải cho thực thể này.
                    Hãy chọn "Khám phá các kết nối" để mở rộng đồ thị.
                </p>
            `;
            return;
        }

        elements.detailRelations.innerHTML = relations.map(relation => `
            <div class="relation-item">
                <span class="relation-type">
                    ${escapeHTML(relation.type || "QUAN HỆ")}
                </span>
                <span class="relation-name">
                    ${escapeHTML(relation.name)}
                </span>
            </div>
        `).join("");
    }

    /* =====================================
       LOAD INITIAL GRAPH
    ===================================== */

    async function loadGraph() {
        if (state.isLoading) return;

        state.isLoading = true;
        setLoading(true);
        hideError();
        elements.empty.hidden = true;
        elements.searchResults.hidden = true;

        try {
            if (!API) {
                throw new Error("Không tìm thấy ApiClient.");
            }

            const response = await API.get("/api/graph/", {
                limit: 100
            });

            if (!response || !Array.isArray(response.nodes)) {
                throw new Error("Dữ liệu đồ thị trả về không đúng định dạng.");
            }

            if (!state.network) {
                initializeNetwork();
            }

            state.nodes.clear();
            state.edges.clear();

            state.network.body.data.nodes.clear();
            state.network.body.data.edges.clear();

            mergeGraphData(response);

            if (state.nodes.size === 0) {
                elements.empty.hidden = false;
                clearNodeDetails();
                return;
            }

            state.network.setOptions({
                physics: {
                    enabled: true
                }
            });

            state.network.fit({
                animation: {
                    duration: 700,
                    easingFunction: "easeInOutQuad"
                }
            });

            clearNodeDetails();

        } catch (error) {
            console.error("Load graph error:", error);
            showError(error.message || "Không thể tải dữ liệu đồ thị.");
        } finally {
            state.isLoading = false;
            setLoading(false);
        }
    }

    /* =====================================
       SEARCH ENTITIES
    ===================================== */

    function renderSearchResults(results) {
        elements.searchResults.hidden = false;

        if (!results.length) {
            elements.searchResults.innerHTML = `
                <div class="search-no-result">
                    Không tìm thấy thực thể phù hợp.
                </div>
            `;
            return;
        }

        elements.searchResults.innerHTML = results.map((item, index) => `
            <button type="button"
                    class="search-result-item"
                    data-result-index="${index}">
                <span class="search-result-name">
                    ${escapeHTML(item.name || "Chưa có tên")}
                </span>
                <span class="search-result-type">
                    ${escapeHTML(
                        (item.entity_type || [])
                            .map(getTypeName)
                            .join(", ")
                    )}
                </span>
            </button>
        `).join("");

        elements.searchResults.querySelectorAll(
            ".search-result-item"
        ).forEach(button => {
            button.addEventListener("click", () => {
                const index = Number(button.dataset.resultIndex);
                selectSearchResult(results[index]);
            });
        });
    }

    async function searchEntities() {
        const keyword = elements.searchInput.value.trim();

        if (!keyword) {
            elements.searchInput.focus();
            return;
        }

        const selectedType = elements.entityFilter.value;

        // API search hiện chỉ hỗ trợ ba loại thực thể này.
        if (
            selectedType !== "all" &&
            !["NhanVat", "SuKien", "DiaDiem"].includes(selectedType)
        ) {
            renderSearchResults([]);
            elements.searchResults.innerHTML = `
                <div class="search-no-result">
                    API tìm kiếm hiện hỗ trợ nhân vật, sự kiện và địa điểm.
                </div>
            `;
            return;
        }

        elements.searchButton.disabled = true;
        elements.searchButton.textContent = "Đang tìm...";

        try {
            const params = {
                keyword,
                limit: 20
            };

            if (selectedType !== "all") {
                params.entity_type = selectedType;
            }

            const response = await API.get(
                "/api/graph/search",
                params
            );

            renderSearchResults(response.results || []);

        } catch (error) {
            console.error("Search graph error:", error);

            elements.searchResults.hidden = false;
            elements.searchResults.innerHTML = `
                <div class="search-no-result">
                    ${escapeHTML(error.message)}
                </div>
            `;
        } finally {
            elements.searchButton.disabled = false;
            elements.searchButton.textContent = "Tìm kiếm";
        }
    }

    /* =====================================
       SELECT SEARCH RESULT
    ===================================== */

    async function selectSearchResult(result) {
        if (!result) return;

        elements.searchResults.hidden = true;

        const nodeId = String(result.id || result.node_id || "");

        if (!nodeId) {
            showError("Thực thể tìm được không có node ID hợp lệ.");
            return;
        }

        // Đưa kết quả tìm kiếm vào đồ thị nếu chưa có.
        const node = {
            id: nodeId,
            business_id: result.business_id,
            labels: result.entity_type || [],
            properties: result.properties || {},
            name: result.name
        };

        state.nodes.set(nodeId, node);

        if (!state.network) {
            initializeNetwork();
        }

        state.network.body.data.nodes.update(convertNode(node));

        // Bỏ lọc nếu node không thuộc loại đang hiển thị.
        const selectedType = elements.entityFilter.value;

        if (
            selectedType !== "all" &&
            !(node.labels || []).includes(selectedType)
        ) {
            elements.entityFilter.value = "all";
            applyNodeFilter();
        }

        try {
            await expandNode(nodeId, true);
        } catch (error) {
            console.error("Load search result error:", error);
            showNodeDetails(nodeId);
            showError(
                "Không thể tải các kết nối của thực thể: " + error.message
            );
        }
    }

    /* =====================================
       EXPAND NODE
    ===================================== */

    async function expandNode(nodeId, focusAfterExpand = false) {
        if (state.isExpanding) return;

        state.isExpanding = true;
        elements.expandButton.disabled = true;
        elements.expandButton.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Đang khám phá...
        `;

        try {
            const response = await API.get(
                `/api/graph/node/${encodeURIComponent(nodeId)}`,
                { limit: 50 }
            );

            if (!response || !Array.isArray(response.nodes)) {
                throw new Error("Dữ liệu kết nối không hợp lệ.");
            }

            mergeGraphData(response);

            // Đảm bảo node trung tâm có trong dữ liệu.
            if (response.center) {
                state.selectedNodeId = String(response.center);
            }

            if (focusAfterExpand && state.network) {
                state.network.selectNodes([String(nodeId)]);
                state.network.focus(String(nodeId), {
                    scale: 1.15,
                    animation: {
                        duration: 600,
                        easingFunction: "easeInOutQuad"
                    }
                });
            }

            applyNodeFilter();
            showNodeDetails(nodeId);

        } finally {
            state.isExpanding = false;
            elements.expandButton.disabled = false;
            elements.expandButton.innerHTML = `
                <i class="bi bi-diagram-3"></i>
                Khám phá các kết nối
            `;
        }
    }

    /* =====================================
       EVENT LISTENERS
    ===================================== */

    elements.searchButton.addEventListener("click", searchEntities);

    elements.searchInput.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            searchEntities();
        }

        if (event.key === "Escape") {
            elements.searchResults.hidden = true;
        }
    });

    elements.searchInput.addEventListener("input", () => {
        if (!elements.searchInput.value.trim()) {
            elements.searchResults.hidden = true;
        }
    });

    elements.entityFilter.addEventListener("change", () => {
        applyNodeFilter();
        elements.searchResults.hidden = true;
    });

    elements.fitButton.addEventListener("click", () => {
        if (!state.network || state.nodes.size === 0) return;

        state.network.fit({
            animation: {
                duration: 500,
                easingFunction: "easeInOutQuad"
            }
        });
    });

    elements.resetButton.addEventListener("click", () => {
        elements.entityFilter.value = "all";
        elements.searchInput.value = "";
        state.selectedNodeId = null;

        loadGraph();
    });

    elements.retryButton.addEventListener("click", loadGraph);

    elements.expandButton.addEventListener("click", async () => {
        if (!state.selectedNodeId) return;

        try {
            await expandNode(state.selectedNodeId);
        } catch (error) {
            console.error("Expand node error:", error);
            showError(
                "Không thể mở rộng kết nối: " + error.message
            );
        }
    });

    document.addEventListener("click", event => {
        if (!event.target.closest(".graph-search")) {
            elements.searchResults.hidden = true;
        }
    });

    /* =====================================
       INITIALIZE
    ===================================== */

    loadGraph();
});
