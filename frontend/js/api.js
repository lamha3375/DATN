
// API Client dùng chung cho toàn bộ Frontend

window.ApiClient = {

  baseUrl:
    window.APP_CONFIG?.API_BASE_URL ||
    "http://127.0.0.1:8000",

  async request(path, options = {}) {

    const url = `${this.baseUrl}${path}`;

    try {

      const response = await fetch(url, {
        ...options,

        headers: {
          ...(options.body !== undefined
            ? { "Content-Type": "application/json" }
            : {}),

          ...(options.headers || {})
        }
      });

      // Đọc response
      const contentType =
        response.headers.get("content-type") || "";

      const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

      // Xử lý HTTP error
      if (!response.ok) {

        const message =
          typeof data === "object" && data !== null
            ? data.detail || data.message || JSON.stringify(data)
            : data || response.statusText;

        throw new Error(
          `API Error (${response.status}): ${message}`
        );
      }

      return data;

    } catch (error) {

      if (error instanceof TypeError) {
        throw new Error(
          "Không thể kết nối Backend. Vui lòng kiểm tra FastAPI."
        );
      }

      throw error;
    }
  },

  // GET request
  get(path, params = {}) {

    const query = new URLSearchParams(params).toString();

    const url = query
      ? `${path}?${query}`
      : path;

    return this.request(url, {
      method: "GET"
    });
  },

  // POST request
  post(path, body) {

    return this.request(path, {
      method: "POST",
      body: JSON.stringify(body)
    });
  }
};
