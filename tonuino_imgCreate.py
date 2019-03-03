import logging
import os
import urllib.parse
import shutil
import pprint
import json
import argparse


def create_dir(d, force_overwrite=False):
    if os.path.exists(d):
        logging.info('%s exists', d)
        if force_overwrite:
            logging.info('delete %s', d)
            shutil.rmtree(d)
    else:
        os.mkdir(d)


def copy_to_folder(files, dir_name, dry_run=True):
    f_dict = {}
    f_id = 0
    for f in files:
        f_str = '%03d.mp3' % f_id
        f_id += 1
        f_name = os.path.join(dir_name, f_str)

        if not dry_run:
            logging.debug('copy %s to %s', f, f_name)
            shutil.copyfile(f, f_name)
        else:
            logging.debug('DRYRUN, would copy %s to %s', f, f_name)
        f_dict[f_str] = f
    return f_dict


def copy_content(content, outdir, forceoverwrite, dryrun):
    out_dict = {}
    dir_id = 0
    for d in content:
        dir_str = '%02d' % dir_id
        dir_id += 1
        dir_name = os.path.join(outdir, dir_str)
        create_dir(dir_name, forceoverwrite)
        out_dict[dir_str] = copy_to_folder(d, dir_name, dryrun)
    for line in pprint.pformat(out_dict).splitlines():
        logging.debug(line.rstrip())
    with open('content.json', 'w') as f:
        logging.info('create content.json')
        f.write(json.dumps(out_dict, indent=4, sort_keys=True))


def copy_voice_cmd_files(outdir, voice_cmd_files):
    for (dirpath, dirnames, filenames) in os.walk(voice_cmd_files):
        for d in dirnames:
            src = os.path.join(voice_cmd_files, d)
            dst = os.path.join(outdir, d)
            if os.path.exists(dst):
                if os.stat(src).st_mtime - os.stat(dst).st_mtime > 1:
                    shutil.copytree(src, dst)
                else:
                    logging.debug('already exists, skipping %s', dst)
            else:
                shutil.copytree(src, dst)


def create_sdcard_img(track_list, voice_cmd_files, outdir, forceoverwrite=False, dryrun=True):
    create_dir(outdir, forceoverwrite)
    logging.info('copy voice_cmd_files from %s', voice_cmd_files)
    copy_voice_cmd_files(outdir, voice_cmd_files)
    copy_content(track_list, outdir, forceoverwrite, dryrun)
    pass


def create_track_list(dir, files):
    track_list = []
    for f in files:
        if f.endswith('.mp3'):
            fname = os.path.join(dir, f)
            logging.debug('found %s', fname)
            track_list.append(fname)
    return track_list


def parse_dir(l):
    for (dirpath, dirnames, filenames) in os.walk(l):
        if len(dirnames):
            for d in dirnames:
                parse_dir(d)
        if len(filenames):
            return create_track_list(dirpath, filenames)


def parse_input_file(fname):
    img = []
    with open(fname) as f:
        for l in f.readlines():
            l = l.strip()
            l = urllib.parse.unquote(l)
            logging.info('looking for mp3 in %s' % l)
            if os.path.isdir(l):
                img.append(parse_dir(l))
    return img


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    parser = argparse.ArgumentParser('create TonUINO SD card layout and copy and rename files and folders')
    parser.add_argument('-s', '--sdcardroot', required=True,
                        help='path to Folder containing advert and mp3 folder, e.g. SD-card')
    parser.add_argument('-o', '--output', required=True, help='path to sdcard content')
    parser.add_argument('-i', '--input', required=True, help='content specification file, one folder per line')
    parser.add_argument('-f', '--forceoverwrite', default=False, help='delete every existing directory --output')
    parser.add_argument('-d', '--dryrun', default=False, help='delete every existing directory --output')
    args = parser.parse_args()

    input_list = parse_input_file(args.input)
    create_sdcard_img(input_list, args.sdcardroot, args.output, args.forceoverwrite, args.dryrun)


if __name__ == "__main__":
    main()
