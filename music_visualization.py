
def generate_spectrum_video(input_video_path, output_video_path, waveform_color='viridis', opacity=0.3):
    # 读取视频
    video_clip = VideoFileClip(input_video_path)
    audio_clip = video_clip.audio
    logging.info("Video and audio clips loaded successfully.")
    
    # 提取音频数据
    audio_samples = audio_clip.to_soundarray(fps=44100)[::10]  # 降低采集密度
    logging.info("Audio samples extracted.")
    
    # 音频可视化 - 生成频谱柱子
    spectrum_data = create_spectrum_data(audio_samples)
    logging.info("Spectrum data generated.")
    
    # 获取视频帧率和尺寸
    fps = video_clip.fps
    frame_width = video_clip.size[0]
    frame_height = video_clip.size[1] // 5  # 调整高度为原高度的 1/5
    
    # 创建视频写入对象
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))
    logging.info("Video writer initialized.")
    
    # 逐帧处理视频，叠加频谱柱子
    for i in range(len(spectrum_data)):
        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)  # 创建空白帧
        combined_frame = overlay_spectrum_on_frame(frame, spectrum_data[i], (frame_width, frame_height), waveform_color, opacity)
        out.write(combined_frame)
        logging.info(f"Processed frame at {i + 1} samples.")
        
    # 释放资源
    out.release()
    logging.info("Video processing completed.")


def overlay_spectrum_on_frame(frame, spectrum, frame_size, color_map, opacity):
    # 绘制频谱柱子
    fig, ax = plt.subplots(figsize=(frame_size[0]/100, frame_size[1]/100), dpi=100)
    ax.bar(range(len(spectrum)), spectrum, color=plt.cm.get_cmap(color_map)(np.linspace(0, 1, len(spectrum))))
    ax.axis('off')
    
    # 将matplotlib图像转换为numpy数组
    fig.canvas.draw()
    spectrum_img = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    spectrum_img = spectrum_img.reshape(fig.canvas.get_width_height()[::-1] + (4,))
    
    # 调整频谱图像大小以匹配视频帧大小
    spectrum_img = cv2.resize(spectrum_img, frame_size)

    # 提取 RGB 通道（忽略 A 通道）
    spectrum_img = spectrum_img[:, :, 1:]

    # 叠加频谱图像到视频帧上
    combined_frame = cv2.addWeighted(frame, 1 - opacity, spectrum_img, opacity, 0)
    
    # 清理绘图
    plt.close(fig)
    
    return combined_frame


def create_spectrum_data(audio_samples):
    # 这里简化为直接使用音频样本的绝对值来模拟频谱数据
    spectrum_data = []
    for sample in audio_samples:
        spectrum = np.abs(np.fft.fft(sample)).mean(axis=1)
        spectrum_data.append(spectrum)
    return spectrum_data

# 示例调用
if __name__ == "__main__":
    input_video_path = r"D:\PycharmProjects\MutilsSingSong\assets\52\TikDownloader.io_7401013767196134661_hd_seg1_rgba_with_audio.mov"
    output_video_path = "output_spectrum_video.mp4"
    generate_spectrum_video(input_video_path, output_video_path)