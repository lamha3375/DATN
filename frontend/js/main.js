document.addEventListener("DOMContentLoaded", () => {
  const searchForm = document.getElementById("siteSearch");
  const searchInput = document.getElementById("searchInput");
  const searchMessage = document.getElementById("searchMessage");

  if (searchForm && searchInput && searchMessage) {
    searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const keyword = searchInput.value.trim();

      if (!keyword) {
        searchMessage.textContent = "Hãy nhập tên nhân vật, sự kiện hoặc địa danh bạn muốn tìm.";
        searchInput.focus();
        return;
      }

      // Chưa điều hướng tới trang kết quả vì cần chốt Search API thực tế của backend.
      searchMessage.textContent = `Từ khóa “${keyword}” đã được ghi nhận. Chức năng tìm kiếm sẽ được kết nối với FastAPI ở bước tiếp theo.`;
    });
  }
});
