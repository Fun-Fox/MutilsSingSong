import datetime
import os
import random

import cv2
from moviepy import VideoFileClip, concatenate_audioclips, AudioFileClip
from pydub import AudioSegment

import pyJianYingDraft.pyJianYingDraft as draft
from preprocess.cute_video import cute_video
from pyJianYingDraft.pyJianYingDraft import Clip_settings, trange, Font_type, Text_style, Export_resolution, \
    Export_framerate, Text_loop_anim, Mask_type

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
    # 添加到轨道
    video_segment.add_mask(Mask_type.矩形, center_x=0, center_y=-50, size=0.8, rect_width=0.8, round_corner=45)

    script.add_segment(video_segment, track_name)
    return start_time + video_material.duration, script


def add_image(script, start_time, end_time, image_path, track_name, relative_index, transform_x, transform_y):
    """添加图片到剪映轨道"""
    script.add_track(draft.Track_type.video, track_name=track_name, relative_index=relative_index)
    video_material = draft.Video_material(image_path)
    video_segment = draft.Video_segment(
        video_material,
        target_timerange=draft.Timerange(start_time, end_time),
        source_timerange=draft.Timerange(0, video_material.duration),
        clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5, transform_x=transform_x, transform_y=transform_y)
    )
    video_segment.add_mask(Mask_type.矩形, center_x=0, center_y=-50, size=0.8, rect_width=0.8, round_corner=45)

    script.add_segment(video_segment, track_name)
    print(f"🖼️ 图片添加到轨道: {track_name}")
    return end_time


def extract_video_frames(video_path):
    """提取视频的第一帧和最后一帧作为图片"""
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    if not success:
        raise ValueError(f"无法读取视频 {video_path}")

    first_frame_path = os.path.splitext(video_path)[0] + "_first.jpg"
    cv2.imwrite(first_frame_path, frame)

    last_frame = None
    while success:
        last_frame = frame
        success, frame = cap.read()
    cap.release()

    last_frame_path = os.path.splitext(video_path)[0] + "_last.jpg"
    cv2.imwrite(last_frame_path, last_frame)

    return first_frame_path, last_frame_path


def export_together_sing_video(video_folder):
    # Step 1: 预处理视频（裁剪）

    # Step 2: 获取视频文件列表
    video_files = [f for f in os.listdir(os.path.join(video_folder, 'trimmed')) if f.endswith(".mp4")][:4]
    random.shuffle(video_files)
    num_videos = len(video_files)

    # Step 3: 创建 audio 文件夹
    audio_dir = os.path.join(video_folder, 'audio')
    os.makedirs(audio_dir, exist_ok=True)

    # Step 4: 提取并分割每个视频的音频
    all_segments = []  # 存储每个视频的4段音频路径
    segment_durations = []  # 每段音频长度（微秒）

    for idx, video_file in enumerate(video_files):
        video_path = os.path.join(video_folder, "trimmed", video_file)
        clip = VideoFileClip(video_path)
        duration_ms = int(clip.duration * 1000)
        segment_duration = duration_ms // 4

        # 提取音频
        audio_clip = clip.audio
        full_audio_path = os.path.join(audio_dir, f"{os.path.splitext(video_file)[0]}_full.mp3")
        audio_clip.write_audiofile(full_audio_path, bitrate="192k")

        # 分割音频
        full_audio = AudioSegment.from_mp3(full_audio_path)
        segments = [
            full_audio[i * segment_duration: (i + 1) * segment_duration]
            for i in range(4)
        ]

        # 保存音频段
        saved_segments = []
        for seg_idx, segment in enumerate(segments):
            seg_path = os.path.join(audio_dir, f"{os.path.splitext(video_file)[0]}_segment{seg_idx + 1}.mp3")
            segment.export(seg_path, format="mp3")
            saved_segments.append(seg_path)

        all_segments.append(saved_segments)
        segment_durations.append(segment.duration_seconds * 1_000_000)  # 微秒

    # Step 5: 随机选择每个段来自哪个视频
    selected_segments = []
    used_video_indices = set()

    for seg_idx in range(4):  # 共4段
        while True:
            video_idx = random.randint(0, num_videos - 1)
            if video_idx not in used_video_indices:
                used_video_indices.add(video_idx)
                selected_segments.append(all_segments[video_idx][seg_idx])
                break

    # Step 6: 合并音频
    print(f"🎵 选择的音频片段为：{selected_segments}")

    final_audio = sum(AudioSegment.from_mp3(path) for path in selected_segments)
    final_audio_path = os.path.join(audio_dir, "final_audio.mp3")
    final_audio.export(final_audio_path, format="mp3")
    print(f"🎵 最终音频已生成：{final_audio_path}")

    # Step 7: 创建剪映草稿
    base_folder = os.path.join(
        os.getenv("LOCALAPPDATA"),
        "JianyingPro\\User Data\\Projects\\com.lveditor.draft"
    )
    draft_folder_name = '找到唱歌的顺序'
    DUMP_PATH = os.path.join(base_folder, draft_folder_name, "draft_content.json")
    os.makedirs(os.path.dirname(DUMP_PATH), exist_ok=True)
    script = draft.Script_file(1080, 1920)
    anim = [Text_loop_anim.彩色火焰, Text_loop_anim.心跳]
    if video_files:
        # 取第一个视频文件作为 first_video_path
        first_video_path = os.path.join(video_folder, video_files[0])
        print(f"✅ 第一个视频路径为: {first_video_path}")
    else:
        raise FileNotFoundError("未找到任何 .mp4 视频文件")

    # 加载第一个视频
    print("📘 正在加载第一个视频...")
    video = VideoFileClip(first_video_path)
    # 添加标题文本
    text_segment_1 = draft.Text_segment(
        "What’s the singing order?",
        trange("0s", video.duration),
        font=Font_type.新青年体,
        style=Text_style(size=13.0, color=(1.0, 1.0, 1.0), underline=False, align=1),
        clip_settings=Clip_settings(transform_y=0)
    )
    anim_type=random.choice(anim)
    text_segment_1.add_animation(anim_type, "2.5s")

    # # 添加标题文本
    # text_segment_2 = draft.Text_segment(
    #     "Let's find out!",
    #     trange("13s", "3s"),
    #     font=Font_type.新青年体,
    #     style=Text_style(size=20.0, color=(1.0, 1.0, 1.0), underline=False, align=1),
    #     clip_settings=Clip_settings(transform_y=0)
    # )
    script.add_track(draft.Track_type.text, track_name="text-title", relative_index=100)

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
    text_segment_1.add_effect(selected_effect)
    script.add_segment(text_segment_1, "text-title")
    # selected_effect = random.choice(effect_ids)
    # text_segment_2.add_effect(selected_effect)
    # script.add_segment(text_segment_2, "text-title")

    # Step 8: 添加音频轨道（完整拼接的音频）
    final_audio_material = draft.Audio_material(final_audio_path)
    final_audio_segment = draft.Audio_segment(
        final_audio_material,
        draft.Timerange(0, final_audio_material.duration)
    )
    script.add_track(draft.Track_type.audio, track_name="final-audio-track", relative_index=10)
    script.add_segment(final_audio_segment, "final-audio-track")

    # Step 9: 添加视频轨道（仅画面）
    cumulative_time = 0

    anim_type = random.choice(anim)
    for idx, video_file in enumerate(video_files):
        video_path = os.path.join(video_folder, "trimmed", video_file)
        clip = VideoFileClip(video_path)
        duration_us = int(clip.duration * 1_000_000)

        if idx == 0:
            first_video_duration = clip.duration  # 保存第一个视频的时长（秒）
            # 提取最后一帧
        _, last_frame_path = extract_video_frames(video_path)
        # 添加视频轨道
        track_name = f'{idx}-{video_file}-video'
        script.add_track(draft.Track_type.video, track_name=track_name, relative_index=idx * 2 + 10)

        # 添加视频素材
        video_material = draft.Video_material(video_path)
        video_segment = draft.Video_segment(
            video_material,
            draft.Timerange(0, video_material.duration),
            source_timerange=draft.Timerange(0, video_material.duration),
            volume=0,
            clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5,
                                        transform_x={0: -0.5, 1: 0.5, 2: -0.5, 3: 0.5}.get(idx, 0),
                                        transform_y={0: 0.5, 1: 0.5, 2: -0.5, 3: -0.5}.get(idx, 0))

        )
        script.add_segment(video_segment, track_name)

        # 添加序号文字
        script.add_track(draft.Track_type.text, track_name=f'text-index-{idx}', relative_index=idx * 2 + 99)
        seg = draft.Text_segment(
            str(idx + 1),
            trange(0, video_material.duration),
            font=Font_type.新青年体,
            style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1),
            clip_settings=Clip_settings(
                transform_x=-0.2 if idx % 2 == 0 else 0.2,
                transform_y=-0.2 if idx >= 2 else 0.2
            )
        )

        seg.add_animation(anim_type, "2.5s")
        script.add_segment(seg, f"text-index-{idx}")

        # 添加最后一帧图片，持续时间 20s (20_000_000 微秒)
        image_start_time = video_material.duration
        image_end_time = image_start_time + 20_000_000  # 20秒
        add_image(
            script,
            image_start_time,
            image_end_time,
            last_frame_path,
            f"{idx}-last-frame",
            (idx + 5) * 2,
            transform_x={0: -0.5, 1: 0.5, 2: -0.5, 3: 0.5}.get(idx, 0),
            transform_y={0: 0.5, 1: 0.5, 2: -0.5, 3: -0.5}.get(idx, 0)
        )

        cumulative_time += duration_us

    # Step 10: 保存脚本并导出视频
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

    # 裁剪视频为第一个视频的长度
    output_video = VideoFileClip(output_path)
    clipped_video = output_video.subclipped(0, first_video_duration)  # 使用第一个视频的时长裁剪
    clipped_output_path = os.path.join(OUTPUT_PATH, f"{draft_folder_name}_{now_date}_裁剪版.mp4")
    clipped_video.write_videofile(clipped_output_path, codec="libx264", audio_codec="aac")
    print(f"✅ 视频已裁剪并保存至: {clipped_output_path}")

    return clipped_output_path
