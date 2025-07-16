import datetime
import os
import random
from typing import Optional

from moviepy import concatenate_videoclips, VideoFileClip

from guess_who_is_sing import export_who_is_singing_video
from preprocess.cute_video import cute_video
from who_sang_better import export_who_sang_it_better
from step_by_step_music import export_step_by_step_music_video
from singing_order import export_what_singing_order
from which_is_cutest import export_which_is_cutest_video


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


import os
from moviepy import VideoFileClip


def capture_last_frame(video_path: str, output_image_path: str = None) -> Optional[str]:
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在：{video_path}")
        return None

    try:
        with VideoFileClip(video_path) as clip:
            last_frame = clip.get_frame(clip.duration - 0.1)  # 获取倒数第0.1秒的画面

        from PIL import Image
        import numpy as np

        # 如果未指定输出路径，则使用视频同名 .jpg
        if output_image_path is None:
            output_image_path = os.path.splitext(video_path)[0] + ".jpg"

        # 将 numpy 数组转换为 PIL 图像并保存
        image = Image.fromarray(last_frame)
        image.save(output_image_path)

        print(f"✅ 成功保存最后一帧到 {output_image_path}")
        return output_image_path

    except Exception as e:
        print(f"❌ 截取最后一帧失败：{e}")
        return None


# 四宫格业务玩法
if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(__file__))
    # *****翻唱歌曲玩法*****

    for i in range(41, 42):
        print(f"处理第{i}集")
        video_folder = os.path.join(root_dir, "assets", str(i))
        cute_video(video_folder, os.path.join(video_folder, 'trimmed'), is_min=True)
        values = [0.0, 1.0, 0.0, 0.0]
        random.shuffle(values)
        # 竞猜-谁在唱歌
        # try:
        #     export_who_is_singing_video(video_folder, values=values, title="Who is singing?")
        # except Exception as e:
        #     print("❌ 竞猜-谁在唱歌失败")
        #     print(e)
        #
        # # 逐句唱歌-无声音的画面暂停# 一起唱（这个数据不好）
        # try:
        #     export_step_by_step_music_video(video_folder, title="Sing Along!")
        # except:
        #     print("❌ 逐句唱歌-无声音的画面暂停失败")
        # 同句唱-擂台赛
        # try:
        #     export_who_sang_it_better(video_folder, title_1="WHO SANG IT BETTER??",)
        # except:
        #     print("❌ 同句唱-擂台赛失败")
        # # 竞猜-逐句唱歌的顺序-有声音的画面不暂停
        try:
            export_what_singing_order(video_folder, title="What’s the singing order?")

        except:
            print("❌ 竞猜-逐句唱歌的顺序-有声音的画面不暂停失败")

    # *****Q版AI动漫卡片*****

    # title_options = [
    #     "Battle! Choose Your Cat Warrior Camp",
    #     "Four Camps! Which Cat Warrior Wins?",
    #     "Cat Warriors' Showdown: Pick Your Camp",
    #     "Ultimate Battle! Which Cat Clan Rules?",
    #     "Camp Clash! Unleash Your Cat Warrior"
    # ]
    #
    #
    #
    # for i in range(1, 9):
    #     title = random.choice(title_options)
    #     print(f"处理第{i}集")
    #     video_folder = os.path.join(root_dir, "assets", "Q", str(i))
    #     cute_video(video_folder, os.path.join(video_folder, 'trimmed'), is_min=True)
    #
    #     export_which_is_cutest_video(video_folder, title)
    #

    # *****Q版AI动漫卡片*****

    # title_options = [
    #     "Mini Heroes Brawl! Pick Your Squad",
    #     "Q-Style Showdown: Choose Your Camp",
    #     "Tiny Heroes Battle! Which Team Rules?",
    #     "Chibi Brawl: Select Your Power Camp",
    #     "Q-Heroes Clash! Lead Your Faction"
    # ]
    #

    # for i in range(8, 13):
    #     title = random.choice(title_options)
    #     print(f"处理第{i}集")
    #     video_folder = os.path.join(root_dir, "assets", "Q", str(i))
    #     cute_video(video_folder, os.path.join(video_folder, 'trimmed'), is_min=True)
    #
    #     export_which_is_cutest_video(video_folder, title)

    # video_folder = os.path.join(root_dir, "output", "待发布","Q版")
    # video_files = [f for f in os.listdir(os.path.join(video_folder)) if f.endswith(".mp4")]
    # for video_file in video_files:
    #     video_path = os.path.join(video_folder, video_file)
    #     capture_last_frame(video_path)
