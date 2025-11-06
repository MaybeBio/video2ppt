import os
from datetime import datetime
import cv2
from fpdf import FPDF
import re

# 指定视频文件所在的目录路径 (绝对路径)
directory_path = r'D:\download\gene\ppt_real'

# 指定输出图像和PDF的目录 (绝对路径)
output_directory = os.path.join(directory_path, 'ppt')
os.makedirs(output_directory, exist_ok=True)  # 如果目录不存在，则创建

# 获取目录下所有文件的列表
file_list = os.listdir(directory_path)

# 按照文件的修改时间进行排序
file_list.sort(key=lambda x: os.path.getmtime(os.path.join(directory_path, x)))

# 遍历排序后的文件列表
for file_name in file_list:
    file_path = os.path.join(directory_path, file_name)

    # 检查是否为文件而非子目录
    if not os.path.isfile(file_path):
        continue  # 跳过非文件项

    # 获取文件的修改时间
    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    print(f"正在处理文件: {file_path}")
    print(f"文件名：{file_name}，修改时间：{modified_time}")

    # 打开视频文件
    cap = cv2.VideoCapture(file_path)

    # 检查视频是否成功打开
    if not cap.isOpened():
        print(f"无法打开视频文件: {file_path}")
        continue  # 跳过无法打开的视频文件

    # 初始化变量
    prev_frame_gray_1 = None
    prev_frame_gray_2 = None
    page_images = []
    i = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break  # 读取完毕或发生错误

        # 检查帧是否为空
        if frame is None:
            continue

        # 确保感兴趣区域的坐标在帧的边界内
        if frame.shape[0] < 720 or frame.shape[1] < 1280:
            print(f"帧尺寸不足，跳过该帧，帧尺寸：{frame.shape}")
            continue

        # 调整感兴趣区域的坐标以适应帧的实际尺寸
        roi_1 = frame[480:660, 1060:1200]  # 感兴趣区域1，往上移动100像素
        roi_2 = frame[280:500, 340:540]    # 感兴趣区域2，扩大一些

        # 将感兴趣区域转换为灰度图像
        roi_gray_1 = cv2.cvtColor(roi_1, cv2.COLOR_BGR2GRAY)
        roi_gray_2 = cv2.cvtColor(roi_2, cv2.COLOR_BGR2GRAY)

        # 初始化前一帧灰度图像
        if prev_frame_gray_1 is None:
            prev_frame_gray_1 = roi_gray_1.copy()
            prev_frame_gray_2 = roi_gray_2.copy()
            continue  # 跳过第一帧的差分检测

        # 计算当前帧和前一帧的差分图像
        frame_diff_1 = cv2.absdiff(roi_gray_1, prev_frame_gray_1)
        frame_diff_2 = cv2.absdiff(roi_gray_2, prev_frame_gray_2)

        # 对差分图像进行阈值处理
        _, threshold_1 = cv2.threshold(frame_diff_1, 30, 255, cv2.THRESH_BINARY)
        _, threshold_2 = cv2.threshold(frame_diff_2, 30, 255, cv2.THRESH_BINARY)

        # 统计阈值图像中非零像素的数量
        diff_pixels_1 = cv2.countNonZero(threshold_1)
        diff_pixels_2 = cv2.countNonZero(threshold_2)

        # 如果两个区域的差分像素数量都超过阈值，则认为帧发生了变化
        if (diff_pixels_1 > 100 and diff_pixels_2 > 300) or diff_pixels_1 > 150 or diff_pixels_2 > 1000:
            print(f"帧发生变化: {i + 1}, 差分像素1: {diff_pixels_1}, 差分像素2: {diff_pixels_2}")

            # 提取文件名中的编号部分
            match = re.search(r'第(\d+)讲', file_name)
            if match:
                lecture_number = match.group(1)
            else:
                lecture_number = 'unknown'

            # 生成简化的文件名
            simplified_file_name = f"{lecture_number}_{i + 1}.jpg"
            page_path = os.path.join(output_directory, simplified_file_name)

            # 尝试保存图像
            try:
                # 检查输出目录是否存在
                if not os.path.exists(output_directory):
                    os.makedirs(output_directory, exist_ok=True)
                    print(f"创建输出目录: {output_directory}")

                # 保存图像
                success = cv2.imwrite(page_path, frame)
                if success:
                    print(f"图像已保存: {page_path}")
                    page_images.append(page_path)
                else:
                    print(f"图像保存失败: {page_path}")
            except Exception as e:
                print(f"保存图像时发生错误: {str(e)}")
            i += 1

        # 更新前一帧
        prev_frame_gray_1 = roi_gray_1.copy()
        prev_frame_gray_2 = roi_gray_2.copy()

        # 显示当前帧 (可选，运行时可关闭窗口加快速度)
        cv2.imshow("Frame", frame)

        # 跳过一定数量的帧以加快处理速度
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        max_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 计算目标帧的索引（例如跳500帧）
        target_frame = current_frame + 100
        if target_frame >= max_frames:
            break  # 超过总帧数，结束处理
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        # 按下 'q' 键退出循环 (可选，已注释)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    cap.release()
    cv2.destroyAllWindows()

    # 创建PDF文件
    pdf = FPDF(orientation='L', unit='mm', format='A4')  # 使用横向A4纸
    pdf.set_auto_page_break(auto=True, margin=15)

    for image_path in page_images:
        if os.path.exists(image_path):
            pdf.add_page()
            # 计算图片的宽度和高度，以适应PDF页面
            pdf_width = pdf.w   # 左右各5的边距
            pdf_height = pdf.h - 20  # 上下各10的边距
            pdf.image(image_path, x=5, y=10, w=pdf_width, h=pdf_height)
        else:
            print(f"图像文件不存在: {image_path}")

    # 保存PDF
    pdf_file_name = os.path.splitext(file_name)[0] + '.pdf'
    pdf_path = os.path.join(output_directory, pdf_file_name)
    try:
        pdf.output(pdf_path)
        print(f"已保存PDF: {pdf_path}")
    except Exception as e:
        print(f"保存PDF时发生错误: {str(e)}")
