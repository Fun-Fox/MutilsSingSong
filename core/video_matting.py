import os
import torch
import numpy as np
import cv2
from einops import rearrange, repeat
from PIL import ImageColor
from tqdm import tqdm
from moviepy import ImageSequenceClip, VideoFileClip, AudioFileClip

# 设置项目根目录和设备
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
device = 'cuda' if torch.cuda.is_available() else 'cpu'


def auto_downsample_ratio(h, w):
    """自动计算下采样比例，使视频的最大边不超过 512 像素"""
    return min(512 / max(h, w), 1)


def matting_video_to_images(video_path, output_folder, bg_color='white', batch_size=4, fp16=False, transparent=False):
    """
    对视频进行抠图处理，仅输出前景图像（不保存 mask 图像）
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    # 加载模型
    model_path = os.path.join(root_dir, 'models', 'mobilenetv3', 'rvm_resnet50_fp32.torchscript')
    assert os.path.exists(model_path), f"模型文件不存在：{model_path}"
    model = torch.jit.load(model_path, map_location=device).eval()
    if fp16:
        model.half()

    cap = cv2.VideoCapture(video_path)
    os.makedirs(output_folder, exist_ok=True)

    pbar = tqdm(total=total_frames, desc=f"处理 {os.path.basename(video_path)}")

    rec = [None] * 4
    frame_idx = 0

    while True:
        frames = []
        for _ in range(batch_size):
            ret, frame = cap.read()
            if not ret:
                break
            # 固定分辨率：1080 x 1920
            frame = cv2.resize(frame, (1080, 1920))
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0)

        if not frames:
            break

        video_frames = torch.from_numpy(np.stack(frames)).float()
        video_frames = rearrange(video_frames, "n h w c -> n c h w").to(device)
        if fp16:
            video_frames = video_frames.half()

        with torch.no_grad():
            try:
                fgrs, phas, *rec = model(video_frames, *rec, auto_downsample_ratio(height, width))
            except Exception as e:
                print(f"处理帧时出错,后续帧处理跳过")
                break
            masks = phas.gt(0).float()  # 转为 float 避免 bool 减法错误

            if transparent:
                # 透明背景：前景 + mask 作为 alpha 通道
                fgrs = fgrs * masks + (1.0 - masks) * 1.0
            else:
                # 固定颜色背景
                # print(f"🎨 固定颜色背景：{bg_color}")
                bg = torch.Tensor(ImageColor.getrgb(bg_color)[:3]).float() / 255.
                bg = repeat(bg, "c -> n c h w", n=fgrs.shape[0], h=1, w=1).to(device)
                if fp16:
                    bg = bg.half()
                fgrs = fgrs * masks + bg * (1.0 - masks)

        fgrs = rearrange(fgrs.float().cpu(), "n c h w -> n h w c").numpy()

        for i, fgr in enumerate(fgrs):
            fgr = (fgr * 255).astype(np.uint8)
            if transparent:
                mask = (masks[i].cpu().numpy() * 255).astype(np.uint8)

                # 通用方式：先降维，再扩展通道维度
                if mask.ndim == 3:
                    mask = mask.squeeze(0)[..., None]  # 变为 [H, W, 1]
                elif mask.ndim == 4:
                    mask = mask.squeeze(0)[..., 0, None]  # 变为 [H, W, 1]

                rgba = np.concatenate([fgr, mask], axis=-1)  # shape: [H, W, 4]
                cv2.imwrite(os.path.join(output_folder, f"frame_{frame_idx:05d}_rgba.png"),
                            cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
            else:
                cv2.imwrite(os.path.join(output_folder, f"frame_{frame_idx:05d}_fgr.png"),
                            cv2.cvtColor(fgr, cv2.COLOR_RGB2BGR))
            frame_idx += 1
            pbar.update(1)

    cap.release()
    pbar.close()
    print("✅ 抠图完成，图像序列已保存至:", output_folder)

    # 返回视频基本信息，供后续使用
    return {
        'total_frames': total_frames,
        'fps': fps
    }


import os
import subprocess
import shutil
from pathlib import Path


def synthesize_video_from_images(output_folder, video_info, video_path, transparent=False):
    """
    使用 ffmpeg 从图像序列生成透明视频，并提取原始视频音频进行合成
    """
    fps = video_info['fps']
    file_name = os.path.splitext(os.path.basename(video_path))[0]

    if transparent:
        image_files = sorted(
            [os.path.join(output_folder, f) for f in os.listdir(output_folder) if f.endswith("_rgba.png")],
            key=lambda x: int(x.split("_")[-2])
        )
        output_video_path = os.path.join(os.path.dirname(output_folder), f"{file_name}_rgba.mov")
    else:
        image_files = sorted(
            [os.path.join(output_folder, f) for f in os.listdir(output_folder) if f.endswith("_fgr.png")],
            key=lambda x: int(x.split("_")[-2])
        )
        output_video_path = os.path.join(os.path.dirname(output_folder), f"{file_name}_fgr.mp4")

    if not image_files:
        print("⚠️ 未找到图像序列，无法生成视频。")
        return

    print("🎬 正在使用 ffmpeg 合成透明视频...")

    # 图像序列文件名格式
    image_pattern = os.path.join(output_folder, "frame_%05d_rgba.png" if transparent else "frame_%05d_fgr.png")

    # 生成临时音频文件路径
    audio_path = os.path.join(output_folder, "extracted_audio.aac")

    # Step 1: 提取原始视频音频
    print("🎵 正在提取原始视频音频...")
    cmd_extract_audio = [
        "ffmpeg",
        "-i", video_path,
        "-vn", "-acodec", "aac",
        "-y", audio_path
    ]
    subprocess.run(cmd_extract_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    has_audio = os.path.exists(audio_path)

    # Step 2: 使用 ffmpeg 合成透明视频
    # "ffmpeg -i %d.png -vcodec qtrle movie_with_alpha.mov"

    cmd_video = [
        "ffmpeg",
        "-framerate", str(fps),
        "-i", image_pattern,
        "-vcodec", "qtrle",  # 或 "libx264rgb"
        "-pix_fmt", "yuva420p",  # 支持 alpha 的像素格式
        "-y", output_video_path
    ]
    print("🎥 正在调用 ffmpeg 合成视频...")
    subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Step 3: 合并音频（如果存在）
    if has_audio:
        print("🔊 正在合成音频到视频...")
        final_video_path = output_video_path.replace(".mov",
                                                     "_with_audio.mov") if transparent else output_video_path.replace(
            ".mp4", "_with_audio.mp4")

        cmd_merge = [
            "ffmpeg",
            "-i", output_video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            "-shortest",
            "-y", final_video_path
        ]
        subprocess.run(cmd_merge, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"🎉 视频和音频已合成：{final_video_path}")
    else:
        print(f"🎉 视频已合成（无音频）：{output_video_path}")
    # 删除无声音的临时文件
    delete_video_file(output_video_path)
    # Step 4: 清理中间文件（可选）
    if os.path.exists(audio_path):
        os.remove(audio_path)


def delete_video_file(file_path):
    """
    删除指定的视频文件
    :param file_path: 要删除的文件路径
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ 成功删除文件: {file_path}")
        else:
            print(f"⚠️ 文件不存在: {file_path}")
    except Exception as e:
        print(f"❌ 删除文件失败: {e}")


def process_videos_in_folder(input_folder, output_folder, bg_color='white', batch_size=8, fp16=False,
                             transparent=False):
    """
    遍历文件夹中的视频并进行抠图处理（不保存 mask 图像）
    """
    supported_exts = ['.mp4', '.avi', '.mov', '.mkv']
    for filename in os.listdir(input_folder):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in supported_exts:
            video_path = os.path.join(input_folder, filename)
            file_name = os.path.splitext(filename)[0]
            out_dir = os.path.join(output_folder, file_name)

            print(f"\n🎥 开始处理视频: {filename}")
            video_info = matting_video_to_images(video_path, out_dir, bg_color, batch_size, fp16, transparent)
            synthesize_video_from_images(out_dir, video_info, video_path, transparent)


if __name__ == '__main__':
    input_folder = os.path.join(root_dir, "assets", "50")
    output_folder = os.path.join(root_dir, "assets", "50", "matting")  # 输出文件夹

    matting_args = dict(
        bg_color='black',  # 可选 black / white / transparent
        batch_size=8,
        fp16=True,  # 若 GPU 支持 FP16 推荐开启
        transparent=True  # 是否输出透明背景图像（RGBA）
    )

    process_videos_in_folder(input_folder, output_folder, **matting_args)
