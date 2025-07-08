import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import os


class ImageEnhanceAndUpscaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片修复与无损放大工具")
        self.root.geometry("1000x700")  # 调整窗口高度以容纳底部信息
        self.root.resizable(True, True)
        self.root.iconbitmap("assets/ico.ico")

        # 图像变量
        self.original_image = None  # OpenCV格式（BGR）
        self.restored_image = None  # 修复后（OpenCV）
        self.upscaled_image = None  # 放大后（PIL格式，便于保存）

        # 参数变量
        self.sharpness = tk.IntVar(value=50)  # 锐化强度（0-100）
        self.denoise = tk.IntVar(value=30)  # 去噪强度（0-100）
        self.contrast = tk.IntVar(value=40)  # 对比度（0-100）
        self.scale_factor = tk.DoubleVar(value=2.0)  # 放大倍数（1-10）

        self.create_widgets()

    def create_widgets(self):
        # 菜单栏
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开图片", command=self.open_image)
        file_menu.add_command(label="保存放大图片", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)

        # 主框架（用于容纳中间内容，留出底部空间）
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 主内容区域（原主框架内容）
        main_frame = ttk.Frame(main_container)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="处理参数", padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 修复参数区域
        ttk.Label(control_frame, text="=== 修复参数 ===").pack(anchor=tk.W, pady=(0, 10))

        # 锐化强度
        ttk.Label(control_frame, text="锐化强度:").pack(anchor=tk.W, pady=(0, 5))
        sharp_frame = ttk.Frame(control_frame)
        sharp_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Scale(sharp_frame, variable=self.sharpness, from_=0, to=100,
                  orient=tk.HORIZONTAL, command=lambda v: self.update_label(v, self.sharp_label)).pack(side=tk.LEFT,
                                                                                                       fill=tk.X,
                                                                                                       expand=True)
        self.sharp_label = ttk.Label(sharp_frame, text="50")
        self.sharp_label.pack(side=tk.LEFT, padx=(5, 0))

        # 去噪强度
        ttk.Label(control_frame, text="去噪强度:").pack(anchor=tk.W, pady=(0, 5))
        denoise_frame = ttk.Frame(control_frame)
        denoise_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Scale(denoise_frame, variable=self.denoise, from_=0, to=100,
                  orient=tk.HORIZONTAL, command=lambda v: self.update_label(v, self.denoise_label)).pack(side=tk.LEFT,
                                                                                                         fill=tk.X,
                                                                                                         expand=True)
        self.denoise_label = ttk.Label(denoise_frame, text="30")
        self.denoise_label.pack(side=tk.LEFT, padx=(5, 0))

        # 对比度增强
        ttk.Label(control_frame, text="对比度增强:").pack(anchor=tk.W, pady=(0, 5))
        contrast_frame = ttk.Frame(control_frame)
        contrast_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Scale(contrast_frame, variable=self.contrast, from_=0, to=100,
                  orient=tk.HORIZONTAL, command=lambda v: self.update_label(v, self.contrast_label)).pack(side=tk.LEFT,
                                                                                                          fill=tk.X,
                                                                                                          expand=True)
        self.contrast_label = ttk.Label(contrast_frame, text="40")
        self.contrast_label.pack(side=tk.LEFT, padx=(5, 0))

        # 放大参数区域
        ttk.Label(control_frame, text="=== 放大参数 ===").pack(anchor=tk.W, pady=(10, 10))

        # 放大倍数
        ttk.Label(control_frame, text="放大倍数:").pack(anchor=tk.W, pady=(0, 5))
        scale_frame = ttk.Frame(control_frame)
        scale_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Scale(scale_frame, variable=self.scale_factor, from_=1.0, to=10.0,
                  orient=tk.HORIZONTAL, command=lambda v: self.update_scale_label(v)).pack(side=tk.LEFT, fill=tk.X,
                                                                                           expand=True)
        self.scale_label = ttk.Label(scale_frame, text="2.0x")
        self.scale_label.pack(side=tk.LEFT, padx=(5, 0))

        # 操作按钮
        self.process_btn = ttk.Button(control_frame, text="修复并放大", command=self.process_image, state=tk.DISABLED)
        self.process_btn.pack(fill=tk.X, pady=(20, 10))
        self.save_btn = ttk.Button(control_frame, text="保存结果", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(fill=tk.X)

        # 右侧图片显示区域（三分栏）
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 原始图片
        original_frame = ttk.LabelFrame(display_frame, text="原始图片", padding="5")
        original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.original_canvas = tk.Canvas(original_frame, bg="#f0f0f0", relief=tk.SUNKEN, bd=1)
        self.original_canvas.pack(fill=tk.BOTH, expand=True)

        # 修复后图片
        restored_frame = ttk.LabelFrame(display_frame, text="修复后图片", padding="5")
        restored_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 5))
        self.restored_canvas = tk.Canvas(restored_frame, bg="#f0f0f0", relief=tk.SUNKEN, bd=1)
        self.restored_canvas.pack(fill=tk.BOTH, expand=True)

        # 放大后图片
        upscaled_frame = ttk.LabelFrame(display_frame, text="最终放大图", padding="5")
        upscaled_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.upscaled_canvas = tk.Canvas(upscaled_frame, bg="#f0f0f0", relief=tk.SUNKEN, bd=1)
        self.upscaled_canvas.pack(fill=tk.BOTH, expand=True)

        # 底部版权信息区域
        copyright_frame = ttk.Frame(self.root, padding="5", relief=tk.SUNKEN, borderwidth=1)
        copyright_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 版权文本
        copyright_text = "作者: Lighting | 版权所有 © 2025 | GitHub: https://github.com/a/b | 禁止未经授权转载、抄袭"
        ttk.Label(
            copyright_frame,
            text=copyright_text,
            font=("SimHei", 9)
        ).pack(anchor=tk.CENTER, pady=2)

    # 更新参数标签
    def update_label(self, value, label):
        label.config(text=str(int(float(value))))

    def update_scale_label(self, value):
        self.scale_label.config(text=f"{float(value):.1f}x")

    # 打开图片
    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if file_path:
            try:
                self.original_image = cv2.imread(file_path)
                if self.original_image is None:
                    raise Exception("无法读取图片")
                # 转换为RGB格式显示
                rgb_img = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
                self.original_pil = Image.fromarray(rgb_img)
                self.display_image(self.original_pil, self.original_canvas)
                # 清空之前的结果
                self.clear_canvas(self.restored_canvas)
                self.clear_canvas(self.upscaled_canvas)
                # 启用处理按钮
                self.process_btn.config(state=tk.NORMAL)
                self.save_btn.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("错误", f"打开图片失败: {str(e)}")

    # 在画布上显示图片（自动缩放适应画布）
    def display_image(self, pil_img, canvas):
        canvas.delete("all")
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 300, 300  # 默认尺寸

        # 计算缩放比例（保持原图比例，不超过画布）
        img_w, img_h = pil_img.size
        scale = min(canvas_width / img_w, canvas_height / img_h, 1.0)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        display_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 显示图片（居中）
        photo = ImageTk.PhotoImage(display_img)
        canvas.image = photo  # 保留引用，防止被销毁
        x = (canvas_width - new_w) // 2
        y = (canvas_height - new_h) // 2
        canvas.create_image(x, y, image=photo, anchor=tk.NW)

    # 清空画布
    def clear_canvas(self, canvas):
        canvas.delete("all")
        canvas.image = None

    # 核心处理流程：修复 -> 放大
    def process_image(self):
        if self.original_image is None:
            return
        try:
            # 1. 修复原图（去噪、锐化、增强）
            restored_cv = self.restore_image(self.original_image.copy())
            # 转换为PIL格式（RGB）
            restored_rgb = cv2.cvtColor(restored_cv, cv2.COLOR_BGR2RGB)
            self.restored_pil = Image.fromarray(restored_rgb)
            self.display_image(self.restored_pil, self.restored_canvas)

            # 2. 放大修复后的图片
            scale = self.scale_factor.get()
            new_w = int(self.restored_pil.width * scale)
            new_h = int(self.restored_pil.height * scale)
            self.upscaled_pil = self.restored_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.display_image(self.upscaled_pil, self.upscaled_canvas)

            # 启用保存按钮
            self.save_btn.config(state=tk.NORMAL)
            messagebox.showinfo("成功", f"已完成修复并放大 {scale:.1f} 倍！")
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")

    # 修复图片（去噪、锐化、对比度增强）
    def restore_image(self, img):
        # 去噪
        denoise_strength = self.denoise.get()
        if denoise_strength > 0:
            h = denoise_strength / 10.0  # 范围0-10（OpenCV推荐值）
            img = cv2.fastNlMeansDenoisingColored(img, None, h, h, 7, 21)

        # 对比度增强
        contrast_strength = self.contrast.get()
        if contrast_strength > 0:
            ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
            y, cr, cb = cv2.split(ycrcb)
            clahe = cv2.createCLAHE(clipLimit=1.0 + contrast_strength / 20.0, tileGridSize=(8, 8))
            y = clahe.apply(y)
            img = cv2.cvtColor(cv2.merge([y, cr, cb]), cv2.COLOR_YCrCb2BGR)

        # 锐化
        sharp_strength = self.sharpness.get()
        if sharp_strength > 0:
            kernel = np.array([[-1, -1, -1],
                               [-1, 9 + sharp_strength / 10, -1],
                               [-1, -1, -1]])
            img = cv2.filter2D(img, -1, kernel)

        return img

    # 保存结果
    def save_image(self):
        if not hasattr(self, 'upscaled_pil'):
            messagebox.showwarning("警告", "请先处理图片再保存！")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg"), ("所有文件", "*.*")],
            initialfile=f"enhanced_upscaled_{self.scale_factor.get():.1f}x.png"
        )
        if save_path:
            try:
                self.upscaled_pil.save(save_path)
                messagebox.showinfo("成功", f"已保存至:\n{save_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEnhanceAndUpscaleApp(root)
    root.mainloop()