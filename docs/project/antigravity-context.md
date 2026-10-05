# Bối cảnh từ cuộc chat Antigravity “Cấu Hình Cài Đặt Font”

Nguồn: transcript cục bộ tại
`~/.gemini/antigravity-ide/brain/163e18d5-7473-4d58-ae61-93d45e140cab/.system_generated/logs/transcript.jsonl`.
Cuộc chat diễn ra từ 21/08 đến 25/09/2026. Đây là bản ghi nhớ các quyết định còn hữu ích; khi sửa code, kiểm tra mã nguồn hiện tại vì nhiều phương án trong chat đã bị thay thế.

## Cài font và Việt hóa

- Cập nhật Việt hóa chỉ tải/cài bản dịch `WuWaVH_99_P.pak` và `winhttp.dll`. Font được quản lý riêng trong tab **Font**; font mặc định chỉ tải khi người dùng chọn cài.
- Hỗ trợ TTF/OTF bằng cách đóng gói thành PAK trong `backend/wuwa_font_packer.py`, và hỗ trợ chọn PAK có sẵn để cài trực tiếp. Trước khi cài font mới, dọn font cũ để tránh xung đột.
- Dùng tên `zzz_CustomFont_99_P.pak` và `zzz_Default_font_99_P.pak` cho file font trong game. Tên `zzz_` được thêm sau khi người dùng báo font không hiển thị khi chạy qua Steam.
- **Không đặt font PAK trong `Client/Content/Paks/~mods`**. Cách nạp kép vào `~mods` từng được thử rồi bị người dùng báo gây crash; vị trí được chọn sau cùng là `Client/Binaries/Win64/wuwaVietHoa/`, thông qua `winhttp.dll`.
- Chức năng khôi phục font mặc định phải vô hiệu hóa font tùy chỉnh. Với AppImage, file PAK dùng làm nguồn/cache cần ở thư mục ghi được như `~/.config/wuwavh/paks/` khi bundle chỉ đọc.

## Các quyết định khác của launcher

- Hỗ trợ chọn Steam hoặc Heroic, ghi nhớ lựa chọn; hỗ trợ `WINEDLLOVERRIDES` để game nạp `winhttp.dll`. Trạng thái “Đang chơi” cần phản ánh tiến trình game thực tế, tránh nhận nhầm tiến trình zombie.
- Ba theme hiện tại là Classic, Modern và Cyber. CSS theme nằm riêng trong `frontend/themes/`; chức năng và vùng bấm phải nhất quán giữa các theme. Tab Font, Hiệu năng và Theme phải hiển thị đầy đủ ở mỗi theme.
- Người dùng chú ý nhiều đến RAM/GPU và video nền. Video cần loop mượt, không nháy đen, và launcher không được giật khi máy có tải GPU khác. Tránh thêm hiệu ứng nặng nếu không đo được lợi ích.
- Tính năng Hiệu năng chỉnh `Engine.ini` theo preset và tùy chỉnh sâu, cần backup và nút khôi phục. Các preset sau đó được chuyển sang nguồn AlteriaX/WuWa-Configs.
- Bản AppImage cần hoạt động khi nội dung bundle chỉ đọc; dữ liệu tải về, font và cấu hình phải dùng vị trí ghi được. Người dùng từng yêu cầu giữ giao diện và tính năng hiện có khi tối ưu.

## Cách dùng ghi nhớ này

Transcript có nhiều thử nghiệm đã bị đảo lại. Ưu tiên yêu cầu mới nhất của người dùng và hành vi trong code hiện tại; dùng các mục trên làm bối cảnh, không coi các lời khẳng định hoàn tất trong chat cũ là kết quả kiểm thử.
