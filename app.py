from flask import Flask, request, jsonify, render_template
from datetime import timedelta
import os
import whisper
import uuid
from moviepy.editor import VideoFileClip

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def save_transcript_in_vtt(transcript, filename):
    vtt_content = "WEBVTT\n\n"
    for segment in transcript:
        start_time = segment['start_time']
        end_time = segment['end_time']
        text = segment['text']
        vtt_content += f"{start_time} --> {end_time}\n{text}\n\n"
    with open(filename, 'w') as vtt_file:
        vtt_file.write(vtt_content)

def save_transcript_in_srt(transcript, filename):
    srt_content = ""
    for idx, segment in enumerate(transcript, start=1):
        start_time = segment['start_time']
        end_time = segment['end_time']
        text = segment['text']
        srt_content += f"{idx}\n{start_time} --> {end_time}\n{text}\n\n"
    with open(filename, 'w') as srt_file:
        srt_file.write(srt_content)

@app.route('/transcribe', methods=['POST'])
def transcribe_video():
    # Check if the POST request has the file part
    if 'video_file' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video_file = request.files['video_file']
    if video_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the video file
    video_filename = str(uuid.uuid4()) + ".mp4"  # Generate a unique filename
    video_path = os.path.join("Videos", video_filename)
    video_file.save(video_path)

    # Convert video to audio
    audio_filename = os.path.splitext(video_filename)[0] + ".mp3"
    audio_path = os.path.join("Audios", audio_filename)
    video_clip = VideoFileClip(video_path)
    video_clip.audio.write_audiofile(audio_path)
    video_clip.close()

    # Transcribe audio
    model = whisper.load_model("base") # Change this to your desired model
    transcribe = model.transcribe(audio=audio_path)
    segments = transcribe['segments']

    transcript = []
    for segment in segments:
        start_time = str(0) + str(timedelta(seconds=int(segment['start']))) + ',000'
        end_time = str(0) + str(timedelta(seconds=int(segment['end']))) + ',000'
        text = segment['text']
        segment_text = text[1:] if text[0] == ' ' else text
        transcript.append({'start_time': start_time, 'end_time': end_time, 'text': segment_text})

    # Save transcript in VTT format
    vtt_filename = os.path.join("Transcripts", f"{uuid.uuid4()}.vtt")
    save_transcript_in_vtt(transcript, vtt_filename)

    # Save transcript in SRT format
    srt_filename = os.path.join("Transcripts", f"{uuid.uuid4()}.srt")
    save_transcript_in_srt(transcript, srt_filename)

    # Clean up: Delete video and audio files
    os.remove(video_path)
    os.remove(audio_path)

    return jsonify({'transcript': transcript, 'vtt_file': vtt_filename, 'srt_file': srt_filename}), 200

if __name__ == '__main__':
    app.run(debug=True)
