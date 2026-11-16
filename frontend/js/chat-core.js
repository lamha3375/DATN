
/* =========================================
   TAY SON CHAT CORE
   Shared conversation storage + API
========================================= */

(function () {
    const STORAGE_KEY = "tay-son-chat-conversations";
    const CURRENT_KEY = "tay-son-chat-current";

    function readConversations() {
        try {
            const data = JSON.parse(
                localStorage.getItem(STORAGE_KEY) || "[]"
            );

            return Array.isArray(data) ? data : [];
        } catch {
            return [];
        }
    }

    function writeConversations(conversations) {
        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(conversations)
        );

        window.dispatchEvent(
            new CustomEvent("tay-son-chat-updated")
        );
    }

    function createConversation() {
        const conversation = {
            id: crypto.randomUUID(),
            title: "Cuộc trò chuyện mới",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            messages: []
        };

        const conversations = readConversations();
        conversations.unshift(conversation);

        writeConversations(conversations);
        setCurrentId(conversation.id);

        return conversation;
    }

    function getCurrentId() {
        return localStorage.getItem(CURRENT_KEY);
    }

    function setCurrentId(id) {
        localStorage.setItem(CURRENT_KEY, id);

        window.dispatchEvent(
            new CustomEvent("tay-son-chat-current-changed", {
                detail: { id }
            })
        );
    }

    function getConversation(id) {
        return readConversations().find(item => item.id === id) || null;
    }

    function getCurrentConversation() {
        const id = getCurrentId();
        return id ? getConversation(id) : null;
    }

    function ensureCurrentConversation() {
        return getCurrentConversation() || createConversation();
    }

    function updateConversation(id, updater) {
        const conversations = readConversations();
        const index = conversations.findIndex(item => item.id === id);

        if (index === -1) return null;

        const conversation = conversations[index];

        updater(conversation);

        conversation.updatedAt = new Date().toISOString();

        conversations.splice(index, 1);
        conversations.unshift(conversation);

        writeConversations(conversations);

        return conversation;
    }

    function addMessage(id, message) {
        return updateConversation(id, conversation => {
            conversation.messages.push({
                role: message.role,
                content: message.content,
                sources: message.sources || [],
                sufficient: message.sufficient,
                createdAt: new Date().toISOString()
            });

            if (
                conversation.title === "Cuộc trò chuyện mới" &&
                message.role === "user"
            ) {
                conversation.title =
                    message.content.length > 42
                        ? message.content.slice(0, 42) + "..."
                        : message.content;
            }
        });
    }

    function deleteConversation(id) {
        const conversations = readConversations().filter(
            item => item.id !== id
        );

        writeConversations(conversations);

        if (getCurrentId() === id) {
            if (conversations.length) {
                setCurrentId(conversations[0].id);
            } else {
                localStorage.removeItem(CURRENT_KEY);
            }
        }
    }

    function clearAll() {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(CURRENT_KEY);

        window.dispatchEvent(
            new CustomEvent("tay-son-chat-updated")
        );
    }

    async function ask(question) {
        if (!window.ApiClient) {
            throw new Error("Không tìm thấy ApiClient. Kiểm tra api.js.");
        }

        const data = await ApiClient.post("/api/v1/chat", {
            query: question,
            vector_top_k: 5,
            graph_top_k: 5
        });

        const answer =
            data?.answer ??
            data?.response ??
            data?.message ??
            "";

        if (!answer) {
            throw new Error("Backend chưa trả về nội dung câu trả lời.");
        }

        return {
            answer: typeof answer === "string"
                ? answer
                : String(answer),
            sources:
                data?.sources ??
                data?.source_documents ??
                data?.metadata?.sources ??
                [],
            sufficient:
                data?.has_sufficient_context ??
                data?.metadata?.has_sufficient_context
        };
    }

    window.TaySonChat = {
        readConversations,
        createConversation,
        getCurrentId,
        setCurrentId,
        getConversation,
        getCurrentConversation,
        ensureCurrentConversation,
        updateConversation,
        addMessage,
        deleteConversation,
        clearAll,
        ask
    };
})();
