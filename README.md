# Histolab TikTok Shop Dashboard — giữ biểu đồ cũ + bổ sung KPI mục tiêu

`app.py` giữ các biểu đồ và phân tích hiện có, đồng thời bổ sung mục 6 KPI mục tiêu:
- Tuần đầu tháng 7/2026 (01–05/07): bình quân ngày tháng 6 × 5 × 1,10.
- Tháng 7/2026: thực tế tháng 6 × 1,10.
- Quý III/2026 (07–09): tổng thực tế tháng 4–6 × 1,10.
Các chỉ tiêu áp dụng: GMV, Orders, Customers, Items sold, nếu cột có trong file.

## Triển khai
Thay `app.py` trên GitHub bằng file này rồi Commit changes; Streamlit Cloud sẽ deploy lại. Không thay `requirements.txt`.
Dữ liệu tải lên từ sidebar; không cần đưa file Excel doanh nghiệp lên GitHub.

## Phương pháp
Dữ liệu lịch sử kết thúc 30/06/2026. Các mức tăng 10% là mục tiêu kế hoạch dựa trên kỳ tham chiếu gần nhất, không phải so sánh YoY chính thức hoặc dự báo thống kê.
