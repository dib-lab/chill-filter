import sourmash

MOLTYPE = "DNA"
KSIZE = 51
SCALED = 100_000


class DatabaseDescription:
    def __init__(self, shortname, filename,
                 merged_sketch_filename,
                 sketch_to_display_names,
                 sketch_to_nextlevel,
                 *,
                 default=False):
        self.shortname = shortname
        self.filename = filename
        self.merged_sketch_filename = merged_sketch_filename
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

    def get_display_name(self, x):
        return self.sketch_to_display_names.get(x, x)

databases = [
    DatabaseDescription('all',
                        'prepare-db/plants+animals+gtdb.rocksdb',
                        'prepare-db/plants+animals+gtdb.merged.sig.zip',
                        {'bosTau9': 'cattle genome (bosTau9)',
                         'canFam6': 'dog genome (canFam6)',
                         'equCab3': 'horse genome (equCab3)',
                         'felCat9': 'cat genome (felCat9)',
                         'galGal6': 'chick genome (galGal6)',
                         'hg38+alt': 'human genome (hg38 + alt tracks)',
                         'mm39': 'mouse genome (mm39)',
                         'oviAri4': 'sheep genome (oviAri4)',
                         'susScr11': 'pig genome (suScr11)',
                         'genbank-plants': 'all plants (GenBank 12/2024)',
                         }, {}, default=True),
    ]
