#  四宫格接力翻唱视频生成器
根据一首视频的节奏卡点，自动生成剪映草稿并导出四宫格接力翻唱视频

# 准备视频素材：
   将视频放入 `assets/zdcf/` 目录下。
   
# 运行主程序：

python main.py

# 查看输出：
   导出视频将保存在 `output/` 文件夹中。

faster-distil-whisper-large-v3.5 是一个 英文优化模型，它专注于提升英文转录的速度和准确率，但 不支持多语言（包括中文）。
Whisper 的 多语言模型 应该是 large-v3 或 large-v2，这些模型支持 99 种语言，包括中文。

```commandline
local_files_only=True 表示加载本地模型
model_size_or_path=path 指定加载模型路径
device="cuda" 指定使用cuda or cpu
compute_type="int8_float16" 量化为8位
language="zh" 指定音频语言
vad_filter=True 开启vad
vad_parameters=dict(min_silence_duration_ms=1000) 设置vad参数


set HF_ENDPOINT=https://hf-mirror.com
cd ..
huggingface-cli download --repo-type model Systran/faster-whisper-large-v3 --local-dir models/faster-whisper-large-v3

# 部署heygem数字人 Docker 容器服务

# 安装PyTorch
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

```