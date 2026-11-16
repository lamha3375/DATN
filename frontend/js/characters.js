
document.addEventListener("DOMContentLoaded", () => {
    const PAGE_SIZE = 12;

    const state = {
        skip: 0,
        limit: PAGE_SIZE,
        keyword: "",
        total: 0,
        characters: [],

        allCharacters: [],
        dynasty: "",
        role: "",
        sortBy: "name_asc"
    };

    const elements = {
        grid: document.getElementById("characterGrid"),
        loading: document.getElementById("characterLoading"),
        error: document.getElementById("characterError"),
        errorMessage: document.getElementById("characterErrorMessage"),
        empty: document.getElementById("characterEmpty"),
        count: document.getElementById("characterCount"),
        pagination: document.getElementById("characterPagination"),
        pageInfo: document.getElementById("pageInfo"),
        prev: document.getElementById("prevPage"),
        next: document.getElementById("nextPage"),
        searchForm: document.getElementById("characterSearchForm"),
        searchInput: document.getElementById("characterSearch"),
        modalBody: document.getElementById("characterModalBody"),
        retry: document.getElementById("retryCharacters"),
        //  bộ lọc nhân vật
        dynastyFilter: document.getElementById("characterDynastyFilter"),
        roleFilter: document.getElementById("characterRoleFilter"),
        sortFilter: document.getElementById("characterSort"),
        resetFilters: document.getElementById("resetCharacterFilters")
    };

    const modalElement = document.getElementById("characterModal");

    const characterModal = bootstrap.Modal.getOrCreateInstance(
        modalElement
    );
    // UTILITIES
    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[char]);
    }

    function normalizeText(value) {
        if (Array.isArray(value)) {
            return value.join(", ");
        }

        return value == null ? "" : String(value);
    }

    // Neo4j Person sử dụng property id, ví dụ PER_001
    function getCharacterId(character) {
        return normalizeText(character.id);
    }

    // Property alias trong Neo4j là chuỗi phân cách bằng dấu ;
    function formatAliases(value) {
        return normalizeText(value)
            .split(";")
            .map(item => item.trim())
            .filter(Boolean)
            .join(", ");
    }
    // CHARACTER FILTERS AND SORTING
    // Tách các vai trò nếu dữ liệu có nhiều vai trò
    function getRoleList(value) {
        return normalizeText(value)
            .split(";")
            .map(item => item.trim())
            .filter(Boolean);
    }

    // Tạo danh sách bộ lọc từ dữ liệu Neo4j
    function populateCharacterFilters(characters) {
        if (!elements.dynastyFilter || !elements.roleFilter) {
            return;
        }

        const selectedDynasty = state.dynasty;
        const selectedRole = state.role;

        const dynasties = [
            ...new Set(
                characters
                    .map(c => normalizeText(c.dynasty).trim())
                    .filter(Boolean)
            )
        ].sort((a, b) => a.localeCompare(b, "vi"));

        const roles = [
            ...new Set(
                characters.flatMap(c => getRoleList(c.role))
            )
        ].sort((a, b) => a.localeCompare(b, "vi"));

        elements.dynastyFilter.innerHTML =
            '<option value="">Tất cả triều đại</option>';

        elements.roleFilter.innerHTML =
            '<option value="">Tất cả vai trò</option>';

        dynasties.forEach(dynasty => {
            const option = document.createElement("option");
            option.value = dynasty;
            option.textContent = dynasty;
            elements.dynastyFilter.appendChild(option);
        });

        roles.forEach(role => {
            const option = document.createElement("option");
            option.value = role;
            option.textContent = role;
            elements.roleFilter.appendChild(option);
        });

        // Giữ lựa chọn nếu giá trị vẫn tồn tại
        elements.dynastyFilter.value =
            dynasties.includes(selectedDynasty)
                ? selectedDynasty
                : "";

        elements.roleFilter.value =
            roles.includes(selectedRole)
                ? selectedRole
                : "";

        state.dynasty = elements.dynastyFilter.value;
        state.role = elements.roleFilter.value;
    }

    // Lọc và sắp xếp danh sách nhân vật
    function renderFilteredCharacters() {
        let filtered = [...state.allCharacters];

        if (state.dynasty) {
            filtered = filtered.filter(character =>
                normalizeText(character.dynasty).trim() === state.dynasty
            );
        }

        if (state.role) {
            filtered = filtered.filter(character =>
                getRoleList(character.role).includes(state.role)
            );
        }

        // Sắp xếp theo tên
        filtered.sort((a, b) => {
            const nameA = normalizeText(a.name);
            const nameB = normalizeText(b.name);

            const result = nameA.localeCompare(
                nameB,
                "vi",
                { sensitivity: "base" }
            );

            return state.sortBy === "name_desc"
                ? -result
                : result;
        });

        // Cập nhật tổng số sau khi lọc
        state.total = filtered.length;

        elements.count.textContent =
            `Tìm thấy ${state.total} nhân vật`;

        // Phân trang trên danh sách đã lọc
        const currentCharacters = filtered.slice(
            state.skip,
            state.skip + state.limit
        );

        state.characters = currentCharacters;

        if (currentCharacters.length === 0) {
            elements.grid.innerHTML = "";
            showState("empty");
            return;
        }

        elements.grid.innerHTML = currentCharacters
            .map(createCharacterCard)
            .join("");

        showState("data");
        renderPagination();
    }

    // Gắn sự kiện cho bộ lọc
    if (elements.dynastyFilter) {
        elements.dynastyFilter.addEventListener("change", () => {
            state.dynasty = elements.dynastyFilter.value;
            state.skip = 0;
            renderFilteredCharacters();
        });
    }

    if (elements.roleFilter) {
        elements.roleFilter.addEventListener("change", () => {
            state.role = elements.roleFilter.value;
            state.skip = 0;
            renderFilteredCharacters();
        });
    }

    if (elements.sortFilter) {
        elements.sortFilter.addEventListener("change", () => {
            state.sortBy = elements.sortFilter.value || "name_asc";
            state.skip = 0;
            renderFilteredCharacters();
        });
    }

    if (elements.resetFilters) {
        elements.resetFilters.addEventListener("click", () => {
            state.dynasty = "";
            state.role = "";
            state.sortBy = "name_asc";
            state.skip = 0;

            if (elements.dynastyFilter) {
                elements.dynastyFilter.value = "";
            }

            if (elements.roleFilter) {
                elements.roleFilter.value = "";
            }

            if (elements.sortFilter) {
                elements.sortFilter.value = "name_asc";
            }

            renderFilteredCharacters();
        });
    }


    

    function getInitials(name) {
        const words = String(name || "?")
            .trim()
            .split(/\s+/);

        if (words.length === 1) {
            return words[0].substring(0, 2).toUpperCase();
        }

        return (
            words[words.length - 2][0]
            + words[words.length - 1][0]
        ).toUpperCase();
    }

    function showState(type) {
        elements.loading.classList.toggle(
            "d-none",
            type !== "loading"
        );

        elements.error.classList.toggle(
            "d-none",
            type !== "error"
        );

        elements.empty.classList.toggle(
            "d-none",
            type !== "empty"
        );

        elements.grid.classList.toggle(
            "d-none",
            type !== "data"
        );

        if (type !== "data") {
            elements.pagination.classList.add("d-none");
        }
    }

    // CHARACTER CARD
    function createCharacterCard(character) {
        const id = getCharacterId(character);

        const name = normalizeText(character.name)
            || "Chưa xác định";

        const aliases = formatAliases(character.alias);

        const role = normalizeText(character.role)
            || "Nhân vật lịch sử";

        const dynasty = normalizeText(character.dynasty)
            || "Chưa cập nhật";

        const period = normalizeText(character.period);

        const description = normalizeText(character.bio)
            || "Thông tin nhân vật đang được cập nhật.";

        return `
            <div class="col-md-6 col-lg-4">
                <article class="character-card">

                    <div class="character-portrait">
                        <span class="character-portrait-id">
                            ${escapeHTML(id || "NHÂN VẬT")}
                        </span>

                        <span class="character-portrait-icon">
                            ${escapeHTML(getInitials(name))}
                        </span>

                        <span class="character-portrait-label">
                            TÂY SƠN SỬ KÝ
                        </span>
                    </div>

                    <div class="character-card-body">

                        <span class="character-category">
                            ${escapeHTML(role)}
                        </span>

                        <h3>${escapeHTML(name)}</h3>

                        <p class="character-alias">
                            ${
                                aliases
                                    ? "Còn được biết đến: "
                                        + escapeHTML(aliases)
                                    : "&nbsp;"
                            }
                        </p>

                        <p class="character-description">
                            ${escapeHTML(description)}
                        </p>

                        <div class="character-card-footer">
                            <span class="character-faction">
                                <i class="bi bi-flag me-1"></i>
                                ${escapeHTML(dynasty)}
                            </span>

                            <button
                                class="character-detail-btn"
                                data-character-id="${escapeHTML(id)}"
                                type="button"
                                ${id ? "" : "disabled"}
                            >
                                Chi tiết
                                <i class="bi bi-arrow-right"></i>
                            </button>
                        </div>

                    </div>
                </article>
            </div>
        `;
    }

    // LOAD CHARACTERS
    async function loadCharacters() {
        showState("loading");

        try {
            const limit = 100;
            let skip = 0;
            let total = 0;
            let allCharacters = [];

            // Lấy trang đầu tiên
            const firstResponse = await ApiClient.get(
                "/api/characters/",
                {
                    skip,
                    limit,
                    ...(state.keyword
                        ? { keyword: state.keyword }
                        : {})
                }
            );

            total = Number(firstResponse.total) || 0;

            allCharacters = Array.isArray(firstResponse.data)
                ? firstResponse.data
                : [];

            // Lấy các trang tiếp theo nếu còn dữ liệu
            skip += limit;

            while (skip < total) {
                const response = await ApiClient.get(
                    "/api/characters/",
                    {
                        skip,
                        limit,
                        ...(state.keyword
                            ? { keyword: state.keyword }
                            : {})
                    }
                );

                const pageData = Array.isArray(response.data)
                    ? response.data
                    : [];

                if (pageData.length === 0) {
                    break;
                }

                allCharacters.push(...pageData);
                skip += limit;
            }

            state.allCharacters = allCharacters;

            // Tạo lựa chọn bộ lọc từ dữ liệu thực tế
            populateCharacterFilters(state.allCharacters);

            // Hiển thị danh sách đã lọc
            renderFilteredCharacters();

        } catch (error) {
            console.error("Character API error:", error);

            elements.errorMessage.textContent =
                error.message || "Không thể kết nối đến máy chủ.";

            showState("error");
        }
    }


    // PAGINATION
    function renderPagination() {
        const totalPages = Math.ceil(
            state.total / state.limit
        );

        const currentPage = Math.floor(
            state.skip / state.limit
        ) + 1;

        elements.pagination.classList.toggle(
            "d-none",
            totalPages <= 1
        );

        elements.pageInfo.textContent =
            `${currentPage} / ${totalPages}`;

        elements.prev.disabled = currentPage <= 1;

        elements.next.disabled =
            currentPage >= totalPages;
    }

    elements.prev.addEventListener("click", () => {
        if (state.skip >= state.limit) {
            state.skip -= state.limit;
            renderFilteredCharacters();
        }
    });

    elements.next.addEventListener("click", () => {
        if (state.skip + state.limit < state.total) {
            state.skip += state.limit;
            renderFilteredCharacters();
        }
    });
    // SEARCH
    elements.searchForm.addEventListener("submit", event => {
        event.preventDefault();

        state.keyword = elements.searchInput.value.trim();
        state.skip = 0;

        loadCharacters();
    });

    // CHARACTER DETAIL
    async function showCharacterDetail(characterId) {
        if (!characterId) return;

        characterModal.show();

        elements.modalBody.innerHTML = `
            <div class="character-state">
                <div class="spinner-border" role="status"></div>
                <p>Đang tải thông tin nhân vật...</p>
            </div>
        `;

        try {
            const response = await ApiClient.get(
                `/api/characters/${encodeURIComponent(characterId)}`
            );

            const character = response.data;

            if (!character) {
                throw new Error(
                    "Không tìm thấy thông tin nhân vật."
                );
            }

            renderCharacterDetail(character);

        } catch (error) {
            console.error("Character detail error:", error);

            elements.modalBody.innerHTML = `
                <div class="character-state">
                    <i class="bi bi-exclamation-circle"></i>
                    <h3>Không thể tải thông tin</h3>
                    <p>${escapeHTML(error.message)}</p>
                </div>
            `;
        }
    }

    function renderCharacterDetail(character) {
        const id = getCharacterId(character);

        const name = normalizeText(character.name)
            || "Chưa xác định";

        const aliases = formatAliases(character.alias);

        const role = normalizeText(character.role);

        const dynasty = normalizeText(character.dynasty);

        const bio = normalizeText(character.bio);

        const period = normalizeText(character.period);

        const module = normalizeText(character.module);

        elements.modalBody.innerHTML = `
            <div class="character-detail">

                <span class="character-category">
                    ${escapeHTML(role || "NHÂN VẬT LỊCH SỬ")}
                </span>

                <h2 class="character-detail-title">
                    ${escapeHTML(name)}
                </h2>

                <div class="character-detail-meta">

                    ${
                        id
                            ? `<span>${escapeHTML(id)}</span>`
                            : ""
                    }

                    ${
                        dynasty
                            ? `<span>
                                <i class="bi bi-flag me-1"></i>
                                ${escapeHTML(dynasty)}
                            </span>`
                            : ""
                    }

                </div>

                ${
                    aliases
                        ? `
                            <div class="character-detail-section">
                                <h4>TÊN GỌI KHÁC</h4>
                                <p>${escapeHTML(aliases)}</p>
                            </div>
                        `
                        : ""
                }

                ${
                    period
                        ? `
                            <div class="character-detail-section">
                                <h4>GIAI ĐOẠN LỊCH SỬ</h4>
                                <p>${escapeHTML(period)}</p>
                            </div>
                        `
                        : ""
                }

                <div class="character-detail-section">
                    <h4>THÔNG TIN LỊCH SỬ</h4>
                    <p>
                        ${escapeHTML(
                            bio || "Thông tin đang được cập nhật."
                        )}
                    </p>
                </div>

                ${
                    module
                        ? `
                            <div class="character-detail-section">
                                <h4>PHÂN HỆ DỮ LIỆU</h4>
                                <p>${escapeHTML(module)}</p>
                            </div>
                        `
                        : ""
                }

            </div>
        `;
    }

    // EVENT DELEGATION
    elements.grid.addEventListener("click", event => {
        const button = event.target.closest(
            ".character-detail-btn"
        );

        if (!button) return;

        showCharacterDetail(
            button.dataset.characterId
        );
    });

    // RETRY
    elements.retry.addEventListener(
        "click",
        loadCharacters
    );

    // INITIAL LOAD
    loadCharacters();
});
