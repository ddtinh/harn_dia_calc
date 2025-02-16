import random 
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import tkinter as tk
from tkinter import filedialog, scrolledtext

# Biến toàn cục lưu file đã chọn
selected_file_path = None

# ======== HÀM CẬP NHẬT LOG ==========
def update_log(message):
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, message + "\n")
    log_text.config(state=tk.DISABLED)
    log_text.see(tk.END)

# ======== HÀM XÓA LOG ==========
def clear_log():
    log_text.config(state=tk.NORMAL)
    log_text.delete("1.0", tk.END)
    log_text.config(state=tk.DISABLED)

# ======== HÀM CHỌN FILE CSV/EXCEL ==========
def select_file():
    global selected_file_path
    file_path = filedialog.askopenfilename(
        title="Chọn file dữ liệu",
        filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xls;*.xlsx")]
    )
    
    if not file_path:
        update_log("⚠ Bạn chưa chọn file!")
        return
    
    selected_file_path = file_path
    update_log(f"📂 File được chọn: {file_path}")

# ======== HÀM CHẠY CHƯƠNG TRÌNH ==========
def run_program():
    if not selected_file_path:
        update_log("⚠ Bạn chưa chọn file!")
        return
    process_file(selected_file_path)

# ======== HÀM ĐỌC FILE & XỬ LÝ DỮ LIỆU ==========
def process_file(file_path):
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path, sep=';')  
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            update_log("❌ File không hợp lệ! Vui lòng chọn CSV hoặc Excel.")
            return
    except Exception as e:
        update_log(f"❌ Lỗi đọc file: {e}")
        return

    # Hiển thị danh sách cột
    columns = df.columns.tolist()
    update_log(f"📊 Danh sách cột: {columns}")

    if len(columns) < 2:
        update_log("❌ LỖI: File dữ liệu phải có ít nhất 2 cột!")
        return

    col_quantity = columns[0]
    col_diameter = columns[1]

    diameters = []
    for idx, row in df.iterrows():
        try:
            count = int(row[col_quantity])
            d = float(row[col_diameter])
            for _ in range(count):
                diameters.append(d)
        except Exception as e:
            update_log(f"⚠ Lỗi dòng {idx+2}: {e}")

    if not diameters:
        update_log("❌ Không có dữ liệu hợp lệ trong file!")
        return

    radii = [d / 2.0 for d in diameters]
    update_log(f"🔢 Tổng số hình tròn: {len(radii)}")

    # Lấy giá trị max_iter và tol từ giao diện
    try:
        max_iter_value = int(entry_max_iter.get())
    except ValueError:
        update_log("❌ Giá trị max_iter không hợp lệ!")
        return

    try:
        tol_value = float(entry_tol.get())
    except ValueError:
        update_log("❌ Giá trị tol không hợp lệ!")
        return

    container_radius, positions = binary_search_packing(radii, max_iter=max_iter_value, tol=tol_value)
    
    if positions is None:
        update_log("❌ Không tìm được cách sắp xếp hợp lệ!")
        return

    update_log(f"📏 Bán kính hình tròn chứa tối ưu: {container_radius:.2f}")
    update_log(f"📏 Đường kính hình tròn chứa tối ưu: {2 * container_radius:.2f}")

    plot_packing(container_radius, radii, positions)

# ======== HÀM SẮP XẾP HÌNH TRÒN ==========
def relax_positions(R, radii, max_iter=5000, tol=1e-5):
    n = len(radii)
    positions = []
    for i in range(n):
        max_r = R - radii[i]
        r_pos = random.uniform(0, max_r)
        theta = random.uniform(0, 2 * math.pi)
        x = r_pos * math.cos(theta)
        y = r_pos * math.sin(theta)
        positions.append([x, y])

    for it in range(max_iter):
        max_disp = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                dx = positions[j][0] - positions[i][0]
                dy = positions[j][1] - positions[i][1]
                dist = math.hypot(dx, dy)
                desired = radii[i] + radii[j]
                if dist < desired:
                    overlap = desired - dist
                    if dist == 0:
                        angle = random.uniform(0, 2 * math.pi)
                        dx = math.cos(angle)
                        dy = math.sin(angle)
                        dist = 1e-6
                    dx_norm = dx / dist
                    dy_norm = dy / dist
                    shift = overlap / 2.0
                    positions[i][0] -= shift * dx_norm
                    positions[i][1] -= shift * dy_norm
                    positions[j][0] += shift * dx_norm
                    positions[j][1] += shift * dy_norm
                    max_disp = max(max_disp, shift)

        for i in range(n):
            x, y = positions[i]
            dist_center = math.hypot(x, y)
            if dist_center + radii[i] > R:
                excess = (dist_center + radii[i]) - R
                if dist_center == 0:
                    angle = random.uniform(0, 2 * math.pi)
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    dist_center = 1e-6
                else:
                    dx = x / dist_center
                    dy = y / dist_center
                positions[i][0] -= excess * dx
                positions[i][1] -= excess * dy
                max_disp = max(max_disp, excess)

        if max_disp < tol:
            break

    return positions if max_disp < tol else None

def binary_search_packing(radii, search_iter=30, max_iter=5000, tol=1e-5):
    lower_bound = max(radii)
    upper_bound = 2 * sum(radii)
    best_positions = None
    best_R = upper_bound

    for _ in range(search_iter):
        mid = (lower_bound + upper_bound) / 2.0
        positions = relax_positions(mid, radii, max_iter, tol)
        if positions is not None:
            best_R = mid
            best_positions = positions
            upper_bound = mid
        else:
            lower_bound = mid
    return best_R, best_positions

# ======== HÀM VẼ KẾT QUẢ ==========
def plot_packing(container_radius, radii, positions):
    fig, ax = plt.subplots()
    
    # Vẽ hình tròn chứa
    container_circle = patches.Circle((0, 0), container_radius, fill=False, edgecolor='red', linewidth=2)
    ax.add_patch(container_circle)
    
    # Danh sách chứa các hình tròn nhỏ để sau dùng cho sự kiện hover
    small_circles = []
    
    # Vẽ các hình tròn nhỏ với màu sắc ngẫu nhiên
    for i, (x, y) in enumerate(positions):
        color = (random.random(), random.random(), random.random())
        circle = patches.Circle((x, y), radii[i], facecolor=color, edgecolor='black', alpha=0.5)
        ax.add_patch(circle)
        small_circles.append(circle)
    
    ax.set_xlim(-container_radius, container_radius)
    ax.set_ylim(-container_radius, container_radius)
    ax.set_aspect('equal', adjustable='box')
    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)
    
    # Tạo annotation để hiển thị đường kính của hình tròn khi hover
    annot = ax.annotate(
        "", 
        xy=(0,0), 
        xytext=(20,20), 
        textcoords="offset points",
        bbox=dict(boxstyle="round", fc="w"),
        arrowprops=dict(arrowstyle="->")
    )
    annot.set_visible(False)
    
    def on_hover(event):
        if event.inaxes == ax:
            found = False
            for circle in small_circles:
                contains, _ = circle.contains(event)
                if contains:
                    # Lấy tọa độ tâm của hình tròn
                    center = circle.center
                    annot.xy = center
                    # Hiển thị đường kính của hình tròn đó (2 * bán kính)
                    diam = 2 * circle.get_radius()
                    annot.set_text(f"φ{diam:.2f}")
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    found = True
                    break
            if not found and annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
    
    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    
    # Thay đổi tiêu đề: hiển thị đường kính hình tròn chứa (đường kính = 2 * bán kính)
    plt.title(f"Đường kính dây: {2 * container_radius:.2f}")
    plt.show()

# ======== GIAO DIỆN TKINTER ==========
root = tk.Tk()
root.title("Đường kính harness")

frame = tk.Frame(root)
frame.pack(pady=10)

btn_select = tk.Button(frame, text="Chọn file csv/xls/xlxs", command=select_file, font=("Arial", 12))
btn_select.pack(side=tk.LEFT, padx=5)

btn_run = tk.Button(frame, text="RUN", command=run_program, font=("Arial", 12))
btn_run.pack(side=tk.LEFT, padx=5)

btn_clear = tk.Button(frame, text="Xóa Log", command=clear_log, font=("Arial", 12))
btn_clear.pack(side=tk.LEFT, padx=5)

# ======== THÊM CÁI ĐẶT CHO max_iter VÀ tol ==========
param_frame = tk.Frame(root)
param_frame.pack(pady=5)

label_max_iter = tk.Label(param_frame, text="max_iter:", font=("Arial", 10))
label_max_iter.pack(side=tk.LEFT, padx=5)
entry_max_iter = tk.Entry(param_frame, width=10, font=("Arial", 10))
entry_max_iter.insert(0, "5000")
entry_max_iter.pack(side=tk.LEFT, padx=5)

label_tol = tk.Label(param_frame, text="tol:", font=("Arial", 10))
label_tol.pack(side=tk.LEFT, padx=5)
entry_tol = tk.Entry(param_frame, width=10, font=("Arial", 10))
entry_tol.insert(0, "1e-5")
entry_tol.pack(side=tk.LEFT, padx=5)

log_text = scrolledtext.ScrolledText(root, width=50, height=15, font=("Arial", 10))
log_text.pack(pady=10)
log_text.config(state=tk.DISABLED)

root.mainloop()
