let danh_sach_don_hang = [];
let chi_tiet_dang_xem = null;
const cac_don_dang_thanh_toan = new Set();

const ten_trang_thai = {
    pending: "Chờ xử lý",
    preparing: "Đang pha chế",
    completed: "Hoàn thành",
    cancelled: "Đã hủy"
};

const ten_phuong_thuc_thanh_toan = {
    cash: "Tiền mặt",
    transfer: "Chuyển khoản"
};

const dinh_dang_gio_don_hang = new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Asia/Ho_Chi_Minh"
});

function dinhDangGioDonHang(gia_tri) {
    if (!gia_tri) return "—";
    const thoi_diem = Date.parse(gia_tri + "Z");
    return Number.isNaN(thoi_diem) ? gia_tri : dinh_dang_gio_don_hang.format(thoi_diem);
}

function datLaiLichSuDonHang() {
    danh_sach_don_hang = [];
    document.querySelector("#danh_sach_don_hang").innerHTML = "";
    dongChiTietDonHang();
}

async function taiDonHang() {
    const token_hien_tai = token;

    try {
        const danh_sach = await goiAPI("/orders");
        if (token !== token_hien_tai) return;

        danh_sach_don_hang = danh_sach;
        hienThiDonHang();
    } catch (loi) {
        if (token === token_hien_tai) hienThongBao(loi.message, true);
    }
}

function hienThiDonHang() {
    const trang_thai = document.querySelector("#loc_trang_thai").value;
    const thanh_toan = document.querySelector("#loc_thanh_toan").value;
    const danh_sach = danh_sach_don_hang.filter(don =>
        (!trang_thai || don.trang_thai === trang_thai) &&
        (!thanh_toan || don.trang_thai_thanh_toan === thanh_toan)
    );

    document.querySelector("#danh_sach_don_hang").innerHTML =
        danh_sach.map(don => {
            const da_thanh_toan = don.trang_thai_thanh_toan === "paid";
            let nut_thao_tac = "";

            if (!da_thanh_toan && don.trang_thai !== "cancelled") {
                nut_thao_tac += `
                    <button type="button" onclick="thanhToanDonHang(${don.ma})"
                            ${cac_don_dang_thanh_toan.has(don.ma) ? "disabled" : ""}>
                        Thanh toán
                    </button>
                `;
            }

            if (don.trang_thai === "pending") {
                nut_thao_tac += `
                    <button type="button" onclick="capNhatTrangThai(${don.ma}, 'preparing')">
                        Pha chế
                    </button>
                `;
            }

            if (don.trang_thai === "preparing") {
                nut_thao_tac += `
                    <button type="button" onclick="capNhatTrangThai(${don.ma}, 'completed')">
                        Hoàn thành
                    </button>
                `;
            }

            if (!da_thanh_toan && ["pending", "preparing"].includes(don.trang_thai)) {
                nut_thao_tac += `
                    <button type="button" class="nut_xoa"
                            onclick="capNhatTrangThai(${don.ma}, 'cancelled')">
                        Hủy đơn
                    </button>
                `;
            }

            return `
                <tr>
                    <td>#${don.ma}</td>
                    <td>${anToan(ten_trang_thai[don.trang_thai] || don.trang_thai)}</td>
                    <td>${dinhDangTien(don.tong_tien)}</td>
                    <td>${da_thanh_toan ? "Đã thanh toán" : "Chưa thanh toán"}</td>
                    <td>${anToan(dinhDangGioDonHang(don.ngay_tao))}</td>
                    <td>
                        ${nut_thao_tac}
                        <button type="button" onclick="xemChiTietDonHang(${don.ma})">Chi tiết</button>
                    </td>
                </tr>
            `;
        }).join("") ||
        '<tr><td colspan="6">Không có đơn hàng phù hợp</td></tr>';
}

async function thanhToanDonHang(ma) {
    const don = danh_sach_don_hang.find(don => don.ma === ma);
    if (!don || don.trang_thai === "cancelled" ||
            don.trang_thai_thanh_toan === "paid" || cac_don_dang_thanh_toan.has(ma)) return;

    const phuong_thuc = prompt(
        "Nhập phương thức thanh toán\n" +
        "cash = Tiền mặt\n" +
        "transfer = Chuyển khoản"
    );
    if (phuong_thuc === null) return;
    if (phuong_thuc !== "cash" && phuong_thuc !== "transfer") {
        hienThongBao("Phương thức thanh toán không hợp lệ.", true);
        return;
    }
    if (!confirm("Bạn xác nhận đã nhận đủ tiền cho đơn #" + ma + "?")) return;

    const token_hien_tai = token;
    cac_don_dang_thanh_toan.add(ma);
    hienThiDonHang();

    try {
        const ket_qua = await goiAPI("/orders/" + ma + "/payment", {
            method: "PATCH",
            body: JSON.stringify({ phuong_thuc })
        });
        if (token !== token_hien_tai) return;

        hienThongBao(
            "Thanh toán đơn #" + ma + " thành công: " + dinhDangTien(ket_qua.tong_tien)
        );
        await taiDonHang();
        if (token !== token_hien_tai) return;
        if (chi_tiet_dang_xem?.ma === ma) await xemChiTietDonHang(ma, false);
        if (token === token_hien_tai && vai_tro === "admin") await taiThongKe();
    } catch (loi) {
        if (token === token_hien_tai) hienThongBao(loi.message, true);
    } finally {
        cac_don_dang_thanh_toan.delete(ma);
        if (token) hienThiDonHang();
    }
}

async function xemChiTietDonHang(ma, cuon_den_chi_tiet = true) {
    chi_tiet_dang_xem?.yeu_cau.abort();
    const yeu_cau = new AbortController();
    chi_tiet_dang_xem = { ma, yeu_cau };

    const khung = document.querySelector("#chi_tiet_don_hang");
    const nut_dong = '<button type="button" class="nut_huy" onclick="dongChiTietDonHang()">Đóng</button>';
    khung.innerHTML = '<p role="status">Đang tải chi tiết đơn hàng…</p>' + nut_dong;
    if (cuon_den_chi_tiet) khung.scrollIntoView({ block: "nearest" });

    try {
        const don = await goiAPI("/orders/" + ma, { signal: yeu_cau.signal });
        if (chi_tiet_dang_xem?.yeu_cau !== yeu_cau) return;

        const danh_sach = don.chi_tiet.map(dong => `
            <tr>
                <td>${anToan(dong.ten)}</td>
                <td>${dong.so_luong}</td>
                <td>${dong.phan_tram_duong}%</td>
                <td>${anToan(ten_muc_da[dong.muc_da] || dong.muc_da)}</td>
                <td>${dinhDangTien(dong.don_gia)}</td>
                <td>${dinhDangTien(dong.thanh_tien)}</td>
                <td>${anToan(dong.ghi_chu || "")}</td>
            </tr>
        `).join("") || '<tr><td colspan="7">Không có chi tiết đồ uống</td></tr>';

        khung.innerHTML = `
            <h3>Chi tiết đơn hàng #${don.ma}</h3>
            <p>Trạng thái xử lý: ${anToan(ten_trang_thai[don.trang_thai] || don.trang_thai)}</p>
            <p>Ngày tạo: ${anToan(dinhDangGioDonHang(don.ngay_tao))}</p>
            <div class="bang_cuon">
                <table>
                    <thead>
                        <tr>
                            <th scope="col">Đồ uống</th>
                            <th scope="col">Số lượng</th>
                            <th scope="col">Đường</th>
                            <th scope="col">Đá</th>
                            <th scope="col">Đơn giá</th>
                            <th scope="col">Thành tiền</th>
                            <th scope="col">Ghi chú</th>
                        </tr>
                    </thead>
                    <tbody>${danh_sach}</tbody>
                </table>
            </div>
            <h3>Tổng tiền: ${dinhDangTien(don.tong_tien)}</h3>
            <p>Thanh toán: ${don.trang_thai_thanh_toan === "paid" ? "Đã thanh toán" : "Chưa thanh toán"}</p>
            <p>Phương thức: ${ten_phuong_thuc_thanh_toan[don.phuong_thuc_thanh_toan] || "—"}</p>
            <p>Ngày thanh toán: ${anToan(dinhDangGioDonHang(don.ngay_thanh_toan))}</p>
            ${nut_dong}
        `;
    } catch (loi) {
        if (chi_tiet_dang_xem?.yeu_cau !== yeu_cau) return;

        dongChiTietDonHang();
        hienThongBao(loi.message, true);
    }
}

function dongChiTietDonHang() {
    chi_tiet_dang_xem?.yeu_cau.abort();
    chi_tiet_dang_xem = null;
    document.querySelector("#chi_tiet_don_hang").innerHTML = "";
}

async function capNhatTrangThai(ma, trang_thai) {
    const don = danh_sach_don_hang.find(don => don.ma === ma);
    if (trang_thai === "cancelled" && don?.trang_thai_thanh_toan === "paid") {
        hienThongBao("Đơn đã thanh toán, không thể hủy trực tiếp.", true);
        return;
    }

    const xac_nhan = confirm(
        "Xác nhận cập nhật đơn #" + ma +
        " thành: " + ten_trang_thai[trang_thai] + "?"
    );

    if (!xac_nhan) return;
    const token_hien_tai = token;

    try {
        await goiAPI("/orders/" + ma + "/status", {
            method: "PATCH",
            body: JSON.stringify({ trang_thai })
        });
        if (token !== token_hien_tai) return;

        await taiDonHang();
        if (token !== token_hien_tai) return;
        if (chi_tiet_dang_xem?.ma === ma) await xemChiTietDonHang(ma, false);
        if (token !== token_hien_tai) return;
        if (vai_tro === "admin") {
            await taiThongKe();
        }

        if (token === token_hien_tai) hienThongBao("Cập nhật trạng thái đơn hàng thành công.");

    } catch (loi) {
        if (token === token_hien_tai) hienThongBao(loi.message, true);
    }
}
