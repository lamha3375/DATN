
/* =========================================
   GLOBAL FLOATING CHAT WIDGET
========================================= */

document.addEventListener("DOMContentLoaded", () => {
    if (!window.TaySonChat || !window.ApiClient) {
        console.warn("Chat widget: thiếu chat-core.js hoặc api.js.");
        return;
    }

    // Không tạo widget trùng nếu script bị nạp nhiều lần.
    if (document.querySelector(".chat-widget-root")) return;

    const chat = window.TaySonChat;
    let isSending = false;

    const root = document.createElement("div");
    root.className = "chat-widget-root";

    const panel = document.createElement("section");
    panel.className = "chat-widget-panel";
    panel.setAttribute("aria-label", "Trợ lý lịch sử Tây Sơn");

    const header = document.createElement("header");
    header.className = "chat-widget-header";

    const heading = document.createElement("div");
    heading.className = "chat-widget-heading";

    const avatar = document.createElement("div");
    avatar.className = "chat-widget-avatar";
    avatar.innerHTML = '<i class="bi bi-compass"></i>';

    const headingText = document.createElement("div");
    headingText.innerHTML =
        "<strong>Trợ lý lịch sử Tây Sơn</strong>" +
        "<small>Đang sẵn sàng hỗ trợ bạn</small>";

    heading.append(avatar, headingText);

    const headerActions = document.createElement("div");
    headerActions.className = "chat-widget-header-actions";

    const fullPageLink = document.createElement("a");
    fullPageLink.href = window.location.pathname.includes("/pages/")
        ? "chat.html"
        : "pages/chat.html";
    fullPageLink.title = "Mở trang chat đầy đủ";
    fullPageLink.innerHTML = '<i class="bi bi-arrows-angle-expand"></i>';

    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.title = "Thu gọn";
    closeButton.innerHTML = '<i class="bi bi-dash-lg"></i>';

    headerActions.append(fullPageLink, closeButton);
    header.append(heading, headerActions);


    /* MESSAGES */

    const messages = document.createElement("div");
    messages.className = "chat-widget-messages";

    const welcome = document.createElement("div");
    welcome.className = "chat-widget-welcome";

    const welcomeIcon = document.createElement("div");
    welcomeIcon.className = "chat-widget-welcome-icon";
    welcomeIcon.innerHTML = '<i class="bi bi-chat-square-text"></i>';

    const welcomeTitle = document.createElement("strong");
    welcomeTitle.textContent = "Xin chào!";

    const welcomeText = document.createElement("p");
    welcomeText.textContent =
        "Bạn đang muốn tìm hiểu điều gì về lịch sử Tây Sơn? " +
        "Hãy đặt câu hỏi để bắt đầu nhé.";

    const suggestions = document.createElement("div");
    suggestions.className = "chat-widget-suggestions";

    [
        "Nguyễn Huệ là ai?",
        "Phong trào Tây Sơn bắt đầu năm nào?",
        "Chiến thắng Ngọc Hồi - Đống Đa"
    ].forEach(question => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = question;

        button.addEventListener("click", () => {
            sendMessage(question);
        });

        suggestions.appendChild(button);
    });

    welcome.append(
        welcomeIcon,
        welcomeTitle,
        welcomeText,
        suggestions
    );

    messages.appendChild(welcome);


    /* INPUT */

    const inputArea = document.createElement("div");
    inputArea.className = "chat-widget-input-area";

    const form = document.createElement("form");
    form.className = "chat-widget-form";

    const textarea = document.createElement("textarea");
    textarea.rows = 1;
    textarea.maxLength = 1000;
    textarea.placeholder = "Nhập câu hỏi của bạn...";

    const sendButton = document.createElement("button");
    sendButton.type = "submit";
    sendButton.disabled = true;
    sendButton.setAttribute("aria-label", "Gửi câu hỏi");
    sendButton.innerHTML = '<i class="bi bi-arrow-up"></i>';

    form.append(textarea, sendButton);

    const footer = document.createElement("div");
    footer.className = "chat-widget-footer";

    const footerText = document.createElement("span");
    footerText.textContent = "AI hỗ trợ khám phá lịch sử";

    const newChatButton = document.createElement("a");
    newChatButton.href = "#";
    newChatButton.textContent = "Chat mới";

    footer.append(footerText, newChatButton);
    inputArea.append(form, footer);

    panel.append(header, messages, inputArea);


    /* TRIGGER */

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "chat-widget-trigger";
    trigger.setAttribute("aria-label", "Mở trợ lý lịch sử");

    trigger.innerHTML = `
        <i class="bi bi-chat-dots widget-open-icon"></i>
        <i class="bi bi-x-lg widget-close-icon"></i>
        <span class="chat-widget-pulse"></span>
    `;

    root.append(panel, trigger);
    document.body.appendChild(root);


    /* HELPERS */

    function getConversation() {
        return chat.getCurrentConversation() ||
            chat.createConversation();
    }

    function formatTime(value) {
        return new Date(value || Date.now()).toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    function renderMessage(message) {
        const wrapper = document.createElement("div");
        wrapper.className = `widget-message ${message.role}`;

        const name = document.createElement("div");
        name.className = "widget-message-name";
        name.textContent = message.role === "user"
            ? "Bạn"
            : "Trợ lý Tây Sơn";

        const bubble = document.createElement("div");
        bubble.className = "widget-message-bubble";
        bubble.textContent = message.content || "";

        const time = document.createElement("div");
        time.className = "widget-message-time";
        time.textContent = formatTime(message.createdAt);

        wrapper.append(name, bubble, time);
        messages.appendChild(wrapper);
    }

    function renderHistory() {
        const conversation = getConversation();

        messages.replaceChildren();

        const history = conversation.messages || [];

        if (!history.length) {
            messages.appendChild(welcome);
            return;
        }

        history.forEach(renderMessage);
        messages.scrollTop = messages.scrollHeight;
    }

    function showTyping() {
        const typing = document.createElement("div");
        typing.className = "widget-message assistant";
        typing.id = "widgetTyping";

        const name = document.createElement("div");
        name.className = "widget-message-name";
        name.textContent = "Trợ lý Tây Sơn";

        const bubble = document.createElement("div");
        bubble.className = "widget-typing";

        for (let i = 0; i < 3; i++) {
            bubble.appendChild(document.createElement("span"));
        }

        typing.append(name, bubble);
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;
    }

    function showError(text) {
        const error = document.createElement("div");
        error.className = "chat-widget-error";
        error.textContent = text;
        messages.appendChild(error);
        messages.scrollTop = messages.scrollHeight;
    }

    function updateSendButton() {
        sendButton.disabled =
            !textarea.value.trim() || isSending;
    }


    /* SEND MESSAGE */

    async function sendMessage(question) {
        const text = question.trim();

        if (!text || isSending) return;

        if (text.length > 1000) {
            showError("Câu hỏi không được vượt quá 1000 ký tự.");
            return;
        }

        isSending = true;
        updateSendButton();

        const conversation = getConversation();

        chat.addMessage(conversation.id, {
            role: "user",
            content: text
        });

        textarea.value = "";
        textarea.style.height = "auto";

        renderHistory();
        showTyping();

        try {
            const result = await chat.ask(text);

            document.getElementById("widgetTyping")?.remove();

            chat.addMessage(conversation.id, {
                role: "assistant",
                content: result.answer,
                sources: result.sources,
                sufficient: result.sufficient
            });

            renderHistory();

        } catch (error) {
            document.getElementById("widgetTyping")?.remove();

            showError(
                error.message || "Không thể kết nối Backend. Vui lòng thử lại."
            );
        } finally {
            isSending = false;
            updateSendButton();
            textarea.focus();
        }
    }


    /* EVENTS */

    trigger.addEventListener("click", () => {
        root.classList.toggle("open");

        if (root.classList.contains("open")) {
            renderHistory();
            textarea.focus();
        }
    });

    closeButton.addEventListener("click", () => {
        root.classList.remove("open");
    });

    form.addEventListener("submit", event => {
        event.preventDefault();
        sendMessage(textarea.value);
    });

    textarea.addEventListener("input", () => {
        textarea.style.height = "auto";
        textarea.style.height =
            `${Math.min(textarea.scrollHeight, 90)}px`;
        updateSendButton();
    });

    textarea.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();

            if (!sendButton.disabled) {
                form.requestSubmit();
            }
        }
    });

    newChatButton.addEventListener("click", event => {
        event.preventDefault();

        if (isSending) return;

        chat.createConversation();
        renderHistory();
        textarea.focus();
    });

    window.addEventListener("tay-son-chat-updated", () => {
        if (root.classList.contains("open") && !isSending) {
            renderHistory();
        }
    });

    window.addEventListener("storage", event => {
        if (
            event.key === "tay-son-chat-conversations" &&
            root.classList.contains("open") &&
            !isSending
        ) {
            renderHistory();
        }
    });

});
