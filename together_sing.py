import datetime
import os
import random

from moviepy import VideoFileClip, AudioFileClip
from pydub import AudioSegment

import pyJianYingDraft.pyJianYingDraft as draft
from preprocess.cute_video import cute_video
from pyJianYingDraft.pyJianYingDraft import Clip_settings, trange, Font_type, Text_style, Export_resolution, \
    Export_framerate

root_dir = os.path.dirname(os.path.abspath(__file__))


def add_video_material(start_time, output_video_path, transform_x, transform_y, track_name, script, volume):
    video_material = draft.Video_material(output_video_path)
    video_segment = draft.Video_segment(
        video_material,
        target_timerange=draft.Timerange(start_time, video_material.duration),
        source_timerange=draft.Timerange(0, video_material.duration),
        volume=volume,
        clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5, transform_x=transform_x, transform_y=transform_y)
    )
    script.add_segment(video_segment, track_name)
    return start_time + video_material.duration, script


def export_together_sing_video(video_folder, values=[0.0, 0.0, 0.0, 0.0]):
    # Step 1: 预处理视频（裁剪）
    cute_video(video_folder, os.path.join(video_folder, 'trimmed'))

    # Step 2: 获取视频文件列表
    video_files = [f for f in os.listdir(os.path.join(video_folder, 'trimmed')) if f.endswith(".mp4")]

    # Step 3: 创建 audio 文件夹
    audio_dir = os.path.join(video_folder, 'audio')
    os.makedirs(audio_dir, exist_ok=True)

    # Step 4: 提取并分割第一个视频的音频
    first_video_path = os.path.join(video_folder, "trimmed", video_files[0])
    clip = VideoFileClip(first_video_path)
    video_duration_ms = clip.duration * 1000  # 转为毫秒
    segment_duration = int(video_duration_ms // 4)  # 每段长度（毫秒）

    # 提取音频
    video_clip = VideoFileClip(first_video_path)
    audio_clip = video_clip.audio
    original_audio_path = os.path.join(audio_dir, f"{os.path.splitext(video_files[0])[0]}_full.mp3")
    audio_clip.write_audiofile(original_audio_path, bitrate="192k")

    # 使用 pydub 加载并分割音频
    full_audio = AudioSegment.from_mp3(original_audio_path)
    segments = [
        full_audio[i * segment_duration: (i + 1) * segment_duration]
        for i in range(4)
    ]

    # Step 5: 保存每个视频对应的音频段
    audio_segments_info = []
    cumulative_time = 0  # 累计开始时间（单位：微秒）

    for idx, video_file in enumerate(video_files[:4]):  # 只处理前4个视频
        segment_idx = idx
        custom_audio_segment = segments[segment_idx]

        # 构建音频文件名
        video_name_base = os.path.splitext(video_file)[0]
        custom_audio_path = os.path.join(audio_dir, f"{video_name_base}_segment{segment_idx + 1}.mp3")

        # 导出音频
        custom_audio_segment.export(custom_audio_path, format="mp3")
        print(f"🎵 音频已保存：{custom_audio_path}")

        # 记录音频信息
        duration_us = int(custom_audio_segment.duration_seconds * 1_000_000)
        audio_segments_info.append({
            "track_name": f"audio-track-{idx}",
            "file_path": custom_audio_path,
            "start_time": cumulative_time,
            "duration": duration_us
        })

        # 更新累计时间
        cumulative_time += duration_us

    # Step 6: 创建剪映草稿
    base_folder = os.path.join(
        os.getenv("LOCALAPPDATA"),
        "JianyingPro\\User Data\\Projects\\com.lveditor.draft"
    )
    draft_folder_name = '猜猜谁在唱歌'
    DUMP_PATH = os.path.join(base_folder, draft_folder_name, "draft_content.json")
    os.makedirs(os.path.dirname(DUMP_PATH), exist_ok=True)
    script = draft.Script_file(1080, 1920)  # 1920x1080分辨率

    # 添加标题文本
    text_segment = draft.Text_segment(
        "Who is singing?",
        trange("0s", "10s"),
        font=Font_type.新青年体,
        style=Text_style(size=20.0, color=(1.0, 1.0, 1.0), underline=False, align=1),
        clip_settings=Clip_settings(transform_y=0)
    )

    effect_ids = [
        "7351319129124506930",
        "7506817303296675123",
        "7507075178447359282",
        "6896144021568179469",
        "6896137924853763336",
        "7244707954585292064",
        "7404300897628540211"
    ]
    selected_effect = random.choice(effect_ids)
    text_segment.add_effect(selected_effect)
    script.add_track(draft.Track_type.text, track_name="text-title", relative_index=100)
    script.add_segment(text_segment, "text-title")

    # Step 7: 添加视频和音频轨道
    for idx, video_file in enumerate(video_files[:4]):  # 只处理前4个视频
        video_path = os.path.join(video_folder, "trimmed", video_file)
        print(f"\n🎬 正在处理视频：{video_file}")
        clip = VideoFileClip(video_path)
        print(f"⏱️ 视频总时长：{clip.duration:.2f} 秒")

        # 添加视频轨道
        script.add_track(
            draft.Track_type.video,
            track_name=f'{idx}-{video_file}-video',
            relative_index=idx * 2 + 10
        )

        # 添加音频轨道
        if idx < len(audio_segments_info):
            audio_info = audio_segments_info[idx]
            audio_material = draft.Audio_material(audio_info["file_path"])
            audio_segment = draft.Audio_segment(
                audio_material,
                draft.Timerange(audio_info["start_time"], audio_info["duration"])
            )
            script.add_track(
                draft.Track_type.audio,
                track_name=f'audio-track-{idx}',
                relative_index=idx + 1
            )
            script.add_segment(audio_segment, f'audio-track-{idx}')

        # 添加视频片段
        transform = {
            0: (-0.5, 0.5),
            1: (0.5, 0.5),
            2: (-0.5, -0.5),
            3: (0.5, -0.5)
        }.get(idx, (0.0, 0.0))

        transform_x, transform_y = transform
        start_time = 0

        if idx == 0:
            start_time, script = add_video_material(
                0, video_path, transform_x, transform_y,
                f"{idx}-{video_file}-video", script, values[idx]
            )
        elif idx == 1:
            prev_duration = audio_segments_info[0]["duration"]
            start_time, script = add_video_material(
                prev_duration, video_path, transform_x, transform_y,
                f"{idx}-{video_file}-video", script, values[idx]
            )
        elif idx == 2:
            prev_duration = sum(seg["duration"] for seg in audio_segments_info[:2])
            start_time, script = add_video_material(
                prev_duration, video_path, transform_x, transform_y,
                f"{idx}-{video_file}-video", script, values[idx]
            )
        elif idx == 3:
            prev_duration = sum(seg["duration"] for seg in audio_segments_info[:3])
            start_time, script = add_video_material(
                prev_duration, video_path, transform_x, transform_y,
                f"{idx}-{video_file}-video", script, values[idx]
            )

        # 添加序号文字
        script.add_track(draft.Track_type.text, track_name=f'text-index-{idx}', relative_index=idx * 2 + 99)
        seg = draft.Text_segment(
            str(idx + 1),
            trange("0s", f"{int(clip.duration)}s"),
            font=Font_type.新青年体,
            style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1),
            clip_settings=Clip_settings(
                transform_x=-0.2 if idx % 2 == 0 else 0.2,
                transform_y=-0.2 if idx >= 2 else 0.2
            )
        )
        script.add_segment(seg, f"text-index-{idx}")

    # Step 8: 保存脚本并导出视频
    script.dump(DUMP_PATH)
    print("\n🎉 所有视频片段及截图已成功处理！")

    ctrl = draft.Jianying_controller()
    OUTPUT_PATH = os.path.join(root_dir, "output")
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    now_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(OUTPUT_PATH, f"{draft_folder_name}_{now_date}.mp4")

    ctrl.export_draft(
        draft_folder_name,
        output_path,
        resolution=Export_resolution.RES_1080P,
        framerate=Export_framerate.FR_24
    )
    print(f"导出视频完成: {output_path}")

    return output_path
