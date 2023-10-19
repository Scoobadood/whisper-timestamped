from flask import Flask, request, Response

import whisper_timestamped as whisper

app = Flask(__name__)

model = None


@app.route('/whisper', methods=['POST'])
def fake_whisper():
    # Must be JSON
    if not request.is_json:
        return Response('Invalid JSON data',
                        status=400
                        )

    payload = request.get_json()
    print(payload)

    # Extract required fields
    url = payload['url']
    if not url:
        return Response('url is required',
                        status=400
                        )

    try:
        audio = whisper.load_audio(url)
        result = whisper.transcribe(model, audio, language="en")

        print(payload)
        return result
    except:
        print(f'Failed :{payload}')
        return Response('file not found',
                        status=400
                        )


if __name__ == '__main__':
    model = whisper.load_model("tiny", device="cpu")
    app.run(host='0.0.0.0', port=5000)
