import datetime
import os
import random

from moviepy import VideoFileClip
from sympy import false

import pyJianYingDraft.pyJianYingDraft as draft
from preprocess.cute_video import cute_video
from pyJianYingDraft.pyJianYingDraft import Clip_settings, trange, Font_type, Text_style, Export_resolution, \
    Export_framerate, Mask_type, Text_loop_anim

root_dir = os.path.dirname(os.path.abspath(__file__))


def add_video_material(start_time, output_video_path, transform_x, transform_y, track_name, script, volume):
    video_material = draft.Video_material(output_video_path)
    video_segment = draft.Video_segment(video_material,
                                        draft.Timerange(start_time, video_material.duration),
                                        source_timerange=draft.Timerange(0, video_material.duration),
                                        volume=volume,
                                        clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5,
                                                                    transform_x=transform_x,
                                                                    transform_y=transform_y))  # 与素材等长
    # 添加到轨道
    # 添加一个线性蒙版，中心点在素材的(100, 0)像素处，顺时针旋转45度
    video_segment.add_mask(Mask_type.矩形, center_x=0, center_y=-100, size=0.8, rect_width=0.8, rotation=45)

    script.add_segment(video_segment, f'{track_name}', )
    start_time += video_material.duration

    return start_time, script


def export_sing_a_song_video(video_folder, text="Which AI doll is the cutest?"):
    # 获取 video_folder 路径下的所有 .mp4 视频文件

    cute_video(video_folder, os.path.join(video_folder, 'trimmed'),is_min=False)

    video_files = [f for f in os.listdir(os.path.join(video_folder, 'trimmed')) if f.endswith(".mp4")]

    # 创建剪映草稿
    base_folder = os.path.join(
        # LOCALAPPDATA 是 Windows 系统中的一个环境变量，表示当前用户的本地应用程序数据存储路径
        # C:\Users\<用户名>\AppData\Local
        os.getenv("LOCALAPPDATA"),
        "JianyingPro\\User Data\\Projects\\com.lveditor.draft"
    )
    draft_folder_name = '歌曲欣赏'
    # 保存路径
    DUMP_PATH = os.path.join(base_folder, draft_folder_name, "draft_content.json")
    os.makedirs(os.path.dirname(DUMP_PATH), exist_ok=True)
    script = draft.Script_file(1080, 1920)  # 1920x1080分辨率
    # 带下划线、位置及大小类似字幕的浅蓝色文本
    script.add_track(draft.Track_type.text, track_name=f'text-title', relative_index=100)

    video_path = os.path.join(video_folder, "trimmed", video_files[0])
    clip = VideoFileClip(video_path)
    emojis = ["🎵", "🎶", "🎼", "🎧", "🎤", "🎸", "🎹", "🥁"]
    random_emoji = random.choice(emojis)
    text_segment = draft.Text_segment(random_emoji + text, trange("0s", f"{int(clip.duration)}s"),
                                      font=Font_type.Amigate,
                                      style=Text_style(size=13.0, color=(1.0, 1.0, 1.0), underline=False, align=1),
                                      clip_settings=Clip_settings(transform_y=0))

    effect_ids = [
        "7506817303296675123",
        "7507075178447359282",
        "6896144021568179469",
        "6896137924853763336",
        "7244707954585292064",
        "7404300897628540211"
    ]

    # 随机选一个特效
    selected_effect = random.choice(effect_ids)

    text_segment.add_effect(selected_effect)
    script.add_segment(text_segment, "text-title")

    values = [0.0, 0.0, 0.0, 1.0]
    random.shuffle(values)
    # 定义表情列表
    emojis = ["😊", "😄", "😁", "😆", "😍", "😎", "🤩", "🥳"]

    for idx, video_file in enumerate(video_files):
        script.add_track(draft.Track_type.text, track_name=f'text-index-{idx}', relative_index=idx * 2 + 99)
        video_path = os.path.join(video_folder, "trimmed", video_file)
        print(f"\n🎬 正在处理视频：{video_file}")

        clip = VideoFileClip(video_path)
        print(f"⏱️ 视频总时长：{clip.duration:.2f} 秒")
        # 添加视频轨道

        script.add_track(draft.Track_type.video, track_name=f'{idx}-{video_file}-video', relative_index=idx * 2 + 10)
        random_emoji = random.choice(emojis)
        if idx == 0:
            # 第一个宫格视频添加视频轨道
            start_time, script = add_video_material(0, video_path, transform_x=-0.5,
                                                    transform_y=0.5, track_name=f"{idx}-{video_file}-video",
                                                    script=script, volume=values[idx])
            seg = draft.Text_segment(f"{random_emoji}", trange("0s", f"{int(clip.duration)}s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1),
                                     clip_settings=Clip_settings(transform_x=-0.2,
                                                                 transform_y=0.2))
            seg.add_animation(Text_loop_anim.彩色火焰)
            script.add_segment(seg, f"text-index-{idx}")

        elif idx == 1:

            # 添加视频
            start_time, script = add_video_material(0, video_path, transform_x=0.5, transform_y=0.5,
                                                    track_name=f"{idx}-{video_file}-video", script=script,
                                                    volume=values[idx])

            seg = draft.Text_segment(f"{random_emoji}", trange("0s", f"{int(clip.duration)}s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1),
                                     clip_settings=Clip_settings(transform_x=0.2, transform_y=0.2))
            seg.add_animation(Text_loop_anim.彩色火焰)
            script.add_segment(seg, f"text-index-{idx}")

        elif idx == 2:

            # 第三个宫格视频添加视频轨道
            start_time, script = add_video_material(0, video_path, transform_x=-0.5,
                                                    transform_y=-0.5,
                                                    track_name=f"{idx}-{video_file}-video", script=script,
                                                    volume=values[idx])
            seg = draft.Text_segment(f"{random_emoji}", trange("0s", f"{int(clip.duration)}s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1),
                                     clip_settings=Clip_settings(transform_x=-0.2,
                                                                 transform_y=-0.2))
            seg.add_animation(Text_loop_anim.彩色火焰)
            script.add_segment(seg, f"text-index-{idx}")

        elif idx == 3:

            start_time, script = add_video_material(0, video_path, transform_x=0.5,
                                                    transform_y=-0.5,
                                                    track_name=f"{idx}-{video_file}-video", script=script,
                                                    volume=values[idx])
            seg = draft.Text_segment(f"{random_emoji}", trange("0s", f"{int(clip.duration)}s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1),
                                     clip_settings=Clip_settings(transform_x=0.2,
                                                                 transform_y=-0.2))
            seg.add_animation(Text_loop_anim.彩色火焰)
            script.add_segment(seg, f"text-index-{idx}")
    script.dump(DUMP_PATH)

    print("\n🎉 所有视频片段及截图已成功处理！")

    ctrl = draft.Jianying_controller()
    OUTPUT_PATH = os.path.join(root_dir, "output")
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    now_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(OUTPUT_PATH, f"{draft_folder_name}_{now_date}.mp4")
    ctrl.export_draft(draft_folder_name, output_path,
                      resolution=Export_resolution.RES_1080P,
                      framerate=Export_framerate.FR_24,
                      )
    print(f"导出视频完成: {output_path}")

    return output_path
