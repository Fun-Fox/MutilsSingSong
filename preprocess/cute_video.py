import os
from moviepy import VideoFileClip


def cute_video(video_dir,output_dir,is_min=False):

    # 设置目录路径
    video_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), video_dir)
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir)

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

    final_duration = sum(durations) / len(durations)
    print(f"⏱️ 平均视频时长: {final_duration:.2f} 秒")
    if is_min:
        final_duration = min(durations)
    # print(f"⏱️ 最短视频时长: {shortest_duration:.2f} 秒")


    # 截取每个视频的前 `shortest_duration` 秒
    for clip, path in zip(clips, video_paths):
        filename = os.path.basename(path)
        output_path = os.path.join(output_dir, f"trimmed_{filename}")
        if clip.duration > final_duration:


            print(f"⚠️ 视频 {filename} 的时长 ({clip.duration:.2f} 秒) 超过平均时长，将截取前 {final_duration:.2f} 秒")
            try:
                subclip = clip.subclipped(0, final_duration)  # 从0秒开始，截取到最短时长
                subclip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    logger=None
                )
                print(f"✅ 已生成裁剪视频：{output_path}")
            except Exception as e:
                print(f"❌ 裁剪失败 {filename}: {str(e)}")
        else:
            # 小于则
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
    return final_duration
