import os

def get_files(target_dir, ext = []):
    files = []
    for fl in os.listdir(target_dir):
        if os.path.isfile(f'{target_dir}/{fl}') :
            f, ex = os.path.splitext(fl)
            if( len(ext) == 0 or ex[1:] in ext ):
                files.append(fl)
    return files