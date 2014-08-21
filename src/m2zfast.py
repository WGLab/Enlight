#!/usr/bin/env python

#===============================================================================
# Copyright (C) 2010 Ryan Welch, Randall Pruim
# 
# LocusZoom is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# LocusZoom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================

import os
import sys

# Fix path of script to be absolute.
sys.argv[0] = os.path.abspath(sys.argv[0]);

# Add the locuszoom bin/ to the PATH. 
LZ_ROOT = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),".."));
LZ_BIN = os.path.join(LZ_ROOT,"bin");
os.environ['PATH'] = LZ_BIN + os.pathsep + os.environ['PATH'];

import time
import re
import tempfile
import platform
from m2zutils import *
from FugueFinder import *
from PlinkFinder import *
from LDRegionCache import *
from pquery import *
from glob import glob
from optparse import OptionParser, SUPPRESS_HELP
from subprocess import *
from shutil import move,rmtree,copyfile
from prettytable import *
from textwrap import fill

# Try importing modules that may not exist on a user's machine. 
try:
  import gzip
except:
  print >> sys.stderr, "Warning: gzip not available on this system";

try:
  import bz2
except:
  print >> sys.stderr, "Warning: bz2 not available on this system";

try:
  import sqlite3
except:
  print >> sys.stderr, "Error: your python interpeter is not compiled against sqlite3 (is it really out of date?)";
  raise;

# Program strings.
M2ZFAST_VERSION = "1.1 mod";
M2ZFAST_TITLE = "+---------------------------------------------+\n"\
                "| LocusZoom 1.1 mod (09/30/2013)              |\n"\
                "| Plot regional association results           |\n"\
                "| from GWA scans or candidate gene studies    |\n"\
		"| and sequence annotations		       |\n"\
                "+---------------------------------------------+\n";

# Program constants. 
M2ZFAST_CONF = "conf/m2zfast.conf";
DEFAULT_SNP_FLANK = "200kb";
DEFAULT_GENE_FLANK = "20kb";
RE_SNP_1000G = re.compile("chr(\d+|[a-zA-z]+):(\d+)$");
RE_SNP_RS = re.compile("rs(\d+)");
M2ZCL_FIRST = False;
MULTI_CAP = 8; 


# Debug flag. Makes all output "more verbose."
#_DEBUG = False;
_DEBUG = True;

class Conf(object):
  def __init__(self,conf_file):
    self._load(conf_file);

  def _load(self,file):
    conf_dict = {};
    execfile(file,conf_dict);

    for k,v in conf_dict.iteritems():
      exec "self.%s = v" % str(k);

def getConf(conf_file=M2ZFAST_CONF):
  conf_file = find_relative(conf_file);
  conf = Conf(conf_file);
  return conf;

# Get LD file information given parameters.
# Returns a dictionary with 4 elements:
# ped_dir, map_dir, dat_dir, pos_file
def getLDInfo(pop,source,build,ld_db):
  if source in ld_db:
    node = ld_db[source];
    if build in node:
      node = node[build];
      if pop in node:
        # Success! File paths are known for this DB/build/population trio.
        return node[pop];

  # If we make it here, the supplied combination of source/build/pop is not supported. 
  return None;

# Print a list of all supported population/build/database combinations. 
def printSupportedTrios(ld_db):
  print "Genotype files available for: ";
  for source in ld_db:
    print source;
    for build in ld_db[source]:
      print "+- %s" % build;
      for pop in ld_db[source][build]:
        print "   +- %s" % pop;

def parseArgs(args):
  result = [];
  for i in xrange(len(args)):
    if args[i] != "=" and args[i].find("=") != -1:
      result.append(args[i]);
    elif args[i] == "=":
      result.append(args[i-1] + "=" + args[i + 1]);
      
  d = dict()
  for e in result:
    (arg, val) = e.split("=");
    d[arg] = val
  return d;

def quoteArgs(m2z_args):
  new_args = [];
  for arg in m2z_args:
    test = arg.split("=");
    if len(test) == 2:
      test[1] = "\"%s\"" % test[1];
    new_args.append("=".join(test));

  return new_args;

# Tests to see if the supplied string is a SNP.
# The SNP should be of the form: rs##### or chr#:pos.
def isSNP(string):
  string = str(string);
  if RE_SNP_RS.search(string):
    return True;
  elif RE_SNP_1000G.search(string):
    return True;
  else:
    return False;

def isRSID(string):
  p = re.compile(r"^rs(\d+?)$");
  if p.search(string) != None:
    return True;
  else:
    return False;

# Parse a 1000G SNP into chromosome/position.
# Example: chr4:172274 --> (4,172274)
def parse1000G(snp):
  if snp == None:
    return None;

  c = snp.split(":");
  if len(c) == 2:
    chr = chrom2chr(c[0][3:]);
    try:
      pos = long(c[1]);
    except:
      return None;
    
    return (chr,long(c[1]));
  else:
    return None;

# Pretty string for chromosome/start/stop interval. 
def regionString(chr,start,end):
  return "chr%s:%s-%s" % (str(chr),str(start),str(end));

# Delete a directory and all files underneath. 
def kill_dir(d):
  def report_error(function,path,excinfo):
    msg = None;
    if excinfo != None:
      msg = str(excinfo[1]);
      
    print >> sys.stderr, "Error: could not remove: %s, message was: " % (
      path,
      msg
    );
    
  if os.path.isdir(d):
    rmtree(d,onerror=report_error);
  else:
    print >> sys.stderr, "Error: could not remove %s, not a directory." % d;

# Pretty string for a given number of seconds. 
def timeString(seconds):
  tuple = time.gmtime(seconds);
  days = tuple[2] - 1;
  hours = tuple[3];
  mins = tuple[4];
  secs = tuple[5];
  if sum([days,hours,mins,secs]) == 0:
    return "<1s";
  else:
    string = str(days) + "d";
    string += ":" + str(hours) + "h";
    string += ":" + str(mins) + "m";
    string += ":" + str(secs) + "s";
  return string;

def transSNP(snp,db_file):
  # If this isn't a rs# SNP, it has no translation. 
  if not isRSID(snp):
    return snp;

  con = sqlite3.connect(db_file);
  cur = con.execute("SELECT * FROM %s where rs_orig='%s'" % (SQLITE_TRANS,snp));

  new_name = None;
  while 1:
    d = cur.fetchone();
    if d != None:
      new_name = d[1];
    else:
      break;

  if cur.rowcount > 1:
    print >> sys.stderr, "Warning: SNP %s had multiple names in the latest build.." % snp;

  if new_name == None:
    print >> sys.stderr, "Warning: tried to translate SNP %s to latest name in genome build, but it does not exist in the database table.." % str(snp);
  elif new_name == snp:
    return snp;
  else:
    print >> sys.stderr, "Warning: %s is not the current name in genome build (should be: %s)" % (snp,new_name);
    return new_name;

# Given a gene, return info for it from the database. 
def findGeneInfo(gene,db_file):
  con = sqlite3.connect(db_file);
  cur = con.execute("SELECT chrom,txStart,txEnd,cdsStart,cdsEnd FROM %s WHERE geneName='%s'" % (SQLITE_REFFLAT,gene));

  row = None;
  while 1:
    d = cur.fetchone();
    if d == None:
      break;
    
    # Turn row into dictionary object.
    d = dict(zip([i[0] for i in cur.description],d));
    
    # This block of code basically picks out the largest isoform
    # as the one we'll use for txstart/txend.
    if row == None:
      row = d;
    else:
      if abs(row['txEnd']-row['txStart']) < abs(d['txEnd']-d['txStart']):
        row = d;

  # Fix chromosome if possible.
  if row != None:
    chrom = chrom2chr(row['chrom'][3:]);
    if chrom == None:
      raise ValueError, "Error: refgene found on non-supported chromosome: %s" % str(row['chrom']);
    else:
      row['chrom'] = chrom;

  # Return row, with fixed chromosome (see chrom2chr function.) 
  return row;

class PosLookup:
  def __init__(self,db_file):  
    if not os.path.isfile(db_file):
      sys.exit("Error: could not locate SQLite database file: %s. Check conf file setting SQLITE_DB." % db_file);
      
    self.db = sqlite3.connect(db_file);
    self.execute = self.db.execute;
    
    self.execute("""
      CREATE TEMP VIEW snp_pos_trans AS SELECT rs_orig as snp,chr,pos FROM %s p INNER JOIN %s t ON (t.rs_current = p.snp);
    """ % (SQLITE_SNP_POS,SQLITE_TRANS));
    
    self.query = """
      SELECT snp,chr,pos FROM snp_pos_trans WHERE snp='%s';
    """;

  def __call__(self,snp):
    snp = str(snp);
    
    # If the SNP is a 1000G SNP, it already knows its chrom/pos by definition,
    # i.e. the SNP will be chr4:91941. 
    gcheck = parse1000G(snp);
    if gcheck:
      return gcheck;
    
    cur = self.execute(self.query % snp);
    chr = None;
    pos = None;

    res = 0;
    for row in cur:
      chr = row[1];
      pos = row[2];
      res += 1;

    region = "chr%s:%s" % (chr,pos);
    if res > 1:
      print >> sys.stderr, "Warning: SNP %s has more than 1 position in database, using: %s" % (str(snp),region);

    return (chr,pos);

# Given a list of header elements, determine if col_name is among them. 
def findCol(header_elements,col_name):
  for i in xrange(len(header_elements)):
    if header_elements[i] == col_name:
      return i;

  return None;

def is_gzip(file):
  b = False;

  try:
    print("338");
    f = gzip.open(file);
    print("339");
    f.read(1024);
    f.close();
    print("341");
    b = True;
  except:
    pass
  finally:
    f.close();

  return b;
  
def is_bz2(file):
  b = False;
  try:
    f = bz2.BZ2File(file);
    f.read(1024);
    f.close();
    b = True;
  except:
    pass
  finally:
    f.close();

  return b;

# Given a metal file, this function extracts the region from the file between
# chr/start/end.
def myPocull(metal_file,snp_column,pval_column,no_transform,chr,start,end,db_file,delim):
  region = "chr%s:%s-%s" % (str(chr),start,end);
  output_file = "temp_pocull_%s_%s" % (region,tempfile.mktemp(dir=""));
  
  con = sqlite3.connect(db_file);
  query = """
    SELECT rs_orig as snp,chr,pos
    FROM %(snp_table)s p
    INNER JOIN %(trans_table)s t on (t.rs_current = p.snp)
    WHERE chr = %(chr)i AND pos < %(end)i AND pos > %(start)i
  """ % {'snp_table':SQLITE_SNP_POS,'trans_table':SQLITE_TRANS,'chr':chr,'end':end,'start':start}
  cur = con.execute(query);
  
  sptable = {};
  while 1:
    row = cur.fetchone();
    if row != None:
      sptable.setdefault(row[0],(int(row[1]),int(row[2])));
    else:
      break;

  cur.close();

  # Open file for reading. Attempt to determine if file is compressed before opening. 
  if is_gzip(metal_file):
    try:
      f = gzip.open(metal_file); # throws exception if gz not on system
    except:
      die("Error: gzip is not supported on your system, cannot read --metal file.");
  elif is_bz2(metal_file):
    try:
      f = bz2.BZ2File(metal_file,"rU");
    except NameError:
      die("Error: bz2 is not supported on your system, cannot read --metal file.");
  else:
    f = open(metal_file,"rU");

  # Find snp column.
  metal_header = f.next().split(delim);
  metal_header[-1] = metal_header[-1].rstrip();

  snp_col = None; 
  if snp_column != None:
    if type(snp_column) == type(str()):
      snp_col = findCol(metal_header,snp_column);
    elif type(snp_column) == type(int()):
      snp_col = snp_column;
    else:
      die("Error: marker column specified with something other than a string or integer: %s" % str(snp_column));

  # After all that, we still couldn't find the snp column. Fail..
  if snp_col == None:
    msg = "Error: could not locate SNP column in data. You may need to specify "\
          "it using --markercol <snp column name>. Your delimiter should also "\
          "be specified if it is not a tab by using --delim.";
    die(msg);

  # Find p-value column.
  pval_col = None;
  if pval_column != None:
    if type(pval_column) == type(str()):
      pval_col = findCol(metal_header,pval_column);
    elif type(pval_column) == type(int()):
      pval_col = pval_column;
    else:
      die("Error: pval column specified with something other than a string or integer: %s" % str(pval_column)); 

  # We still couldn't find the p-value column. FAIL!
  if pval_col == None:
    die("Error: could not locate p-value column in data, column name I'm looking for is: %s. Is your delimiter correct?" % (pval_column));
  
  out = open(output_file,"w");
  print >> out, "\t".join(["chr","pos"] + metal_header);
  format_str = "\t".join(["%i","%i"] + ["%s" for i in xrange(len(metal_header))]);
  
  found_in_region = False;
  found_chrpos = False;
  min_snp = None;
  min_pval = decimal.Decimal(1);
  for line in f:
    # Skip blank lines. 
    if line.rstrip() == "":
      continue;
    
    e = line.split(delim);
    e[-1] = e[-1].rstrip();

    snp = e[snp_col];

    # Is this a 1000G SNP? If so, we can pull the position from it.
    gcheck = parse1000G(snp);
    if gcheck:
      found_chrpos = True;
      gchr = gcheck[0];
      gpos = gcheck[1];
      
      if gchr == int(chr) and gpos > int(start) and gpos < int(end):
        sptable.setdefault(snp,(gchr,gpos));

    if snp in sptable:
      found_in_region = True;
      
      # Insert fixed log10 p-value
      pval = e[pval_col];
  
      if is_number(pval):     
        dec_pval = decimal.Decimal(pval);
      
        if dec_pval < min_pval:
          min_snp = snp;
          min_pval = dec_pval; 
          
        if not no_transform:
          e[pval_col] = str(-1*dec_pval.log10());
        
        (schr,spos) = sptable.get(snp);
        e[snp_col] = "chr%i:%i" % (schr,spos);
        elements = (schr,spos) + tuple(e);
        print >> out, format_str % elements;
      else:
        print >> sys.stderr, "Warning: SNP %s has invalid p-value: %s, skipping.." % (snp,str(pval));

  f.close();
  out.close();
  
  if found_chrpos:
    print >> sys.stderr, "";
    print >> sys.stderr, fill("WARNING: your association results file has both rsID and "
                          "chr:pos SNP names. Please make sure you have selected the "
                          "correct genome build by using the --build parameter, or by "
                          "selecting the appropriate build on the website.");
    print >> sys.stderr, "";

  return (found_in_region,output_file,min_snp);

# Runs the R script which actually generates the plot. 
def runM2Z(metal,metal2zoom_path,ld_file,refsnp,chr,start,end,verbose,args=""):
  # If no LD file was created, make m2z use the database instead. 
  if ld_file == None:
    ld_file = "NULL";

  com = "%s metal=%s clobber=F clean=F refsnp=%s refsnpName=%s ld=%s chr=%s start=%s end=%s %s" % (
    metal2zoom_path,
    metal,
    refsnp.chrpos,
    refsnp.snp,
    ld_file,
    str(chr),
    str(start),
    str(end),
    args
  );

  if _DEBUG:
    print "DEBUG: locuszoom.R command: %s" % com;
    #time.sleep(999);

  #if verbose:
  if 1:
    proc = Popen(com,shell=True);
  else:
    proc = Popen(com,shell=True,stdout=PIPE,stderr=PIPE);
    
  proc.wait();

  if proc.returncode != 0:
    die("Error: locuszoom.R did not complete successfully. Check logs for more information.");

# Attemps to delete a list of files.
# Prints a warning if a file could not be deleted, but does not throw
# an exception. 
def cleanup(files):
  if _DEBUG:
    print "cleanup() called for files: ";
    for f in files:
      print ".. %s" % f;
      
  files = filter(lambda x: x != None,files)
  for f in files:
      #generic tables are comma-delimited
      for i in f.split(','):
        try:
          os.remove(i);
        except:
          print >> sys.stderr, "Warning: failed to remove file %s" % i;

# Terminates program with a message, and a list of help options.
def die_help(msg,parser):
  print >> sys.stderr, msg;
  parser.print_help();
  sys.exit(1);

def safe_int(x):
  try:
    x = int(x);
  except:
    x = None;

  return x;

# Reads a "hitspec" or batch run configuration file. 
# The file has 6 columns: 
# 0 - snp or gene
# 1 - chromosome
# 2 - start
# 3 - stop
# 4 - flank 
# 5 - run?
# 6 - m2zargs
# 
# Each row is for a SNP or gene, specified in column 0. 
# Either chr/start/stop or flank must be specified in each row. 
# If neither is specified, a default flank is used (see DEFAULT_*_FLANK variables.) 
# Missing values should be entered as "NA"
# Column 5 is either 'yes' or 'no' denoting whether or not this snp/gene should be plotted. 
# The final column contains a list of arguments to be passed to locuszoom.R, separated by whitespace. 
# The entire file is whitespace delimited. 
def readWhitespaceHitList(file,db_file):
  if not os.path.isfile(file):
    die("Could not open hitspec file for reading - check your path.");

  f = open(file,"rU");
  h = f.readline();

  # This format should have at least 6 columns.
  if len(h.split()) < 6:
    die("Error: hitspec not formatted properly, see documentation. Should be 6 columns, found: %i " % len(h.split()));

  find_pos = PosLookup(db_file);

  snplist = [];
  for line in f:
    # Skip blank lines. 
    if line.strip() == "":
      print >> sys.stderr, "Warning: skipping blank line in hitspec file..";
      continue;

    e = line.split();
    e[-1] = e[-1].strip();
    
    if len(e) < 6:
      print >> sys.stderr, "Error: hitspec line not formatted properly, missing the proper number of columns on line #%i: %s" (lineno,str(line));
      continue;

    if e[5] == 'no'or e[5] == "":
      print >> sys.stderr, "Skipping disabled line '%s' in hitspec file.." % " ".join(e);
      continue;

    snp = e[0];
    chr = e[1];
    start = e[2];
    end = e[3];
    flank = e[4];

    m2z_args = None;
    if len(e) > 6:
      m2z_args = " ".join(e[6:]);

    if flank != "" and flank != "NA":
      flank = convertFlank(flank);
      if flank == None:
        die("Error: could not parse flank \"%s\", format incorrect." % e[4]);

    if isSNP(snp):
      snp = SNP(snp=snp);
      snp.tsnp = transSNP(snp.snp,db_file);
      (snp.chr,snp.pos) = find_pos(snp.tsnp);
      snp.chrpos = "chr%s:%s" % (snp.chr,snp.pos);
        
    if flank != None and flank != "NA":
      if isSNP(snp):
        fchr = snp.chr;
        fpos = snp.pos;
        try:
          chr = int(fchr);
          start = fpos - flank;
          end = fpos + flank;
        except:
          if fchr == None or fpos == None:
            print >> sys.stderr, "Error: could not find position for SNP %s, skipping.." % e[0];
          else:
            print >> sys.stderr, "Error: bad chromosome/position for SNP %s, chr/pos were: %s,%s, skipping.." % (e[0],str(fchr),str(fpos));
          continue;
      else:
        gene_info = findGeneInfo(snp,db_file);
    
        if gene_info != None:
          if m2z_args == None:
            m2z_args = "requiredGene=%s" % snp;
          else:
            m2z_args += " requiredGene=%s" % snp;        
  
          chr = gene_info['chrom'];
          start = gene_info['txStart'] - flank;
          end = gene_info['txEnd'] + flank;
        else:
          try:
            chr = int(chr);
            start = long(start);
            end = long(end);
          except:
            print >> sys.stderr, "Error: no known SNP or gene present in first column, and invalid chr/start/end given in hitspec file."
            continue;
          
          snp = regionString(chr,start,end);
    else:
      try:
        chr = int(chr);
      except:
        if isSNP(snp):
          chr = snp.chr;
        else:
          print >> sys.stderr, "Error: invalid chr/start/end in hitspec file, no chrom given, line was: '%s'" % " ".join(e);
          continue;

      try:
        start = long(start);
        end = long(end);
      except:
        print >> sys.stderr, "Error: invalid start/end in hitspec file, line was: '%s'" % " ".join(e);
        continue;
      
      # If something wasn't given in the SNP/gene column, need a placeholder.
      if not isSNP(snp) and findGeneInfo(snp,db_file) == None:
        snp = regionString(chr,start,end);

    snplist.append((
      snp,
      chr,
      start,
      end,
      m2z_args
    ));

  f.close();

  return snplist;

# Given a flank string, such as: "500kb" or "500MB", convert to raw position.
# Examples:
# 500kb --> 500,000
# 1.5MB --> 1,500,000
def convertFlank(flank):
  iFlank = None;
  p = re.compile("(.+)(kb|KB|Kb|kB|MB|Mb|mb|mB)")
  match = p.search(flank);
  if match:
    digits = match.groups()[0];
    suffix = match.groups()[1];

    if suffix in ('kb','KB','Kb','kB'):
      iFlank = float(digits)*1000;
    elif suffix in ('MB','Mb','mb','mB'):
      iFlank = float(digits)*1000000;

    iFlank = int(round(iFlank));

  return iFlank;

def printOpts(opts):
  table = PrettyTable(['Option','Value']);
  table.set_field_align('Option','l');
  table.set_field_align('Value','l');
  
  table.add_row(['metal',os.path.split(opts.metal)[1]]);
  if opts.refsnp:
    table.add_row(['refsnp',opts.refsnp]);
  elif opts.refgene:
    table.add_row(['refgene',opts.refgene]);
  elif opts.hitspec:
    table.add_row(['hitspec',opts.hitspec]);
  elif opts.chr and opts.start and opts.end:
    table.add_row(['chr',opts.chr]);
    table.add_row(['start',opts.start]);
    table.add_row(['end',opts.end]);

  display_opts = ('flank','build','ld','pop','source','snpset','db','cache',
    'no_clean','no_transform','verbose','m2zpath','plotonly'
  );
  
  for opt in display_opts:
    val = getattr(opts,opt);
    if val != None and val:
        table.add_row([opt,str(val)]);
    
  table.printt();

def printArgs(args):
  table = PrettyTable(['Option','Value']);
  table.set_field_align('Option','l');
  table.set_field_align('Value','l');
  
  d = parseArgs(args);
  for i,j in d.iteritems():
    table.add_row([str(i),str(j)]);
  
  table.printt();

def printHeader(title):
  print title;

class SNP:
  def __init__(self,snp=None,tsnp=None,chrpos=None,chr=None,pos=None):
    self.snp = snp;         # snp name given by user
    self.tsnp = tsnp;       # snp name translated to current genome build
    self.chrpos = chrpos;   # "chrpos" name for SNP, e.g. chr#:###
    self.chr = chr;         # chromosome
    self.pos = pos;         # position
  
  def __str__(self):
    return self.snp;

# Parse command line arguments and return a tuple (opts,args) where:
# opts - settings that are specific to the program and have been error-checked
# opts looks like an object, settings are of the form: opt.some_setting
# args - all command line arguments that were positional, these are not checked
# and are immediately passed on to locuszoom.R 
def getSettings():
  conf = getConf();
  
  parser = OptionParser();
  parser.add_option("--metal",dest="metal",help="Metal file.");
  parser.add_option("--delim",dest="delim",help="Delimiter for metal file.");
  parser.add_option("--pvalcol",dest="pvalcol",help="Name of p-value column or 0-based integer specifying column number.");
  parser.add_option("--markercol",dest="snpcol",help="Name of SNP column or 0-based integer specifying column number.");
  parser.add_option("--cache",dest="cache",help="Change the location of the cache file to use for LD. Set to 'None' to disable.");
  parser.add_option("--hitspec",dest="hitspec",help="File containing a list of SNPs, chromosome, start, and stop.");
  parser.add_option("--refsnp",dest="refsnp",help="Create region plot around this reference SNP.");
  parser.add_option("--refgene",dest="refgene",help="Create region plot flanking a gene.");
  parser.add_option("--flank",dest="flank",help="Distance around refsnp to plot.");
  parser.add_option("--chr",dest="chr",help="Chromosome that refsnp is located on - this is only used for sanity checking, but it is good to include.");
  parser.add_option("--chr2",dest="chr2",help="If specified, will generate interaction heatmap. If chr2 is same as chr, intrachromosomal o/w inter-chr");
  parser.add_option("--interactionfile",dest="interactionfile",help="File for interaction heatmap, it is queried for the specified region");
  parser.add_option("--start",dest="start",help="Start position for interval near refsnp. Can be specified along with --end instead of using --flank.");
  parser.add_option("--end",dest="end",help="End position for interval near refsnp.");
  parser.add_option("--ld",dest="ld",help="Specify a user-defined LD file.");
  parser.add_option("--no-ld",dest="no_ld",help="Disable calculating and displaying LD information.",action="store_true");
  parser.add_option("--build",dest="build",help="NCBI build to use when looking up SNP positions.");
  parser.add_option("--pop",dest="pop",help="Population to use for LD.");
  parser.add_option("--source",dest="source",help="Source to use for LD (defaults to hapmap.)");
  parser.add_option("--snpset",dest="snpset",help="Set of SNPs to plot as a rug.");
  parser.add_option("--generic",dest="generic",help="comma delimited generic tables to plot.");
  parser.add_option("--category",dest="category",help="comma delimited categorical annotation tables to plot.");
  parser.add_option("--categoryKey",dest="categoryKey",help="comma delimited categorical annotation tables to plot.");
  parser.add_option("--no-cleanup",dest="no_clean",action="store_true",help="Leave temporary files generated by this script. This does not affect clobber or clean in locuszoom.R.");
  parser.add_option("--write-ld-to",dest="write_ld_to",help="Write LD in specified region to user-named column (refsnp appended) in corresponding lines. LD shows up as the last column.");
  parser.add_option("--no-transform",dest="no_trans",action="store_true",help="Disable automatic transformation of p-values.");
  parser.add_option("-v","--verbose",dest="verbose",action="store_true",help="Make the script be more talkative.");
  parser.add_option("--multi",dest="multi",type="int",help="Number of zoomplots to create in parallel. Default is 1 (serial mode). (not yet implemented)");
  parser.add_option("--plotonly",dest="plotonly",help="Generate only the plot figure, delete all other temporary files and do not create a directory.",action="store_true");
  parser.add_option("-p","--prefix",dest="prefix",type="str",help="Prefix to add to zoomplot pdfs or directories.");
  parser.add_option("--no-date",dest="no_date",action="store_true",default=False,help="Remove date from directory and filenames.");
  parser.add_option("--rundir",dest="rundir",help="Directory where m2zfast will attempt to run.");
  parser.add_option("-e","--experimental",dest="exper",action="store_true",help=SUPPRESS_HELP);
  parser.add_option("--override-m2z",dest="m2zpath",help=SUPPRESS_HELP);
  parser.add_option("--db",type="string",help="SQLite database file. This overrides the conf file.");
  parser.add_option("--offline",dest="offline",action="store_true",default=False,help=SUPPRESS_HELP);


  # Defaults.
  parser.set_defaults(
    multi = 1,
    delim = "\t",
    no_clean = False,
    no_ld = False,
    no_transform = False,
    build = conf.DEFAULT_BUILD,
    plotonly = False,
    prefix = None,
    pvalcol = "P-value",
    snpcol = "MarkerName", 
    verbose = False,
    pop = conf.DEFAULT_POP,
    snpset = "Illu1M",
    rundir = ".",
    source = conf.DEFAULT_SOURCE,
    experimental = False,
    cache = "../ld_cache.db",
  );

  (opts,args) = parser.parse_args();

  # Database constants. 
  # Original code didn't put them here
  global SQLITE_SNP_POS;
  global SQLITE_REFFLAT;
  global SQLITE_SNP_SET;
  global SQLITE_VAR_ANNOT;
  global SQLITE_RECOMB_RATE;
  global SQLITE_TRANS;
  global SQLITE_GENERIC;
  global SQLITE_CATEGORY;
  global DB_INTERACTION;
  global CHR_INTERACTION;

  SQLITE_SNP_POS = "snp_pos";
  SQLITE_REFFLAT = "refFlat";
  SQLITE_SNP_SET = "snp_set";
  SQLITE_VAR_ANNOT = "var_annot";
  SQLITE_RECOMB_RATE = "recomb_rate";
  SQLITE_TRANS = "refsnp_trans";
  DB_INTERACTION = opts.interactionfile;
  CHR_INTERACTION = opts.chr2;
  try:
      SQLITE_GENERIC = opts.generic.split(',');
  except AttributeError:
      SQLITE_GENERIC = None;
  try:
      SQLITE_CATEGORY = opts.category.split(',');
  except AttributeError:
      SQLITE_CATEGORY = None;

  # Should we override M2Z path?
  if opts.m2zpath != None:
    if os.path.isfile(opts.m2zpath):
      print "Overriding locuszoom.R path: %s" % opts.m2zpath;
      opts.metal2zoom_path = os.path.abspath(os.path.expanduser(opts.m2zpath));
      
      opts.metal2zoom_path = find_systematic(opts.metal2zoom_path);
      if opts.metal2zoom_path == None:
        die("Error: could not find locuszoom.R - check conf file %s" % M2ZFAST_CONF);
      
    else:
      print "locuszoom.R override specified, but path \'%s\' does not exist - using default." % opts.m2zpath;
      print "Current directory is: %s" % os.getcwd();
  else:
    opts.metal2zoom_path = find_systematic(conf.METAL2ZOOM_PATH);
    if not os.path.isfile(opts.metal2zoom_path):
      die("Error: could not find locuszoom.R - check conf file %s" % M2ZFAST_CONF);

  # Are we running in experimental mode?
    opts.verbose = True;
    globals()['_DEBUG'] = True;
  
  # Did they specify a SQLite database to use? 
  if opts.db:
    if os.path.isfile(opts.db):
      opts.sqlite_db_file = os.path.abspath(opts.db);
    else:
      die("Error: --db %s does not exist!" % str(opts.db));
  else:
    opts.sqlite_db_file = find_relative(conf.SQLITE_DB[opts.build]); # read from conf file
    if not os.path.isfile(opts.sqlite_db_file):
      die("Error: could not locate sqlite database, tried: %s, check your conf file" % str(opts.sqlite_db_file));

  # SNP position looker-upper. 
  find_pos = PosLookup(opts.sqlite_db_file);

  # If a temporary directory was specified, it better exist!
  if opts.rundir:
    if not os.path.isdir(opts.rundir):
      die("Error: temporary directory %s does not exist, you must create it first." % str(opts.tempdir));

  # Check to see if --hitspec and --refsnp were specified together. This shouldn't happen.
  mode_count = sum(map(lambda x: x != None,[opts.hitspec,opts.refsnp]));
  if mode_count > 1:
    die_help("Must specify either --refsnp or --hitspec. These options are mutually exclusive.",parser);

  # Check to see if --hitspec and --refgene were specified together. This shouldn't happen.
  mode_count = sum(map(lambda x: x != None,[opts.hitspec,opts.refgene]));
  if mode_count > 1:
    die_help("Must specify either --refgene or --hitspec. These options are mutually exclusive.",parser);
  
  # Check metal file for existence.
  if not opts.metal:
    die("Must supply --metal <file>.");
  else:
    metal_test = find_systematic(opts.metal);
    if metal_test == None:
      die("Error: could not find metal file %s" % opts.metal);
    else:
      opts.metal = os.path.abspath(metal_test);

  # Check metal file size. 
  if os.path.getsize(opts.metal) <= 0:
    die("Error: metal file is empty: %s" % str(opts.metal));

  # Fix delimiter.
  if opts.delim in ("tab","\\t","\t"):
    opts.delim = "\t";
  elif opts.delim in (" ","space"):
    opts.delim = " ";
  elif opts.delim in ("","whitespace","None"):
    opts.delim = None;
  elif opts.delim in (",","comma"):
    opts.delim = ",";
  else:
    opts.delim = "\t";

  # Error checking on main modes.
  if opts.refsnp:
    if not isSNP(opts.refsnp):
      die_help("Error: SNP %s not recognized as SNP" % str(opts.refsnp),parser);
  elif opts.hitspec:
    opts.hitspec = find_systematic(opts.hitspec);
    if opts.hitspec == None:
      die("Error: hitspec file does not exist.");

  # Check that multithread count is less than maximum allowed.
  if opts.multi > MULTI_CAP:
    opts.multi = MULTI_CAP;
    print >> sys.stderr, "Warning: --multi was higher than maximum allowed value of %i, reducing value to that limit." % MULTI_CAP;

  # Compute flank in raw digits instead of with kb or mb as a suffix, i.e. "100kb" --> "100000"
  if opts.flank != None:
    iFlank = convertFlank(opts.flank);

    if iFlank == None:
      die("Error: flank specification did not match pattern, flank was: %s.\n"
          "Example flanks are: \n"
          "500kb (kilobases)\n"
          "1.25MB (megabases)\n"
          "1323414 (bases)\n"
          % opts.flank);

    opts.flank = iFlank;

  # If the user disabled LD, we shouldn't use it..
  if opts.no_ld:
    opts.ld = None;

  # Check to see if user passed in LD file. If they did, it better exist.
  # A user passing in an LD file eliminates the need to check if their
  # build/population/source combination (see directly below) is correct.
  if opts.ld != None:
    opts.ld = find_systematic(opts.ld);
    if opts.ld == None or not os.path.isfile(opts.ld):
      die("Error: user-specified LD file does not exist.\nFile was: %s " % opts.ld)
  else:
    if not opts.no_ld:
      # Fix up population/build/source settings before checking.
      opts.pop = opts.pop.upper(); # populations are always upper-case

      # Check to see if the population, LD source, and build supplied are compatible.
      info_geno = getLDInfo(opts.pop,opts.source,opts.build,conf.LD_DB);
      if info_geno == None:
        print >> sys.stderr, "Error: source %s, population %s, and build %s are not jointly supported." % (
          opts.source,opts.pop,opts.build);
        print >> sys.stderr, "See below for supported combinations.";
        print >> sys.stderr, "";
        printSupportedTrios(conf.LD_DB);
        sys.exit(1);

  # Change refSNP into a chr:pos SNP. 
  if opts.refsnp:
    opts.refsnp = SNP(snp=opts.refsnp);
    opts.refsnp.tsnp = transSNP(opts.refsnp.snp,opts.sqlite_db_file);
    (chr,pos) = find_pos(opts.refsnp.tsnp);
  
    if chr == None or pos == None:
      die("Error: could not find chr/pos information for SNP %s in database." % opts.refsnp);
    
    opts.refsnp.chrpos = "chr%s:%s" % (chr,pos);
    opts.refsnp.chr = chr;
    opts.refsnp.pos = pos;

  # Compute start/end positions for each SNP, unless already specified and in refsnp mode.
  opts.snplist = [];
  if opts.refsnp:
    (chr,pos) = (opts.refsnp.chr,opts.refsnp.pos);

    if opts.start and opts.end and opts.chr:
      opts.start = long(opts.start);
      opts.end = long(opts.end);
      opts.chr = chrom2chr(chr);
      if opts.chr == chr and opts.start < pos and opts.end > pos:
        opts.snplist.append( (opts.refsnp,chr,opts.start,opts.end) );
      else:
        msg = "Warning: skipping SNP %s, genomic interval given does not overlap SNP position according to our database." % opts.refsnp.snp;
        msg += "\nGiven interval: %s\t Genomic position: %s" % (
          regionString(opts.chr,opts.start,opts.end),
          "chr" + str(chr) + ":" + str(pos)
        );
        die(msg);
        
    elif opts.refgene:
      refgene_info = findGeneInfo(opts.refgene,opts.sqlite_db_file);
      if refgene_info == None:
        die("Error: gene selected for plotting was not found in refFlat.");
  
      flank = opts.flank;
      if opts.flank == None:
        flank = convertFlank(DEFAULT_GENE_FLANK);
        
      gene_rs = refgene_info['txStart'] - flank;
      gene_re = refgene_info['txEnd'] + flank;
  
      opts.snplist.append((
        opts.refsnp,
        refgene_info['chrom'],
        gene_rs,
        gene_re,
      ));
      
    elif opts.flank:
      opts.snplist.append( (opts.refsnp,chr,pos-opts.flank,pos+opts.flank) );
      
    else:
      print "No flank, chr/start/stop, or reference gene given, using default flank of %s.." % DEFAULT_SNP_FLANK;
      def_flank = convertFlank(DEFAULT_SNP_FLANK);
      opts.snplist.append( (opts.refsnp,chr,pos-def_flank,pos+def_flank) );
      
  elif opts.hitspec:
    opts.snplist = readWhitespaceHitList(opts.hitspec,opts.sqlite_db_file);
  
  elif opts.refgene:
    refgene_info = findGeneInfo(opts.refgene,opts.sqlite_db_file);
    if refgene_info == None:
      die("Error: gene selected for plotting was not found in refFlat.");

    flank = opts.flank;
    if opts.flank == None:
      flank = convertFlank(DEFAULT_GENE_FLANK);
      
    gene_rs = refgene_info['txStart'] - flank;
    gene_re = refgene_info['txEnd'] + flank;

    opts.snplist.append((
      opts.refgene,
      refgene_info['chrom'],
      gene_rs,
      gene_re,
    ));

  elif opts.chr and opts.start and opts.end:
    region = "chr%s_%s-%s" % (str(opts.chr),str(opts.start),str(opts.end));
    opts.snplist.append((
      region,
      chrom2chr(opts.chr),
      int(opts.start),
      int(opts.end),
    ))
  
  else:
    die("Error: you must specify one of these options: \n"
        "--refsnp\n"
        "--refgene\n"
        "--hitspec\n"
        "--chr, --start, and --end together\n"
    );

  # Fix cache location.
  if opts.cache not in (None,"None","False","disable"):
    (cache_path,cache_file) = os.path.split(opts.cache);
    if cache_path == '':
      cache_path = "..";
  
    opts.cache = os.path.join(cache_path,cache_file);
  else:
    opts.cache = None;

  # Do we need to add snpcol and pvalcol to the m2z args? 
  if opts.snpcol != None:
    args.append("markerCol=%s" % opts.snpcol);

  if opts.pvalcol != None:
    args.append("pvalCol=%s" % opts.pvalcol);

  # Print warnings about deprecated options. 
  if opts.offline:
    print >> sys.stderr, "Warning: --offline no longer required, option will be ignored..";

  return (opts,args);


# On Unix: use gunzip to decompress a gzipped file
# On Windows: use gzip module to write gzipped file
# If file "out" exists, appends to file. Otherwise creates a new file "out". 
def decompGZFile(file,out):
  if not os.path.isfile(file):
    raise ValueError, "Error: file does not exist: %s" % file;

  if platform.system() == "Linux":
    if os.path.isfile(out):
      os.system("gunzip -c %s >> %s" % (file,out));
    else:
      os.system("gunzip -c %s > %s" % (file,out));
  
    if not os.path.isfile(out) or os.path.getsize(out) < 1:
      raise Exception, "Error: could not decompress file %s" % file;
  else:
    out = None;
    if os.path.isfile(out):
      out = open(out,"a");
    else:
      out = open(out,"w");
    
    f = gzip.open(file);
    out.writelines(f);
    f.close();
    out.close();

def computeLD(snp,chr,start,end,build,pop,source,cache_file,fugue_cleanup,verbose):
  conf = getConf();
 
  conf.NEWFUGUE_PATH = find_systematic(conf.NEWFUGUE_PATH);
  conf.PLINK_PATH = find_systematic(conf.PLINK_PATH);
 
  ld_info = getLDInfo(pop,source,build,conf.LD_DB);
  if 'map_dir' in ld_info:
    settings = FugueSettings(
      ld_info['map_dir'],
      ld_info['ped_dir'],
      conf.NEWFUGUE_PATH
    );
  elif 'bim_dir' in ld_info:
    settings = PlinkSettings(
      ld_info['bim_dir'],
      conf.PLINK_PATH
    );
  else:
    raise Exception, "Error: conf file specification for %s/%s/%s is invalid, please check syntax." % (pop,source,build);

  # Check that LD program exists. 
  if isinstance(settings,FugueSettings):
    if not os.path.exists(conf.NEWFUGUE_PATH):
      raise Exception, "Error: could not find %s for computing LD.." % conf.NEWFUGUE_PATH;
    else:
      print "Using %s to compute LD.." % conf.NEWFUGUE_PATH;
  elif isinstance(settings,PlinkSettings):
    if not os.path.exists(conf.PLINK_PATH):
      raise Exception, "Error: could not find %s for computing LD.." % conf.PLINK_PATH;
    else:
      print "Using %s to compute LD.." % conf.PLINK_PATH;

  if cache_file != None:
    cache = LDRegionCache(settings.createLDCacheKey(),cache_file);
  else:
    cache = None;
  
  if isinstance(settings,FugueSettings): 
    ld_finder = FugueFinder(settings,cache,fugue_cleanup,verbose);
  elif isinstance(settings,PlinkSettings):
    ld_finder = PlinkFinder(settings,cache,fugue_cleanup,verbose);

  ld_success = ld_finder.compute(snp.chrpos,chr,start,end);
  if ld_success:
    ld_filename = "templd_" + snp.snp + "_" + time.strftime("%y%m%d",time.localtime()) + "-" + time.strftime("%H%M%S",time.localtime()) + ".txt";
    
    if os.path.isfile(ld_filename):
      print >> sys.stderr, "Warning: LD file already exists for some reason: %s" % ld_filename;

    write_success = ld_finder.write(ld_filename);
    
    if not write_success:
      ld_filename = None;
  else:
    print >> sys.stderr, "Warning: LD could not be computed for SNP %s. "\
    "This SNP does not exist in the genotype files for computing LD from %s/%s/%s.." % (str(snp),source,build,pop);
    ld_filename = None;

  return ld_filename;

# Fixes up a user supplied LD file for passing into m2z.
# "Fixing" means:
# -- remove rows that do not contain the refsnp
# -- return None if the header does not contain dprime or rsquare
# -- return None if refsnp is not ever seen
# -- translates SNP names into chr:pos format
# Returns filename of fixed LD file, or None if a failure occurred
def fixUserLD(file,refsnp,db_file):
  # Create temporary file to write LD to.
  out = "temp_user_ld_" + tempfile.mktemp(dir="");
  
  # Open user LD file. 
  if os.path.splitext(file)[1] == ".gz":
    f = gzip.open(file);
  else:
    f = open(file);
  
  found_refsnp = False;
  
  # Checks on LD file format. 
  h = f.readline().lower().rstrip();
  h_s = h.split();
  
  for column in ('snp1','snp2','dprime','rsquare'):
    try:
      exec "%s_col = h_s.index(column)" % column;
    except:
      print >> sys.stderr, "Error: user-supplied LD file does not have column '%s' in header (or no header row exists.)" % column;
      return None;
  
  find_pos = PosLookup(db_file);
  
  out_file = open(out,"w");
  print >> out_file, h;
  for line in f:
    e = line.rstrip().split();
    
    # If the line contains the refsnp, extract it. 
    if line.find(refsnp.snp) != -1:
      found_refsnp = True;
      
      skip = False;
      for col in (snp1_col,snp2_col):
        snp = e[col];
        (chr,pos) = find_pos(snp);
        if chr != None and pos != None:
          e[col] = "chr%s:%s" % (chr,pos);
        else:
          print >> sys.stderr, "Warning: could not find position for SNP %s in user-supplied --ld file, skipping.." % str(snp);
          skip = True;
          
      if not skip:
        print >> out_file, " ".join(e);
  
  f.close();
  out_file.close();
  
  if found_refsnp:
    return out;
  else:
    print >> sys.stderr, "Error: user-supplied LD file does not contain the reference SNP %s.." % str(refsnp);
    return None;

def windows_filename(name):
  bad_chars = "\\ / : * ? \" < >".split();
  for c in bad_chars:
    name = name.replace(c,"_");
  
  return name;

def runInteractionQuery(query,args):
  hash = str(int(time.time())) + "_" + str(os.getpid());
  if query.func_name=='interaction_in_region':
      file ="%s_%s.txt" % (hash,args[0]);
  else:
      file = None;
      return file;

  try:
    cur = query(*args);
  except:
    error_msg = str(sys.exc_info()[1]);
    print >> sys.stderr, "Error: Interaction data query failed, error was: %s" % error_msg;
    cur = None;
    file = None;
  
  count = 0;
  if cur != None:
    try:
      out = open(file,"w");
      count = print_results(cur,"\t",out);
      out.close();
      
      #we still examine the file in locuszoom.R even if it's empty
      #in this case, just output an empty figure
#      if count <= 0:
#	  file = None;
    except:
      error_msg = str(sys.exc_info()[1]);
      print >> sys.stderr, "Error: could not write interaction query to file. Exception was: %s" % error_msg;
      file = None;

  return file;

def runQuery(query,args):
  hash = str(int(time.time())) + "_" + str(os.getpid());
  file = "%s_%s_%s.txt" % (query.func_name,hash,args[1]);
  if query.func_name=='generic_in_region':
      file ="%s_%s.txt" % (hash,args[1]);
  if query.func_name=='category_in_region':
      file ="%s_%s.txt" % (hash,args[1]);

  try:
    cur = query(*args);
  except:
    error_msg = str(sys.exc_info()[1]);
    print >> sys.stderr, "Error: SQL query failed, error was: %s" % error_msg;
    cur = None;
    file = None;
  
  count = 0;
  if cur != None:
    try:
      out = open(file,"w");
      count = print_results(cur,"\t",out);
      out.close();
      
      if count <= 0:
	  if query.func_name != 'generic_in_region' and query.func_name != 'category_in_region':
	      file = None;

    except:
      error_msg = str(sys.exc_info()[1]);
      print >> sys.stderr, "Error: could not write SQL query to file. Exception was: %s" % error_msg;
      file = None;

  return file;

def runQueries(chr,start,stop,snpset,build,db_file):
  results = {};
  generic_file_list=[];
  category_file_list=[];
  
  db = sqlite3.connect(db_file);
  
  results['refFlat'] = runQuery(refflat_in_region,[db,SQLITE_REFFLAT,chr,start,stop,build]);
  if SQLITE_GENERIC:
      for i in SQLITE_GENERIC:
	  generic_file_list.append (runQuery(generic_in_region,[db,i,chr,start,stop,build]));
      results['generic'] = ','.join(str(v) for v in generic_file_list);
  if SQLITE_CATEGORY:
      for i in SQLITE_CATEGORY:
	  category_file_list.append (runQuery(category_in_region,[db,i,chr,start,stop,build]));
      results['category'] = ','.join(str(v) for v in category_file_list);
  if DB_INTERACTION:
      results['heatmapFile'] = runInteractionQuery(interaction_in_region,[DB_INTERACTION,chr,start,stop,CHR_INTERACTION]);
  results['annot'] = runQuery(snp_annot_in_region,[db,SQLITE_SNP_POS,SQLITE_VAR_ANNOT,chr,start,stop,build]);
  results['recomb'] = runQuery(recomb_in_region,[db,SQLITE_RECOMB_RATE,chr,start,stop,build]);
  results['snpsetFile'] = runQuery(snpset_in_region,[db,SQLITE_SNP_POS,SQLITE_SNP_SET,snpset,chr,start,stop,build]);
  
  return results;

def writeLD2metal(ld_col_name,ld_file,metal_file,snp_column,refsnp,chr,start,end,db_file,delim):
  output_file = metal_file+".withld";
  
  con = sqlite3.connect(db_file);
  query = """
    SELECT rs_orig as snp,chr,pos
    FROM %(snp_table)s p
    INNER JOIN %(trans_table)s t on (t.rs_current = p.snp)
    WHERE chr = %(chr)i AND pos < %(end)i AND pos > %(start)i
  """ % {'snp_table':SQLITE_SNP_POS,'trans_table':SQLITE_TRANS,'chr':chr,'end':end,'start':start}
  cur = con.execute(query);
  

  sptable = {};
  while 1:
    row = cur.fetchone();
    if row != None:
      sptable.setdefault(row[0],(int(row[1]),int(row[2])));
    else:
      break;

  cur.close();

  # Open file for reading. Attempt to determine if file is compressed before opening. 
  if is_gzip(metal_file):
    try:
      f = gzip.open(metal_file); # throws exception if gz not on system
    except:
      die("Error: gzip is not supported on your system, cannot read --metal file.");
  elif is_bz2(metal_file):
    try:
      f = bz2.BZ2File(metal_file,"rU");
    except NameError:
      die("Error: bz2 is not supported on your system, cannot read --metal file.");
  else:
    f = open(metal_file,"rU");

  # Find snp column.
  metal_header = f.next().split(delim);
  metal_header[-1] = metal_header[-1].rstrip();

  snp_col = None; 
  if snp_column != None:
    if type(snp_column) == type(str()):
      snp_col = findCol(metal_header,snp_column);
    elif type(snp_column) == type(int()):
      snp_col = snp_column;
    else:
      die("Error: marker column specified with something other than a string or integer: %s" % str(snp_column));

  # After all that, we still couldn't find the snp column. Fail..
  if snp_col == None:
    msg = "Error: could not locate SNP column in data. You may need to specify "\
          "it using --markercol <snp column name>. Your delimiter should also "\
          "be specified if it is not a tab by using --delim.";
    die(msg);

  #read ld information
  ldtable = {};
  ld = open(ld_file,"rU");
  next(ld);
  for line in ld:
    e = line.split("\t");
    snp = e[0]
    ldtable.setdefault(snp,e[3]);
  ld.close();

  out = open(output_file,"w");
  #ld_col_name is a str, convert it to list first
  ld_col_name=str(ld_col_name)+"_"+str(refsnp);
  print >> out, "\t".join(metal_header + [ld_col_name]);
  
  for line in f:
    # Skip blank lines. 
    if line.rstrip() == "":
      continue;
    
    e = line.split(delim);
    e[-1] = e[-1].rstrip();

    snp = e[snp_col];

    # Is this a 1000G SNP? If so, we can pull the position from it.
    gcheck = parse1000G(snp);
    if gcheck:
      gchr = gcheck[0];
      gpos = gcheck[1];
      
      if gchr == int(chr) and gpos > int(start) and gpos < int(end):
        sptable.setdefault(snp,(gchr,gpos));

    if snp in sptable:
      chrpos = ":".join(map(str,sptable.get(snp)));
      chrpos = "chr"+chrpos;
      #SNPs in LD file are in 1000G format
      ld = ldtable.get(chrpos);
      if ld != None:
	  elements = tuple(e) + (float(ld),);
          format_str = delim.join(["%s" for i in xrange(len(metal_header))] + ["%.2f"]);
          print >> out, format_str % elements;
      else:
	  elements = tuple(e) + ('NA',);
          format_str = delim.join(["%s" for i in xrange(len(metal_header))] + ["%s"]);
          print >> out, format_str % elements;

  f.close();
  out.close();

  #overwrite old file with the new one
  try:
      copyfile(output_file,metal_file);
  except IOError as e:
      print >> sys.stderr, "I/O Error({0}): {1}".format(e.errno,e.strerror);

  #remove new one
  cleanup([output_file]);
  
  print >> sys.stderr, "LD information written to %s" % metal_file;

def runAll(metal_file,refsnp,chr,start,end,opts,args):
  build = opts.build;
  delim = opts.delim;
  no_clean = opts.no_clean;
  
  print "Beginning plotting sequence for: %s" % str(refsnp);
  print "Extracting region of interest (%s) from metal file.." % regionString(chr,start,end);
  (bPocull,metal_temp,min_snp) = myPocull(metal_file,opts.snpcol,opts.pvalcol,opts.no_trans,chr,start,end,opts.sqlite_db_file,delim);
  ld_temp = None;
  
  # If poculling does not give us any SNPs in the region, we're done. 
  if not bPocull:
    print >> sys.stderr, "Error: region specified contains no SNPs, skipping..";
    if not no_clean:
      print "Deleting temporary files.."
      cleanup([ld_temp,metal_temp]);
    return; # hack

  # If a gene was passed in, we need to tell M2Z it is a required gene to plot. 
  if not isSNP(refsnp):
    if findGeneInfo(refsnp,opts.sqlite_db_file) != None:
      args += " requiredGene=\"%s\"" % str(refsnp);

  find_pos = PosLookup(opts.sqlite_db_file);

  # If something other than a SNP was passed in, we need to find 
  # the best SNP in the region. 
  if not isSNP(refsnp):
    print "Attempting to find best SNP in region..";
    print "Found: %s" % min_snp;  
    
    refsnp = SNP(snp=min_snp);
    refsnp.tsnp = transSNP(min_snp,opts.sqlite_db_file);
    (best_chr,best_pos) = find_pos(refsnp.tsnp);
    refsnp.chr = best_chr;
    refsnp.pos = best_pos;
    refsnp.chrpos = "chr%s:%s" % (best_chr,best_pos);

  # Get refsnp position. 
  # If a position cannot be found, bail out. 
  if refsnp.pos == None:
    print >> sys.stderr, "Error: could not find position for %s, skipping.." % str(refsnp);
    if not no_clean:
      print "Deleting temporary files.."
      cleanup([ld_temp,metal_temp]);
    return; # hack
  
  # Should we calculate LD? 
  if not opts.no_ld:
    # Did the user supply an LD file? If so, we don't need to calculate it.
    if opts.ld:
      print "Using user-specified LD file..";
      opts.ld = fixUserLD(opts.ld,refsnp,opts.sqlite_db_file);
      if opts.ld == None:
        return; # hack.. but this whole script is a giant hack anyway. 
    else:
      print "Finding pairwise LD with %s.." % str(refsnp);
      print "Source: %s | Population: %s | Build: %s" % (opts.source,opts.pop,build);
      ld_temp = computeLD(refsnp,chr,start,end,build,opts.pop,opts.source,opts.cache,not no_clean,opts.verbose);
  else:
    print "Skipping LD computations, --no-ld was given..";
    ld_temp = "NULL";

  pqueries = {};
  print "Grabbing annotations from SQLite database..";
  pqueries = runQueries(chr,start,end,opts.snpset,build,opts.sqlite_db_file);
  for m2zarg,file in pqueries.iteritems():
    if file != None:
      args += " %s=%s" % (m2zarg,file);
    else:
      args += " %s=NULL" % m2zarg;


  ld_file = opts.ld if opts.ld != None else ld_temp;
  #write LD to metal if okay
  if opts.write_ld_to and (not opts.no_ld) and ld_file != None:
    writeLD2metal(opts.write_ld_to,ld_file,metal_file,opts.snpcol,refsnp,chr,start,end,opts.sqlite_db_file,delim);

  print "Creating plot..";
  runM2Z(metal_temp,opts.metal2zoom_path,ld_file,refsnp,chr,start,end,opts.verbose,args);

  if not no_clean:
    print "Deleting temporary files.."
    pquery_files = filter(lambda x: x != None,pqueries.values());
    cleanup([ld_temp,metal_temp] + pquery_files);

def main():
  printHeader(M2ZFAST_TITLE);
  conf = getConf();

  # Get command-line arguments and parse them for errors.
  print "Loading settings..";
  opts,args = getSettings();

  # Print important options. 
  print "Options in effect are:\n";
  printOpts(opts);
  print "";
  if len(args) > 0:
    print "Plotting parameters in effect are:\n";
    printArgs(args);
    print "";
  print "Using %s.." % opts.metal2zoom_path;

  # Metal2zoom arguments must be quoted to work properly on the command line.
  # i.e. title="Plot title"
  args = quoteArgs(args);
  args = " ".join(args);

  # Build parameter.
  args += " build=%s" % opts.build;

  # Always disable p-value transformation in R. 
  # It is dangerous to leave it enabled - we don't always know what the R script will do. 
  args += " alreadyTransformed=TRUE";

  # Change into runtime directory.
  os.chdir(opts.rundir);

  # Single process mode - one plot generated at a time. 
  if opts.multi == 1:
    # entry[0] - snp
    # entry[1] - chr
    # entry[2] - start plotting position
    # entry[3] - end plotting position
    # entry[4] - locuszoom.R args specified in hitspec file, if one was used
    # all of these are computed in getSettings()
    for entry in opts.snplist:
      # Time the code.
      st = time.time();

      # M2Z arguments can be passed in either via the command line,
      # or by using a "hitspec" file passed into this script. They need to
      # be merged appropriately.
      iter_args = args;
      if len(entry) == 5:
        if entry[4] != None:
          more_args = entry[4];

          if M2ZCL_FIRST:
            iter_args = args + " " + more_args;
          else:
            iter_args = more_args + " " + args;

      # Figure out what the temp directory should be called.
      temp_dir = "";
      if opts.prefix != None:
        temp_dir += opts.prefix + "_";
      if not opts.no_date:
        temp_dir += time.strftime("%y%m%d") + "_";
      temp_dir += str(entry[0]);

      # Setup the temporary directory.
      # If it exists already, it was used on a previous plotting run, and should
      # be killed so as not to use the temporary files left in it on accident. 
      if os.path.isdir(temp_dir):
        kill_dir(temp_dir);

      # Create the directory.
      os.mkdir(temp_dir);

      # Change into our temporary directory. This is where files will be generated
      # while creating the plot. locuszoom.R, new_fugue, and m2zfast will all
      # create files here. 
      os.chdir(temp_dir);

      # Create the plot. This runs through the whole sequence of fetching LD and running M2Z.
      runAll(opts.metal,entry[0],entry[1],entry[2],entry[3],opts,iter_args);

      # Change back up to the parent directory where we started running from. 
      os.chdir("..");

      # If they only want the plot, move/rename the pdf and delete the directory created.
      if opts.plotonly:
        image_file = glob(os.path.join(temp_dir,"*.[dfgpn]*")); # grabs pdf or png, or both
        exts = [os.path.splitext(i)[1] for i in image_file];
        if len(image_file) == 0:
          print >> sys.stderr, "Error: no image file found";
          kill_dir(temp_dir);
        else:
          for i in xrange(len(image_file)):
            image = image_file[i];
            ext = exts[i];

            new_image_name = "";
            if opts.prefix != None:
              new_image_name += opts.prefix + "_";
            if not opts.no_date:
              new_image_name += time.strftime("%y%m%d%H%M%S") + "_";
            new_image_name += windows_filename(str(entry[0]));
            new_image_name += ext;

            try:
              move(image,new_image_name);
            except:
              print >> sys.stderr, "Error: extracting image %s failed.." % image;

          kill_dir(temp_dir);

      se = time.time();
      print "Time required: %s\n" % (timeString(se - st));

  # Generate plots simultaneously. Not planning on implementing this anytime soon. 
  elif opts.multi > 1:
    die("--multi not yet implemented.");

# Call main if script is executed. 
if __name__ == "__main__":
  main();

