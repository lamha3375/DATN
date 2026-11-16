
import { useEffect, useState, useCallback } from "react";
import { getTimeline } from "../services/timeline";

const MIN_YEAR = 1771;
const MAX_YEAR = 1802;

function formatDate(date) {
    if (!date) return "Chưa xác định";

    return String(date);
}

function TimelineCard({ event, onClick }) {
    return (
        <button
            type="button"
            className="timeline-event"
            onClick={onClick}
        >
            <div className="timeline-event-header">
                <span className="timeline-event-type">
                    {event.eventType || "Sự kiện lịch sử"}
                </span>

                <span className="timeline-event-date">
                    {formatDate(event.startDate)}
                    {event.endDate &&
                        event.endDate !== event.startDate &&
                        ` — ${formatDate(event.endDate)}`}
                </span>
            </div>

            <h3>{event.name || "Sự kiện chưa có tên"}</h3>

            <p>
                {event.description || "Chưa có mô tả cho sự kiện này."}
            </p>

            <span className="timeline-view-more">
                Xem chi tiết →
            </span>
        </button>
    );
}

function TimelineDetail({ event, onClose }) {
    if (!event) return null;

    return (
        <div
            className="timeline-modal-overlay"
            onClick={onClose}
        >
            <div
                className="timeline-modal"
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-modal="true"
                aria-labelledby="timeline-detail-title"
            >
                <button
                    type="button"
                    className="timeline-close"
                    onClick={onClose}
                    aria-label="Đóng"
                >
                    ×
                </button>

                <span className="timeline-event-type">
                    {event.eventType || "Sự kiện lịch sử"}
                </span>

                <h2 id="timeline-detail-title">
                    {event.name || "Sự kiện lịch sử"}
                </h2>

                <div className="timeline-detail-date">
                    {formatDate(event.startDate)}
                    {event.endDate &&
                        ` — ${formatDate(event.endDate)}`}
                </div>

                {event.period && (
                    <p><strong>Giai đoạn:</strong> {event.period}</p>
                )}

                {event.description && (
                    <section>
                        <h3>Mô tả</h3>
                        <p>{event.description}</p>
                    </section>
                )}

                {event.result && (
                    <section>
                        <h3>Kết quả</h3>
                        <p>{event.result}</p>
                    </section>
                )}

                {event.significance && (
                    <section>
                        <h3>Ý nghĩa lịch sử</h3>
                        <p>{event.significance}</p>
                    </section>
                )}

                {event.tags && (
                    <div className="timeline-tags">
                        {(Array.isArray(event.tags)
                            ? event.tags
                            : [event.tags]
                        ).map((tag, index) => (
                            <span key={index}>{tag}</span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function Timeline() {
    const [timeline, setTimeline] = useState([]);
    const [total, setTotal] = useState(0);

    const [startYear, setStartYear] = useState(MIN_YEAR);
    const [endYear, setEndYear] = useState(MAX_YEAR);
    const [keyword, setKeyword] = useState("");

    const [selectedEvent, setSelectedEvent] = useState(null);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const fetchTimeline = useCallback(async () => {
        setLoading(true);
        setError("");

        try {
            const result = await getTimeline({
                start_year: startYear,
                end_year: endYear,
                keyword
            });

            setTimeline(result.data || []);
            setTotal(result.total || 0);
        } catch (err) {
            setTimeline([]);
            setTotal(0);
            setError(
                err.message || "Không thể tải dòng thời gian."
            );
        } finally {
            setLoading(false);
        }
    }, [startYear, endYear, keyword]);

    useEffect(() => {
        const timeout = setTimeout(() => {
            fetchTimeline();
        }, 300);

        return () => clearTimeout(timeout);
    }, [fetchTimeline]);

    const resetFilters = () => {
        setStartYear(MIN_YEAR);
        setEndYear(MAX_YEAR);
        setKeyword("");
        setSelectedEvent(null);
    };

    const handleStartYearChange = (value) => {
        const year = Number(value);

        if (year <= endYear) {
            setStartYear(year);
        }
    };

    const handleEndYearChange = (value) => {
        const year = Number(value);

        if (year >= startYear) {
            setEndYear(year);
        }
    };

    return (
        <main className="timeline-page">

            {/* Hero */}
            <section className="timeline-hero">
                <div className="timeline-hero-content">
                    <span className="timeline-eyebrow">
                        LỊCH SỬ VIỆT NAM
                    </span>

                    <h1>DÒNG THỜI GIAN TÂY SƠN</h1>

                    <p>
                        Hành trình lịch sử từ cuộc khởi nghĩa Tây Sơn
                        năm 1771 đến khi kết thúc triều đại năm 1802.
                    </p>

                    <div className="timeline-hero-years">
                        <span>1771</span>
                        <div className="timeline-hero-line" />
                        <span>1802</span>
                    </div>
                </div>
            </section>

            {/* Filters */}
            <section className="timeline-controls">
                <div className="timeline-search">
                    <span>⌕</span>

                    <input
                        type="text"
                        placeholder="Tìm kiếm sự kiện lịch sử..."
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                    />
                </div>

                <div className="timeline-filter">
                    <label htmlFor="start-year">
                        Từ năm
                    </label>

                    <select
                        id="start-year"
                        value={startYear}
                        onChange={(e) =>
                            handleStartYearChange(e.target.value)
                        }
                    >
                        {Array.from(
                            { length: MAX_YEAR - MIN_YEAR + 1 },
                            (_, i) => MIN_YEAR + i
                        ).map(year => (
                            <option key={year} value={year}>
                                {year}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="timeline-filter">
                    <label htmlFor="end-year">
                        Đến năm
                    </label>

                    <select
                        id="end-year"
                        value={endYear}
                        onChange={(e) =>
                            handleEndYearChange(e.target.value)
                        }
                    >
                        {Array.from(
                            { length: MAX_YEAR - MIN_YEAR + 1 },
                            (_, i) => MIN_YEAR + i
                        ).filter(year => year >= startYear).map(year => (
                            <option key={year} value={year}>
                                {year}
                            </option>
                        ))}
                    </select>
                </div>

                <button
                    type="button"
                    className="timeline-reset"
                    onClick={resetFilters}
                >
                    Xóa bộ lọc
                </button>
            </section>

            {/* Statistics */}
            <section className="timeline-stats">
                <div>
                    <strong>{total}</strong>
                    <span>Sự kiện tìm thấy</span>
                </div>

                <div>
                    <strong>{startYear} – {endYear}</strong>
                    <span>Khoảng thời gian</span>
                </div>
            </section>

            {/* Timeline */}
            <section className="timeline-content">
                <div className="timeline-section-heading">
                    <h2>Hành trình lịch sử</h2>
                    <p>
                        Các dấu mốc quan trọng trong phong trào Tây Sơn
                    </p>
                </div>

                {loading && (
                    <div className="timeline-status">
                        Đang tải dữ liệu lịch sử...
                    </div>
                )}

                {!loading && error && (
                    <div className="timeline-error">
                        <p>{error}</p>
                        <button onClick={fetchTimeline}>
                            Thử lại
                        </button>
                    </div>
                )}

                {!loading && !error && timeline.length === 0 && (
                    <div className="timeline-empty">
                        <h3>Không tìm thấy sự kiện</h3>
                        <p>
                            Hãy thử thay đổi khoảng năm hoặc từ khóa tìm kiếm.
                        </p>
                    </div>
                )}

                {!loading && !error && timeline.length > 0 && (
                    <div className="timeline-list">
                        {timeline.map((group) => (
                            <div
                                className="timeline-year-group"
                                key={group.year}
                            >
                                <div className="timeline-year-marker">
                                    <span>{group.year}</span>
                                </div>

                                <div className="timeline-year-events">
                                    {group.events.map((event, index) => (
                                        <TimelineCard
                                            key={
                                                event.id ||
                                                `${group.year}-${index}`
                                            }
                                            event={event}
                                            onClick={() =>
                                                setSelectedEvent(event)
                                            }
                                        />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <footer className="timeline-footer">
                DÒNG THỜI GIAN LỊCH SỬ TÂY SƠN · 1771 – 1802
            </footer>

            <TimelineDetail
                event={selectedEvent}
                onClose={() => setSelectedEvent(null)}
            />
        </main>
    );
}
