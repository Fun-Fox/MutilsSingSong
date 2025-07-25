import os
import subprocess

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

    if is_min:
        final_duration = min(durations)
    print(f"⏱️ 视频时长: {final_duration:.2f} 秒")
    # print(f"⏱️ 最短视频时长: {shortest_duration:.2f} 秒")

    # 截取每个视频的前 `final_duration` 秒
    for clip, path in zip(clips, video_paths):
        filename = os.path.basename(path)
        # 确保输出为.mov格式以支持透明通道
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"trimmed_{base_name}.mov")

        if clip.duration > final_duration:
            print(f"⚠️ 视频 {filename} 的时长 ({clip.duration:.2f} 秒) 超过平均时长，将截取前 {final_duration:.2f} 秒")
            try:
                # 使用ffmpeg命令直接裁剪视频
                cmd_video = [
                    "ffmpeg",
                    "-i", path,
                    "-t", str(final_duration),
                    "-vcodec", "qtrle",
                    "-pix_fmt", "yuva420p",
                    "-y", output_path
                ]
                print(f"正在裁剪视频: {filename}")
                subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                print(f"✅ 已生成裁剪视频：{output_path}")
            except subprocess.CalledProcessError as e:
                print(f"❌ 裁剪失败 {filename}: {str(e)}")
            except Exception as e:
                print(f"❌ 裁剪失败 {filename}: {str(e)}")
        else:
            # 如果视频时长小于等于目标时长，直接复制或转换格式
            try:
                cmd_video = [
                    "ffmpeg",
                    "-i", path,
                    "-vcodec", "qtrle",
                    "-pix_fmt", "yuva420p",
                    "-y", output_path
                ]
                print(f"正在转换视频格式: {filename}")
                subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                print(f"✅ 已生成转换视频：{output_path}")
            except subprocess.CalledProcessError as e:
                print(f"❌ 转换失败 {filename}: {str(e)}")
            except Exception as e:
                print(f"❌ 转换失败 {filename}: {str(e)}")

    # 关闭所有剪辑以释放资源
    for clip in clips:
        clip.close()

    return final_duration
