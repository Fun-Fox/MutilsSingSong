# 四宫格互动视频生成工具

使用Whisper对翻唱内容进行分析，实现多歌手自动歌词对齐。 自动实现剪辑及粉丝互动的视频生成

## TK海外账号测试结果

** 5小内互动效果，点赞10个，评论10个 **

![](/doc/1.jpg)

[测试视频效果-查看地址](https://www.bilibili.com/video/BV1GEgrzmEaz/?vd_source=4d12893260db69d541b5046e851cef83)

![](/doc/2.png)

## 下载模型

```commandline

set HF_ENDPOINT=https://hf-mirror.com
cd ..
huggingface-cli download --repo-type model Systran/faster-whisper-large-v3 --local-dir models/faster-whisper-large-v3

# 安装PyTorch
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

```