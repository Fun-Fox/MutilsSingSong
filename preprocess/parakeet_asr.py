import os
import sys
from pathlib import Path
from moviepy import AudioFileClip  # 新增：使用 moviepy 获取音频时长
import datetime  # 新增：用于时间格式化

ROOT_DIR = Path(os.getcwd()).as_posix()
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HOME'] = ROOT_DIR + "/models"
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = 'true'

print("正在加载 NVIDIA NeMo ASR 模型...若不存在将下载")
print("模型名称: nvidia/parakeet-tdt-0.6b-v2")
print("这可能需要几分钟时间，请耐心等待...")

try:
    # 这一步会下载并加载模型，需要较长时间和网络连接
    import nemo.collections.asr as nemo_asr

    asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
    print("✅ NeMo ASR 模型加载成功！")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    print("请确保已正确安装 'nemo_toolkit[asr]' 及其依赖，并有可用的网络连接。")
    exit(1)

print("=" * 50)


# 新增：使用 moviepy 获取音频时长
def get_audio_duration(file_path: str) -> float:
    """使用 moviepy 获取音频文件的时长（秒）"""
    try:
        audio = AudioFileClip(file_path)
        return audio.duration
    except Exception as e:
        print(f"无法获取文件 '{file_path}' 的时长: {e}")
        return 0.0


# 新增：将秒数格式化为 SRT 时间戳格式
def format_srt_time(seconds: float) -> str:
    """将秒数格式化为 SRT 时间戳格式 HH:MM:SS,ms"""
    delta = datetime.timedelta(seconds=seconds)
    # 格式化为 0:00:05.123000
    s = str(delta)
    # 分割秒和微秒
    if '.' in s:
        parts = s.split('.')
        integer_part = parts[0]
        fractional_part = parts[1][:3]  # 取前三位毫秒
    else:
        integer_part = s
        fractional_part = "000"

    # 填充小时位
    if len(integer_part.split(':')) == 2:
        integer_part = "0:" + integer_part

    return f"{integer_part},{fractional_part}"


# 新增：将 NeMo 的分段时间戳转换为 SRT 格式字符串
def segments_to_srt(segments: list) -> str:
    """将 NeMo 的分段时间戳转换为 SRT 格式字符串"""
    srt_content = []
    for i, segment in enumerate(segments):
        start_time = format_srt_time(segment['start'])
        end_time = format_srt_time(segment['end'])
        text = segment['segment'].strip()

        srt_content.append(f"{i + 1}")
        srt_content.append(f"{start_time} --> {end_time}")
        srt_content.append(text)
        srt_content.append("")  # 空行

    return '\n'.join(srt_content)


# 新增：生成 SRT 字幕文件
def generate_srt_file(segments: list, output_srt_path: str):
    """生成 SRT 字幕文件"""
    srt_content = segments_to_srt(segments)
    with open(output_srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    print(f"✅ SRT 字幕文件已生成：{output_srt_path}")
    return output_srt_path


def transcribe_audio_with_nemo(audio_path, output_srt_path):
    """使用 NeMo ASR 模型转录音频文件并生成 SRT 字幕"""
    print(f"🔊 正在转录音频: {audio_path}")
    all_segments = []
    all_words = []
    cumulative_time_offset = 0.0
    try:
        # 对当前切片进行转录
        output = asr_model.transcribe([audio_path], timestamps=True)

        if output and output[0].timestamp:
            # 修正并收集 segment 时间戳
            if 'segment' in output[0].timestamp:
                for seg in output[0].timestamp['segment']:
                    seg['start'] += cumulative_time_offset
                    seg['end'] += cumulative_time_offset
                    all_segments.append(seg)

            # 修正并收集 word 时间戳
            if 'word' in output[0].timestamp:
                for word in output[0].timestamp['word']:
                    word['start'] += cumulative_time_offset
                    word['end'] += cumulative_time_offset
                    all_words.append(word)

        # 更新下一个切片的时间偏移量
        # 使用实际切片时长来更新，更精确
        chunk_actual_duration = get_audio_duration(audio_path)
        cumulative_time_offset += chunk_actual_duration

        # 生成 SRT 文件
        generate_srt_file(all_segments, output_srt_path)
        return output_srt_path
    except Exception as e:
        print(f"❌ 转录失败 {audio_path}: {str(e)}")
        return None


