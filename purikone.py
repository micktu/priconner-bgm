import os, shutil, hashlib, sqlite3, subprocess, struct


USER_NAME = 'turut'
DATA_DIR = 'c:/Users/{0}/AppData/LocalLow/Cygames/PrincessConnectReDive'.format(USER_NAME)
MANIFEST_FILENAME = 'manifest.db'
ASSET_DIR = 'b'
OUT_DIR = 'out'
TEMP_DIR = 'temp'

HCA_KEY = 3201512 # 000000000030D9E8
IS_BATCH = False # Can be True when vgmstream .hcakey works for new keys.
SKIP_SUBKEY = True # Leave it to vgmstream.

VGMSTREAM_PATH = 'vendor/vgmstream/test.exe'

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def create_or_clean_dir(dirname):
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    os.makedirs(dirname)


def make_keyfile(awb_path = ''):
    subkey = 0
    key_path = os.path.join(TEMP_DIR, '.hcakey')

    if awb_path:
        key_path = awb_path + '.hcakey'

        if not SKIP_SUBKEY:
            f = open(awb_path, 'rb')
            f.seek(14)
            subkey = struct.unpack('<h', f.read(2))[0]
            f.close()

    key = struct.pack('>qh', HCA_KEY, subkey)

    f = open(key_path, 'wb')
    f.write(key)
    f.close()


def decompress_awb(awb_path, index = 1):
    metadata = subprocess.check_output([VGMSTREAM_PATH, '-s', str(index), '-m', awb_path])
    lines = [line.split(' ') for line in metadata.split(os.linesep)]
    names = ' '.join(lines[-2][2:]).split('; ')
    #print('Stream {0} names: {1}'.format(index, names))
    #print('')

    name = names[0]
    if (name in processed):
        processed[name] +=1
        out_name = '{0}-{1}.wav'.format(name, processed[name])
    else:
        processed[name] = 1
        out_name = name + '.wav'

    subprocess.call([VGMSTREAM_PATH, '-s', str(index), '-o', os.path.join(CURRENT_DIR, OUT_DIR, out_name), awb_path])


print ("-- Reading database...")
db = sqlite3.connect(os.path.join(DATA_DIR, MANIFEST_FILENAME))
cursor = db.cursor()
pattern = ASSET_DIR + '/'
cursor.execute('SELECT k FROM t WHERE k LIKE "{0}%"'.format(pattern))
files = [r[0].replace(pattern, '') for r in cursor.fetchall()]
db.close()


create_or_clean_dir(TEMP_DIR)

print ("-- Copying {0} files...".format(len(files)))
hashes = [hashlib.sha1(f.encode('utf-8')).hexdigest() for f in files]
for hash, file in zip(hashes, files):
    src = os.path.join(DATA_DIR, ASSET_DIR, hash)
    dst = os.path.join(TEMP_DIR, file)
    shutil.copy(src, dst)


create_or_clean_dir(OUT_DIR)

if IS_BATCH:
    make_keyfile()

awb_files = [f for f in files if f.endswith('.awb')]
processed = {}

for awb_index, awb in enumerate(awb_files):
    print('-- Processing {0} ({1} of {2})...\n'.format(awb, awb_index, len(awb_files)))

    awb_path = os.path.join(TEMP_DIR, awb)
    if not IS_BATCH:
        make_keyfile(awb_path)    

    metadata = subprocess.check_output([VGMSTREAM_PATH, '-m', awb_path])
    #print(metadata)
    #print('')
    lines = [line.split(' ') for line in metadata.split(os.linesep)]

    count = 1    
    if lines[-4][1] == 'count:':
        count = int(lines[-4][2])

    for i in range(1, count + 1):
        decompress_awb(awb_path, i)

    awb_root = awb_path[:-4]
    os.remove(awb_root + '.awb')
    os.remove(awb_root + '.acb')
    if not IS_BATCH:
        os.remove(awb_root + '.awb.hcakey')


print('Done.')
