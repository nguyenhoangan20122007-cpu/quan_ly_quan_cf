let gio_hang = [];
let san_pham_dang_chon = null;
let dang_gui_don = false;

const ten_muc_da = {
    none: "Không đá",
    less: "Ít đá",
    normal: "Bình thường",
    more: "Nhiều đá"
};

function datLaiTaoDonHang() {
    gio_hang = [];
    dongTuyChinh();
    hienThiGioHang();
}

function chonSanPham(ma) {
    san_pham_dang_chon = danh_sach_san_pham.find(
        sp => sp.ma === ma
    );

    if (!san_pham_dang_chon) return;

    document.querySelector("#san_pham_dang_chon").textContent =
        san_pham_dang_chon.ten + " - " +
        dinhDangTien(san_pham_dang_chon.gia);

    document.querySelector("#so_luong").value = 1;
    document.querySelector("#phan_tram_duong").value = 100;
    document.querySelector("#muc_da").value = "normal";
    document.querySelector("#ghi_chu").value = "";

    document.querySelector("#khung_tuy_chinh").classList.remove("an");

    document.querySelector("#khung_tuy_chinh")
        .scrollIntoView({ behavior: "smooth" });
}

function dongTuyChinh() {
    san_pham_dang_chon = null;
    document.querySelector("#khung_tuy_chinh").classList.add("an");
}

function themVaoGio() {
    if (!san_pham_dang_chon) return;

    const so_luong = Number(document.querySelector("#so_luong").value);

    if (!Number.isInteger(so_luong) || so_luong < 1) {
        hienThongBao("Số lượng phải lớn hơn hoặc bằng 1.", true);
        return;
    }

    gio_hang.push({
        ma_san_pham: san_pham_dang_chon.ma,
        ten: san_pham_dang_chon.ten,
        gia: Number(san_pham_dang_chon.gia),
        so_luong,
        phan_tram_duong: Number(
            document.querySelector("#phan_tram_duong").value
        ),
        muc_da: document.querySelector("#muc_da").value,
        ghi_chu: document.querySelector("#ghi_chu").value.trim() || null
    });

    dongTuyChinh();
    hienThiGioHang();
    hienThongBao("Đã thêm sản phẩm vào giỏ hàng.");
}

function hienThiGioHang() {
    document.querySelector("#danh_sach_gio_hang").innerHTML =
        gio_hang.map((dong, vi_tri) => `
            <tr>
                <td>
                    ${anToan(dong.ten)}
                    ${dong.ghi_chu
                        ? `<br><small>${anToan(dong.ghi_chu)}</small>`
                        : ""}
                </td>
                <td>${dong.so_luong}</td>
                <td>${dong.phan_tram_duong}%</td>
                <td>${ten_muc_da[dong.muc_da]}</td>
                <td>${dinhDangTien(dong.gia * dong.so_luong)}</td>
                <td>
                    <button class="nut_xoa"
                            onclick="xoaKhoiGio(${vi_tri})">
                        Xóa
                    </button>
                </td>
            </tr>
        `).join("") ||
        '<tr><td colspan="6">Giỏ hàng đang trống</td></tr>';

    const tong_tien = gio_hang.reduce(
        (tong, dong) => tong + dong.gia * dong.so_luong,
        0
    );

    document.querySelector("#tong_tien").textContent =
        "Tổng tiền: " + dinhDangTien(tong_tien);
}

function xoaKhoiGio(vi_tri) {
    gio_hang.splice(vi_tri, 1);
    hienThiGioHang();
}

async function taoDonHang() {
    if (dang_gui_don) return;

    if (gio_hang.length === 0) {
        hienThongBao("Giỏ hàng đang trống.", true);
        return;
    }

    const ma_khach_hang = document.querySelector("#chon_khach_hang").value;
    const du_lieu = {
        ma_khach_hang: ma_khach_hang ? Number(ma_khach_hang) : null,
        chi_tiet: gio_hang.map(dong => ({
            ma_san_pham: dong.ma_san_pham,
            so_luong: dong.so_luong,
            phan_tram_duong: dong.phan_tram_duong,
            muc_da: dong.muc_da,
            ghi_chu: dong.ghi_chu
        }))
    };

    dang_gui_don = true;
    document.querySelector("#nut_tao_don").disabled = true;

    try {
        const ket_qua = await goiAPI("/orders", {
            method: "POST",
            body: JSON.stringify(du_lieu)
        });

        gio_hang = [];
        hienThiGioHang();
        document.querySelector("#chon_khach_hang").value = "";

        hienThongBao(
            "Tạo đơn hàng #" + ket_qua.ma +
            " thành công. Tổng tiền: " +
            dinhDangTien(ket_qua.tong_tien)
        );

        await taiDonHang();

        if (vai_tro === "admin") {
            await taiThongKe();
        }

    } catch (loi) {
        hienThongBao(loi.message, true);
    } finally {
        dang_gui_don = false;
        document.querySelector("#nut_tao_don").disabled = false;
    }
}
