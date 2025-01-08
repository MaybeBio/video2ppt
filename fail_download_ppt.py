from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fpdf import FPDF
import os
from PIL import Image
import io
import time

# 初始化浏览器
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 无头模式
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.binary_location = '/usr/bin/chromium-browser'  # 使用系统Chromium

driver = webdriver.Chrome(options=options)

try:
    # 访问jAccount登录页面
    driver.get('https://jaccount.sjtu.edu.cn/oauth2/authorize')
    
    # 等待并填写登录表单
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'user'))
    ).send_keys('用户名')
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'pass'))
    ).send_keys('密码')
    
    # 点击登录按钮
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, 'submit'))
    ).click()
    
    # 等待跳转完成
    time.sleep(5)
    
    # 检查是否登录成功
    if 'jaccount.sjtu.edu.cn' in driver.current_url:
        raise Exception("jAccount登录失败，请检查用户名和密码")

    # 访问课程页面
    course_url = 'https://oc.sjtu.edu.cn/courses/71832/external_tools/8329'
    driver.get(course_url)
    
    # 等待页面加载
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'title'))
    )
    
    # 获取页面内容
    page_source = driver.page_source
    
    # 保存页面用于调试
    with open('course_page.html', 'w', encoding='utf-8') as f:
        f.write(page_source)
    
    # 创建保存目录
    if not os.path.exists('lectures'):
        os.makedirs('lectures')
    
    # 查找所有课程节次
    lectures = driver.find_elements(By.CLASS_NAME, 'title.sle')
    
    for lecture in lectures:
        lecture_title = lecture.text.strip()
        print(f"\n正在处理: {lecture_title}")
        
        # 创建PDF
        pdf = FPDF()
        
        # 查找该节次的所有PPT图片
        images = lecture.find_elements(By.TAG_NAME, 'img')
        
        for i, img in enumerate(images):
            img_url = img.get_attribute('src')
            print(f"正在下载图片 {i+1}: {img_url}")
            
            # 下载图片
            img_data = io.BytesIO(img.screenshot_as_png)
            
            # 打开图片获取尺寸
            with Image.open(img_data) as img_pil:
                width, height = img_pil.size
                aspect = width / height
                
                # 设置PDF页面尺寸
                pdf.add_page(format=(width/10, height/10))  # 转换为毫米
                
                # 添加图片到PDF
                pdf.image(img_data, x=0, y=0, w=pdf.w, h=pdf.h)
        
        # 保存PDF
        safe_title = ''.join(c for c in lecture_title if c.isalnum() or c in (' ', '_')).rstrip()
        pdf_path = f'lectures/{safe_title}.pdf'
        pdf.output(pdf_path)
        print(f"已保存: {pdf_path}")

    print('\n所有课程PPT已处理完成')

except Exception as e:
    print(f"发生错误: {str(e)}")
finally:
    driver.quit()
