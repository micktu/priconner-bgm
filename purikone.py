import os, shutil, hashlib, sqlite3, subprocess, zlib


USER_NAME = 'turut'
DATA_DIR = 'c:/Users/{0}/AppData/LocalLow/Cygames/PrincessConnectReDive'.format(USER_NAME)
MANIFEST_FILENAME = 'manifest.db'
ASSET_DIR = 'b'
OUT_DIR = 'out'
TEMP_DIR = 'temp'

ACBEDITOR_PATH = 'vendor/SonicAudioTools/ACBEditor.exe'
VGMSTREAM_PATH = 'vendor/vgmstream/test.exe'

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def create_or_clean_dir(dirname):
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    os.makedirs(dirname)

def crc32(filename):
    BUFFER_SIZE = 4096
    with open(filename, 'rb') as f:
        crc = zlib.crc32('')
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            crc = zlib.crc32(data, crc)
    return crc


print ("Reading database...")
db = sqlite3.connect(os.path.join(DATA_DIR, MANIFEST_FILENAME))
cursor = db.cursor()
pattern = ASSET_DIR + '/'
cursor.execute('SELECT k FROM t WHERE k LIKE "{0}%"'.format(pattern))
files = [r[0].replace(pattern, '') for r in cursor.fetchall()]
db.close()

create_or_clean_dir(TEMP_DIR)
create_or_clean_dir(OUT_DIR)

print ("Copying {0} files...".format(len(files)))
hashes = [hashlib.sha1(f.encode('utf-8')).hexdigest() for f in files]
for hash, file in zip(hashes, files):
    src = os.path.join(DATA_DIR, ASSET_DIR, hash)
    dst = os.path.join(TEMP_DIR, file)
    shutil.copy(src, dst)

acb_files = [f for f in files if f.endswith('.acb')]
for f in acb_files:
    name = f[:-4]
    print('Processing {0}...'.format(name))
    filename = os.path.join(TEMP_DIR, f)
    subprocess.call([ACBEDITOR_PATH, filename])
    os.remove(filename)
    os.remove(os.path.join(TEMP_DIR, name + '.awb'))
    
    hca_path = os.path.join(TEMP_DIR, name)
    crc_map = {}
    for root, dirs, files in os.walk(hca_path):
        for f in files:
            crc = crc32(os.path.join(CURRENT_DIR, hca_path, f))
            if crc in crc_map:
                print('{0} is a duplicate of {1}.'.format(f, crc_map[crc]))
            else:
                crc_map[crc] = f
        
    for i, f in enumerate(crc_map.values(), start=1):
        name_format = r'{0}-{1:0>2d}.wav' if len(crc_map) > 1 else r'{0}.wav'
        wav_filename = name_format.format(name, i)
        subprocess.call([VGMSTREAM_PATH, '-o', os.path.join(CURRENT_DIR, OUT_DIR, wav_filename), os.path.join(hca_path, f)])

    shutil.rmtree(hca_path)

print('Done.')
