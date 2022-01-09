from os import urandom, path, listdir, EX_OK, remove
from magic import from_file as file_id
from hashlib import md5
import argparse
import ffmpeg

FONT_NAME = 'OpenSans-BoldItalic.ttf'
WATERMARK_TEXT = 'put_it_here'

class Video:

    def __init__(self, fpath, outpath, outname=None):
        if not path.isfile(fpath):
            raise FileNotFoundError(f'{fpath} does not exist!')
        self.fpath = path.abspath(fpath)
        if outname is None:
            outname = self.rand_basename()
        self.outpath = path.abspath(path.join(outpath, outname))

    def rand_basename(self):
        extension = path.splitext(self.fpath)[-1]
        rand_digest = md5(urandom(128)).hexdigest()
        return f'{rand_digest}{extension}'

    def is_video(self):
        if 'video' in file_id(self.fpath, mime=True):
            return True
        return False
    
    def compose_watermark(self, text):
        fontfile = path.join(path.dirname(__file__), FONT_NAME)
        if not path.isfile(fontfile):
            raise FileNotFoundError(f'Font {FONT_NAME} is not found!')
        if not text:
            raise ValueError('Text should not be empty!')
        probe = ffmpeg.probe(self.fpath)
        video_s = ffmpeg.input(self.fpath)
        has_audio = [True for i in probe['streams'] if i.get('codec_type') == 'audio']
        audio_s = video_s.audio
        overlay = video_s.drawtext(text, box=0, fontfile=fontfile, y='(h-text_h)/2', x='(w-text_w)/2', fontsize=40, fontcolor='white', alpha=0.15)
        if not has_audio:
            return ffmpeg.output(overlay, self.outpath, format='mp4')
        return ffmpeg.output(overlay, audio_s, self.outpath, format='mp4')

def main():
    parser = argparse.ArgumentParser(description='Watermark all videos in specified directory')
    parser.add_argument('input_dir', type=str, help='path to the input directory')
    parser.add_argument('output_dir', type=str, help='path to the output directory')
    parser.add_argument('-l', action='store_true', help='do not remove original files')
    args = parser.parse_args()

    if not path.isdir(args.input_dir):
        raise FileNotFoundError(f'{args.input_dir} does not exist!')
    if not listdir(args.input_dir):
        print('The directory is empty, nothing to do.')
        return EX_OK
    if not path.isdir(args.output_dir):
        os.mkdir(args.output_dir)

    abs_output_path = path.abspath(args.output_dir)
    abs_paths = [path.join(path.abspath(args.input_dir), i) for i in listdir(args.input_dir)]
    print('Videos found... ', end='')
    videos_list = [Video(i, abs_output_path) for i in abs_paths if not path.isdir(i) and Video(i, abs_output_path).is_video()]
    total_count = len(videos_list)
    print(f'{total_count}')
    
    if not total_count:
        print('No videos found, nothing to do.')
        return EX_OK

    for count, video in enumerate(videos_list, start=1):
        print(f'({count}/{total_count}) {path.basename(video.fpath)} => {path.basename(video.outpath)}... ', end='')
        ffmpeg.run(video.compose_watermark(WATERMARK_TEXT), overwrite_output=True, quiet=True)
        if not args.l:
            remove(video.fpath)
        print('OK')

    print('Done!')

if __name__ == '__main__':
    main()

