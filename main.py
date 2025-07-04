import datetime
import os
import random

from moviepy import concatenate_videoclips, VideoFileClip

from guess_who_is_sing import export_who_is_singing_video
from preprocess.cute_video import cute_video
from sing_a_song import export_sing_a_song_video
from step_by_step_music import export_step_by_step_music_video
from together_sing import export_together_sing_video


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

    for i in range(28, 29):
        print(f"处理第{i}集")
        video_folder = os.path.join(root_dir, "assets", str(i))
        cute_video(video_folder, os.path.join(video_folder, 'trimmed'), is_min=True)
        values = [0.0, 1.0, 0.0, 0.0]
        random.shuffle(values)
        # 竞猜-谁在唱歌
        try:
            export_who_is_singing_video(video_folder, values=values, title="Who is singing?")
        except:
            print("❌ 竞猜-谁在唱歌失败")

        # 逐句唱歌-无声音的画面暂停
        try:
            export_step_by_step_music_video(video_folder, title="Sing Along!")
        except:
            print("❌ 逐句唱歌-无声音的画面暂停失败")
        # 同句唱-擂台赛
        try:
            export_sing_a_song_video(video_folder, title_1="Karaoke Battle",
                                     title_2="🏆 Battle of the Voices – Who Wins?")
        except:
            print("❌ 同句唱-擂台赛失败")
        # 竞猜-逐句唱歌的顺序-有声音的画面不暂停
        try:
            export_together_sing_video(video_folder, title="What’s the singing order?")

        except:
            print("❌ 竞猜-逐句唱歌的顺序-有声音的画面不暂停失败")

    # video_folder = os.path.join(root_dir, "assets", "4")  # 视频文件夹路径
    # 选择可爱的猫咪
    # export_which_animal_is_cutest_video(video_folder)
