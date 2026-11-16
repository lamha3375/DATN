
document.addEventListener("DOMContentLoaded", () => {
    const PAGE_SIZE = 12;

    const state = {
        skip: 0,
        limit: PAGE_SIZE,
        keyword: "",
        total: 0,
        characters: []
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
        modalBody: document.getElementById("characterModalBody")
    };

    const modalElement = document.getElementById("characterModal");
    const characterModal = bootstrap.Modal.getOrCreateInstance(modalElement);

    // -------------------------------------
    // UTILITIES
    // -------------------------------------

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

    function getCharacterId(character) {
        return character.character_id
            || character.person_id
            || character.id;
    }

    function getInitials(name) {
        const words = String(name || "?").trim().split(/\s+/);

        if (words.length === 1) {
            return words[0].substring(0, 2).toUpperCase();
        }

        return (
            words[words.length - 2][0]
            + words[words.length - 1][0]
        ).toUpperCase();
    }

    function showState(type) {
        elements.loading.classList.toggle("d-none", type !== "loading");
        elements.error.classList.toggle("d-none", type !== "error");
        elements.empty.classList.toggle("d-none", type !== "empty");
        elements.grid.classList.toggle("d-none", type !== "data");

        if (type !== "data") {
            elements.pagination.classList.add("d-none");
        }
    }

    // -------------------------------------
    // CHARACTER CARD
    // -------------------------------------

    function createCharacterCard(character) {
        const id = getCharacterId(character);
        const name = normalizeText(character.name) || "Chưa xác định";

        const aliases = normalizeText(character.aliases);
        const role = normalizeText(character.role) || "Nhân vật lịch sử";
        const faction = normalizeText(character.faction) || "Chưa cập nhật";

        const description = normalizeText(
            character.historical_notes
        ) || "Thông tin nhân vật đang được cập nhật.";

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
                            ${aliases
                                ? "Còn được biết đến: " + escapeHTML(aliases)
                                : "&nbsp;"}
                        </p>

                        <p class="character-description">
                            ${escapeHTML(description)}
                        </p>

                        <div class="character-card-footer">
                            <span class="character-faction">
                                <i class="bi bi-flag me-1"></i>
                                ${escapeHTML(faction)}
                            </span>

                            <button
                                class="character-detail-btn"
                                data-character-id="${escapeHTML(id || "")}"
                                type="button"
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

    // -------------------------------------
    // LOAD CHARACTERS
    // -------------------------------------

    async function loadCharacters() {
        showState("loading");

        try {
            const params = {
                skip: state.skip,
                limit: state.limit
            };

            if (state.keyword) {
                params.keyword = state.keyword;
            }

            const response = await ApiClient.get(
                "/api/characters/",
                params
            );

            // API trả về:
            // {
            //   total: number,
            //   skip: number,
            //   limit: number,
            //   data: [...]
            // }

            const characters = Array.isArray(response.data)
                ? response.data
                : [];

            state.characters = characters;
            state.total = Number(response.total) || 0;

            elements.count.textContent =
                `Tìm thấy ${state.total} nhân vật`;

            if (characters.length === 0) {
                showState("empty");
                return;
            }

            elements.grid.innerHTML = characters
                .map(createCharacterCard)
                .join("");

            showState("data");
            renderPagination();

        } catch (error) {
            console.error("Character API error:", error);

            elements.errorMessage.textContent =
                error.message || "Không thể kết nối đến máy chủ.";

            showState("error");
        }
    }

    // -------------------------------------
    // PAGINATION
    // -------------------------------------

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
        elements.next.disabled = currentPage >= totalPages;
    }

    elements.prev.addEventListener("click", () => {
        if (state.skip >= state.limit) {
            state.skip -= state.limit;
            loadCharacters();
        }
    });

    elements.next.addEventListener("click", () => {
        if (state.skip + state.limit < state.total) {
            state.skip += state.limit;
            loadCharacters();
        }
    });

    // -------------------------------------
    // SEARCH
    // -------------------------------------

    elements.searchForm.addEventListener("submit", event => {
        event.preventDefault();

        state.keyword = elements.searchInput.value.trim();
        state.skip = 0;

        loadCharacters();
    });

    // -------------------------------------
    // CHARACTER DETAIL
    // -------------------------------------

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
                throw new Error("Không tìm thấy thông tin nhân vật.");
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
        const name = normalizeText(character.name) || "Chưa xác định";
        const aliases = normalizeText(character.aliases);
        const role = normalizeText(character.role);
        const faction = normalizeText(character.faction);
        const notes = normalizeText(character.historical_notes);

        elements.modalBody.innerHTML = `
            <div class="character-detail">

                <span class="character-category">
                    ${escapeHTML(role || "NHÂN VẬT LỊCH SỬ")}
                </span>

                <h2 class="character-detail-title">
                    ${escapeHTML(name)}
                </h2>

                <div class="character-detail-meta">
                    ${faction
                        ? `<span><i class="bi bi-flag me-1"></i>
                            ${escapeHTML(faction)}</span>`
                        : ""}

                    ${character.person_id
                        ? `<span>${escapeHTML(character.person_id)}</span>`
                        : ""}
                </div>

                ${aliases ? `
                    <div class="character-detail-section">
                        <h4>TÊN GỌI KHÁC</h4>
                        <p>${escapeHTML(aliases)}</p>
                    </div>
                ` : ""}

                <div class="character-detail-section">
                    <h4>THÔNG TIN LỊCH SỬ</h4>
                    <p>
                        ${escapeHTML(
                            notes || "Thông tin đang được cập nhật."
                        )}
                    </p>
                </div>

            </div>
        `;
    }

    // Event delegation: xử lý nút chi tiết
    elements.grid.addEventListener("click", event => {
        const button = event.target.closest(
            ".character-detail-btn"
        );

        if (!button) return;

        showCharacterDetail(
            button.dataset.characterId
        );
    });

    // -------------------------------------
    // RETRY
    // -------------------------------------

    document.getElementById("retryCharacters")
        .addEventListener("click", loadCharacters);

    // INITIAL LOAD
    loadCharacters();
});
