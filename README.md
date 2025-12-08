# whisper.axcl

This repository is a fork of [whisper.axcl](https://github.com/ml-inory/whisper.axcl) which is an optimized implementation of OpenAI's Whisper model for LLM8850 accelerator card.

## Key Improvements

The original project loads the model (small size, ~10 seconds) for each command execution and immediately unloads it after transcription. This fork modifies the workflow to load the model once and then accept continuous input (wav file paths), making it suitable for high-frequency transcription scenarios.

A flask server is added to provide continuous speech-to-text transcription service.

## Build

```bash
./build.sh
pip install -r server/requirements.txt --break-system-packages
```

## Download Model

https://huggingface.co/M5Stack/whisper-small-axmodel
https://huggingface.co/M5Stack/whisper-tiny-axmodel
https://huggingface.co/M5Stack/whisper-base-axmodel

Place the downloaded model files in the `models/` directory.
The default model is `whisper-small-axmodel`. To use a different model, create a `arguments.json` file in the project root with the following content:

```json
{
  "encoder": "./models/small-encoder.axmodel",
  "decoder_main": "./models/small-decoder_main.axmodel",
  "decoder_loop": "./models/small-decoder_loop.axmodel",
  "position_embedding": "./models/small-positional_embedding.bin",
  "token": "./models/small-tokens.txt",
  "model_type": "small"
}
```

Other supported arguments include:

- `language` if not specified, the model will attempt to detect the language automatically.

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
