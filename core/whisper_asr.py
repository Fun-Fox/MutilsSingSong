import os
import warnings

from faster_whisper import WhisperModel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCAL_MODEL_PATH = os.path.join(root_dir, 'models', "faster-whisper-large-v3")

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
