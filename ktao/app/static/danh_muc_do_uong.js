let danh_sach_danh_muc = [];
let danh_sach_san_pham = [];

function datLaiDanhMucDoUong() {
    danh_sach_danh_muc = [];
    danh_sach_san_pham = [];
    document.querySelector("#danh_sach_danh_muc").innerHTML = "";
    document.querySelector("#tim_danh_muc").value = "";
    huySuaDanhMuc();
    document.querySelector("#danh_sach_san_pham").innerHTML = "";
}

async function taiDuLieu() {
    try {
        danh_sach_danh_muc = await goiAPI("/categories");
        danh_sach_san_pham = await goiAPI("/products");

        const danh_muc_san_pham = document.querySelector("#danh_muc_san_pham");
        const gia_tri_danh_muc = danh_muc_san_pham.value;
        const tuy_chon_danh_muc = danh_sach_danh_muc.map(
            muc => `<option value="${muc.ma}">${anToan(muc.ten)}</option>`
        ).join("");
        danh_muc_san_pham.innerHTML =
            '<option value="">Chọn danh mục</option>' +
            tuy_chon_danh_muc;
        danh_muc_san_pham.value = gia_tri_danh_muc;
        if (!danh_muc_san_pham.value) danh_muc_san_pham.value = "";

        const loc_danh_muc = document.querySelector("#loc_danh_muc");
        const gia_tri_loc = loc_danh_muc.value;
        loc_danh_muc.innerHTML = '<option value="">Tất cả danh mục</option>' +
            tuy_chon_danh_muc;
        loc_danh_muc.value = gia_tri_loc;
        if (!loc_danh_muc.value) loc_danh_muc.value = "";
        hienThiDanhMuc();
        hienThiSanPham();

    } catch (loi) {
        hienThongBao(loi.message, true);
    }

}

function hienThiDanhMuc() {
    const tu_khoa = document.querySelector("#tim_danh_muc").value.trim().toLowerCase();
    const danh_sach = danh_sach_danh_muc.filter(muc =>
        muc.ten.toLowerCase().includes(tu_khoa)
    );

    document.querySelector("#danh_sach_danh_muc").innerHTML =
        danh_sach.map(muc => {
            const so_do_uong = danh_sach_san_pham.filter(sp => sp.ma_danh_muc === muc.ma).length;
            const dang_hoat_dong = muc.trang_thai === "active";

            return `
                <tr>
                    <td>${muc.ma}</td>
                    <td>${anToan(muc.ten)}</td>
                    <td>${so_do_uong}</td>
                    <td>${dang_hoat_dong ? "Đang hoạt động" : "Ngừng hoạt động"}</td>
                    <td>
                        ${vai_tro === "admin" ? `
                            <button type="button" class="nut_sua" onclick="batDauSuaDanhMuc(${muc.ma})">Sửa</button>
                            <button type="button" class="nut_xoa" onclick="xoaDanhMuc(${muc.ma})">Xóa</button>
                            <button type="button" onclick="doiTrangThaiDanhMuc(${muc.ma}, '${dang_hoat_dong ? "active" : "inactive"}')">
                                ${dang_hoat_dong ? "Tạm ẩn" : "Kích hoạt"}
                            </button>
                        ` : "Chỉ xem"}
                    </td>
                </tr>
            `;
        }).join("") || '<tr><td colspan="5">Không tìm thấy danh mục</td></tr>';
}

function batDauSuaDanhMuc(ma) {
    if (vai_tro !== "admin") return;

    const danh_muc = danh_sach_danh_muc.find(muc => muc.ma === ma);
    if (!danh_muc) {
        hienThongBao("Không tìm thấy danh mục.", true);
        return;
    }

    const khung = document.querySelector("#khung_them_danh_muc");
    khung.classList.remove("an");
    document.querySelector("#ma_danh_muc_sua").value = danh_muc.ma;
    document.querySelector("#ten_danh_muc").value = danh_muc.ten;
    document.querySelector("#tieu_de_danh_muc").textContent = "Sửa danh mục";
    document.querySelector("#nut_luu_danh_muc").textContent = "Lưu thay đổi";
    khung.scrollIntoView();
}

function huySuaDanhMuc() {
    document.querySelector("#ma_danh_muc_sua").value = "";
    document.querySelector("#ten_danh_muc").value = "";
    document.querySelector("#tieu_de_danh_muc").textContent = "Thêm danh mục";
    document.querySelector("#nut_luu_danh_muc").textContent = "Thêm danh mục";
}

async function themDanhMuc() {
    if (vai_tro !== "admin") return;

    const nut_luu = document.querySelector("#nut_luu_danh_muc");
    if (nut_luu.disabled) return;

    const ma = document.querySelector("#ma_danh_muc_sua").value;
    const ten = document.querySelector("#ten_danh_muc").value.trim();

    if (!ten) {
        hienThongBao("Vui lòng nhập tên danh mục.", true);
        return;
    }

    nut_luu.disabled = true;
    try {
        await goiAPI(ma ? "/categories/" + ma : "/categories", {
            method: ma ? "PUT" : "POST",
            body: JSON.stringify({ ten })
        });

        huySuaDanhMuc();
        await taiDuLieu();
        hienThongBao(ma ? "Sửa danh mục thành công." : "Thêm danh mục thành công.");

    } catch (loi) {
        hienThongBao(loi.message, true);
    } finally {
        nut_luu.disabled = false;
    }
}

async function xoaDanhMuc(ma) {
    if (vai_tro !== "admin") return;

    const danh_muc = danh_sach_danh_muc.find(muc => muc.ma === ma);
    if (!danh_muc) {
        hienThongBao("Không tìm thấy danh mục.", true);
        return;
    }

    const so_do_uong = danh_sach_san_pham.filter(sp => sp.ma_danh_muc === ma).length;
    if (so_do_uong > 0) {
        hienThongBao("Danh mục đang có " + so_do_uong + " đồ uống. Không thể xóa.", true);
        return;
    }

    if (!confirm("Bạn có chắc muốn xóa danh mục " + danh_muc.ten + "?")) return;

    try {
        await goiAPI("/categories/" + ma, { method: "DELETE" });

        if (document.querySelector("#ma_danh_muc_sua").value === String(ma)) {
            huySuaDanhMuc();
        }

        await taiDuLieu();
        hienThongBao("Xóa danh mục thành công.");
    } catch (loi) {
        hienThongBao(loi.message, true);
    }
}

async function doiTrangThaiDanhMuc(ma, trang_thai_hien_tai) {
    if (vai_tro !== "admin") return;

    const trang_thai_moi =
        trang_thai_hien_tai === "active" ? "inactive" : "active";

    const xac_nhan = confirm(
        trang_thai_moi === "inactive"
            ? "Bạn có chắc muốn tạm ẩn danh mục này?"
            : "Bạn muốn kích hoạt lại danh mục này?"
    );

    if (!xac_nhan) return;

    try {
        await goiAPI("/categories/" + ma + "/status", {
            method: "PATCH",
            body: JSON.stringify({
                trang_thai: trang_thai_moi
            })
        });

        await taiDuLieu();

        hienThongBao("Cập nhật trạng thái danh mục thành công.");
    } catch (loi) {
        hienThongBao(loi.message, true);
    }
}

function batDauSuaSanPham(ma) {
    if (vai_tro !== "admin") return;

    const sp = danh_sach_san_pham.find(sp => sp.ma === ma);

    if (!sp) return;

    document.querySelector("#ma_san_pham_sua").value = sp.ma;
    document.querySelector("#ten_san_pham").value = sp.ten;
    document.querySelector("#danh_muc_san_pham").value = sp.ma_danh_muc;
    document.querySelector("#gia_san_pham").value = sp.gia;
    document.querySelector("#mo_ta_san_pham").value = sp.mo_ta || "";
    document.querySelector("#hinh_anh_san_pham").value = sp.hinh_anh || "";

    document.querySelector("#tieu_de_form_san_pham").textContent =
        "Sửa sản phẩm #" + sp.ma;

    document.querySelector("#nut_luu_san_pham").textContent =
        "Lưu thay đổi";

    document.querySelector("#khung_san_pham_admin")
        .scrollIntoView({ behavior: "smooth" });
}

function huySuaSanPham() {
    document.querySelector("#bieu_mau_san_pham").reset();
    document.querySelector("#ma_san_pham_sua").value = "";

    document.querySelector("#tieu_de_form_san_pham").textContent =
        "Thêm sản phẩm";

    document.querySelector("#nut_luu_san_pham").textContent =
        "Thêm sản phẩm";
}

async function luuSanPham(su_kien) {
    su_kien.preventDefault();

    if (vai_tro !== "admin") return;

    const ma = document.querySelector("#ma_san_pham_sua").value;

    const du_lieu = {
        ma_danh_muc: Number(
            document.querySelector("#danh_muc_san_pham").value
        ),
        ten: document.querySelector("#ten_san_pham").value.trim(),
        gia: Number(document.querySelector("#gia_san_pham").value),
        mo_ta: document.querySelector("#mo_ta_san_pham").value.trim() || null,
        hinh_anh: document.querySelector("#hinh_anh_san_pham").value.trim() || null
    };

    try {
        await goiAPI(
            ma ? "/products/" + ma : "/products",
            {
                method: ma ? "PUT" : "POST",
                body: JSON.stringify(du_lieu)
            }
        );

        huySuaSanPham();
        await taiDuLieu();

        if (vai_tro === "admin") {
            await taiThongKe();
        }

        hienThongBao(
            ma ? "Sửa sản phẩm thành công." : "Thêm sản phẩm thành công."
        );

    } catch (loi) {
        hienThongBao(loi.message, true);
    }
}

async function xoaSanPham(ma) {
    if (vai_tro !== "admin") return;

    const xac_nhan = confirm(
        "Bạn có chắc muốn xóa sản phẩm #" + ma + "?"
    );

    if (!xac_nhan) return;

    try {
        await goiAPI("/products/" + ma, {
            method: "DELETE"
        });

        await taiDuLieu();
        await taiThongKe();

        hienThongBao("Xóa sản phẩm thành công.");

    } catch (loi) {
        hienThongBao(loi.message, true);
    }
}

async function doiTrangThaiSanPham(ma, trang_thai_hien_tai) {
    if (vai_tro !== "admin") return;

    const trang_thai_moi =
        trang_thai_hien_tai === "available" ? "unavailable" : "available";

    const xac_nhan = confirm(
        trang_thai_moi === "unavailable"
            ? "Bạn có chắc muốn ngừng bán đồ uống này?"
            : "Bạn muốn mở bán lại đồ uống này?"
    );

    if (!xac_nhan) return;

    try {
        await goiAPI("/products/" + ma + "/status", {
            method: "PATCH",
            body: JSON.stringify({
                trang_thai: trang_thai_moi
            })
        });

        await taiDuLieu();

        hienThongBao("Cập nhật trạng thái đồ uống thành công.");
    } catch (loi) {
        hienThongBao(loi.message, true);
    }
}

function hienThiSanPham() {
    const tu_khoa = document.querySelector("#tim_san_pham")
        .value.toLowerCase().trim();

    const ma_danh_muc = document.querySelector("#loc_danh_muc").value;

    const danh_sach_loc = danh_sach_san_pham.filter(sp => {
        const dung_ten = sp.ten.toLowerCase().includes(tu_khoa);

        const dung_danh_muc =
            !ma_danh_muc ||
            sp.ma_danh_muc === Number(ma_danh_muc);

        return dung_ten && dung_danh_muc;
    });

    document.querySelector("#danh_sach_san_pham").innerHTML =
        danh_sach_loc.map(sp => `
            <div class="san_pham">
                ${sp.hinh_anh ? `
                    <img
                        src="${anToan(sp.hinh_anh)}"
                        alt="${anToan(sp.ten)}"
                        class="anh_do_uong"
                        onerror="this.hidden = true; this.nextElementSibling.classList.remove('an')"
                    >
                ` : ""}
                <div class="anh_mac_dinh${sp.hinh_anh ? " an" : ""}" aria-hidden="true">☕</div>

                <h3>${anToan(sp.ten)}</h3>

                <p>${anToan(sp.mo_ta || "Đồ uống tại quán")}</p>

                <p class="gia">${dinhDangTien(sp.gia)}</p>

                <p>${sp.trang_thai === "available" ? "🟢 Đang bán" : "🔴 Ngừng bán"}</p>

                ${sp.trang_thai === "available" && sp.trang_thai_danh_muc === "active" ? `
                    <button onclick="chonSanPham(${sp.ma})">
                        Chọn món
                    </button>
                ` : `
                    <button disabled style="background:#999;cursor:not-allowed">
                        Không thể đặt
                    </button>
                `}

                ${vai_tro === "admin" ? `
                    <button class="nut_sua"
                            onclick="batDauSuaSanPham(${sp.ma})">
                        Sửa
                    </button>

                    <button onclick="doiTrangThaiSanPham(${sp.ma}, '${sp.trang_thai === "available" ? "available" : "unavailable"}')">
                        ${sp.trang_thai === "available" ? "Ngừng bán" : "Mở bán"}
                    </button>

                    <button class="nut_xoa"
                            onclick="xoaSanPham(${sp.ma})">
                        Xóa
                    </button>
                ` : ""}
            </div>
        `).join("") || "<p>Không tìm thấy sản phẩm</p>";
}

document.querySelector("#bieu_mau_san_pham")
    .addEventListener("submit", luuSanPham);
