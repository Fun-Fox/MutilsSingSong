import os
from moviepy import VideoFileClip

# 设置目录路径
video_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pre')
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'trimmed')

os.makedirs(output_dir, exist_ok=True)

# 支持的视频格式
video_exts = ('.mp4', '.avi', '.mov')

# 读取所有视频并获取它们的时长
video_files = [f for f in os.listdir(video_dir) if f.lower().endswith(video_exts)]
video_paths = [os.path.join(video_dir, f) for f in video_files]

# 获取每个视频的持续时间
durations = []
clips = []

for path in video_paths:
    try:
        clip = VideoFileClip(path)
        durations.append(clip.duration)
        clips.append(clip)
    except Exception as e:
        print(f"⚠️ 跳过无效视频 {path}: {e}")

if not durations:
    print("❌ 没有有效的视频文件")
else:
    shortest_duration = min(durations)
    print(f"⏱️ 最短视频时长: {shortest_duration:.2f} 秒")

    # 截取每个视频的前 `shortest_duration` 秒
    for clip, path in zip(clips, video_paths):
        filename = os.path.basename(path)
        output_path = os.path.join(output_dir, f"trimmed_{filename}")

        try:
            subclip = clip.subclipped(0, shortest_duration)  # 从0秒开始，截取到最短时长
            subclip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            print(f"✅ 已生成裁剪视频：{output_path}")
        except Exception as e:
            print(f"❌ 裁剪失败 {filename}: {str(e)}")
