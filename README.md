# whisper.axcl

This repository is a fork of [whisper.axcl](https://github.com/ml-inory/whisper.axcl) which is an optimized implementation of OpenAI's Whisper model for LLM8850 accelerator card.

## Key Improvements

The original project loads the model (small size, ~10 seconds) for each command execution and immediately unloads it after transcription. This fork modifies the workflow to load the model once and then accept continuous input (wav file paths), making it suitable for high-frequency transcription scenarios.

A flask server is added to provide continuous speech-to-text transcription service.

## Prerequisites

Building this project requires `cmake`, make sure to install it first:

```bash
sudo apt update
sudo apt install -y cmake
```

## Build

```bash
cd
git clone https://github.com/PiSugar/whisper.axcl.git
cd whisper.axcl
pip install -r server/requirements.txt --break-system-packages
./build.sh
```

## Download Model

https://huggingface.co/M5Stack/whisper-small-axmodel

https://huggingface.co/M5Stack/whisper-tiny-axmodel

https://huggingface.co/M5Stack/whisper-base-axmodel

You can clone the model repositories and link them in `arguments.json` for easier management:

```json
{
  "encoder": "/home/pi/whisper-small-axmodel/ax650/small-encoder.axmodel",
  "decoder_main": "/home/pi/whisper-small-axmodel/ax650/small-decoder-main.axmodel",
  "decoder_loop": "/home/pi/whisper-small-axmodel/ax650/small-decoder-loop.axmodel",
  "position_embedding": "/home/pi/whisper-small-axmodel/small-positional_embedding.bin",
  "token": "/home/pi/whisper-small-axmodel/small-tokens.txt",
  "model_type": "small",
  "language": "en"
}
```

If `language` is not specified, the model will attempt to detect the language automatically.

## Run Server

working directory: project root

```bash
bash serve.sh
```

## API Usage

The server exposes a RESTful API on `http://localhost:8801` for transcription. You can send a POST request to the `/recognize` endpoint with a JSON payload containing the path to the audio file.

```json
{
  "filePath": "/path/to/your/audio.wav"
}
```

Response:

```json
{
  "filePath": "/path/to/your/audio.wav",
  "recognition": "How is your day?"
}
```

## Run as Systemd Service

This script sets up the transcription server to run as a systemd service, ensuring it starts on boot and restarts on failure.

```bash
sudo bash startup.sh
sudo systemctl status whisper.service
```
