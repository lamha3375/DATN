
// API Client dùng chung cho toàn bộ Frontend

window.ApiClient = {
  baseUrl: (
    window.APP_CONFIG?.API_BASE_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/+$/, ""),

  async request(path, options = {}) {
    const normalizedPath = path.startsWith("/")
      ? path
      : `/${path}`;

    const url = `${this.baseUrl}${normalizedPath}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          Accept: "application/json",

          ...(options.body !== undefined
            ? { "Content-Type": "application/json" }
            : {}),

          ...(options.headers || {})
        }
      });

      const contentType =
        response.headers.get("content-type") || "";

      const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

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

  get(path, params = {}) {
    const [pathname, existingQuery = ""] = path.split("?");

    const queryParams = new URLSearchParams(existingQuery);

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.set(key, value);
      }
    });

    const query = queryParams.toString();

    return this.request(
      query ? `${pathname}?${query}` : pathname,
      { method: "GET" }
    );
  },

  post(path, body) {
    return this.request(path, {
      method: "POST",
      body: JSON.stringify(body)
    });
  }
};
