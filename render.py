"""Generate a captioned Korean sample with Azure narration and original procedural BGM."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import urllib.error
import urllib.request
import wave
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont, ImageOps
import base64
import io

OUT = Path('output')
CONTENT = json.loads(Path('content/current.json').read_text())
CARDS = [(s['heading'], s['title'], s['narration']) for s in CONTENT['scenes']]

def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)

def duration(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(path)], text=True))

def font(size):
    candidates = [Path(os.environ.get('KOREAN_FONT', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))]
    candidates += list(Path('/usr/share/fonts').rglob('*CJK*Regular*'))
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise SystemExit('Korean font not found. Install fonts-noto-cjk.')

def card(i, heading, title, narration):
    atlas = Image.open(io.BytesIO(base64.b64decode(Path(CONTENT['atlas']).read_text()))).convert('RGB')
    cols, rows = CONTENT['columns'], CONTENT['rows']
    w, h = atlas.size
    x, y = i % cols, i // cols
    im = ImageOps.fit(atlas.crop((x*w//cols, y*h//rows, (x+1)*w//cols, (y+1)*h//rows)), (1080,1920), method=Image.Resampling.LANCZOS)
    overlay = Image.new('RGBA', im.size, (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    d.rectangle((0,0,1080,230), fill=(12,25,40,210))
    d.text((65,68), heading, font=font(48), fill='white')
    d.text((65,145), '이해를 돕기 위한 가상 사례', font=font(28), fill='#ead8b6')
    d.rounded_rectangle((60,1030,970,1280), radius=30, fill=(255,255,255,235))
    d.multiline_text((95,1070), title, font=font(58), fill='#10263d', spacing=20)
    d.rectangle((0,1370,1080,1920), fill=(12,25,40,225))
    words = narration.split()
    lines, line = [], ''
    for word in words:
        trial = (line+' '+word).strip()
        if d.textbbox((0,0),trial,font=font(40))[2] > 850:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    d.multiline_text((75,1410), '\n'.join(lines), font=font(40), fill='white', spacing=17)
    d.text((75,1660), '지수행정사사무소', font=font(38), fill='#e1be83')
    d.text((75,1720), '0507-1333-4475', font=font(45), fill='white')
    d.rounded_rectangle((830,1675,965,1755), radius=18, fill='#e1be83')
    d.text((851,1685), '지수', font=font(42), fill='#10263d')
    if i == len(CARDS)-1:
        d.text((75,1790), '대전광역시 유성구 계룡로105번길 15, 403호', font=font(28), fill='white')
    Image.alpha_composite(im.convert('RGBA'), overlay).convert('RGB').save(OUT/f'card-{i}.png')


def speak(i, text):
    key = os.environ.get('AZURE_SPEECH_KEY', '').strip()
    region = os.environ.get('AZURE_SPEECH_REGION', '').strip()
    if not key or not region:
        raise SystemExit('Missing AZURE_SPEECH_KEY or AZURE_SPEECH_REGION repository secret.')
    if not re.fullmatch('[a-z0-9-]+', region):
        raise SystemExit('AZURE_SPEECH_REGION must be a region code such as koreacentral.')
    ssml = '<speak version="1.0" xml:lang="ko-KR"><voice name="ko-KR-SunHiNeural"><prosody rate="+15%">' + escape(text) + '</prosody></voice></speak>'
    req = urllib.request.Request(f'https://{region}.tts.speech.microsoft.com/cognitiveservices/v1', data=ssml.encode(), headers={'Ocp-Apim-Subscription-Key': key, 'Content-Type': 'application/ssml+xml', 'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3', 'User-Agent': 'jisu-sns-renderer'})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
    except urllib.error.HTTPError as e:
        # Do not print request headers, response bodies or secrets.
        raise SystemExit(f'Azure Speech returned HTTP {e.code}. Check region, key and free-tier quota.') from None
    if len(data) < 100:
        raise SystemExit('Azure returned an empty audio file.')
    path = OUT / f'voice-{i}.mp3'
    path.write_bytes(data)
    return path

def music(seconds):
    # Original synthesized pad: no third-party music, samples or melodies.
    sr = 24000
    chords = [(130.81, 164.81, 196.0), (110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (98.0, 123.47, 146.83)]
    with wave.open(str(OUT / 'bgm.wav'), 'wb') as w:
        w.setparams((1, 2, sr, 0, 'NONE', 'not compressed'))
        for start in range(0, math.ceil(seconds * sr), sr):
            samples = bytearray()
            for j in range(min(sr, math.ceil(seconds * sr) - start)):
                t = (start + j) / sr
                local = t % 6
                envelope = min(local / .7, 1, (6 - local) / .8)
                fade = max(0, min(t / 1.2, 1, (seconds - t) / 1.5))
                value = sum(math.sin(2 * math.pi * hz * t) + .15 * math.sin(4 * math.pi * hz * t) for hz in chords[int(t / 6) % 4]) / 3
                samples.extend(struct.pack('<h', int(4800 * envelope * fade * value)))
            w.writeframes(samples)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--visual-only', action='store_true', help='Local rendering check; no Azure calls')
    args = p.parse_args()
    OUT.mkdir(exist_ok=True)
    lengths = []
    for i, (heading, title, text) in enumerate(CARDS):
        card(i, heading, title, text)
        voice = None if args.visual_only else speak(i, text)
        seconds = 5.0 if voice is None else duration(voice) + .5
        lengths.append(seconds)
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', str(OUT / f'card-{i}.png')]
        cmd += ['-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono'] if voice is None else ['-i', str(voice)]
        cmd += ['-vf', "zoompan=z='min(zoom+0.00004,1.01)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=25", '-af', 'apad', '-t', str(seconds), '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '24', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '24000', str(OUT / f'segment-{i}.mp4')]
        run(cmd)
    (OUT / 'concat.txt').write_text(''.join(f"file 'segment-{i}.mp4'\n" for i in range(len(CARDS))))
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(OUT / 'concat.txt'), '-c', 'copy', str(OUT / 'joined.mp4')])
    # User music is mixed privately after download; do not publish original audio assets.
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(OUT / 'joined.mp4'), '-map', '0:v', '-map', '0:a', '-c', 'copy', '-movflags', '+faststart', str(OUT / 'jisu-sample.mp4')])
    (OUT / 'manifest.json').write_text(json.dumps({'sample_only': False, 'batch_id': CONTENT['batch_id'], 'detail_url': CONTENT['detail_url'], 'voice': 'ko-KR-SunHiNeural', 'has_azure_narration': not args.visual_only, 'bgm': 'pending private user music mix; do not publish before mixing', 'seconds': duration(OUT / 'jisu-sample.mp4'), 'cards': CARDS}, ensure_ascii=False, indent=2))
    print('Rendered jisu-sample.mp4; no social post was created.')

if __name__ == '__main__':
    main()
