import os, shutil, hashlib, sqlite3, subprocess, zlib, struct


USER_NAME = 'turut'
DATA_DIR = 'c:/Users/{0}/AppData/LocalLow/Cygames/PrincessConnectReDive'.format(USER_NAME)
MANIFEST_FILENAME = 'manifest.db'
ASSET_DIR = 'b'
OUT_DIR = 'out'
TEMP_DIR = 'temp'

HCA_KEY = 3201512 # 000000000030D9E8

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
        f = open(awb_path, 'rb')
        f.seek(14)
        subkey = struct.unpack('<h', f.read(2))[0]
        f.close()

        key_path = awb_path + '.hcakey'

    subkey = 0
    key = struct.pack('>qh', HCA_KEY, subkey)

    f = open(key_path, 'wb')
    f.write(key)
    f.close()

print ("-- Reading database...")
db = sqlite3.connect(os.path.join(DATA_DIR, MANIFEST_FILENAME))
cursor = db.cursor()
pattern = ASSET_DIR + '/'
cursor.execute('SELECT k FROM t WHERE k LIKE "{0}%"'.format(pattern))
files = [r[0].replace(pattern, '') for r in cursor.fetchall()]
db.close()

create_or_clean_dir(TEMP_DIR)
create_or_clean_dir(OUT_DIR)

print ("-- Copying {0} files...".format(len(files)))
hashes = [hashlib.sha1(f.encode('utf-8')).hexdigest() for f in files]
for hash, file in zip(hashes, files):
    src = os.path.join(DATA_DIR, ASSET_DIR, hash)
    dst = os.path.join(TEMP_DIR, file)
    shutil.copy(src, dst)

#make_keyfile()

awb_files = [f for f in files if f.endswith('.awb')]
awb_index = 0
processed = {}

for awb in awb_files:
    awb_index += 1 
    print('-- Processing {0} ({1} of {2})...\n'.format(awb, awb_index, len(awb_files)))

    awb_path = os.path.join(TEMP_DIR, awb)
    make_keyfile(awb_path)    

    metadata = subprocess.check_output([VGMSTREAM_PATH, '-m', awb_path])
    print(metadata)
    print('')
    lines = [line.split(' ') for line in metadata.split(os.linesep)]

    count = 1    
    if lines[-4][1] == 'count:':
        count = int(lines[-4][2])

    for i in range(1, count + 1):
        stream_metadata = subprocess.check_output([VGMSTREAM_PATH, '-s', str(i), '-m', awb_path])
        stream_lines = [line.split(' ') for line in metadata.split(os.linesep)]
        names = ' '.join(stream_lines[-2][2:]).split('; ')
        print('Stream {0} names: {1}'.format(i, names))
        print('')

        name = names[0]

        if (name in processed):
            processed[name] +=1
            out_name = '{0}-{1}.wav'.format(name, processed[name])
        else:
            processed[name] = 1
            out_name = name + '.wav'

        subprocess.call([VGMSTREAM_PATH, '-s', str(i), '-o', os.path.join(CURRENT_DIR, OUT_DIR, out_name), awb_path])

    awb_root = awb_path[:-4]
    os.remove(awb_root + '.awb')
    os.remove(awb_root + '.acb')
    os.remove(awb_root + '.awb.hcakey')

print('Done.')
