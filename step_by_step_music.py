import datetime
import random

from moviepy import VideoFileClip
import os
import shutil
import librosa
import tempfile
import cv2
import pyJianYingDraft.pyJianYingDraft as draft
from pyJianYingDraft.pyJianYingDraft import Clip_settings, Export_resolution, Export_framerate, trange, Font_type, \
    Text_style, Text_loop_anim

root_dir = os.path.dirname(os.path.abspath(__file__))


def export_step_by_step_music_video(video_folder):
    # === 第一步：从第一个视频提取卡点时间点 ===

    # 获取 video_folder 路径下的所有 .mp4 视频文件
    video_files = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
    random.shuffle(video_files)
    # 检查是否存在至少一个视频文件
    if video_files:
        # 取第一个视频文件作为 first_video_path
        first_video_path = os.path.join(video_folder, video_files[0])
        print(f"✅ 第一个视频路径为: {first_video_path}")
    else:
        raise FileNotFoundError("未找到任何 .mp4 视频文件")

    # 加载第一个视频
    print("📘 正在加载第一个视频...")
    video = VideoFileClip(first_video_path)

    # 创建临时目录保存音频
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "audio.wav")
    print(f"📁 已创建临时音频文件夹: {temp_dir}")

    # 提取音频并保存为 WAV 文件
    print("🎵 正在提取音频...")
    video.audio.write_audiofile(audio_path, codec='pcm_s16le')

    # 提取音频并检测节拍
    print("🎼 正在分析音频节奏...")
    y, sr = librosa.load(audio_path, sr=None)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # 设置最小间隔为 5 秒，并过滤密集卡点
    segment_duration = 4
    # if video.duration / 4.5 > 10:
    #     segment_duration = 4.5
    # if video.duration / 7 > 7:
    #     segment_duration = 7

    MIN_INTERVAL = video.duration / segment_duration - 0.5
    MAX_INTERVAL = video.duration / segment_duration
    filtered_beat_times = []
    last_time = -MIN_INTERVAL

    for time in sorted(beat_times):
        interval = time - last_time
        if interval >= MIN_INTERVAL:
            # 如果间隔超过最大间隔，可以插入一个中间点
            while interval > MAX_INTERVAL:
                last_time += MAX_INTERVAL
                filtered_beat_times.append(last_time)
                interval = time - last_time
            filtered_beat_times.append(time)
            last_time = time

    rounded_beat_times = [round(t, 2) for t in filtered_beat_times]
    print(f"✅ 检测到节奏卡点时间（秒）：{rounded_beat_times}")

    # 构造片段区间
    segments = [(rounded_beat_times[i], rounded_beat_times[i + 1]) for i in range(len(rounded_beat_times) - 1)]

    if filtered_beat_times:
        last_time = rounded_beat_times[-1]
        if last_time < video.duration:  # 确保还有剩余内容
            segments.append((last_time, video.duration))
            print(f"📎 已添加尾段：{last_time:.2f}s 到 {video.duration:.2f}s")
    print(f"✂️ 已构造视频{len(segments)}个片段区间：{segments}")

    # 删除临时音频文件
    shutil.rmtree(temp_dir)
    print("🗑️ 已删除临时音频文件")

    # === 第二步：遍历所有视频，按上述片段截图 ===
    # 2.1 剪映草稿生成

    base_folder = os.path.join(
        # LOCALAPPDATA 是 Windows 系统中的一个环境变量，表示当前用户的本地应用程序数据存储路径
        # C:\Users\<用户名>\AppData\Local
        os.getenv("LOCALAPPDATA"),
        "JianyingPro\\User Data\\Projects\\com.lveditor.draft"
    )
    draft_folder_name = '四宫格接力翻唱'
    # 保存路径
    DUMP_PATH = os.path.join(base_folder, draft_folder_name, "draft_content.json")
    os.makedirs(os.path.dirname(DUMP_PATH), exist_ok=True)

    # 创建剪映草稿
    script = draft.Script_file(1080, 1920)  # 1920x1080分辨率

    script.add_track(draft.Track_type.text, track_name=f'text-title', relative_index=100)
    text = "Can You Keep Up with the Lyrics?"
    # "Which cover is best?"
    text_segment = draft.Text_segment(text, trange("0s", "10s"),
                                      font=Font_type.新青年体,
                                      style=Text_style(size=14.0, color=(1.0, 1.0, 1.0), underline=False, align=1),
                                      clip_settings=Clip_settings(transform_y=0))
    effect_ids = [
        "7351319129124506930",
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

    # 2.2 一边保存素材，一边生成剪映草稿

    output_folder = os.path.join(video_folder, "captured_frames")
    os.makedirs(output_folder, exist_ok=True)
    print(f"📸 图片输出路径已设置为: {output_folder}")

    video_files = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
    print(f"🎞️ 检测到以下视频文件：{video_files}")

    def add_video_material(start_time, output_video_path, transform_x, transform_y):
        video_material = draft.Video_material(output_video_path)
        print(f"🎬 添加视频：{output_video_path}，\n 开始时间{start_time}，时长{video_material.duration}")
        video_segment = draft.Video_segment(video_material,
                                            draft.Timerange(start_time, video_material.duration),
                                            source_timerange=draft.Timerange(0, video_material.duration),
                                            clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5,
                                                                        transform_x=transform_x,
                                                                        transform_y=transform_y))  # 与素材等长
        print(f"🎬 添加到视频轨道{idx}-{video_file}-video")
        # 添加到轨道
        script.add_segment(video_segment, f'{idx}-{video_file}-video', )
        start_time += video_material.duration
        return start_time, script

    # 增加封面轨道
    script.add_track(draft.Track_type.video, track_name=f'封面', relative_index=0)

    def add_end_frame_image(script, start_time, output_path_end, transform_x, transform_y):
        # if start_time + 1000000 < (video.duration * 1000000):
        script.add_track(draft.Track_type.video, track_name=f'{idx}-{output_path_end}-image',
                         relative_index=(idx + 5) * 2 - i + 1)
        video_material = draft.Video_material(output_path_end)
        print(f"图片添加视频：{output_video_path}，\n 开始时间{start_time}，时长{video_material.duration}")
        video_segment = draft.Video_segment(video_material,
                                            # 7s= 7000000
                                            target_timerange=draft.Timerange(start_time, MAX_INTERVAL * 1000000 * 3),
                                            source_timerange=draft.Timerange(0, video_material.duration),
                                            clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5,
                                                                        transform_x=transform_x,
                                                                        transform_y=transform_y))  # 与素材等长
        print(f"图片添加到视频轨道{idx}-{video_file}")
        # 添加到轨道
        script.add_segment(video_segment, f'{idx}-{output_path_end}-image', )

    #  增加emoji
    emoji = [
        "😊", "😄", "😃", "😁", "😆", "😅", "😂", "🤣", "☺️", "😇",
        "🥰", "😍", "🤩", "🥳", "🤗", "😋", "😌", "😏", "😎", "🤓",
        "👶", "😂", "🤣", "😅", "😆", "😈", "😺", "😸", "😻", "😽"
    ]
    for idx, video_file in enumerate(video_files):
        video_path = os.path.join(video_folder, video_file)
        print(f"\n🎬 正在处理视频：{video_file}")

        clip = VideoFileClip(video_path)
        print(f"⏱️ 视频总时长：{clip.duration:.2f} 秒")

        # 添加视频轨道
        script.add_track(draft.Track_type.video, track_name=f'{idx}-{video_file}-video', relative_index=idx * 2 + 100)
        script.add_track(draft.Track_type.text, track_name=f'text-index-{idx}', relative_index=idx * 2 + 200)

        start_time = 0

        random_emoji = random.choice(emoji)

        if idx == 0:
            seg = draft.Text_segment(f"{random_emoji}", trange("0s", f"{int(clip.duration)}s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=12, color=(1.0, 1.0, 1.0), underline=False, align=1,
                                                      bold=True),
                                     clip_settings=Clip_settings(transform_x=-0.2,
                                                                 transform_y=0.2))

        elif idx == 1:

            seg = draft.Text_segment(f"{random_emoji}", trange("0s", f"{int(clip.duration)}s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=12, color=(1.0, 1.0, 1.0), underline=False, align=1,
                                                      bold=True),
                                     clip_settings=Clip_settings(transform_x=0.2, transform_y=0.2))

        elif idx == 2:

            seg = draft.Text_segment(f"{random_emoji}", trange("0s", f"{int(clip.duration)}s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=12, color=(1.0, 1.0, 1.0), underline=False, align=1,
                                                      bold=True),
                                     clip_settings=Clip_settings(transform_x=-0.2,
                                                                 transform_y=-0.2))

        else:

            seg = draft.Text_segment(f"{random_emoji}", trange("0s", f"{int(clip.duration)}s"),
                                     font=Font_type.新青年体,
                                     style=Text_style(size=15, color=(1.0, 1.0, 1.0), underline=False, align=1,
                                                      bold=True),
                                     clip_settings=Clip_settings(transform_x=0.2,
                                                                 transform_y=-0.2))
        seg.add_animation(Text_loop_anim.彩色火焰)
        script.add_segment(seg, f"text-index-{idx}")

        # 裁剪的节点片段
        for i, (start, end) in enumerate(segments):

            print(f"\n📌 处理第 {i} 个片段：开始时间={start:.2f}s，结束时间={end:.2f}s")

            # 提取第一帧（start）
            try:
                frame_start = clip.get_frame(start)
            except Exception as e:
                print(f"[❌ 错误] 获取起始帧失败: {e}")
                continue

            # 提取最后一帧（end）
            try:
                frame_end = clip.get_frame(end)
            except Exception as e:
                print(f"[❌ 错误] 获取结束帧失败: {e}")
                continue

            # 转换为 OpenCV 可用的 BGR 格式
            frame_start_bgr = cv2.cvtColor(frame_start, cv2.COLOR_RGB2BGR)
            frame_end_bgr = cv2.cvtColor(frame_end, cv2.COLOR_RGB2BGR)

            # 构造输出路径
            base_name = os.path.splitext(video_file)[0]

            output_path_start = os.path.join(
                output_folder,
                f"{base_name}_seg_{i:03d}_start_{start:.2f}.jpg"
            )
            output_path_end = os.path.join(
                output_folder,
                f"{base_name}_seg_{i:03d}_end_{end:.2f}.jpg"
            )

            # 保存第一帧
            success = cv2.imwrite(output_path_start, frame_start_bgr)
            if not success:
                print(f"[❌ 错误] 图片保存失败：{output_path_start}")
            # else:
            #     print(f"✅ 已保存起始帧图片至：{output_path_start}")

            # 保存最后一帧
            success = cv2.imwrite(output_path_end, frame_end_bgr)
            if not success:
                print(f"[❌ 错误] 图片保存失败：{output_path_end}")
            # else:
            #     print(f"✅ 已保存结束帧图片至：{output_path_end}")

            # 创建片段视频输出目录
            segment_video_folder = os.path.join(video_folder, "segment_videos", base_name)
            os.makedirs(segment_video_folder, exist_ok=True)

            # 截取片段并保存
            # 示例修复代码
            end = min(end, clip.duration, video.duration)  # 自动限制 end 不超过视频长度
            if start >= end:
                continue
            sub_clip = clip.subclipped(start, end)

            output_video_path = os.path.join(
                segment_video_folder,
                f"{base_name}_seg_{i:03d}_{start:.2f}_{end:.2f}.mp4"
            )

            # 写入视频文件（使用 libx264 编码）
            sub_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac", logger=None)
            # sub_clip.close()
            print(f"💾 已保存视频片段至：{output_video_path}")

            if idx == 0 and i % 4 == 0:
                # 第一个宫格视频添加视频轨道
                start_time, script = add_video_material(start_time, output_video_path, transform_x=-0.5,
                                                        transform_y=0.5)
                # 添加静止图片
                add_end_frame_image(script, start_time, output_path_end, transform_x=-0.5, transform_y=0.5)



            elif idx == 1 and i % 4 == 1:
                # 第二个宫格视频添加视频轨道

                if i == 1:
                    # 添加首帧图片
                    # 生成每个轨道的草稿脚本
                    script.add_track(draft.Track_type.video, track_name=f'{idx}-{output_path_start}-image',
                                     relative_index=idx * 2 - i)
                    video_material = draft.Video_material(output_path_start)
                    video_segment = draft.Video_segment(video_material,
                                                        target_timerange=draft.Timerange(0, start_time),
                                                        source_timerange=draft.Timerange(0, video_material.duration),
                                                        clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5,
                                                                                    transform_x=0.5,
                                                                                    transform_y=0.5))  # 与素材等长
                    # 添加到轨道
                    script.add_segment(video_segment, f'{idx}-{output_path_start}-image', )

                # 添加视频
                start_time, script = add_video_material(start_time, output_video_path, transform_x=0.5, transform_y=0.5)

                # 添加静止图片
                add_end_frame_image(script, start_time, output_path_end, transform_x=0.5, transform_y=0.5)


            elif idx == 2 and i % 4 == 2:
                if i == 2:
                    # 添加首帧图片
                    # 生成每个轨道的草稿脚本
                    script.add_track(draft.Track_type.video, track_name=f'{idx}-{output_path_start}-image',
                                     relative_index=idx * 2 - i)
                    video_material = draft.Video_material(output_path_start)
                    video_segment = draft.Video_segment(video_material,
                                                        target_timerange=draft.Timerange(0, start_time),
                                                        source_timerange=draft.Timerange(0, video_material.duration),
                                                        clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5,
                                                                                    transform_x=-0.5,
                                                                                    transform_y=-0.5))  # 与素材等长
                    # 添加到轨道
                    script.add_segment(video_segment, f'{idx}-{output_path_start}-image', )
                # 第三个宫格视频添加视频轨道
                start_time, script = add_video_material(start_time, output_video_path, transform_x=-0.5,
                                                        transform_y=-0.5)

                # 添加静止图片
                add_end_frame_image(script, start_time, output_path_end, transform_x=-0.5, transform_y=-0.5)

            elif idx == 3 and i % 4 == 3:
                if i == 3:
                    # 添加首帧图片
                    # 生成每个轨道的草稿脚本
                    script.add_track(draft.Track_type.video, track_name=f'{idx}-{output_path_start}-image',
                                     relative_index=idx * 2 - i)
                    video_material = draft.Video_material(output_path_start)
                    video_segment = draft.Video_segment(video_material,
                                                        target_timerange=draft.Timerange(0, start_time),
                                                        source_timerange=draft.Timerange(0, video_material.duration),
                                                        clip_settings=Clip_settings(scale_x=0.5, scale_y=0.5,
                                                                                    transform_x=0.5,
                                                                                    transform_y=-0.5))  # 与素材等长
                    # 添加到轨道
                    script.add_segment(video_segment, f'{idx}-{output_path_start}-image', )
                # 第四个宫格视频添加视频轨道
                start_time, script = add_video_material(start_time, output_video_path, transform_x=0.5,
                                                        transform_y=-0.5)
                # 添加静止图片
                add_end_frame_image(script, start_time, output_path_end, transform_x=0.5, transform_y=-0.5)

            else:
                video_material = draft.Video_material(output_video_path)
                start_time += video_material.duration

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

    # 使用视频长度裁剪视频
    output_video = VideoFileClip(output_path)

    # 使用原始视频的 duration 进行裁剪
    clipped_video = output_video.subclipped(0, video.duration)

    # 保存裁剪后的视频
    clipped_output_path = os.path.join(OUTPUT_PATH, f"{draft_folder_name}_{now_date}_裁剪版.mp4")
    clipped_video.write_videofile(clipped_output_path, codec="libx264", audio_codec="aac")

    print(f"✅ 视频已裁剪并保存至: {clipped_output_path}")

    return clipped_output_path
