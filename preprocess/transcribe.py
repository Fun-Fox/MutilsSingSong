import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from faster_whisper import WhisperModel
from moviepy import VideoFileClip
import warnings

# 定义模型存放位置
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_MODEL_PATH = os.path.join(root_dir, 'models', "large-v3")
AUDIO_DIR = os.path.join(root_dir, "audios")  # 音频文件存储目录
OUTPUT_DIR = os.path.join(root_dir, "output")  # 输出目录

from difflib import SequenceMatcher

def are_all_sentences_similar(seg1, seg2, threshold=0.8):
    """
    判断两个歌词片段的每一句是否都相似（每句相似度 >= threshold）
    :param seg1: 片段1 (tuple)
    :param seg2: 片段2 (tuple)
    :param threshold: 相似度阈值
    :return: True/False
    """
    if len(seg1) != len(seg2):
        return False  # 只比较长度相同的片段

    return all(SequenceMatcher(None, s1, s2).ratio() >= threshold for s1, s2 in zip(seg1, seg2))



class WhisperModelSingleton:
    _instance = None
    _model = None

    def __new__(cls, model_size="large-v3", device="cuda"):
        if cls._instance is None:
            cls._instance = super(WhisperModelSingleton, cls).__new__(cls)

            warnings.filterwarnings("ignore", category=FutureWarning)
            warnings.filterwarnings("ignore", category=UserWarning)
            # 如果本地存在模型，则从本地加载
            if os.path.exists(LOCAL_MODEL_PATH):
                print(f"📦 正在从本地加载模型: {LOCAL_MODEL_PATH}")
                cls._model = WhisperModel(
                    model_size_or_path=LOCAL_MODEL_PATH,
                    device=device,
                )
            else:
                print(f"🌐 未找到本地模型，正在从远程下载: {model_size}")
                cls._model = WhisperModel(
                    model_size_or_path=model_size,
                    device=device,
                )
        return cls._instance

    def transcribe(self, audio_path, **kwargs):
        """
        调用 whisper 模型进行语音识别
        :param audio_path: 音频文件路径
        :param kwargs: 其他 transcribe 参数
        :return: segments, info
        """
        segments, info = self._model.transcribe(audio_path, **kwargs)
        segments = list(segments)
        return segments, info


# 提供一个全局接口调用
def get_whisper_model():
    """
    获取单例的 Whisper 模型
    """
    return WhisperModelSingleton()


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"


def generate_srt(segments, output_srt_path):
    with open(output_srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments):
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            text = segment.text.strip()

            f.write(f"{i + 1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
    print(f"✅ SRT 字幕文件已生成：{output_srt_path}")


def extract_audio_from_videos(video_dir, output_dir=AUDIO_DIR):
    """从视频目录提取音频"""
    os.makedirs(output_dir, exist_ok=True)
    audio_files = []

    for video_file in os.listdir(video_dir):
        if video_file.endswith(('.mp4', '.avi', '.mov')):
            video_path = os.path.join(video_dir, video_file)
            audio_path = os.path.join(output_dir, os.path.splitext(video_file)[0] + ".wav")

            if not os.path.exists(audio_path):
                try:
                    video = VideoFileClip(video_path)
                    video.audio.write_audiofile(audio_path, codec='pcm_s16le')
                    audio_files.append(audio_path)
                except Exception as e:
                    print(f"❌ 提取音频失败 {video_file}: {str(e)}")
            else:
                audio_files.append(audio_path)
    return audio_files


def batch_transcribe_audio(audio_files):
    """批量转录音频文件"""
    whisper = get_whisper_model()
    srt_files = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for audio_path in audio_files:
            base_name = os.path.basename(audio_path).replace(".wav", "")
            output_srt_path = os.path.join(OUTPUT_DIR, f"{base_name}.srt")

            if not os.path.exists(output_srt_path):
                future = executor.submit(process_single_audio, whisper, audio_path, output_srt_path)
                futures.append((future, output_srt_path))  # ✅ 把 future 和 srt_path 一起保存
            else:
                srt_files.append(output_srt_path)
        for future, srt_path in futures:
            try:
                future.result()
                srt_files.append(srt_path)
            except Exception as e:
                print(f"❌ 转录失败: {str(e)}")

    return srt_files


def process_single_audio(whisper, audio_path, output_srt_path):
    """处理单个音频文件"""
    print(f"🔊 处理音频: {audio_path}")
    segments, _ = whisper.transcribe(audio_path, beam_size=5, language="zh", condition_on_previous_text=False)
    generate_srt(segments, output_srt_path)
    return output_srt_path


def load_srt_content(srt_file):
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read().strip().split('\n\n')
    lyrics = []
    for block in content:
        lines = block.split('\n')
        if len(lines) >= 3:
            lyrics.append(lines[2].strip())  # 提取歌词文本
    return lyrics


def parse_time(time_str):
    """解析时间字符串为秒数"""
    h, m, s = time_str.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(f"{s[:2]}.{s[3:]}")


def extract_segments_multi_length(lyrics_list, min_length=3, max_length=7):
    """
    提取所有长度在 [min_length, max_length] 范围内的连续歌词片段
    """
    segments = []
    for length in range(min_length, max_length + 1):
        for i in range(len(lyrics_list) - length + 1):
            segment = tuple(lyrics_list[i:i + length])
            segments.append((segment, length))  # 带上长度信息用于后续处理
    return segments


def merge_overlapping_segments(candidate_segments):
    """
    合并重复/包含关系的片段，保留最长且不被其他片段包含的片段
    :param candidate_segments: [(segment, files, length), ...]
    :return: merged_segments
    """
    # 先按长度排序，长的优先保留
    sorted_segments = sorted(candidate_segments, key=lambda x: -x[2])

    result = []
    used_indices = set()

    for i, (seg, files, length) in enumerate(sorted_segments):
        is_contained = False
        for j, (seg_j, _, _) in enumerate(sorted_segments):
            if i == j or j in used_indices:
                continue
            # 如果当前片段被更长的片段包含，则跳过
            if is_segment_contained(seg, seg_j):
                is_contained = True
                break
        if not is_contained:
            result.append((seg, files))
            used_indices.add(i)

    return result


def is_segment_contained(shorter, longer):
    """判断 shorter 是否完全包含在 longer 中"""
    shorter_str = " ".join(shorter)
    longer_str = " ".join(longer)
    return shorter_str in longer_str and len(shorter) < len(longer)


from itertools import combinations


def find_common_segments(srt_files, min_files=4, min_segment_length=4, max_segment_length=10, similarity_threshold=0.8):
    file_lyrics = {}
    all_segments = []

    # 提取每个文件中的所有片段
    for srt_file in srt_files:
        lyrics = load_srt_content(srt_file)
        segments_with_length = extract_segments_multi_length(lyrics, min_segment_length, max_segment_length)
        segments_only = [seg for seg, length in segments_with_length]
        file_lyrics[srt_file] = lyrics
        all_segments.extend(segments_only)

    # 构建一个“主片段池”，用于合并相似片段
    unique_segments = []
    # 在构建主片段池时使用新函数
    for segment in all_segments:
        matched = False
        for us in unique_segments:
            if are_all_sentences_similar(segment, us, similarity_threshold):
                matched = True
                break
        if not matched:
            unique_segments.append(segment)

    # 统计每个主片段出现在哪些文件中
    segment_to_files = defaultdict(set)
    for srt_file in srt_files:
        lyrics = file_lyrics[srt_file]
        segments_only = extract_segments_multi_length(lyrics, min_segment_length, max_segment_length)
        segments_only = [seg for seg, length in segments_only]
        # 统计每个主片段出现在哪些文件中
        for seg in segments_only:
            for main_seg in unique_segments:
                if are_all_sentences_similar(seg, main_seg, similarity_threshold):
                    segment_to_files[main_seg].add(srt_file)
                    break

    # 筛选出现次数 >= min_files 的片段
    candidate_segments = [
        (seg, list(files)) for seg, files in segment_to_files.items()
        if len(files) >= min_files and len(seg) >= min_segment_length
    ]

    # 合并重叠或包含关系的片段，保留最长的
    merged_segments = merge_overlapping_segments([(seg, files, len(seg)) for seg, files in candidate_segments])

    return merged_segments, file_lyrics


def locate_segments_in_srt(srt_file, target_segment, file_lyrics, similarity_threshold=0.8):
    lyrics = file_lyrics[srt_file]
    segment_length = len(target_segment)

    start_indices = []
    for i in range(len(lyrics) - segment_length + 1):
        current_segment = tuple(lyrics[i:i + segment_length])
        if are_all_sentences_similar(current_segment, target_segment, similarity_threshold):
            start_indices.append(i)

    # 解析时间戳
    time_ranges = []
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read().strip().split('\n\n')

    for start_idx in start_indices:
        start_time = parse_time(content[start_idx].split('\n')[1].split(' --> ')[0])
        end_time = parse_time(content[start_idx + segment_length - 1].split('\n')[1].split(' --> ')[1])
        time_ranges.append((start_time, end_time))

    return time_ranges



def crop_videos_based_on_common_segments(common_segments, file_lyrics, video_dir, output_dir, similarity_threshold=0.8):
    os.makedirs(output_dir, exist_ok=True)

    # 找到段数最多的歌词片段的最大段数
    max_segment_length = max(len(segment) for segment, _ in common_segments)

    # 筛选出所有达到最大段数的歌词片段
    max_segments = [(segment, srt_files) for segment, srt_files in common_segments if
                    len(segment) == max_segment_length]

    for idx, (segment, srt_files) in enumerate(max_segments):
        print(f"📦 正在处理第 {idx + 1} 组歌词片段（段数最多）：{segment}")
        segment_dir = os.path.join(output_dir, f"segment_{idx + 1}")
        os.makedirs(segment_dir, exist_ok=True)

        for srt_file in srt_files:
            video_file = os.path.splitext(os.path.basename(srt_file))[0] + ".mp4"
            video_path = os.path.join(video_dir, video_file)

            if not os.path.exists(video_path):
                print(f"❌ 视频文件不存在：{video_path}")
                continue

            try:
                video = VideoFileClip(video_path)
                time_ranges = locate_segments_in_srt(srt_file, segment, file_lyrics, similarity_threshold=similarity_threshold)

                for i, (start, end) in enumerate(time_ranges):
                    subclip = video.subclipped(start, end)
                    output_path = os.path.join(segment_dir, f"{os.path.splitext(video_file)[0]}_seg{i + 1}.mp4")
                    subclip.write_videofile(
                        output_path,
                        codec='libx264',
                        audio_codec='aac'
                    )
                    print(f"✅ 已生成裁剪视频：{output_path}")
            except Exception as e:
                print(f"❌ 裁剪失败：{video_file}，错误：{str(e)}")



def main(video_dir):
    # 1. 提取音频
    audio_files = extract_audio_from_videos(video_dir)
    print(f"✅ 已提取音频文件: {audio_files}")

    # 2. 批量转录
    srt_files = batch_transcribe_audio(audio_files)
    print(f"✅ 已生成SRT文件: {srt_files}")

    # 3. 查找共同歌词片段（至少4个文件中出现，7段连续）
    common_segments, file_lyrics = find_common_segments(srt_files, min_files=4, min_segment_length=6,
                                                        max_segment_length=20, similarity_threshold=0.8)
    print(f"✅ 共同歌词片段：{common_segments}")
    if not common_segments:
        print("⚠️ 未找到符合条件的歌词片段")
        return

    # 4. 裁剪视频
    output_dir = os.path.join(root_dir, "output", "cropped")
    crop_videos_based_on_common_segments(common_segments, file_lyrics, video_dir, output_dir)


if __name__ == '__main__':
    main(os.path.join(root_dir, "pre"))
