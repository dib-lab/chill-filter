import sourmash

MOLTYPE = "DNA"
KSIZE = 51
SCALED = 100_000


class DatabaseDescription:
    def __init__(self,
                 shortname,
                 filename,
                 merged_sketch_filename,
                 description,
                 sketch_to_display_names,
                 sketch_to_nextlevel,
                 *,
                 default=False):
        self.shortname = shortname
        self.filename = filename
        self.merged_sketch_filename = merged_sketch_filename
        self.description = description
        self.sketch_to_display_names = sketch_to_display_names
        self.sketch_to_nextlevel = sketch_to_nextlevel
        self.default = default

    def load(self):
        ss = sourmash.load_file_as_index(self.merged_sketch_filename)
        ss = ss.select(moltype=MOLTYPE, ksize=KSIZE, scaled=SCALED)
        if len(ss) != 1:
            raise Exception("more than one sketch in merged sketches?!")
        
        ss = list(ss.signatures())[0]
        self.merged_hashes = ss.minhash.hashes

    def get_display_name(self, match_name):
        "Translate match names."
        return self.sketch_to_display_names.get(match_name, match_name)

    def get_nextlevel_db(self, match_name):
        "Get the next database to search."
        return self.sketch_to_nextlevel.get(match_name)

_databases = [
    DatabaseDescription('all',
                        'prepare-db/plants+animals+gtdb.rocksdb',
                        'prepare-db/plants+animals+gtdb.merged.sig.zip',
                        'all reference genomes',
                        {'bosTau9': 'cattle genome (bosTau9)',
                         'canFam6': 'dog genome (canFam6)',
                         'equCab3': 'horse genome (equCab3)',
                         'felCat9': 'cat genome (felCat9)',
                         'galGal6': 'chick genome (galGal6)',
                         'hg38+alt': 'human genome (hg38 + alt tracks)',
                         'mm39': 'mouse genome (mm39)',
                         'oviAri4': 'sheep genome (oviAri4)',
                         'susScr11': 'pig genome (suScr11)',
                         'genbank-plants': 'all plants (GenBank July 2024)',
                         },
                        {
                            'bacteria and archaea (GTDB rs220)': 'gtdb-rs220-phylum',
                            'genbank-plants': 'genbank-plants-2024.07',
                        }, default=True),
    DatabaseDescription('gtdb-only',
                        'prepare-db/gtdb.rocksdb',
                        'prepare-db/gtdb.merged.sig.zip',
                        'microbes only (GTDB rs220, merged)',
                        {}, {}),
    DatabaseDescription('podar-ref',
                        'prepare-db/podar-ref.rocksdb',
                        'prepare-db/podar-ref.merged.sig.zip',
                        'podar-ref (64 microbes)',
                        {}, {}),
    DatabaseDescription('gtdb-rs220-phylum',
                        'prepare-db/gtdb-rs220-phylum.rocksdb',
                        '',
                        'all bacterial and archaeal phyla (GTDB rs220)',
                        {}, {}),
    DatabaseDescription('genbank-plants-2024.07',
                        'prepare-db/genbank-plants-2024.07.rocksdb',
                        '',
                        'plants (Genbank, July 2024)',
                        {}, {}),
    ]


def get_search_db(*, name=None):
    if name:
        for db in _databases:
            if db.shortname == name:
                return db
        raise Exception(f"cannot match to search db '{name}'")
    else:
        for db in _databases:
            if db.default:
                return db
        raise Exception("no default search DB!?")
