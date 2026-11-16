
/* =========================================
   TIMELINE - TAY SON SU KY
   API INTEGRATION
========================================= */

const TIMELINE_API_URL = "/api/timeline/";

let allTimelineEvents = [];
let currentTimelineEvents = [];

let eventModal = null;


/* =========================================
   DOM ELEMENTS
========================================= */

const timelineList = document.getElementById("timelineList");
const timelineLoading = document.getElementById("timelineLoading");
const timelineError = document.getElementById("timelineError");
const timelineErrorMessage = document.getElementById("timelineErrorMessage");
const timelineEmpty = document.getElementById("timelineEmpty");
const timelineCount = document.getElementById("timelineCount");

const startYearSelect = document.getElementById("startYear");
const endYearSelect = document.getElementById("endYear");

const filterForm = document.getElementById("timelineFilterForm");
const searchForm = document.getElementById("timelineSearchForm");

const keywordInput = document.getElementById("timelineKeyword");
const resetButton = document.getElementById("resetTimeline");
const retryButton = document.getElementById("retryTimeline");

const eventModalBody = document.getElementById("eventModalBody");


/* =========================================
   HELPER FUNCTIONS
========================================= */

// Escape HTML để tránh lỗi khi render dữ liệu.
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        };

        return entities[char];
    });
}


// Lấy năm từ ngày.
function extractYear(date) {
    if (date === null || date === undefined || date === "") {
        return null;
    }

    const match = String(date).match(/\b(1[0-9]{3}|20[0-9]{2})\b/);

    return match ? Number(match[0]) : null;
}


// Lấy năm bắt đầu.
function getEventYear(event) {
    return (
        extractYear(event.startDate) ??
        extractYear(event.start_date) ??
        extractYear(event.startYear) ??
        extractYear(event.start_year) ??
        extractYear(event.year) ??
        null
    );
}


// Lấy ngày bắt đầu.
function getStartDate(event) {
    return (
        event.startDate ??
        event.start_date ??
        event.startYear ??
        event.start_year ??
        event.year ??
        ""
    );
}


// Lấy ngày kết thúc.
function getEndDate(event) {
    return (
        event.endDate ??
        event.end_date ??
        event.endYear ??
        event.end_year ??
        ""
    );
}


// Lấy tên sự kiện.
function getEventName(event) {
    return (
        event.name ??
        event.title ??
        event.eventName ??
        event.event_name ??
        "Sự kiện lịch sử"
    );
}


// Lấy mô tả.
function getEventDescription(event) {
    return (
        event.description ??
        event.rag_text ??
        event.summary ??
        "Chưa có mô tả cho sự kiện này."
    );
}


// Lấy loại sự kiện.
function getEventType(event) {
    return (
        event.eventType ??
        event.event_type ??
        event.type ??
        "Sự kiện lịch sử"
    );
}


// Lấy thông tin dạng mảng hoặc chuỗi.
function formatList(value) {
    if (!value) return "Chưa có thông tin";

    if (Array.isArray(value)) {
        const result = value.map(item => {
            if (typeof item === "object" && item !== null) {
                return item.name ?? item.title ?? "";
            }

            return String(item);
        }).filter(Boolean);

        return result.join(", ") || "Chưa có thông tin";
    }

    if (typeof value === "object") {
        return value.name ?? value.title ?? "Chưa có thông tin";
    }

    return String(value);
}


// Lấy địa điểm.
function getEventLocations(event) {
    return formatList(
        event.locations ??
        event.location ??
        event.places
    );
}


// Lấy nhân vật.
function getEventCharacters(event) {
    return formatList(
        event.characters ??
        event.character ??
        event.people
    );
}


// Chuẩn hóa danh sách sự kiện.
function normalizeEvents(response) {

    if (!response) return [];

    // API trả về mảng trực tiếp.
    if (Array.isArray(response)) {
        return response;
    }

    if (typeof response !== "object") {
        return [];
    }

    // Kiểm tra các trường có thể chứa danh sách.
    const possibleArrays = [
        response.events,
        response.items,
        response.results,
        response.timeline,
        response.data
    ];

    for (const value of possibleArrays) {

        if (!Array.isArray(value)) continue;

        // Dữ liệu đã được phân nhóm theo năm.
        const isGrouped = value.some(item =>
            item &&
            typeof item === "object" &&
            Array.isArray(item.events)
        );

        if (isGrouped) {
            return value.flatMap(group => {

                if (!Array.isArray(group.events)) {
                    return [];
                }

                return group.events.map(event => ({
                    ...event,
                    year: event.year ?? group.year
                }));
            });
        }

        return value;
    }

    // Hỗ trợ response dạng:
    // { data: { events: [...] } }
    const nestedObjects = [
        response.data,
        response.result,
        response.payload
    ];

    for (const nested of nestedObjects) {
        if (nested && typeof nested === "object") {
            const result = normalizeEvents(nested);

            if (result.length > 0) {
                return result;
            }
        }
    }

    console.warn(
        "[Timeline] Không nhận diện được cấu trúc response:",
        response
    );

    return [];
}


/* =========================================
   UI STATES
========================================= */

function showLoading() {

    timelineLoading?.classList.remove("d-none");
    timelineError?.classList.add("d-none");
    timelineEmpty?.classList.add("d-none");

    if (timelineList) {
        timelineList.innerHTML = "";
    }

    if (timelineCount) {
        timelineCount.textContent = "Đang tải dữ liệu lịch sử...";
    }
}


function hideLoading() {
    timelineLoading?.classList.add("d-none");
}


function showError(message) {

    hideLoading();

    timelineError?.classList.remove("d-none");
    timelineEmpty?.classList.add("d-none");

    if (timelineList) {
        timelineList.innerHTML = "";
    }

    if (timelineErrorMessage) {
        timelineErrorMessage.textContent =
            message || "Không thể kết nối đến máy chủ.";
    }

    if (timelineCount) {
        timelineCount.textContent = "Không thể tải dữ liệu.";
    }
}


function showEmpty() {

    hideLoading();

    timelineEmpty?.classList.remove("d-none");
    timelineError?.classList.add("d-none");

    if (timelineList) {
        timelineList.innerHTML = "";
    }

    if (timelineCount) {
        timelineCount.textContent = "Không tìm thấy sự kiện phù hợp.";
    }
}


/* =========================================
   FETCH API
========================================= */

async function fetchTimeline() {

    console.log("[Timeline] API URL:", TIMELINE_API_URL);

    // Sử dụng API Client dùng chung.
    if (window.ApiClient) {
        return await window.ApiClient.get(TIMELINE_API_URL);
    }

    // Fallback nếu API Client chưa được khởi tạo.
    const response = await fetch(
        `http://127.0.0.1:8000${TIMELINE_API_URL}`,
        {
            method: "GET",
            headers: {
                Accept: "application/json"
            }
        }
    );

    if (!response.ok) {
        throw new Error(
            `Không thể tải dữ liệu. HTTP ${response.status}`
        );
    }

    return await response.json();
}


/* =========================================
   YEAR FILTER OPTIONS
========================================= */

function populateYearOptions(events) {

    if (!startYearSelect || !endYearSelect) return;

    const years = [
        ...new Set(
            events
                .map(getEventYear)
                .filter(year => year !== null)
        )
    ].sort((a, b) => a - b);

    const currentStart = startYearSelect.value;
    const currentEnd = endYearSelect.value;

    function fillSelect(select, selectedValue) {

        select.innerHTML = '<option value="">Tất cả</option>';

        years.forEach(year => {

            const option = document.createElement("option");

            option.value = year;
            option.textContent = year;

            select.appendChild(option);
        });

        if (years.includes(Number(selectedValue))) {
            select.value = selectedValue;
        }
    }

    fillSelect(startYearSelect, currentStart);
    fillSelect(endYearSelect, currentEnd);
}


/* =========================================
   GROUP EVENTS BY YEAR
========================================= */

function groupEventsByYear(events) {

    const groups = new Map();

    events.forEach(event => {

        const year = getEventYear(event);
        const key = year ?? "unknown";

        if (!groups.has(key)) {
            groups.set(key, []);
        }

        groups.get(key).push(event);
    });

    return [...groups.entries()].sort((a, b) => {

        if (a[0] === "unknown") return 1;
        if (b[0] === "unknown") return -1;

        return Number(a[0]) - Number(b[0]);
    });
}


/* =========================================
   RENDER EVENT CARD
========================================= */

function renderEventCard(event, index) {

    const name = escapeHTML(getEventName(event));
    const description = escapeHTML(getEventDescription(event));

    const startDate = escapeHTML(
        String(getStartDate(event) || "Chưa xác định")
    );

    const endDate = escapeHTML(
        String(getEndDate(event))
    );

    const eventType = escapeHTML(getEventType(event));

    const location = escapeHTML(getEventLocations(event));

    const tags = Array.isArray(event.tags)
        ? event.tags
        : [];

    const dateLabel = endDate
        ? `${startDate} — ${endDate}`
        : startDate;

    return `
        <article class="timeline-event-card">

            <div class="timeline-event-meta">

                <span class="timeline-event-type">
                    ${eventType}
                </span>

                <span class="timeline-event-date">
                    <i class="bi bi-calendar3 me-1"></i>
                    ${dateLabel}
                </span>

            </div>

            <h3 class="timeline-event-title">
                ${name}
            </h3>

            <p class="timeline-event-description">
                ${description}
            </p>

            ${tags.length ? `
                <div class="timeline-event-tags">
                    ${tags.map(tag => `
                        <span>${escapeHTML(tag)}</span>
                    `).join("")}
                </div>
            ` : ""}

            <div class="timeline-event-footer">

                <span class="timeline-event-location">
                    <i class="bi bi-geo-alt me-1"></i>
                    ${location}
                </span>

                <button
                    type="button"
                    class="timeline-event-detail"
                    data-event-index="${index}">

                    Khám phá sự kiện
                    <i class="bi bi-arrow-right ms-1"></i>

                </button>

            </div>

        </article>
    `;
}


/* =========================================
   RENDER TIMELINE
========================================= */

function renderTimeline(events) {

    hideLoading();

    timelineError?.classList.add("d-none");
    timelineEmpty?.classList.add("d-none");

    if (!timelineList) {
        console.error("[Timeline] Không tìm thấy #timelineList");
        return;
    }

    if (!Array.isArray(events) || events.length === 0) {
        currentTimelineEvents = [];
        showEmpty();
        return;
    }

    // Sắp xếp sự kiện theo năm.
    const sortedEvents = [...events].sort((a, b) => {

        const yearA = getEventYear(a) ?? 9999;
        const yearB = getEventYear(b) ?? 9999;

        if (yearA !== yearB) {
            return yearA - yearB;
        }

        return String(getStartDate(a)).localeCompare(
            String(getStartDate(b))
        );
    });

    currentTimelineEvents = sortedEvents;

    // Phân nhóm theo năm.
    const yearGroups = groupEventsByYear(sortedEvents);

    let eventIndex = 0;

    timelineList.innerHTML = yearGroups.map(([year, eventsInYear]) => {

        const displayYear = year === "unknown"
            ? "N/A"
            : year;

        const cards = eventsInYear.map(event => {

            const card = renderEventCard(event, eventIndex);

            eventIndex++;

            return card;

        }).join("");

        return `
            <div class="timeline-year-group">

                <div class="timeline-year-rail">

                    <span class="timeline-year-label">
                        ${displayYear}
                    </span>

                    <span class="timeline-year-caption">
                        NĂM LỊCH SỬ
                    </span>

                    <span class="timeline-year-dot"></span>

                </div>

                <div class="timeline-events">
                    ${cards}
                </div>

            </div>
        `;

    }).join("");

    if (timelineCount) {
        timelineCount.textContent =
            `Tìm thấy ${sortedEvents.length} sự kiện lịch sử qua ${yearGroups.length} mốc thời gian.`;
    }

    console.log("[Timeline] Đã render:", sortedEvents.length, "sự kiện");
}


/* =========================================
   EVENT DETAIL MODAL
========================================= */

function openEventDetail(index) {

    const event = currentTimelineEvents[index];

    if (!event || !eventModalBody) return;

    const year = getEventYear(event);

    const name = escapeHTML(getEventName(event));

    const startDate = escapeHTML(
        String(getStartDate(event) || "Chưa xác định")
    );

    const endDate = escapeHTML(
        String(getEndDate(event))
    );

    const description = escapeHTML(getEventDescription(event));

    const result = escapeHTML(
        event.result ?? event.outcome ?? "Chưa có thông tin."
    );

    const significance = escapeHTML(
        event.significance ?? "Chưa có thông tin."
    );

    const period = escapeHTML(
        event.period ?? "Chưa xác định"
    );

    const eventType = escapeHTML(getEventType(event));

    const tags = escapeHTML(formatList(event.tags));

    const locations = escapeHTML(getEventLocations(event));

    const characters = escapeHTML(getEventCharacters(event));

    eventModalBody.innerHTML = `

        <div class="event-detail-year">
            ${year ?? "N/A"}
        </div>

        <h2 class="event-detail-title">
            ${name}
        </h2>

        <div class="event-detail-meta">

            <span>
                <i class="bi bi-calendar3 me-1"></i>
                ${startDate}${endDate ? ` — ${endDate}` : ""}
            </span>

            <span>
                ${eventType}
            </span>

            <span>
                ${period}
            </span>

        </div>

        <div class="event-detail-section">

            <h4>DIỄN BIẾN SỰ KIỆN</h4>

            <p>${description}</p>

        </div>

        <div class="event-detail-section">

            <h4>KẾT QUẢ</h4>

            <p>${result}</p>

        </div>

        <div class="event-detail-section">

            <h4>Ý NGHĨA LỊCH SỬ</h4>

            <p>${significance}</p>

        </div>

        <div class="event-detail-section">

            <h4>NHÂN VẬT LIÊN QUAN</h4>

            <p>${characters}</p>

        </div>

        <div class="event-detail-section">

            <h4>ĐỊA ĐIỂM</h4>

            <p>${locations}</p>

        </div>

        <div class="event-detail-section">

            <h4>TỪ KHÓA</h4>

            <p>${tags}</p>

        </div>

    `;

    eventModal?.show();
}


/* =========================================
   SEARCH & FILTER
========================================= */

function applyLocalFilters() {

    const startYear = startYearSelect?.value
        ? Number(startYearSelect.value)
        : null;

    const endYear = endYearSelect?.value
        ? Number(endYearSelect.value)
        : null;

    const keyword = keywordInput?.value.trim().toLocaleLowerCase("vi") || "";

    if (startYear && endYear && startYear > endYear) {

        showError(
            "Năm bắt đầu không được lớn hơn năm kết thúc."
        );

        return;
    }

    const filteredEvents = allTimelineEvents.filter(event => {

        const year = getEventYear(event);

        if (startYear && (year === null || year < startYear)) {
            return false;
        }

        if (endYear && (year === null || year > endYear)) {
            return false;
        }

        if (keyword) {

            const searchableContent = [

                getEventName(event),
                getEventDescription(event),

                event.result,
                event.significance,

                getEventType(event),
                event.period,

                event.tags,
                getEventLocations(event),
                getEventCharacters(event)

            ].map(value => {

                if (Array.isArray(value)) {
                    return value.join(" ");
                }

                return String(value ?? "");

            }).join(" ").toLocaleLowerCase("vi");

            if (!searchableContent.includes(keyword)) {
                return false;
            }
        }

        return true;
    });

    renderTimeline(filteredEvents);
}


/* =========================================
   LOAD TIMELINE
========================================= */

async function loadTimeline() {

    showLoading();

    try {

        console.log("[Timeline] Bắt đầu tải dữ liệu...");

        const response = await fetchTimeline();

        console.log("[Timeline] API Response:", response);

        const events = normalizeEvents(response);

        console.log(
            "[Timeline] Tổng số sự kiện:",
            events.length
        );

        if (!events.length) {

            console.warn(
                "[Timeline] API trả về nhưng không tìm thấy mảng sự kiện."
            );

            allTimelineEvents = [];

            populateYearOptions([]);

            showEmpty();

            return;
        }

        allTimelineEvents = events;

        populateYearOptions(allTimelineEvents);

        renderTimeline(allTimelineEvents);

    } catch (error) {

        console.error("[Timeline] Lỗi:", error);

        showError(error.message);

    }
}


/* =========================================
   EVENT LISTENERS
========================================= */

// Lọc theo năm.
filterForm?.addEventListener("submit", event => {

    event.preventDefault();

    applyLocalFilters();

});


// Tìm kiếm.
searchForm?.addEventListener("submit", event => {

    event.preventDefault();

    applyLocalFilters();

});


// Đặt lại bộ lọc.
resetButton?.addEventListener("click", () => {

    if (startYearSelect) {
        startYearSelect.value = "";
    }

    if (endYearSelect) {
        endYearSelect.value = "";
    }

    if (keywordInput) {
        keywordInput.value = "";
    }

    renderTimeline(allTimelineEvents);

});


// Thử tải lại.
retryButton?.addEventListener("click", () => {
    loadTimeline();
});


// Xem chi tiết sự kiện.
timelineList?.addEventListener("click", event => {

    const button = event.target.closest("[data-event-index]");

    if (!button) return;

    const index = Number(button.dataset.eventIndex);

    openEventDetail(index);

});


/* =========================================
   INITIALIZE
========================================= */

function initializeTimeline() {

    const modalElement = document.getElementById("eventModal");

    if (modalElement && window.bootstrap) {

        eventModal = bootstrap.Modal.getOrCreateInstance(
            modalElement
        );

    }

    loadTimeline();

}


// Khởi chạy.
if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        initializeTimeline
    );

} else {

    initializeTimeline();

}
