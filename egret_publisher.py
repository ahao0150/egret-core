import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import sys
import json
import re
import shutil
import glob

class EgretPublisher:
    def __init__(self, root):
        self.root = root
        self.root.title("Egret Engine 发布器")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        # 设置变量
        self.project_path = tk.StringVar()
        # 引擎目录固定为当前运行目录
        self.engine_path = tk.StringVar(value=os.getcwd())
        self.runtime_path = tk.StringVar()
        self.target_platform = tk.StringVar()
        
        # 支持的平台列表（初始化为web，会在引擎路径设置后自动更新）
        self.platforms = ["web"]
        self.platform_combobox = None  # 存储平台选择下拉框的引用
        
        # 配置文件路径
        self.config_file = "egret_publisher_config.json"
        
        # 动态参数配置
        self.target_config_data = None  # 存储target.json的数据
        
        self.create_widgets()
        self.load_config()
        
        # 初始化时自动加载支持的平台列表
        self.on_engine_path_changed()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="Egret Engine 发布器", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 项目路径选择
        project_label = ttk.Label(main_frame, text="白鹭项目路径:")
        project_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        project_entry = ttk.Entry(main_frame, textvariable=self.project_path, width=50)
        project_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        project_button = ttk.Button(main_frame, text="浏览...", command=self.browse_project)
        project_button.grid(row=1, column=2, pady=5, padx=(5, 0))
        
        # Runtime目录选择（用于替代启动器下载）
        runtime_label = ttk.Label(main_frame, text="Runtime目录:")
        runtime_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        runtime_entry = ttk.Entry(main_frame, textvariable=self.runtime_path, width=50)
        runtime_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        runtime_button = ttk.Button(main_frame, text="浏览...", command=self.browse_runtime)
        runtime_button.grid(row=2, column=2, pady=5, padx=(5, 0))
        
        # 监听Runtime路径变化，自动读取target.json
        self.runtime_path.trace_add("write", lambda *args: self.on_runtime_path_changed())
        
        # 目标平台选择
        platform_label = ttk.Label(main_frame, text="目标平台:")
        platform_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.platform_combobox = ttk.Combobox(main_frame, textvariable=self.target_platform, 
                                        values=self.platforms, state="readonly", width=47)
        self.platform_combobox.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        self.platform_combobox.set("web")  # 默认选择web平台
        
        # 发布按钮
        self.publish_button = ttk.Button(main_frame, text="开始发布", command=self.publish)
        self.publish_button.grid(row=4, column=0, columnspan=3, pady=20)
        
        # 进度文本框
        self.progress_label_row = 5
        self.progress_text_row = 6
        self.button_frame_row = 7
        
        self.progress_label = ttk.Label(main_frame, text="发布进度:")
        self.progress_label.grid(row=self.progress_label_row, column=0, sticky=tk.W, pady=(10, 5))
        
        self.progress_text = tk.Text(main_frame, height=12, width=80)
        self.progress_text.grid(row=self.progress_text_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 滚动条
        self.scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.progress_text.yview)
        self.scrollbar.grid(row=self.progress_text_row, column=3, sticky=(tk.N, tk.S))
        self.progress_text.configure(yscrollcommand=self.scrollbar.set)
        
        # 按钮框架
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.grid(row=self.button_frame_row, column=0, columnspan=3, pady=10)
        
        # 清除按钮
        clear_button = ttk.Button(self.button_frame, text="清除日志", command=self.clear_log)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # 帮助按钮
        help_button = ttk.Button(self.button_frame, text="使用说明", command=self.show_help)
        help_button.pack(side=tk.LEFT, padx=5)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
    def browse_project(self):
        """选择项目路径"""
        directory = filedialog.askdirectory(title="选择白鹭项目目录")
        if directory:
            self.project_path.set(directory)
    
    def on_engine_path_changed(self):
        """引擎路径变化时，自动读取支持的平台列表"""
        engine_path = self.engine_path.get()
        if not engine_path or not os.path.exists(engine_path):
            return
        
        # 读取平台列表
        platforms = self.load_platforms_from_engine(engine_path)
        if platforms:
            self.platforms = platforms
            # 更新下拉框
            if self.platform_combobox:
                self.platform_combobox['values'] = self.platforms
                # 如果当前选择的平台不在新列表中，重置为web
                if self.target_platform.get() not in self.platforms:
                    self.target_platform.set("web" if "web" in self.platforms else self.platforms[0])
    
    def load_platforms_from_engine(self, engine_path):
        """从引擎目录读取支持的平台列表"""
        try:
            # 查找 tools/templates/empty/scripts 目录
            scripts_dir = os.path.join(engine_path, "tools", "templates", "empty", "scripts")
            
            if not os.path.exists(scripts_dir):
                print(f"未找到scripts目录: {scripts_dir}")
                return ["web"]
            
            platforms = []
            
            # 遍历scripts目录，查找 config.*.ts 文件
            for file_name in os.listdir(scripts_dir):
                if file_name.startswith("config.") and file_name.endswith(".ts"):
                    # 提取平台名称：config.wxgame.ts -> wxgame
                    platform_name = file_name[7:-3]  # 去掉 "config." 和 ".ts"
                    if platform_name:
                        platforms.append(platform_name)
            
            # 检查是否有 config.ts 文件（web平台的默认配置）
            if os.path.exists(os.path.join(scripts_dir, "config.ts")):
                platforms.append("web")
            
            # 排序，web放在第一位
            if "web" in platforms:
                platforms.remove("web")
                platforms.sort()
                platforms.insert(0, "web")
            else:
                platforms.sort()
            
            print(f"发现 {len(platforms)} 个支持的平台: {', '.join(platforms)}")
            return platforms if platforms else ["web"]
            
        except Exception as e:
            print(f"读取平台列表时出错: {e}")
            return ["web"]
            
    def browse_runtime(self):
        """选择Runtime目录"""
        directory = filedialog.askdirectory(title="选择Runtime目录（可选）")
        if directory:
            self.runtime_path.set(directory)
    
    def on_runtime_path_changed(self):
        """Runtime路径变化时，读取target.json配置"""
        runtime_path = self.runtime_path.get()
        print(f"🔄 Runtime路径变化: {runtime_path}")
        
        if not runtime_path or not os.path.exists(runtime_path):
            print("❌ Runtime路径无效或不存在")
            self.target_config_data = None
            return
        
        # 查找target.json（支持多种嵌套结构）
        target_json_paths = [
            os.path.join(runtime_path, "target.json"),
            os.path.join(runtime_path, os.path.basename(runtime_path), "target.json"),
            # 支持更深层的嵌套：egret-wxgame-support-1.3.7/egret-wxgame-support-1.3.7/target.json
            os.path.join(runtime_path, os.path.basename(runtime_path), os.path.basename(runtime_path), "target.json"),
        ]
        
        target_json_path = None
        for path in target_json_paths:
            if os.path.exists(path):
                target_json_path = path
                break
        
        if target_json_path:
            self.load_target_config(target_json_path)
        else:
            print("❌ 未找到target.json文件")
            self.target_config_data = None
    
    def load_target_config(self, target_json_path):
        """加载target.json配置"""
        try:
            with open(target_json_path, 'r', encoding='utf-8') as f:
                self.target_config_data = json.load(f)
            
            print(f"✅ 成功读取target.json: {target_json_path}")
            print(f"📊 发现 {len(self.target_config_data.get('args', []))} 个参数")
            
        except Exception as e:
            print(f"❌ 读取target.json失败: {e}")
            self.target_config_data = None
    
    def show_dynamic_params_dialog(self):
        """显示动态参数输入对话框"""
        if not self.target_config_data or "args" not in self.target_config_data:
            return {}
        
        args = self.target_config_data.get("args", [])
        if not args:
            return {}
        
        # 计算对话框高度（根据参数数量动态调整）
        param_count = len(args)
        # 每个参数大约需要120像素高度，加上标题、按钮区域和额外空间
        dialog_height = max(400, min(800, 200 + param_count * 120 + 100))  # 增加100px预留按钮空间
        
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("平台参数配置")
        dialog.geometry(f"500x{dialog_height}")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()  # 模态对话框
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="平台参数配置", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 创建滚动区域的框架
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)  # 滚动区域填充剩余空间
        
        # 创建滚动区域
        canvas = tk.Canvas(scroll_frame)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 参数输入区域
        params_frame = scrollable_frame
        
        # 存储参数变量
        param_vars = {}
        param_widgets = []
        
        # 创建参数输入控件
        for i, arg in enumerate(args):
            arg_name = arg.get("name", "")
            arg_default = arg.get("default", "")
            arg_files = arg.get("files", [])
            
            if not arg_name:
                continue
            
            # 参数组框架
            param_group = ttk.LabelFrame(params_frame, text=f"参数: {arg_name}", padding="15")
            param_group.pack(fill=tk.X, pady=10)
            
            # 默认值标签
            if arg_default:
                default_label = ttk.Label(param_group, text=f"默认值: {arg_default}", 
                                        font=("Arial", 9), foreground="gray")
                default_label.pack(anchor=tk.W, pady=(0, 8))
            
            # 输入框
            var = tk.StringVar(value=arg_default)
            param_vars[arg_name] = var
            entry = ttk.Entry(param_group, textvariable=var, width=50, font=("Arial", 10))
            entry.pack(fill=tk.X, pady=(0, 8))
            
            # 应用文件说明
            if arg_files:
                files_label = ttk.Label(param_group, text=f"应用于: {', '.join(arg_files)}", 
                                    font=("Arial", 8), foreground="blue")
                files_label.pack(anchor=tk.W)
            
            param_widgets.append(param_group)
        
        # 按钮框架（固定在底部）
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 15), padx=10)
        
        # 确认发布按钮
        ok_button = ttk.Button(button_frame, text="确认发布", 
                            command=lambda: self.on_dialog_ok(dialog, param_vars))
        ok_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 取消发布按钮
        cancel_button = ttk.Button(button_frame, text="取消发布", 
                                command=lambda: self.on_dialog_cancel(dialog))
        cancel_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # 等待对话框关闭
        dialog.wait_window()
        
        # 返回用户输入的值
        return getattr(self, '_dialog_result', {})
    
    def on_dialog_ok(self, dialog, param_vars):
        """确认发布按钮回调"""
        result = {}
        for param_name, var in param_vars.items():
            result[param_name] = var.get()
        
        self._dialog_result = result
        dialog.destroy()
    
    def on_dialog_cancel(self, dialog):
        """取消发布按钮回调"""
        self._dialog_result = {}
        dialog.destroy()
            
    def clear_log(self):
        """清除日志"""
        self.progress_text.delete(1.0, tk.END)
    
    def show_help(self):
        """显示使用说明"""
        help_text = """Egret Engine 发布器使用说明

1. 白鹭项目路径：
   选择您要发布的Egret项目的根目录
   （包含egretProperties.json的目录）

2. Runtime目录（可选）：
   如果需要发布到特定平台（如小游戏），
   可能需要指定对应的Runtime支持目录

3. 目标平台：
   选择要发布的目标平台类型
   - web: 网页版本
   - native: 原生版本
   - wxgame: 微信小游戏
   - tbgame: 淘宝小游戏
   - tbcreativeapp: 淘宝创意互动
   - 其他小游戏平台...

4. 发布流程：
   点击"开始发布"后，工具将：
   - 检查必要的环境（Node.js）
   - 编译项目代码
   - 生成平台特定的发布文件
   - 应用平台参数配置
   - 输出到项目的上层目录

注意事项：
- 请确保已安装Node.js环境
- 发布器必须在引擎根目录（egret-core）下运行
- 发布前建议先在项目中测试编译
- 首次发布某平台可能需要下载额外支持包
- 支持Node.js 12.x ~ 22.x（已自动处理兼容性）
- 发布成功后会自动打开输出目录

版本：1.2.0
"""
        messagebox.showinfo("使用说明", help_text)
            
    def publish(self):
        """开始发布"""
        project_path = self.project_path.get()
        engine_path = self.engine_path.get()
        runtime_path = self.runtime_path.get()
        target = self.target_platform.get()
        
        # 检查必要参数
        if not project_path:
            messagebox.showerror("错误", "请选择白鹭项目路径")
            return
            
        if not engine_path:
            messagebox.showerror("错误", "请选择引擎目录")
            return
            
        if not target:
            messagebox.showerror("错误", "请选择目标平台")
            return
            
        # 检查路径是否存在
        if not os.path.exists(project_path):
            messagebox.showerror("错误", "项目路径不存在")
            return
            
        if not os.path.exists(engine_path):
            messagebox.showerror("错误", "引擎目录不存在")
            return
            
        # 检查Runtime路径（如果指定了的话）
        if runtime_path and not os.path.exists(runtime_path):
            messagebox.showerror("错误", "Runtime目录不存在")
            return
            
        # 检查是否需要输入动态参数
        dynamic_params = {}
        if self.target_config_data and "args" in self.target_config_data:
            args = self.target_config_data.get("args", [])
            if args:
                # 显示参数输入对话框
                dynamic_params = self.show_dynamic_params_dialog()
                if not dynamic_params:  # 用户取消了对话框
                    return
        
        # 保存配置
        self.save_config()
            
        # 开始发布流程
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.insert(tk.END, f"开始发布项目到 {target} 平台...\n")
        self.progress_text.insert(tk.END, f"项目路径: {project_path}\n")
        self.progress_text.insert(tk.END, f"引擎路径: {engine_path}\n")
        if runtime_path:
            self.progress_text.insert(tk.END, f"Runtime路径: {runtime_path}\n")
        if dynamic_params:
            self.progress_text.insert(tk.END, f"用户配置参数: {dynamic_params}\n")
        self.progress_text.insert(tk.END, "-" * 50 + "\n")
        self.root.update()
        
        # 执行发布命令
        self.execute_publish(project_path, engine_path, target, runtime_path, dynamic_params)
        
    def clean_build_output(self, project_path, target):
        """删除历史构建内容"""
        try:
            # 可能的输出目录
            possible_output_dirs = [
                os.path.join(project_path, "bin-release", target),
                os.path.join(os.path.dirname(project_path), f"{os.path.basename(project_path)}_{target}"),
                os.path.join(project_path, "bin-release"),
            ]
            
            cleaned_dirs = []
            for output_dir in possible_output_dirs:
                if os.path.exists(output_dir):
                    try:
                        shutil.rmtree(output_dir)
                        cleaned_dirs.append(output_dir)
                        self.progress_text.insert(tk.END, f"已清理历史构建目录: {output_dir}\n")
                    except Exception as e:
                        self.progress_text.insert(tk.END, f"清理目录失败 {output_dir}: {str(e)}\n")
            
            if not cleaned_dirs:
                self.progress_text.insert(tk.END, f"未找到需要清理的历史构建目录\n")
                
        except Exception as e:
            self.progress_text.insert(tk.END, f"清理历史构建内容时出错: {str(e)}\n")
    
    def execute_publish(self, project_path, engine_path, target, runtime_path, dynamic_params=None):
        """执行发布命令"""
        try:
            # 使用引擎目录中的egret脚本
            egret_script = os.path.join(engine_path, "tools", "bin", "egret")
            
            # 检查egret脚本是否存在
            if not os.path.exists(egret_script):
                self.progress_text.insert(tk.END, f"错误: 找不到egret脚本 {egret_script}\n")
                self.progress_text.see(tk.END)
                messagebox.showerror("错误", f"找不到egret脚本 {egret_script}")
                return
                
            self.progress_text.insert(tk.END, f"使用egret脚本: {egret_script}\n")
            
            # 1. 删除历史构建内容
            self.progress_text.insert(tk.END, f"步骤1: 删除历史构建内容\n")
            self.clean_build_output(project_path, target)
            
            # 2. 检查并创建目标平台的配置文件
            self.progress_text.insert(tk.END, f"步骤2: 创建目标平台配置文件\n")
            self.create_target_config_file(project_path, target, runtime_path)
            
            # 3. 复制模板文件到编译目录（如果Runtime目录中有模板）
            self.progress_text.insert(tk.END, f"步骤3: 复制模板文件\n")
            self.copy_template_files_to_compile_dir(project_path, target, runtime_path)
            
            # 设置环境变量（必须在构建命令前设置）
            env = os.environ.copy()
            # 设置EGRET_PATH环境变量指向引擎目录（注意是EGRET_PATH不是EGRET_HOME）
            env["EGRET_PATH"] = engine_path
            
            # 设置NODE_OPTIONS以支持Node.js 17+版本
            # 启用OpenSSL旧版算法支持，解决 "digital envelope routines::unsupported" 错误
            existing_node_options = env.get("NODE_OPTIONS", "")
            if "--openssl-legacy-provider" not in existing_node_options:
                if existing_node_options:
                    env["NODE_OPTIONS"] = existing_node_options + " --openssl-legacy-provider"
                else:
                    env["NODE_OPTIONS"] = "--openssl-legacy-provider"
                self.progress_text.insert(tk.END, f"已启用Node.js旧版OpenSSL支持（兼容Node.js 17+）\n")
            
            # 在Windows下，需要检查node是否可用
            try:
                node_version_check = subprocess.Popen(
                    ["node", "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                stdout, stderr = node_version_check.communicate(timeout=5)
                if node_version_check.returncode == 0 or stdout:
                    self.progress_text.insert(tk.END, f"Node.js版本: {stdout.strip()}\n")
                else:
                    self.progress_text.insert(tk.END, f"警告: Node.js检测返回错误\n")
            except Exception as e:
                self.progress_text.insert(tk.END, f"警告: 无法检测Node.js版本: {str(e)}\n")
            
            # 4. 执行Node.js构建脚本
            self.progress_text.insert(tk.END, f"步骤4: 执行Node.js构建脚本\n")
            
            # 构建Node.js命令 - 使用绝对路径
            cmd = ["node", egret_script, "publish", "--target", target, "--projectDir", project_path]
            
            # 如果指定了runtime目录，设置EGRET_RUNTIME环境变量
            if runtime_path:
                # 检查runtime目录中是否包含target相关的支持文件
                target_support_dir = os.path.join(runtime_path, f"egret-{target}-support")
                if os.path.exists(target_support_dir):
                    env["EGRET_RUNTIME"] = target_support_dir
                    self.progress_text.insert(tk.END, f"使用特定平台Runtime目录: {target_support_dir}\n")
                else:
                    # 检查runtime路径是否直接就是target支持目录
                    if os.path.exists(os.path.join(runtime_path, "manifest.json")) or os.path.exists(os.path.join(runtime_path, "template")):
                        env["EGRET_RUNTIME"] = runtime_path
                        self.progress_text.insert(tk.END, f"使用Runtime目录: {runtime_path}\n")
                    else:
                        # 尝试在runtime路径中查找匹配的目录
                        found_target_dir = self.find_target_support_dir(runtime_path, target)
                        if found_target_dir:
                            env["EGRET_RUNTIME"] = found_target_dir
                            self.progress_text.insert(tk.END, f"使用匹配的Runtime目录: {found_target_dir}\n")
                        else:
                            # 如果找不到特定的target目录，使用整个runtime路径
                            env["EGRET_RUNTIME"] = runtime_path
                            self.progress_text.insert(tk.END, f"使用Runtime目录: {runtime_path}\n")
                            self.progress_text.insert(tk.END, f"警告: 未找到特定的 {target} 平台支持目录\n")
            
            self.progress_text.insert(tk.END, f"执行命令: {' '.join(cmd)}\n")
            self.progress_text.insert(tk.END, f"工作目录: {project_path}\n")
            self.progress_text.insert(tk.END, f"EGRET_PATH: {engine_path}\n")
            if runtime_path and "EGRET_RUNTIME" in env:
                self.progress_text.insert(tk.END, f"EGRET_RUNTIME: {env['EGRET_RUNTIME']}\n")
            self.progress_text.insert(tk.END, "-" * 50 + "\n")
            self.progress_text.see(tk.END)
            self.root.update()
            
            # 执行命令 - 使用更兼容的方式
            # 在Windows下创建进程时使用shell=False，但需要确保路径正确
            if sys.platform == "win32":
                # Windows环境，使用CREATE_NO_WINDOW标志避免弹出黑窗口
                try:
                    CREATE_NO_WINDOW = 0x08000000
                    process = subprocess.Popen(
                        cmd,
                        cwd=project_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        encoding='utf-8',
                        env=env,
                        creationflags=CREATE_NO_WINDOW
                    )
                except:
                    # 如果CREATE_NO_WINDOW不可用，使用普通方式
                    process = subprocess.Popen(
                        cmd,
                        cwd=project_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        encoding='utf-8',
                        env=env
                    )
            else:
                process = subprocess.Popen(
                    cmd,
                    cwd=project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    encoding='utf-8',
                    env=env
                )
            
            # 实时显示输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress_text.insert(tk.END, output)
                    self.progress_text.see(tk.END)
                    self.root.update()
                    
            # 获取返回码
            return_code = process.poll()
            
            # 检查输出中是否包含错误信息
            output_contains_error = False
            output_text = self.progress_text.get(1.0, tk.END)
            if "TypeError:" in output_text or "Error:" in output_text or "_ is not a function" in output_text:
                output_contains_error = True
            
            if return_code == 0 and not output_contains_error:
                self.progress_text.insert(tk.END, "\n" + "=" * 50 + "\n")
                self.progress_text.insert(tk.END, "发布成功完成!\n")
                
                # 步骤5: 应用参数替换
                self.progress_text.insert(tk.END, f"步骤5: 应用参数替换\n")
                if self.target_config_data:
                    self.progress_text.insert(tk.END, f"正在应用参数替换...\n")
                    # 找到实际的输出目录进行参数替换
                    actual_output_dir = self.find_actual_output_directory(project_path, target, output_text)
                    if actual_output_dir and os.path.exists(actual_output_dir):
                        self.apply_dynamic_params_to_template(actual_output_dir, project_path, dynamic_params)
                
                # 尝试从输出中找到实际的输出目录
                actual_output_dir = self.find_actual_output_directory(project_path, target, output_text)
                
                if actual_output_dir and os.path.exists(actual_output_dir):
                    actual_output_dir = actual_output_dir.replace("/", os.sep).replace("\\", os.sep)
                    
                    self.progress_text.insert(tk.END, f"发布目录: {actual_output_dir}\n")
                    self.progress_text.insert(tk.END, f"您可以在此目录中找到发布的平台工程文件\n")
                    
                    # 尝试打开输出目录
                    try:
                        if sys.platform == "win32":
                            os.startfile(actual_output_dir)
                            self.progress_text.insert(tk.END, f"已在资源管理器中打开发布目录\n")
                    except Exception as e:
                        self.progress_text.insert(tk.END, f"注意: 无法自动打开目录: {str(e)}\n")
                    
                    message = f"项目发布成功!\n\n发布目录: {actual_output_dir}\n"
                    messagebox.showinfo("成功", message)
                else:
                    # 尝试几个可能的位置
                    possible_dirs = [
                        os.path.join(project_path, "bin-release", target),
                        os.path.join(os.path.dirname(project_path), f"{os.path.basename(project_path)}_{target}"),
                    ]
                    
                    found_dir = None
                    for possible_dir in possible_dirs:
                        if os.path.exists(possible_dir):
                            found_dir = possible_dir
                            break
                    
                    if found_dir:
                        found_dir = found_dir.replace("/", os.sep).replace("\\", os.sep)
                        self.progress_text.insert(tk.END, f"发布目录: {found_dir}\n")
                        self.progress_text.insert(tk.END, f"您可以在此目录中找到发布的平台工程文件\n")
                        message = f"项目发布成功!\n\n发布目录: {found_dir}\n"
                        messagebox.showinfo("成功", message)
                    else:
                        self.progress_text.insert(tk.END, f"注意: 无法自动定位发布目录\n")
                        self.progress_text.insert(tk.END, f"请检查项目上层目录或bin-release目录\n")
                        message = f"项目发布成功!\n\n请在项目目录或上层目录中查找发布文件\n"
                        messagebox.showinfo("成功", message)
                
                self.progress_text.insert(tk.END, "=" * 50 + "\n")
            else:
                self.progress_text.insert(tk.END, "\n" + "=" * 50 + "\n")
                if output_contains_error:
                    self.progress_text.insert(tk.END, f"发布失败，输出中包含错误信息\n")
                else:
                    self.progress_text.insert(tk.END, f"发布失败，返回码: {return_code}\n")
                self.progress_text.insert(tk.END, "=" * 50 + "\n")
                messagebox.showerror("失败", f"项目发布失败\n返回码: {return_code}")
                
        except FileNotFoundError:
            error_msg = "找不到Node.js，请确保已正确安装Node.js并配置了环境变量\n"
            self.progress_text.insert(tk.END, error_msg)
            messagebox.showerror("错误", "找不到Node.js，请确保已正确安装Node.js并配置了环境变量")
        except Exception as e:
            error_msg = f"发布过程中出现错误: {str(e)}\n"
            self.progress_text.insert(tk.END, error_msg)
            messagebox.showerror("错误", f"发布过程中出现错误: {str(e)}")
            
        self.progress_text.see(tk.END)
        self.root.update()
        
    def find_target_support_dir(self, runtime_path, target):
        """在runtime路径中查找匹配target的支持目录"""
        try:
            # 遍历runtime路径下的所有目录
            for item in os.listdir(runtime_path):
                item_path = os.path.join(runtime_path, item)
                if os.path.isdir(item_path):
                    # 检查目录名是否包含target
                    if target.lower() in item.lower():
                        return item_path
                    # 检查目录中是否包含manifest.json或template目录
                    if (os.path.exists(os.path.join(item_path, "manifest.json")) or 
                        os.path.exists(os.path.join(item_path, "template"))):
                        # 进一步检查目录名是否与target相关
                        if (target.replace("game", "") in item.lower() or 
                            item.replace("egret-", "").replace("-support", "").replace("-game", "") in target.lower()):
                            return item_path
        except Exception as e:
            self.progress_text.insert(tk.END, f"查找target支持目录时出错: {str(e)}\n")
        return None
    
    def find_actual_output_directory(self, project_path, target, output_text):
        """查找实际的输出目录"""
        try:
            # 获取项目名称
            project_name = os.path.basename(project_path)
            
            # 可能的输出目录位置
            possible_dirs = [
                # 标准位置：bin-release/target
                os.path.join(project_path, "bin-release", target),
                # 带版本号的位置
                os.path.join(project_path, "bin-release", target, "*"),
                # 配置文件中的默认位置：../${projectName}_${target}
                os.path.join(os.path.dirname(project_path), f"{project_name}_{target}"),
                # 其他可能位置
                os.path.join(os.path.dirname(project_path), f"{project_name}-{target}"),
            ]
            
            # 遍历可能的目录
            for pattern in possible_dirs:
                if "*" in pattern:
                    # 使用glob查找带版本号的目录
                    import glob as glob_module
                    matches = glob_module.glob(pattern)
                    if matches:
                        # 获取最新的目录（按修改时间排序）
                        matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                        if os.path.isdir(matches[0]):
                            return matches[0]
                else:
                    if os.path.exists(pattern) and os.path.isdir(pattern):
                        # 检查目录是否不为空
                        if os.listdir(pattern):
                            return pattern
            
            # 如果还是找不到，尝试从输出文本中解析
            # 查找类似 "输出目录：" 或 "output:" 的行
            for line in output_text.split('\n'):
                if 'output' in line.lower() or '输出' in line:
                    # 尝试提取路径
                    import re
                    path_match = re.search(r'[A-Z]:[\\\/][\w\\\/\-\.]+', line)
                    if path_match:
                        potential_path = path_match.group(0)
                        if os.path.exists(potential_path) and os.path.isdir(potential_path):
                            return potential_path
            
        except Exception as e:
            self.progress_text.insert(tk.END, f"查找输出目录时出错: {str(e)}\n")
        
        return None
        
    def save_config(self):
        """保存配置到文件"""
        config = {
            "project_path": self.project_path.get(),
            "runtime_path": self.runtime_path.get(),
            "target_platform": self.target_platform.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            
    def load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                self.project_path.set(config.get("project_path", ""))
                self.runtime_path.set(config.get("runtime_path", ""))
                self.target_platform.set(config.get("target_platform", "web"))
                
                # 如果加载了Runtime路径，读取target.json配置
                if self.runtime_path.get():
                    print(f"🚀 启动时检测到Runtime路径: {self.runtime_path.get()}")
                    # 延迟执行，确保界面完全初始化后再处理
                    self.root.after(200, lambda: self.on_runtime_path_changed())
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            
    def create_target_config_file(self, project_path, target, runtime_path):
        """创建目标平台的配置文件"""
        try:
            # 检查scripts目录是否存在
            scripts_dir = os.path.join(project_path, "scripts")
            if not os.path.exists(scripts_dir):
                self.progress_text.insert(tk.END, f"警告: 项目中没有scripts目录\n")
                return
                
            # 检查目标平台的配置文件是否存在
            config_file = os.path.join(scripts_dir, f"config.{target}.ts")
            
            # 尝试从Runtime目录复制配置文件
            if runtime_path:
                # 查找Runtime目录中的配置文件
                runtime_config_sources = [
                    os.path.join(runtime_path, "scripts", f"config.{target}.ts"),
                    os.path.join(runtime_path, "template", "scripts", f"config.{target}.ts"),
                    os.path.join(runtime_path, f"config.{target}.ts"),
                ]
                
                for runtime_config in runtime_config_sources:
                    if os.path.exists(runtime_config):
                        # 如果目标配置文件已存在，检查是否需要更新
                        if os.path.exists(config_file):
                            # 检查文件内容是否包含buildConfig函数
                            with open(config_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if 'buildConfig' not in content or 'buildConfig:' not in content:
                                    # 配置文件格式不正确，需要替换
                                    shutil.copy2(runtime_config, config_file)
                                    self.progress_text.insert(tk.END, f"已更新配置文件（从Runtime）: {config_file}\n")
                                else:
                                    self.progress_text.insert(tk.END, f"配置文件已存在且格式正确: {config_file}\n")
                        else:
                            # 复制Runtime目录中的配置文件
                            shutil.copy2(runtime_config, config_file)
                            self.progress_text.insert(tk.END, f"已从Runtime复制配置文件: {config_file}\n")
                            
                            # 同时复制相关的平台支持文件
                            platform_dir = os.path.join(scripts_dir, target)
                            runtime_platform_dir = os.path.join(os.path.dirname(runtime_config), target)
                            if os.path.exists(runtime_platform_dir) and not os.path.exists(platform_dir):
                                shutil.copytree(runtime_platform_dir, platform_dir)
                                self.progress_text.insert(tk.END, f"已复制平台支持文件: {platform_dir}\n")
                        return
            
            # 如果Runtime目录中没有配置文件，检查是否已存在
            if os.path.exists(config_file):
                # 检查现有配置文件是否有效
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'buildConfig' in content or 'buildConfig:' in content:
                        self.progress_text.insert(tk.END, f"配置文件已存在: {config_file}\n")
                        return
                    else:
                        self.progress_text.insert(tk.END, f"警告: 现有配置文件格式不正确，将被替换\n")
                
            # 创建默认的配置文件
            default_content = self.create_default_config_content(target)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(default_content)
            self.progress_text.insert(tk.END, f"已创建默认配置文件: {config_file}\n")
                
        except Exception as e:
            self.progress_text.insert(tk.END, f"创建配置文件时出错: {str(e)}\n")
    
    def copy_template_files_to_compile_dir(self, project_path, target, runtime_path, dynamic_params=None):
        """复制模板文件到编译目录"""
        try:
            if not runtime_path:
                return
                
            # 查找模板目录（支持多种结构）
            template_dirs = [
                os.path.join(runtime_path, "template"),
                os.path.join(runtime_path, "scripts", target, "template"),
                os.path.join(runtime_path, target, "template"),
                # 支持嵌套结构：egret-wxgame-support-1.3.7/egret-wxgame-support-1.3.7/template/
                os.path.join(runtime_path, os.path.basename(runtime_path), "template"),
                # 支持更深层的嵌套
                os.path.join(runtime_path, os.path.basename(runtime_path), os.path.basename(runtime_path), "template"),
            ]
            
            template_dir = None
            for template_candidate in template_dirs:
                if os.path.exists(template_candidate) and os.path.isdir(template_candidate):
                    template_dir = template_candidate
                    break
            
            if not template_dir:
                self.progress_text.insert(tk.END, f"未找到 {target} 平台的模板目录\n")
                return
            
            self.progress_text.insert(tk.END, f"找到模板目录: {template_dir}\n")
            
            # 确定编译目录（Egret会输出到这里）
            compile_dir = os.path.join(os.path.dirname(project_path), f"{os.path.basename(project_path)}_{target}")
            
            # 如果编译目录不存在，创建它
            if not os.path.exists(compile_dir):
                os.makedirs(compile_dir, exist_ok=True)
                self.progress_text.insert(tk.END, f"创建编译目录: {compile_dir}\n")
            
            # 复制模板文件到编译目录
            self.progress_text.insert(tk.END, f"正在复制模板文件到编译目录: {compile_dir}\n")
            self.copy_directory_contents_simple(template_dir, compile_dir)
            
            self.progress_text.insert(tk.END, f"模板文件复制完成\n")
            
        except Exception as e:
            self.progress_text.insert(tk.END, f"复制模板文件到编译目录时出错: {str(e)}\n")
    
    def copy_directory_contents_simple(self, src_dir, dst_dir):
        """简单复制目录内容（不使用重试机制）"""
        try:
            for item in os.listdir(src_dir):
                src_path = os.path.join(src_dir, item)
                dst_path = os.path.join(dst_dir, item)
                
                if os.path.isdir(src_path):
                    # 如果是目录，递归复制
                    if not os.path.exists(dst_path):
                        os.makedirs(dst_path, exist_ok=True)
                    self.copy_directory_contents_simple(src_path, dst_path)
                else:
                    # 如果是文件，直接复制
                    shutil.copy2(src_path, dst_path)
                    self.progress_text.insert(tk.END, f"复制: {item}\n")
                    
        except Exception as e:
            self.progress_text.insert(tk.END, f"复制目录内容时出错: {str(e)}\n")
    
    def apply_dynamic_params_to_template(self, compile_dir, project_path, dynamic_params):
        """应用用户配置的动态参数到模板文件"""
        try:
            import urllib.parse
            
            # 获取项目名称
            project_name = os.path.basename(project_path)
            
            # 获取target.json中的args配置
            args = self.target_config_data.get("args", [])
            
            for arg in args:
                arg_name = arg.get("name", "")
                arg_files = arg.get("files", [])
                arg_default = arg.get("default", "")
                
                if not arg_name:
                    continue
                
                # 获取用户输入的值，如果没有则使用默认值
                user_value = dynamic_params.get(arg_name, "")
                
                # 如果用户没有输入且没有默认值，使用项目名称
                if not user_value:
                    if arg_default:
                        user_value = arg_default
                    else:
                        user_value = project_name
                
                # 替换指定文件中的占位符
                for file_name in arg_files:
                    file_path = os.path.join(compile_dir, file_name)
                    if os.path.exists(file_path):
                        self.progress_text.insert(tk.END, f"  替换参数 {arg_name}: {user_value} (文件: {file_name})\n")
                        self.replace_placeholder_in_file(file_path, arg_name, user_value)
                        
        except Exception as e:
            self.progress_text.insert(tk.END, f"应用动态参数时出错: {str(e)}\n")
    
    def replace_placeholder_in_file(self, file_path, param_name, value):
        """在文件中替换占位符"""
        try:
            import urllib.parse
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 格式1：{占位符名}
            placeholder = "{" + param_name + "}"
            if placeholder in content:
                content = content.replace(placeholder, value)
                self.progress_text.insert(tk.END, f"  替换 {placeholder} -> {value} ({os.path.basename(file_path)})\n")
            
            # 格式2：URL编码的占位符 %7B占位符名%7D
            placeholder_encoded = urllib.parse.quote(placeholder)
            if placeholder_encoded in content:
                content = content.replace(placeholder_encoded, value)
                self.progress_text.insert(tk.END, f"  替换 {placeholder_encoded} -> {value} ({os.path.basename(file_path)})\n")
            
            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            self.progress_text.insert(tk.END, f"替换占位符时出错 ({os.path.basename(file_path)}): {str(e)}\n")
    
    def copy_directory_contents(self, src_dir, dst_dir):
        """递归复制目录内容"""
        try:
            for item in os.listdir(src_dir):
                src_path = os.path.join(src_dir, item)
                dst_path = os.path.join(dst_dir, item)
                
                if os.path.isdir(src_path):
                    # 如果是目录，递归复制
                    if not os.path.exists(dst_path):
                        os.makedirs(dst_path, exist_ok=True)
                    self.copy_directory_contents(src_path, dst_path)
                else:
                    # 如果是文件，直接复制
                    shutil.copy2(src_path, dst_path)
                    
        except Exception as e:
            self.progress_text.insert(tk.END, f"复制目录内容时出错: {str(e)}\n")
    
    
    def copy_directory_contents_overwrite(self, src_dir, dst_dir):
        """复制目录内容，覆盖已存在的文件"""
        try:
            for item in os.listdir(src_dir):
                src_path = os.path.join(src_dir, item)
                dst_path = os.path.join(dst_dir, item)
                
                if os.path.isdir(src_path):
                    # 如果是目录，递归复制
                    if not os.path.exists(dst_path):
                        os.makedirs(dst_path, exist_ok=True)
                    self.copy_directory_contents_overwrite(src_path, dst_path)
                else:
                    # 如果是文件，直接复制（覆盖）
                    shutil.copy2(src_path, dst_path)
                    self.progress_text.insert(tk.END, f"复制: {item}\n")
                        
        except Exception as e:
            self.progress_text.insert(tk.END, f"覆盖复制目录内容时出错: {str(e)}\n")
            
    def create_default_config_content(self, target):
        """创建默认的配置文件内容（针对不同平台生成对应的配置）"""
        
        # 针对wxgame平台，需要特殊处理
        if target == "wxgame":
            content = f'''/// 阅读 api.d.ts 查看文档
///<reference path="api.d.ts"/>

import * as path from 'path';
import {{ UglifyPlugin, CompilePlugin, ManifestPlugin, ExmlPlugin, EmitResConfigFilePlugin, TextureMergerPlugin, CleanPlugin }} from 'built-in';
import {{ WxgamePlugin }} from './wxgame/wxgame';
import {{ CustomPlugin }} from './myplugin';
import * as defaultConfig from './config';
import {{ EuiCompilerPlugin }} from './plugins/eui-compiler-plugin';
import {{ WebpackBundlePlugin }} from './plugins/webpack-plugin';
import {{ wxgameIDEPlugin }} from './plugins/wxgameIDEPlugin';
//是否使用微信分离插件
const useWxPlugin: boolean = false;
const config: ResourceManagerConfig = {{

    buildConfig: (params) => {{

        const {{ target, command, projectName, version }} = params;
        const outputDir = `../${{projectName}}_wxgame`;
        if (command == 'build') {{
            return {{
                outputDir,
                commands: [
                    new CleanPlugin({{ matchers: ["js", "resource", "egret-library"] }}),
                    new WebpackBundlePlugin({{ libraryType: "debug", defines: {{ DEBUG: true, RELEASE: false }} }}),
                    new ExmlPlugin('commonjs'), // 非 EUI 项目关闭此设置
                    new WxgamePlugin(useWxPlugin),
                    new ManifestPlugin({{ output: 'manifest.js' }})
                ]
            }}
        }}
        else if (command == 'publish') {{
            return {{
                outputDir,
                commands: [
                    new CleanPlugin({{ matchers: ["js", "resource", "egret-library"] }}),
                    new WebpackBundlePlugin({{ libraryType: "release", defines: {{ DEBUG: false, RELEASE: true }} }}),
                    new ExmlPlugin('commonjs'), // 非 EUI 项目关闭此设置
                    new WxgamePlugin(useWxPlugin),
                    new UglifyPlugin([
                        {{
                            sources: ["main.js"],
                            target: "main.min.js"
                        }}
                    ]),
                    new ManifestPlugin({{ output: 'manifest.js', useWxPlugin: useWxPlugin }})
                ]
            }}
        }}
        else if (command == 'run') {{
            return {{
                outputDir,
                commands: [
                    new CleanPlugin({{ matchers: ["js", "resource", "egret-library"] }}),
                    new WebpackBundlePlugin({{ libraryType: "debug", defines: {{ DEBUG: true, RELEASE: false }} }}),
                    new ExmlPlugin('commonjs'), // 非 EUI 项目关闭此设置
                    new WxgamePlugin(useWxPlugin),
                    new ManifestPlugin({{ output: 'manifest.js' }}),
                    new wxgameIDEPlugin()
                ]
            }}
        }}
        else {{
            throw `unknown command : ${{params.command}}`;
        }}
    }},

    mergeSelector: defaultConfig.mergeSelector,

    typeSelector: defaultConfig.typeSelector
}}

export = config;
'''
        else:
            # 其他平台使用通用配置
            content = f'''/// 阅读 api.d.ts 查看文档
///<reference path="api.d.ts"/>

import * as path from 'path';
import {{ UglifyPlugin, CompilePlugin, ManifestPlugin, ExmlPlugin, EmitResConfigFilePlugin, TextureMergerPlugin, CleanPlugin }} from 'built-in';
import {{ WebpackBundlePlugin }} from './plugins/webpack-plugin';
import * as defaultConfig from './config';

const config: ResourceManagerConfig = {{

    buildConfig: (params) => {{

        const {{ target, command, projectName, version }} = params;
        const outputDir = `../${{projectName}}_${{target}}`;
        if (command == 'build') {{
            return {{
                outputDir,
                commands: [
                    new CleanPlugin({{ matchers: ["js", "resource"] }}),
                    new WebpackBundlePlugin({{ libraryType: "debug", defines: {{ DEBUG: true, RELEASE: false }} }}),
                    new ExmlPlugin('commonjs'), // 非 EUI 项目关闭此设置
                    new ManifestPlugin({{ output: 'manifest.js' }})
                ]
            }}
        }}
        else if (command == 'publish') {{
            return {{
                outputDir,
                commands: [
                    new CleanPlugin({{ matchers: ["js", "resource"] }}),
                    new WebpackBundlePlugin({{ libraryType: "release", defines: {{ DEBUG: false, RELEASE: true }} }}),
                    new ExmlPlugin('commonjs'), // 非 EUI 项目关闭此设置
                    new UglifyPlugin([
                        {{
                            sources: ["main.js"],
                            target: "main.min.js"
                        }}
                    ]),
                    new ManifestPlugin({{ output: 'manifest.js' }})
                ]
            }}
        }}
        else {{
            throw `unknown command : ${{params.command}}`;
        }}
    }},

    mergeSelector: defaultConfig.mergeSelector,

    typeSelector: defaultConfig.typeSelector
}}

export = config;
'''
        return content

def main():
    root = tk.Tk()
    app = EgretPublisher(root)
    root.mainloop()

if __name__ == "__main__":
    main()

