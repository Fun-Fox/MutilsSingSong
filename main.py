import datetime
import os
import random

from moviepy import concatenate_videoclips, VideoFileClip

from guess_who_is_sing import export_who_is_singing_video
from step_by_step_music import export_step_by_step_music_video
from which_is_cutest import export_which_is_cutest_video
from sing_a_song import export_sing_a_song_video


def concatenate_videos(video_paths, output_path):
    """
    拼接多个视频文件为一个
    :param video_paths: 视频路径列表
    :param output_path: 输出视频路径
    """
    clips = []
    for path in video_paths:
        if os.path.exists(path):
            clips.append(VideoFileClip(path))
        else:
            print(f"⚠️ 文件不存在：{path}")

    if not clips:
        print("❌ 没有可用的视频片段")
        return

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    print(f"✅ 视频合并完成，输出路径：{output_path}")


if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # for i in ['love the way you lie', "105-1", "105-2", "zdht", "bbg", "dqsj", "dqsj-1"]:
    #     video_folder = os.path.join(root_dir, "assets", i)  # 视频文件夹路径
    #     export_video(video_folder)

    # video_folder = os.path.join(root_dir, "assets", "yourman")  # 视频文件夹路径
    # export_video(video_folder)

    # video_folder = os.path.join(root_dir, "assets", "cydd-1")  # 视频文件夹路径
    # export_video(video_folder)
    #
    # for i in range(6,13):
    #     video_folder = os.path.join(root_dir, "assets", str(i))  # 视频文件夹路径
    #     video_1 = export_who_is_singing_video(video_folder)
    #     video_2 = export_step_by_step_music_video(video_folder)
    #     now_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #     # 新增：拼接两个视频
    #     output_final_video = os.path.join(root_dir, "output", f"你猜对了吗_{now_date}.mp4")
    #     concatenate_videos([video_1, video_2], output_final_video)
    #
    # #
    video_folder = os.path.join(root_dir, "assets", "1")  # 视频文件夹路径
    #
    # export_which_is_cutest_video(video_folder)

    export_sing_a_song_video(video_folder,text="Spring Day")

    # video_folder = os.path.join(root_dir, "assets", "yellow")  # 视频文件夹路径
    # export_video(video_folder)
