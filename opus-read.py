import argparse
import gzip

from parse.alignment_parser import AlignmentParser
from parse.moses_read import MosesRead


class PairPrinter:

    def __init__(self):
        parser = argparse.ArgumentParser(prog="opus-read", description="Read sentence alignments")

        parser.add_argument("-d", help="Corpus name", required=True)
        parser.add_argument("-s", help="Source language", required=True)
        parser.add_argument("-t", help="Target language", required=True)
        parser.add_argument("-r", help="Release (default=latest)", default="latest")
        parser.add_argument("-p", help="Pre-process-type (default=xml)", default="xml")
        parser.add_argument("-m", help="Maximum number of alignments", default="all")
        parser.add_argument("-S",
                            help="Maximum number of source sentences in alignments (range is allowed, eg. -S 1-2)", \
                            default="all")
        parser.add_argument("-T",
                            help="Maximum number of target sentences in alignments (range is allowed, eg. -T 1-2)", \
                            default="all")
        parser.add_argument("-a", help="Set attribute for filttering", default="any")
        parser.add_argument("-tr", help="Set threshold for an attribute", default=0)
        parser.add_argument("-ln", help="Leave non-alignments out", action="store_true")
        parser.add_argument("-w", help="Write to file. Enter two file names separated by a comma when writing in moses format \
							(e.g. -w moses.src,moses.trg). Otherwise enter one file name.", default=-1)
        parser.add_argument("-wm", help="Set writing mode (normal, moses, tmx, links)", default="normal")
        parser.add_argument("-f", help="Fast parsing. Slightly faster than normal parsing, but requires the sentence ids in \
							alignment files to be in sequence.", action="store_true")
        parser.add_argument("-rd", help="Change root directory (default=/proj/nlpl/data/OPUS/)",
                            default="/proj/nlpl/data/OPUS/")
        parser.add_argument("-af", help="Use given alignment file", default=-1)

        self.args = parser.parse_args()

        self.fromto = [self.args.s, self.args.t]
        self.fromto.sort()

        if self.args.af == -1:
            self.alignment = self.args.rd + self.args.d + "/" + self.args.r + "/xml/" + self.fromto[0] + "-" + \
                             self.fromto[1] + ".xml.gz"
        else:
            self.alignment = self.args.af
        self.source = self.args.rd + self.args.d + "/" + self.args.r + "/" + self.args.p + "/" + self.fromto[0] + ".zip"
        self.target = self.args.rd + self.args.d + "/" + self.args.r + "/" + self.args.p + "/" + self.fromto[1] + ".zip"
        self.moses = self.args.rd + self.args.d + "/" + self.args.r + "/moses/" + self.fromto[0] + "-" + self.fromto[
            1] + ".txt.zip"

        self.resultfile = None

        if self.args.w != -1:
            self.filenames = self.args.w.split(",")
            if self.args.wm == "moses":
                self.mosessrc = open(self.filenames[0], "w")
                self.mosestrg = open(self.filenames[1], "w")
            else:
                self.resultfile = open(self.filenames[0], "w")

    def printPair(self, sPair):
        if self.args.wm == "links":
            print(sPair)
        else:
            if self.args.wm == "moses":
                print(sPair[0] + "\t" + sPair[1])
            else:
                print(sPair[0] + "\n" + sPair[1])
            if self.args.wm == "normal":
                print("================================")

    def writePair(self, sPair):
        if self.args.wm == "links":
            self.resultfile.write(sPair + "\n")
        else:
            if self.args.wm == "moses":
                self.mosessrc.write(sPair[0] + "\n")
                self.mosestrg.write(sPair[1] + "\n")
            else:
                self.resultfile.write(sPair[0] + "\n" + sPair[1] + "\n")
            if self.args.wm == "normal":
                self.resultfile.write("================================\n")

    def outputPair(self, par, line):
        par.parseLine(line)
        sPair = par.readPair()

        par.fromids = []
        par.toids = []

        # if the sentence pair doesn't meet the requirements in AlignmentParser.readLine(),
        # don't output the sentence pair and return 0, which won't increment the pairs-counter in printPairs()
        if sPair == -1:
            return 0, sPair

        if sPair == 1:
            sPair = line.decode("utf-8")[:-1]

        if self.args.w != -1:
            self.writePair(sPair)
        else:
            self.printPair(sPair)

        # if the sentence pair is printed:
        # return 1, which will increment the pairs-counter in printPairs()
        if par.start == "link":
            par.start = ""
            return 1, sPair
        return 0, sPair

    def addTmxHeader(self):
        tmxheader = '<?xml version="1.0" encoding="utf-8"?>\n<tmx version="1.4.">\n<header srclang="' + self.fromto[0] + \
                    '"\n\tadminlang="en"\n\tsegtype="sentence"\n\tdatatype="PlainText" />\n\t<body>'
        if self.args.w != -1:
            self.resultfile.write(tmxheader + "\n")
        else:
            print(tmxheader)

    def addTmxEnding(self):
        if self.args.w != -1:
            self.resultfile.write("\t</body>\n</tmx>")
        else:
            print("\t</body>\n</tmx>")

    def addLinkFileEnding(self):
        if self.args.w != -1:
            self.resultfile.write("  </linkGrp>\n</cesAlign>")
        else:
            print("  </linkGrp>\n</cesAlign>")

    def closeResultFiles(self):
        if self.args.wm == "moses":
            self.mosessrc.close()
            self.mosestrg.close()
        elif self.args.wm == "tmx":
            self.resultfile.close()

    def readAlignment(self, align):
        if self.args.m == "all":
            for line in align:
                lastline = self.outputPair(self.par, line)[1]
        else:
            pairs = int(self.args.m)
            while True:
                line = align.readline()
                link, lastline = self.outputPair(self.par, line)
                pairs -= link
                if pairs == 0:
                    break
        return lastline

    def printPairs(self):
        self.par = AlignmentParser(self.source, self.target, self.args, self.resultfile)

        if self.args.wm == "tmx":
            self.addTmxHeader()

        if self.alignment[-3:] == ".gz":
            with gzip.open(self.alignment) as gzipAlign:
                lastline = self.readAlignment(gzipAlign)
        else:
            with open(self.alignment) as xmlAlign:
                lastline = self.readAlignment(xmlAlign)

        if self.args.wm == "links" and lastline != "</cesAlign>":
            self.addLinkFileEnding()

        if self.args.wm == "tmx":
            self.addTmxEnding()

        self.par.closeFiles()

        if self.args.w != -1:
            self.closeResultFiles()

    def printPairsMoses(self):
        mread = MosesRead(self.moses, self.args.d, self.fromto[0], self.fromto[1])
        if self.args.m == "all":
            mread.printAll()
        else:
            print("\n# " + self.moses + "\n\n================================")

            for i in range(int(self.args.m)):
                print(mread.readPair())

            mread.closeFiles()


pp = PairPrinter()
if pp.args.p == "moses":
    pp.printPairsMoses()
else:
    pp.printPairs()
