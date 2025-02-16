import random
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import tkinter as tk
from tkinter import filedialog, scrolledtext

# Biến toàn cục lưu đường dẫn file đã chọn
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

    # Tính danh sách bán kính (d = đường kính)
    radii = [d / 2.0 for d in diameters]
    update_log(f"🔢 Tổng số hình tròn: {len(radii)}")

    container_radius, positions = pack_circles(radii)
    
    if positions is None:
        update_log("❌ Không tìm được cách sắp xếp hợp lệ!")
        return

    update_log(f"📏 Bán kính hình tròn chứa tối ưu: {container_radius:.2f}")
    update_log(f"📏 Đường kính hình tròn chứa tối ưu: {2 * container_radius:.2f}")

    plot_packing(container_radius, radii, positions)

# ======== HÀM KIỂM TRA VỊ TRÍ HỢP LỆ ==========
def is_valid(candidate_x, candidate_y, r_i, placed, positions, radii):
    for j in placed:
        xj, yj = positions[j]
        r_j = radii[j]
        if math.hypot(candidate_x - xj, candidate_y - yj) < (r_i + r_j - 1e-6):
            return False
    return True

# ======== HÀM TINH CHỈNH VỊ TRÍ ỨNG VIÊN ==========
def refine_candidate(candidate, r_i, placed, positions, radii, current_container):
    # Sử dụng tìm kiếm cục bộ quanh vị trí candidate ban đầu
    refinement_step = r_i * 0.05  # bước ban đầu có thể điều chỉnh
    best_position = candidate
    best_container = current_container
    improved = True

    while improved and refinement_step > 1e-6:
        improved = False
        for dx in [-refinement_step, 0, refinement_step]:
            for dy in [-refinement_step, 0, refinement_step]:
                new_candidate = (best_position[0] + dx, best_position[1] + dy)
                if not is_valid(new_candidate[0], new_candidate[1], r_i, placed, positions, radii):
                    continue
                new_container = max(current_container, math.hypot(new_candidate[0], new_candidate[1]) + r_i)
                if new_container < best_container:
                    best_container = new_container
                    best_position = new_candidate
                    improved = True
        refinement_step *= 0.5
    return best_position, best_container

# ======== THUẬT TOÁN PACKCIRCLE ==========
def pack_circles(radii):
    """
    Sắp xếp các hình tròn vào trong một hình tròn chứa.
    - radii: danh sách bán kính các hình tròn.
    Trả về:
        container_radius: bán kính của hình tròn chứa tối ưu
        positions: danh sách tọa độ (x, y) của các hình tròn theo chỉ số ban đầu.
    """
    n = len(radii)
    positions = [None] * n
    ANGLE_STEP = 1  # Giảm bước quét góc từ 5° xuống 1° để tăng độ chính xác

    # Sắp xếp chỉ số các hình theo bán kính giảm dần
    sorted_indices = sorted(range(n), key=lambda i: radii[i], reverse=True)
    placed = []

    # Đặt hình tròn lớn nhất tại tâm (0,0)
    first_idx = sorted_indices[0]
    positions[first_idx] = (0, 0)
    container_radius = radii[first_idx]
    placed.append(first_idx)

    # Đặt các hình tròn còn lại
    for idx in sorted_indices[1:]:
        r_i = radii[idx]
        best_position = None
        best_container = float('inf')
        # Xét các vị trí ứng viên dựa trên các hình đã được đặt
        for j in placed:
            xj, yj = positions[j]
            r_j = radii[j]
            # Quét các góc với bước nhỏ hơn để tăng độ chính xác
            for angle_deg in range(0, 360, ANGLE_STEP):
                angle = math.radians(angle_deg)
                candidate_x = xj + (r_j + r_i) * math.cos(angle)
                candidate_y = yj + (r_j + r_i) * math.sin(angle)
                if not is_valid(candidate_x, candidate_y, r_i, placed, positions, radii):
                    continue
                candidate_container = max(container_radius, math.hypot(candidate_x, candidate_y) + r_i)
                if candidate_container < best_container:
                    best_container = candidate_container
                    best_position = (candidate_x, candidate_y)
        if best_position is None:
            # Nếu không tìm được vị trí ứng viên, đặt hình bên phải vùng chứa hiện tại
            best_position = (container_radius + r_i, 0)
            best_container = math.hypot(best_position[0], best_position[1]) + r_i

        # Tinh chỉnh vị trí ứng viên bằng tìm kiếm cục bộ
        best_position, best_container = refine_candidate(best_position, r_i, placed, positions, radii, best_container)

        positions[idx] = best_position
        container_radius = max(container_radius, best_container)
        placed.append(idx)
    return container_radius, positions

# ======== HÀM VẼ KẾT QUẢ ==========
def plot_packing(container_radius, radii, positions):
    fig, ax = plt.subplots()
    
    # Vẽ hình tròn chứa
    container_circle = patches.Circle((0, 0), container_radius, fill=False, edgecolor='red', linewidth=2)
    ax.add_patch(container_circle)
    
    # Vẽ các hình tròn nhỏ với màu sắc ngẫu nhiên
    small_circles = []
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
    
    # Tạo annotation hiển thị đường kính khi hover chuột
    annot = ax.annotate(
        "", 
        xy=(0, 0), 
        xytext=(20, 20), 
        textcoords="offset points",
        bbox=dict(boxstyle="round", fc="w"),
        arrowprops=dict(arrowstyle="->")
    )
    annot.set_visible(False)
    
    def on_hover(event):
        if event.inaxes == ax:
            for circle in small_circles:
                contains, _ = circle.contains(event)
                if contains:
                    annot.xy = circle.center
                    diam = 2 * circle.get_radius()
                    annot.set_text(f"φ{diam:.2f}")
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    break
            else:
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
    
    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    plt.title(f"Đường kính chứa: {2 * container_radius:.2f}")
    plt.show()

# ======== GIAO DIỆN TKINTER ==========
root = tk.Tk()
root.title("Đường kính harness")

frame = tk.Frame(root)
frame.pack(pady=10)

btn_select = tk.Button(frame, text="Chọn file csv/xls/xlsx", command=select_file, font=("Arial", 12))
btn_select.pack(side=tk.LEFT, padx=5)

btn_run = tk.Button(frame, text="RUN", command=run_program, font=("Arial", 12))
btn_run.pack(side=tk.LEFT, padx=5)

btn_clear = tk.Button(frame, text="Xóa Log", command=clear_log, font=("Arial", 12))
btn_clear.pack(side=tk.LEFT, padx=5)

log_text = scrolledtext.ScrolledText(root, width=50, height=15, font=("Arial", 10))
log_text.pack(pady=10)
log_text.config(state=tk.DISABLED)

root.mainloop()
