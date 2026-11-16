
/* =========================================
   FULL PAGE CHAT
========================================= */

document.addEventListener("DOMContentLoaded", () => {
    const app = document.querySelector(".chat-app");
    if (!app) return;

    const chatMessages = document.getElementById("chatMessages");
    const welcomeContent = document.getElementById("welcomeContent");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const sendButton = document.getElementById("sendChatBtn");
    const historyList = document.getElementById("historyList");
    const historyEmpty = document.getElementById("historyEmpty");
    const newChatBtn = document.getElementById("newChatBtn");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const characterCounter = document.getElementById("characterCounter");

    let isSending = false;
    let activeConversationId = null;

    const chat = window.TaySonChat;


    /* ---------- HELPERS ---------- */

    function scrollBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatTime(value) {
        return new Date(value || Date.now()).toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    function updateInput() {
        sendButton.disabled =
            !chatInput.value.trim() || isSending;

        characterCounter.textContent =
            `${chatInput.value.length}/1000`;
    }

    function showWelcome(show) {
        welcomeContent.style.display = show ? "flex" : "none";
    }

    function safeInline(parent, text) {
        const parts = String(text).split(
            /(\*\*[^*]+\*\*|\*[^*]+\*)/g
        );

        parts.forEach(part => {
            if (!part) return;

            if (part.startsWith("**") && part.endsWith("**")) {
                const strong = document.createElement("strong");
                strong.textContent = part.slice(2, -2);
                parent.appendChild(strong);
            } else if (part.startsWith("*") && part.endsWith("*")) {
                const em = document.createElement("em");
                em.textContent = part.slice(1, -1);
                parent.appendChild(em);
            } else {
                parent.appendChild(document.createTextNode(part));
            }
        });
    }

    function renderText(parent, content) {
        const lines = String(content || "").replace(/\r/g, "").split("\n");
        let paragraph = [];
        let list = null;

        function flushParagraph() {
            if (!paragraph.length) return;

            const p = document.createElement("p");
            safeInline(p, paragraph.join(" "));
            parent.appendChild(p);
            paragraph = [];
        }

        function flushList() {
            if (list) {
                parent.appendChild(list);
                list = null;
            }
        }

        lines.forEach(line => {
            const value = line.trim();

            if (!value) {
                flushParagraph();
                flushList();
                return;
            }

            const unordered = value.match(/^[-*]\s+(.+)$/);
            const ordered = value.match(/^\d+[.)]\s+(.+)$/);

            if (unordered || ordered) {
                flushParagraph();

                const tag = unordered ? "ul" : "ol";

                if (!list || list.tagName.toLowerCase() !== tag) {
                    flushList();
                    list = document.createElement(tag);
                }

                const li = document.createElement("li");
                safeInline(li, (unordered || ordered)[1]);
                list.appendChild(li);
                return;
            }

            flushList();
            paragraph.push(value);
        });

        flushParagraph();
        flushList();
    }


    /* ---------- SOURCES ---------- */

    function sourceTitle(source) {
        return source.source_title ||
            source.document_title ||
            source.title ||
            source.document_name ||
            source.file_name ||
            source.name ||
            "Tài liệu lịch sử";
    }

    function sourceDetail(source) {
        const values = [];

        const page = source.page_number ?? source.page ?? source.page_index;

        if (page !== undefined && page !== null && page !== "") {
            values.push(`Trang ${page}`);
        }

        if (source.author) values.push(source.author);
        if (source.year) values.push(source.year);

        return values.join(" · ");
    }

    function renderSources(parent, sources) {
        if (!Array.isArray(sources) || !sources.length) return;

        const section = document.createElement("div");
        section.className = "message-sources";

        const heading = document.createElement("div");
        heading.className = "sources-heading";
        heading.innerHTML = '<i class="bi bi-journal-bookmark"></i><span>Nguồn tài liệu tham khảo</span>';
        section.appendChild(heading);

        sources.forEach(source => {
            if (!source || typeof source !== "object") return;

            const item = document.createElement("div");
            item.className = "source-item";

            const icon = document.createElement("i");
            icon.className = "bi bi-file-earmark-text";

            const info = document.createElement("div");
            info.className = "source-info";

            const title = document.createElement("span");
            title.className = "source-title";
            title.textContent = sourceTitle(source);

            info.appendChild(title);

            const detailText = sourceDetail(source);

            if (detailText) {
                const detail = document.createElement("span");
                detail.className = "source-detail";
                detail.textContent = detailText;
                info.appendChild(detail);
            }

            item.append(icon, info);
            section.appendChild(item);
        });

        if (section.children.length > 1) {
            parent.appendChild(section);
        }
    }


    /* ---------- MESSAGE RENDERING ---------- */

    function renderMessage(message) {
        const isUser = message.role === "user";

        const wrapper = document.createElement("article");
        wrapper.className = `chat-message ${isUser ? "user" : "assistant"}`;

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";

        const avatarIcon = document.createElement("i");
        avatarIcon.className = isUser
            ? "bi bi-person-fill"
            : "bi bi-compass";
        avatar.appendChild(avatarIcon);

        const content = document.createElement("div");
        content.className = "message-content";

        const name = document.createElement("div");
        name.className = "message-name";
        name.textContent = isUser ? "Bạn" : "Trợ lý lịch sử Tây Sơn";

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        renderText(bubble, message.content);

        const time = document.createElement("div");
        time.className = "message-time";
        time.textContent = formatTime(message.createdAt);

        content.append(name, bubble, time);

        if (!isUser) {
            renderSources(content, message.sources);

            if (message.sufficient === false) {
                const warning = document.createElement("div");
                warning.className = "context-warning";
                warning.textContent =
                    "Dữ liệu hiện có chưa đủ để đưa ra câu trả lời chắc chắn. " +
                    "Bạn nên đối chiếu thêm với tài liệu lịch sử gốc.";
                content.appendChild(warning);
            }
        }

        wrapper.append(avatar, content);
        chatMessages.appendChild(wrapper);
    }

    function renderTyping() {
        const wrapper = document.createElement("article");
        wrapper.className = "chat-message assistant";
        wrapper.id = "typingIndicator";

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.innerHTML = '<i class="bi bi-compass"></i>';

        const content = document.createElement("div");
        content.className = "message-content";

        const name = document.createElement("div");
        name.className = "message-name";
        name.textContent = "Trợ lý lịch sử Tây Sơn";

        const bubble = document.createElement("div");
        bubble.className = "typing-bubble";

        for (let i = 0; i < 3; i++) {
            bubble.appendChild(document.createElement("span"));
        }

        content.append(name, bubble);
        wrapper.append(avatar, content);
        chatMessages.appendChild(wrapper);
        scrollBottom();
    }

    function removeTyping() {
        document.getElementById("typingIndicator")?.remove();
    }

    function showError(message) {
        const error = document.createElement("div");
        error.className = "chat-error";
        error.textContent = message;
        chatMessages.appendChild(error);
        scrollBottom();
    }


    /* ---------- HISTORY SIDEBAR ---------- */

    function renderHistory() {
        const conversations = chat.readConversations();

        historyList.replaceChildren();
        historyEmpty.style.display =
            conversations.length ? "none" : "flex";

        conversations.forEach(conversation => {
            const item = document.createElement("div");
            item.className = "history-item" +
                (conversation.id === activeConversationId ? " active" : "");

            const icon = document.createElement("i");
            icon.className = "bi bi-chat-left-text";

            const title = document.createElement("span");
            title.className = "history-item-title";
            title.textContent = conversation.title || "Cuộc trò chuyện mới";

            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "history-delete";
            remove.title = "Xóa cuộc trò chuyện";
            remove.innerHTML = '<i class="bi bi-trash3"></i>';

            remove.addEventListener("click", event => {
                event.stopPropagation();

                if (!confirm("Bạn có chắc muốn xóa cuộc trò chuyện này?")) {
                    return;
                }

                chat.deleteConversation(conversation.id);

                if (activeConversationId === conversation.id) {
                    activeConversationId = chat.getCurrentId();
                    if (!activeConversationId) {
                        const created = chat.createConversation();
                        activeConversationId = created.id;
                    }
                    loadConversation(activeConversationId);
                }

                renderHistory();
            });

            item.append(icon, title, remove);

            item.addEventListener("click", () => {
                if (isSending) return;

                activeConversationId = conversation.id;
                chat.setCurrentId(conversation.id);
                loadConversation(conversation.id);
                renderHistory();
            });

            historyList.appendChild(item);
        });
    }


    /* ---------- LOAD CONVERSATION ---------- */

    function loadConversation(id) {
        const conversation = chat.getConversation(id);
        if (!conversation) return;

        activeConversationId = id;

        chatMessages.querySelectorAll(
            ".chat-message, .chat-error"
        ).forEach(element => element.remove());

        const messages = conversation.messages || [];

        showWelcome(messages.length === 0);

        messages.forEach(renderMessage);
        renderHistory();
        scrollBottom();
    }

    function startNewConversation() {
        if (isSending) return;

        const conversation = chat.createConversation();
        activeConversationId = conversation.id;

        loadConversation(conversation.id);
        chatInput.value = "";
        updateInput();
        chatInput.focus();
    }


    /* ---------- SEND ---------- */

    async function sendMessage(question) {
        const text = question.trim();

        if (!text || isSending) return;

        if (text.length > 1000) {
            showError("Câu hỏi không được vượt quá 1000 ký tự.");
            return;
        }

        isSending = true;
        updateInput();

        const conversation = chat.getConversation(activeConversationId) ||
            chat.createConversation();

        activeConversationId = conversation.id;
        chat.setCurrentId(activeConversationId);

        showWelcome(false);

        chat.addMessage(activeConversationId, {
            role: "user",
            content: text
        });

        renderMessage({
            role: "user",
            content: text,
            createdAt: new Date().toISOString()
        });

        chatInput.value = "";
        chatInput.style.height = "auto";
        updateInput();
        renderHistory();

        renderTyping();

        try {
            const result = await chat.ask(text);

            removeTyping();

            const assistantMessage = {
                role: "assistant",
                content: result.answer,
                sources: result.sources,
                sufficient: result.sufficient,
                createdAt: new Date().toISOString()
            };

            chat.addMessage(activeConversationId, assistantMessage);
            renderMessage(assistantMessage);
            renderHistory();

        } catch (error) {
            removeTyping();
            showError(
                error.message || "Không thể kết nối đến hệ thống. Vui lòng thử lại."
            );
        } finally {
            isSending = false;
            updateInput();
            chatInput.focus();
        }
    }


    /* ---------- EVENTS ---------- */

    chatForm.addEventListener("submit", event => {
        event.preventDefault();
        sendMessage(chatInput.value);
    });

    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height =
            `${Math.min(chatInput.scrollHeight, 130)}px`;
        updateInput();
    });

    chatInput.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();

            if (!sendButton.disabled) {
                chatForm.requestSubmit();
            }
        }
    });

    newChatBtn.addEventListener("click", startNewConversation);

    sidebarToggle.addEventListener("click", () => {
        app.classList.toggle("sidebar-collapsed");
    });

    document.querySelectorAll(".suggestion-card").forEach(button => {
        button.addEventListener("click", () => {
            if (!isSending) {
                sendMessage(button.dataset.question || "");
            }
        });
    });

    window.addEventListener("tay-son-chat-updated", () => {
        renderHistory();
    });

    window.addEventListener("storage", event => {
        if (event.key === "tay-son-chat-conversations") {
            renderHistory();
        }
    });


    /* ---------- INITIALIZE ---------- */

    let current = chat.getCurrentConversation();

    if (!current) {
        current = chat.createConversation();
    }

    activeConversationId = current.id;

    loadConversation(activeConversationId);
    renderHistory();
    updateInput();
});
