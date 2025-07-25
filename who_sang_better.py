import datetime
import random
from moviepy import VideoFileClip
import os
import cv2
import pyJianYingDraft.pyJianYingDraft as draft
from pyJianYingDraft.pyJianYingDraft import Clip_settings, Export_resolution, Export_framerate, trange, Font_type, \
    Text_style, Text_loop_anim, Mask_type, Intro_type

root_dir = os.path.dirname(os.path.abspath(__file__))


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
    # video_segment.add_mask(Mask_type.矩形, center_x=0, center_y=-50, size=0.8, rect_width=0.8, round_corner=45)
    script.add_segment(video_segment, track_name)
    print(f"🖼️ 图片添加到轨道: {track_name}")


def add_video_material(script, track_name, relative_index, video_path, start_time, transform_x, transform_y):
    """添加视频素材到剪映轨道"""
    video_material = draft.Video_material(video_path)
    print(f"🎬 添加视频：{video_path}，开始时间 {start_time}，时长 {video_material.duration}")
    video_segment = draft.Video_segment(
        video_material,
        target_timerange=draft.Timerange(start_time, video_material.duration),
        source_timerange=draft.Timerange(0, video_material.duration),
        clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5, transform_x=transform_x, transform_y=transform_y)
    )
    # 添加到轨道
    # video_segment.add_mask(Mask_type.矩形, center_x=0, center_y=-50, size=0.8, rect_width=0.8, round_corner=45)

    script.add_track(draft.Track_type.video, track_name=track_name, relative_index=relative_index)
    script.add_segment(video_segment, track_name)
    return start_time + video_material.duration


def export_who_sang_it_better(video_folder, title_1="WHO SANG IT Better??",):
    # 如果trimmed 目录存在则清除
    # 获取视频文件列表
    # video_folder = os.path.join(video_folder, "trimmed")
    video_files = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
    video_files = random.sample(video_files, k=2)  # 随机选取2个
    random.shuffle(video_files)
    base_folder = os.path.join(
        os.getenv("LOCALAPPDATA"),
        "JianyingPro\\User Data\\Projects\\com.lveditor.draft"
    )
    draft_folder_name = '2人唱歌比拼'
    DUMP_PATH = os.path.join(base_folder, draft_folder_name, "draft_content.json")
    os.makedirs(os.path.dirname(DUMP_PATH), exist_ok=True)

    script = draft.Script_file(1080, 1920)  # 1920x1080分辨率

    # 添加标题文本
    script.add_track(draft.Track_type.text, track_name="text-title", relative_index=100)
    effect_ids = [
        "7351319129124506930", "7506817303296675123", "7507075178447359282",
        "6896144021568179469", "6896137924853763336", "7244707954585292064",
        "7404300897628540211"
    ]
    selected_effect = random.choice(effect_ids)
    if video_files:
        # 取第一个视频文件作为 first_video_path
        first_video_path = os.path.join(video_folder, video_files[0])
        print(f"✅ 第一个视频路径为: {first_video_path}")
    else:
        raise FileNotFoundError("未找到任何 .mp4 视频文件")

        # 加载第一个视频
    print("📘 正在加载第一个视频...")
    video = VideoFileClip(first_video_path)
    text_segment_1 = draft.Text_segment(
        title_1,
        trange("0s", f"{video.duration / 2}s"),
        font=Font_type.新青年体,
        style=Text_style(size=14.0, color=(1.0, 1.0, 1.0), underline=False, align=1),
        clip_settings=Clip_settings(transform_y=0.9)
    )
    anim = [Text_loop_anim.彩色火焰, Text_loop_anim.心跳]
    anim_type = random.choice(anim)
    text_segment_1.add_animation(anim_type, "2.5s")

    # text_segment_2 = draft.Text_segment(
    #     title_2,
    #     trange(f"{video.duration / 2}s", f"{video.duration / 2}s"),
    #     font=Font_type.新青年体,
    #     style=Text_style(size=14.0, color=(1.0, 1.0, 1.0), underline=False, align=1),
    #     clip_settings=Clip_settings(transform_y=0.8)
    # )
    text_segment_1.add_effect(selected_effect)
    selected_effect = random.choice(effect_ids)
    # text_segment_2.add_effect(selected_effect)
    # text_segment_2.add_animation(anim_type, "2.5s")
    script.add_segment(text_segment_1, "text-title")
    # script.add_segment(text_segment_2, "text-title")

    total_duration = 0
    start_time = 0
    # 增加封面轨道
    script.add_track(draft.Track_type.video, track_name=f'封面', relative_index=0)

    anim_type = random.choice(anim)
    for idx, video_file in enumerate(video_files, start=1):
        full_video_path = os.path.join(video_folder, video_file)
        first_frame, last_frame = extract_video_frames(full_video_path)

        track_video_name = f'{idx}-{video_file}-video'
        track_relative_index = idx * 2 + 100
        video_material = draft.Video_material(full_video_path)
        video_duration = video_material.duration
        script.add_track(draft.Track_type.text, track_name=f'text-index-{idx}', relative_index=idx * 2 + 200)

        if idx == 1:
            seg = draft.Text_segment(f"Cover {idx}", trange("0s", f"120s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1,
                                                      bold=True),
                                     clip_settings=Clip_settings(transform_x=-0.7,
                                                                 transform_y=0.7))
            seg.add_animation(anim_type, "2.5s")
            script.add_segment(seg, f"text-index-{idx}")
            start_time = add_video_material(script, track_video_name, track_relative_index, full_video_path, start_time,
                                            -0.5, 0)
            add_image(script, start_time, start_time + 80000000, last_frame, f"{idx}-last-frame", (idx + 5) * 2, -0.5,
                      0)
        elif idx == 2:
            seg = draft.Text_segment(f"Cover {idx}", trange("0s", f"120s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1,
                                                      bold=True),
                                     clip_settings=Clip_settings(transform_x=0.7,
                                                                 transform_y=0.7))
            seg.add_animation(anim_type, "2.5s")
            script.add_segment(seg, f"text-index-{idx}")
            add_image(script, 0, start_time, first_frame, f"{idx}-first-frame", (idx + 5) * 2, 0.5, 0)
            start_time = add_video_material(script, track_video_name, track_relative_index, full_video_path, start_time,
                                            0.5, 0)
            add_image(script, start_time, start_time + 50000000, last_frame, f"{idx}-last-frame", (idx + 5) * 2, 0.5,
                      0)
        # elif idx == 3:
        #     seg = draft.Text_segment(f"{idx}", trange("13s", f"120s"),
        #                              font=Font_type.新青年体,
        #                              style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1,
        #                                               bold=True),
        #                              clip_settings=Clip_settings(transform_x=-0.2,
        #                                                          transform_y=-0.2))
        #     seg.add_animation(anim_type, "2.5s")
        #     script.add_segment(seg, f"text-index-{idx}")
        #     add_image(script, 0, start_time, first_frame, f"{idx}-first-frame", (idx + 5) * 2, -0.5, -0.5)
        #     start_time = add_video_material(script, track_video_name, track_relative_index, full_video_path, start_time,
        #                                     -0.5, -0.5)
        #     add_image(script, start_time, start_time + 50000000, last_frame, f"{idx}-last-frame", (idx + 5) * 2, -0.5,
        #               -0.5)
        # elif idx == 4:
        #     seg = draft.Text_segment(f"{idx}", trange("13s", f"120s"),
        #                              font=Font_type.新青年体,
        #                              style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1,
        #                                               bold=True),
        #                              clip_settings=Clip_settings(transform_x=0.2,
        #                                                          transform_y=-0.2))
        #     seg.add_animation(anim_type, "2.5s")
        #     script.add_segment(seg, f"text-index-{idx}")
        #     add_image(script, 0, start_time, first_frame, f"{idx}-first-frame", (idx + 5) * 2, 0.5, -0.5)
        #     start_time = add_video_material(script, track_video_name, track_relative_index, full_video_path, start_time,
        #                                     0.5, -0.5)

        total_duration += video_duration
    # 结尾 欢迎关注部分
    # render_index_track_mode_on
    # 开启自由层级
    script.add_track(draft.Track_type.video, track_name=f'end', absolute_index=99990)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_end_path = os.path.join(current_dir, 'doc', "end.jpg")
    video_material = draft.Video_material(image_end_path)
    video_segment = draft.Video_segment(video_material,
                                        target_timerange=trange(f'{(total_duration / 1e6)}s', "4s"), )  # 与素材等长
    #
    video_segment.add_animation(Intro_type.画出爱心, "1s")

    script.add_segment(video_segment, f'end', )

    script.add_track(draft.Track_type.text, track_name=f'text-1', absolute_index=99992)
    text_1 = draft.Text_segment(f"""
Follow me!
Grab your crew
Unlock 4 bangers:
""", trange(f'{(total_duration / 1e6) + 1}s', "3s"),
                                font=Font_type.新青年体,
                                style=Text_style(size=15, color=(0.8, 0.8, 0.8), underline=False, align=0),
                                clip_settings=Clip_settings(transform_x=0,
                                                            transform_y=0.5)
                                )
    script.add_track(draft.Track_type.text, track_name=f'text-2', absolute_index=99994)

    text_2 = draft.Text_segment(f"""
• Guess Who’s Singing
• Song Order Showdown
• Sing-Along Frenzy
• Cover Duel
""", trange(f'{(total_duration / 1e6) + 1}s', "3s"),
                                font=Font_type.新青年体,
                                style=Text_style(size=13, color=(1.0, 1.0, 1.0), underline=False, align=0),
                                clip_settings=Clip_settings(transform_x=0,
                                                            transform_y=0)
                                )
    script.add_track(draft.Track_type.text, track_name=f'text-3', absolute_index=99996)
    text_3 = draft.Text_segment(f"""
Total vibes, nonstop fun!
""", trange(f'{(total_duration / 1e6) + 1}s', "3s"),
                                font=Font_type.新青年体,
                                style=Text_style(size=14, color=(0.5, 0.5, 0.5), underline=False, align=0),
                                clip_settings=Clip_settings(transform_x=0,
                                                            transform_y=-0.5)
                                )
    script.add_segment(text_1, f"text-1")
    script.add_segment(text_2, f"text-2")
    script.add_segment(text_3, f"text-3")

    script.add_track(draft.Track_type.sticker, track_name=f'sticker-1', absolute_index=99997)
    script.add_track(draft.Track_type.sticker, track_name=f'sticker-2', absolute_index=99998)
    script.add_track(draft.Track_type.sticker, track_name=f'sticker-3', absolute_index=99999)
    sticker_segment_1 = draft.Sticker_segment("7210227770583043383",
                                              trange(f'{(total_duration / 1e6) + 1}s', "3s"),
                                              clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5, transform_x=0.4,
                                                                          transform_y=-0.2))

    sticker_segment_2 = draft.Sticker_segment("7210227770583043383",
                                              trange(f'{(total_duration / 1e6) + 1}s', "3s"),
                                              clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5, transform_x=0.4,
                                                                          transform_y=-0.4))

    sticker_segment_3 = draft.Sticker_segment("7210227770583043383",
                                              trange(f'{(total_duration / 1e6) + 1}s', "3s"),
                                              clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5, transform_x=0.4,
                                                                          transform_y=-0.6))
    script.add_segment(sticker_segment_1, f"sticker-1")
    script.add_segment(sticker_segment_2, f"sticker-2")
    script.add_segment(sticker_segment_3, f"sticker-3")
    script.dump(DUMP_PATH)
    print("\n🎉 所有视频片段及截图已成功处理！")

    ctrl = draft.Jianying_controller()
    OUTPUT_PATH = os.path.join(root_dir, "output")
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    now_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(OUTPUT_PATH, f"{draft_folder_name}_{now_date}.mp4")

    ctrl.export_draft(draft_folder_name, output_path,
                      resolution=Export_resolution.RES_1080P,
                      framerate=Export_framerate.FR_24)
    print(f"导出视频完成: {output_path}")

    # 裁剪视频
    output_video = VideoFileClip(output_path)
    clipped_video = output_video.subclipped(0, (total_duration / 1e6) + 4)
    clipped_output_path = os.path.join(OUTPUT_PATH, f"{draft_folder_name}_{now_date}_裁剪版.mp4")
    clipped_video.write_videofile(clipped_output_path, codec="libx264", audio_codec="aac")
    print(f"✅ 视频已裁剪并保存至: {clipped_output_path}")

    return clipped_output_path
