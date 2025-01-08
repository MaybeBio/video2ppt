# video2ppt

参考<https://shuiyuan.sjtu.edu.cn/t/topic/271815>，

使用<https://github.com/prcwcy/sjtu-canvas-video-download>下载canvas网课视频，  

再使用该脚本提取处理获取ppt/pdf文件，适用于无课件上传的canvas课程，用于获取课件；   

缺点：  

（1）需要自己调节所关注的差分区域，大小尺寸以及位置宽高度像素位置等  
（2）需要自己调节间隔跳跃的frame，具体因课程讲授速度不同而不同，可设置低阈值，然后人工筛除重复部分
（3）所获取的pdf为图片型，若要翻译识别等需要OCR支持

