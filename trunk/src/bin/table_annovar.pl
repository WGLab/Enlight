#!/usr/bin/env perl
use warnings;
use strict;
use Pod::Usage;
use Getopt::Long;
use File::Basename;

our $VERSION = 			'$Revision: 516 $';
our $LAST_CHANGED_DATE =	'$LastChangedDate: 2013-02-08 11:10:50 -0800 (Fri, 08 Feb 2013) $';

our ($verbose, $help, $man);
our ($queryfile, $dbloc);
our ($outfile, $buildver, $remove, $checkfile, $protocol, $operation, $otherinfo, $alltranscript, $sortout, $nastring, $genericdbfile, $gff3dbfile, $bedfile, $vcfdbfile, $csvout);

GetOptions('verbose|v'=>\$verbose, 'help|h'=>\$help, 'man|m'=>\$man, 'outfile=s'=>\$outfile, 'buildver=s'=>\$buildver, 'remove'=>\$remove, 'checkfile!'=>\$checkfile, 
	'protocol=s'=>\$protocol, 'operation=s'=>\$operation, 'otherinfo'=>\$otherinfo, 'alltranscript'=>\$alltranscript, 'sortout'=>\$sortout, 'nastring=s'=>\$nastring,
	'genericdbfile=s'=>\$genericdbfile, 'gff3dbfile=s'=>\$gff3dbfile, 'bedfile=s'=>\$bedfile, 'vcfdbfile=s'=>\$vcfdbfile,
	'csvout'=>\$csvout,
	) or pod2usage ();
	
$help and pod2usage (-verbose=>1, -exitval=>1, -output=>\*STDOUT);
$man and pod2usage (-verbose=>2, -exitval=>1, -output=>\*STDOUT);
@ARGV or pod2usage (-verbose=>0, -exitval=>1, -output=>\*STDOUT);
@ARGV == 2 or pod2usage ("Syntax error");

($queryfile, $dbloc) = @ARGV;


my @unlink;	#a list of files to be deleted
my @header;	#annotation output header
my %varanno;	#varstring as key of 1st hash, anno_db as key of 2nd hash, anno as value of 2nd hash
my (@protocol, @operation, @dbtype1);	#@dbtype1 is the translated file name for @protocol
my (@genericdbfile, @gff3dbfile, @vcfdbfile, @bedfile);

processArgument ();
@dbtype1 = proxyDBType(@protocol);
$checkfile and checkFileExistence (@dbtype1);

for my $i (0 .. @protocol-1) {
	print STDERR "-----------------------------------------------------------------\n";
	print STDERR "NOTICE: Processing operation=$operation[$i] protocol=$protocol[$i]\n";
	if ($operation[$i] eq 'g') {
		geneOperation ($protocol[$i], $dbtype1[$i]);
	} elsif ($operation[$i] eq 'r') {
		regionOperation ($protocol[$i], $dbtype1[$i]);
	} elsif ($operation[$i] eq 'f') {
		filterOperation ($protocol[$i], $dbtype1[$i]);
	}
}

if ($sortout) {
	$otherinfo and readOtherinfo ($queryfile);
	printSortOutput();
} else {
	printOrigOutput ();
}

$remove and unlink(@unlink);


sub printSortOutput {
	my $final_out;
	if ($csvout) {
		$final_out="$outfile.${buildver}_multianno.csv";
	} else {
		$final_out="$outfile.${buildver}_multianno.txt";
	}
	open OUT,">",$final_out or die "Cannot write to $final_out: $!\n";
	print STDERR "NOTICE: output file is written to $final_out\n";
	
	my @expanded_header;
	for my $i (0 .. @header-1) {
		if ($header[$i] eq 'ljb_all') {
			push @expanded_header, qw/LJB_PhyloP LJB_PhyloP_Pred LJB_SIFT LJB_SIFT_Pred LJB_PolyPhen2 LJB_PolyPhen2_Pred LJB_LRT LJB_LRT_Pred LJB_MutationTaster LJB_MutationTaster_Pred LJB_GERP++/;
		} else {
			push @expanded_header, $header[$i];
		}
	}
	
	if ($csvout) {
		print OUT join(",", qw/Chr Start End Ref Alt/, @expanded_header), $otherinfo?",Otherinfo":"", "\n";
	} else {
		print OUT join("\t", qw/Chr Start End Ref Alt/, @expanded_header), $otherinfo?"\tOtherinfo":"", "\n";
	}
	
	for my $var(&chr_sort(keys %varanno)) {
		my @oneline;
		my @var = split (/\s+/, $var);
		for my $item (@header) {
			if ($csvout) {
				if ($item eq 'ljb_all') {
					push @oneline,($varanno{$var}{$item} || join (",", ($nastring) x 11));	#value is already comma-delimited
				} else {
					push @oneline,(defined $varanno{$var}{$item}) ? qq/"$varanno{$var}{$item}"/ : $nastring;
				}
			} else {
				if ($item eq 'ljb_all') {
					if ($varanno{$var}{$item}) {
						for my $nextscore (split (/,/, $varanno{$var}{$item})) {
							push @oneline, $nextscore;
						}
					} else {
						for (1 .. 11) {
							push @oneline, $nastring;
						}
					}
				} else {
					push @oneline,(defined $varanno{$var}{$item}) ? $varanno{$var}{$item} : $nastring;	#value of $varanno{$var}{$item} could be zero
				}
			}
		}
		if ($otherinfo) {
			my @otherinfo = split (/\n/, $varanno{$var}{otherinfo});
			for my $nextinfo (@otherinfo) {
				if ($csvout) {
					my @var = split (/\s+/, $var);
					print OUT join (",", @var, @oneline, qq/"$nextinfo"/), "\n";
				} else {
					my @var = split (/\s+/, $var);
					print OUT join ("\t", @var, @oneline, $nextinfo), "\n";
				}
			}
		} else {
			if ($csvout) {
				print OUT join (",", @var, @oneline), "\n";
			} else {
				print OUT join ("\t", @var, @oneline), "\n";
			}
		}
	}
	close (OUT);
}

sub printOrigOutput {
	my $final_out;
	if ($csvout) {
		$final_out="$outfile.${buildver}_multianno.csv";
	} else {
		$final_out="$outfile.${buildver}_multianno.txt";
	}
	open OUT,">",$final_out or die "Cannot write to $final_out: $!\n";
	print STDERR "NOTICE: output file is written to $final_out\n";
	
	my @expanded_header;
	for my $i (0 .. @header-1) {
		if ($header[$i] eq 'ljb_all') {
			push @expanded_header, qw/LJB_PhyloP LJB_PhyloP_Pred LJB_SIFT LJB_SIFT_Pred LJB_PolyPhen2 LJB_PolyPhen2_Pred LJB_LRT LJB_LRT_Pred LJB_MutationTaster LJB_MutationTaster_Pred LJB_GERP++/;
		} else {
			push @expanded_header, $header[$i];
		}
	}
	
	if ($csvout) {
		print OUT join(",", qw/Chr Start End Ref Alt/, @expanded_header), $otherinfo?",Otherinfo":"", "\n";
	} else {
		print OUT join("\t", qw/Chr Start End Ref Alt/, @expanded_header), $otherinfo?"\tOtherinfo":"", "\n";
	}
	
	open (FH, $queryfile) or die "Error: cannot read from inputfile $queryfile: $!\n";
	while (<FH>) {
		s/[\r\n]+$//;
		m/^(\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*)/ or next;
		my ($varstring, $info) = ($1, $2);
		my @varstring = split (/\s+/, $varstring);
		$varstring = join ("\t", @varstring);
		
		my @oneline;
		for my $item (@header) {
			if ($csvout) {
				if ($item eq 'ljb_all') {
					push @oneline,($varanno{$varstring}{$item} || join (",", ($nastring) x 11));	#value is already comma-delimited
				} else {
					push @oneline,(defined $varanno{$varstring}{$item}) ? qq/"$varanno{$varstring}{$item}"/ : $nastring;	#value of $varanno{$varstring}{$item} could be zero
				}
			} else {
				if ($item eq 'ljb_all') {
					if ($varanno{$varstring}{$item}) {
						for my $nextscore (split (/,/, $varanno{$varstring}{$item})) {
							push @oneline, $nextscore;
						}
					} else {
						for (1 .. 11) {
							push @oneline, $nastring;
						}
					}
				} else {
					push @oneline, (defined $varanno{$varstring}{$item})? $varanno{$varstring}{$item} : $nastring;	#value of $varanno{$varstring}{$item} could be zero
				}
			}
		}
		if ($csvout) {
			print OUT join (",", @varstring, @oneline), $otherinfo?qq/,"$info"/:"", "\n";
		} else {
			print OUT join ("\t", @varstring, @oneline), $otherinfo?"\t$info":"", "\n";
		}
	}
}


sub readOtherinfo {
	my ($infile) = @_;
	open (FH, $infile) or die "Error: cannot read from inputfile $infile: $!\n";
	while (<FH>) {
		s/[\r\n]+$//;
		m/^(\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*)/ or next;
		my ($varstring, $info) = ($1, $2);
		$varstring =~ s/\s+/\t/g;
		if ($varanno{$varstring}{otherinfo}) {
			if (not $varanno{$varstring}{otherinfo} =~ m/$info/m) {		#treat string as multiple lines
				$varanno{$varstring}{otherinfo} .= "\n$otherinfo";	#multiple input lines have same variant but different otherinfo
			}
		} else {
			$varanno{$varstring}{otherinfo} = $info;
		}
	}
}

sub processArgument {
	$outfile ||= $queryfile;
	
	if (not defined $buildver) {
		$buildver = 'hg18';
		print STDERR "NOTICE: the --buildver argument is set as 'hg18' by default\n";
	}
	$buildver eq 'hg18' or $buildver eq 'hg19' or pod2usage ("Error in argument: the --buildver argument must be 'hg18' or 'hg19'");
	
	not defined $checkfile and $checkfile = 1;
	
	defined $nastring or $nastring = '';
	
	if (not $protocol) {
		$operation and pod2usage ("Error in argument: you must specify --protocol if you specify --operation");
		if ($buildver eq 'hg18') {
			$protocol = 'gene,phastConsElements44way,genomicSuperDups,esp6500si_all,1000g2012apr_all,snp135,avsift,ljb_all';
			$operation = 'g,r,r,f,f,f,f,f';
			print STDERR "NOTICE: the --protocol argument is set as 'gene,phastConsElements44way,genomicSuperDups,esp6500si_all,1000g2012apr_all,snp137,avsift,ljb_all' by default\n";
		} elsif ($buildver eq 'hg19') {
			$protocol = 'gene,phastConsElements46way,genomicSuperDups,esp6500si_all,1000g2012apr_all,snp137,avsift,ljb_all';
			$operation = 'g,r,r,f,f,f,f,f';
			print STDERR "NOTICE: the --protocol argument is set as 'gene,phastConsElements44waygenomicSuperDups,esp6500si_all,1000g2012apr_all,snp137,avsift,ljb_all' by default\n";
		}
	}
	
	if ($protocol =~ m/\bgeneric\b/) {
		$genericdbfile or pod2usage ("Error in argument: please specify -genericdbfile argument when 'generic' operation is specified");
	}
	
	#additional preparation work
	@protocol = split (/,/, $protocol);
	@operation = split (/,/, $operation);
	@protocol == @operation or pod2usage ("Error in argument: different number of elements are specified in --protocol and --operation argument");
	for my $op (@operation) {
		$op =~ m/^g|r|f|m$/ or pod2usage ("Error in argument: the --operation argument must be comma-separated list of 'g', 'r', 'f' or 'm'");
	}
		
	my %uniq_protocol;
	for (@protocol) {
		$uniq_protocol{$_}++;
	}
	if ($uniq_protocol{generic}) {
		$genericdbfile or pod2usage ("Error in argument: please specify -genericdbfile argument when 'generic' protocol is specified");
		@genericdbfile = split (/,/, $genericdbfile);
		@genericdbfile == $uniq_protocol{generic} or pod2usage ("Error in argument: you specified $uniq_protocol{generic} 'generic' in 'protocol' argument, but only ${\(scalar @genericdbfile)} filenames in 'genericdbfile' argument");
	}
	if ($uniq_protocol{gff3}) {
		$gff3dbfile or pod2usage ("Error in argument: please specify -gff3dbfile argument when 'gff3' protocol is specified");
		@gff3dbfile = split (/,/, $gff3dbfile);
		@gff3dbfile == $uniq_protocol{gff3} or pod2usage ("Error in argument: you specified $uniq_protocol{gff3} 'gff3' in 'protocol' argument, but only ${\(scalar @gff3dbfile)} filenames in 'gff3dbfile' argument");
	}
	if ($uniq_protocol{vcf}) {
		$vcfdbfile or pod2usage ("Error in argument: please specify -vcfdbfile argument when 'vcf' protocol is specified");
		@vcfdbfile = split (/,/, $vcfdbfile);
		@vcfdbfile == $uniq_protocol{vcf} or pod2usage ("Error in argument: you specified $uniq_protocol{vcf} 'vcf' in 'protocol' argument, but only ${\(scalar @vcfdbfile)} filenames in 'vcfdbfile' argument");
	}
	if ($uniq_protocol{bed}) {
		$bedfile or pod2usage ("Error in argument: please specify -bedfile argument when 'bed' protocol is specified");
		@bedfile = split (/,/, $bedfile);
		@bedfile == $uniq_protocol{bed} or pod2usage ("Error in argument: you specified $uniq_protocol{bed} 'bed' in 'protocol' argument, but only ${\(scalar @bedfile)} filenames in 'bedfile' argument");
	}

	#prepare PATH environmental variable
	my $path = File::Basename::basename ($0);
	$path and $ENV{PATH} = "$path:$ENV{PATH}";		#set up the system executable path to include the path where this program is located in
}


sub chr_sort
{
	#sort chr1-22 numerically, X and others alphabetically
	my @varstring=@_;
	my @num_alpha_sorted;
	my ($num_tmp,$alpha_tmp)=("tmp_num_$$","tmp_alpha_$$");
	
	push @unlink,$num_tmp,$alpha_tmp;
	
	open NUM,">",$num_tmp or die "Cannot open $num_tmp: $!\n";
	open ALPHA,">",$alpha_tmp or die "Cannot open $alpha_tmp: $!\n";
	
	for (@varstring)
	{
		if (/^\d/)
		{
			print NUM "$_\n";
		} else
		{
			print ALPHA "$_\n";
		}
	}
	close NUM;
	close ALPHA;
	
	open NUM,"sort -n $num_tmp |" or warn "Cannot open pipe to 'sort': $!\n";
	open ALPHA,"sort -k1 -d $alpha_tmp | sort -k2,5 -n - |" or warn "Cannot open pipe to 'sort': $!\n";
	
	while (<NUM>)
	{
		chomp;
		push @num_alpha_sorted,$_;
	}
	close NUM;
	while (<ALPHA>)
	{
		chomp;
		push @num_alpha_sorted,$_;
	}
	close ALPHA;
	
	unlink ("tmp_num_$$","tmp_alpha_$$");
	return @num_alpha_sorted; 
}

#gene annotations
sub geneOperation {
	my ($protocol) = @_;
	#generate gene anno
	my $sc;
	$sc = "annotate_variation.pl -geneanno -buildver $buildver -dbtype $protocol -outfile $outfile -exonsort $queryfile $dbloc";
	system ($sc) and die "Error running system command: <$sc>\n";
	
	#read in gene anno
	my $anno_outfile="$outfile.variant_function";
	my $e_anno_outfile="$outfile.exonic_variant_function";
	
	open (FUNCTION, "<",$anno_outfile) or die "Error: cannot read from $anno_outfile: $!\n";	
	open (EFUNCTION,"<",$e_anno_outfile) or die "Error: cannot read from $e_anno_outfile: $!\n";
	
	push @header,qw/Func Gene ExonicFunc AAChange/; #header
	while (<FUNCTION>) 
	{
		s/[\r\n]+$//;
		m/^(\S+)\t([^\t]+)\t(\S+\s+\S+\s+\S+\s+\S+\s+\S+).*/ or die "Error: invalid record found in annovar outputfile: <$_>\n";
		my ($function, $gene, $varstring) = ($1, $2, $3);
		$varstring =~ s/\s+/\t/g;
		$varanno{$varstring}{Func}=$function;
		$varanno{$varstring}{Gene}=$gene;
	}
	close FUNCTION;
	while (<EFUNCTION>)
	{
		m/^line\d+\t([^\t]+)\t(\S+)\t(\S+\s+\S+\s+\S+\s+\S+\s+\S+)/ or die "Error: invalid record found in annovar outputfile 2: <$_>\n";
		my ($efunc, $aachange, $varstring) = ($1, $2, $3);
		my @aachange = split (/:|,/, $aachange);

		$varanno{$varstring}{ExonicFunc}=$efunc;
		if ($alltranscript) {
			$varanno{$varstring}{AAChange}=$aachange;
		} else {
			if (@aachange >= 5) 
			{
			    $varanno{$varstring}{AAChange}="$aachange[1]:$aachange[3]:$aachange[4]"; #only output aachange in first transcript
			} else 
			{
			    $varanno{$varstring}{AAChange}=$aachange;		#aachange could be "UNKNOWN"
			}
		}
	}
	close EFUNCTION;
	push @unlink, $anno_outfile, $e_anno_outfile;
}







sub regionOperation {
	my ($dbtype, $dbtype1) = @_;
	my $sc = "annotate_variation.pl -regionanno -dbtype $dbtype -buildver $buildver -outfile $outfile $queryfile $dbloc";
	print STDERR "\nNOTICE: Running with system command <$sc>\n";
	system ($sc) and die "Error running system command: <$sc>\n";

	
	open (FH, "$outfile.${buildver}_$dbtype1") or die "Error: cannot open file\n";
	while (<FH>) 
	{
		m/^([^\t]+)\t(\S+)\t(\S+\s+\S+\s+\S+\s+\S+\s+\S+).*/ or die "Error: invalid record found in annovar outputfile: \n";
		my ($db,$anno,$varstring)=($1,$2,$3);
		$varstring =~ s/\s+/\t/g;
		#preprocess $anno
		$varanno{$varstring}{$db}=$anno;
	}
	close (FH);
	push @header,$dbtype;
	push @unlink, "$outfile.${buildver}_$dbtype1";
}

sub filterOperation {
	my ($dbtype, $dbtype1) = @_;
	my $sc = "annotate_variation.pl -filter -dbtype $dbtype -buildver $buildver -outfile $outfile $queryfile $dbloc";
	
	if ($dbtype =~ m/^ljb\d*_all/) {
		$sc .= " -otherinfo";
	}
	print STDERR "\nNOTICE: Running  with system command <$sc>\n";
	system ($sc) and die "Error running system command: <$sc>\n";

	
	open (FH, "$outfile.${buildver}_${dbtype1}_dropped") or die "Error: cannot open file\n";
	while (<FH>) 
	{
		m/^([^\t]+)\t(\S+)\t(\S+\s+\S+\s+\S+\s+\S+\s+\S+).*/ or die "Error: invalid record found in annovar outputfile\n";
		my ($db,$anno,$varstring)=($1,$2,$3);
		$varstring =~ s/\s+/\t/g;
		#preprocess $anno
		$varanno{$varstring}{$db}=$anno;
	}
	close (FH);
	push @header,$dbtype;
	push @unlink, "$outfile.${buildver}_${dbtype1}_dropped", "$outfile.${buildver}_${dbtype1}_filtered";
}

sub proxyDBType {
	my @db_names = @_;
	#    my @db_for_check;
	
	#    map {push @db_for_check,"${buildver}_$_.txt" } @db_names;
	#to overcome case-sensitive matching problem, check file existence case-INsensitively
	#    my @all_db=glob File::Spec->catfile ($dbloc,"*");
	#    my $all_db_string = join (',',@all_db);
	
	#    for (@db_for_check)
	#    {
	#	$all_db_string =~ m/$_/i or die "Error: the required database file $_ does not exist. Please download it via -downdb argument by annotate_variation.pl.\n";
	#    }
	my %dbalias=(
		'gene'=>'refGene', 
		'refgene'=>'refGene', 
		'knowngene'=>'knownGene', 
		'ensgene'=>'ensGene', 
		'band'=>'cytoBand', 
		'cytoband'=>'cytoBand', 
		'tfbs'=>'tfbsConsSites', 
		'mirna'=>'wgRna',
		'mirnatarget'=>'targetScanS', 
		'segdup'=>'genomicSuperDups', 
		'omimgene'=>'omimGene', 
		'gwascatalog'=>'gwasCatalog',
		'1000g_ceu'=>'CEU.sites.2009_04', 
		'1000g_yri'=>'YRI.sites.2009_04', 
		'1000g_jptchb'=>'JPTCHB.sites.2009_04',
		'1000g2010_ceu'=>'CEU.sites.2010_03', 
		'1000g2010_yri'=>'YRI.sites.2010_03', 
		'1000g2010_jptchb'=>'JPTCHB.sites.2010_03',
		'1000g2010jul_ceu'=>'CEU.sites.2010_07', 
		'1000g2010jul_yri'=>'YRI.sites.2010_07', 
		'1000g2010jul_jptchb'=>'JPTCHB.sites.2010_07',
		'1000g2010nov_all'=>'ALL.sites.2010_11', 
		'1000g2011may_all'=>'ALL.sites.2011_05'
	);
    
	for (@db_names) {
		$_ = $dbalias{$_} || $_;
		if (m/^1000g(20\d\d)([a-z]{3})_([a-z]+)$/) {
			my %monthhash = ('jan'=>'01', 'feb'=>'02', 'mar'=>'03', 'apr'=>'04', 'may'=>'05', 'jun'=>'06', 'jul'=>'07', 'aug'=>'08', 'sep'=>'09', 'oct'=>'10', 'nov'=>'11', 'dec'=>'12');
			$_ = uc($3) . ".sites." . $1 . '_' . $monthhash{$2};
			$monthhash{$2} or die "Error: the '$_' operation does not contain a valid month abbreviation\n";
		}
	}
	for (@db_names) {
		m/^mce(\d+way)$/ and $_ = "phastConsElements$1";		#for backward compatibility in ANNOVAR
	}
	return @db_names;
}

sub checkFileExistence {    
	my @db_names = @_;
	my @genericdbfile1 = @genericdbfile;
	my @vcfdbfile1 = @vcfdbfile;
	my @bedfile1 = @bedfile;
	my @gff3dbfile1 = @gff3dbfile;
	for my $i (0 .. @db_names-1) {
		my $dbfile;
		if ($db_names[$i] eq 'generic') {
			$dbfile = File::Spec->catfile ($dbloc, shift @genericdbfile1);
		} elsif ($db_names[$i] eq 'vcf') {
			$dbfile = File::Spec->catfile ($dbloc, shift @vcfdbfile1);
		} elsif ($db_names[$i] eq 'bed') {
			$dbfile = File::Spec->catfile ($dbloc, shift @bedfile1);
		} elsif ($db_names[$i] eq 'gff3') {
			$dbfile = File::Spec->catfile ($dbloc, shift @gff3dbfile1);
		} else {
			$dbfile = File::Spec->catfile ($dbloc, "${buildver}_$db_names[$i].txt");
		}
		-f $dbfile or die "Error: the required database file $dbfile does not exist.\n";
	}
}

=head1 SYNOPSIS

 table_annovar.pl [arguments] <query-file> <database-location>

 Optional arguments:
        -h, --help                      print help message
        -m, --man                       print complete documentation
        -v, --verbose                   use verbose output
            --protocol <string>		comma-delimited strong specifying database protocol
            --operation <string>	comma-delimited string specifying type of operation
            --outfile <string>		output file name prefix
            --buildver <string>		genome build version (default: hg18)
            --remove			remove all temporary files
            --(no)checkfile		check if database file exists (default: ON)
            --genericdbfile <files>	specify comma-delimited generic db files
            --gff3dbfile <files>	specify comma-delimited GFF3 files
            --bedfile <files>		specify comma-delimited BED files
            --vcfdbfile <files>		specify comma-delimited VCF files
            --otherinfo			print out otherinfo (infomration after fifth column in queryfile)
            --alltranscript		print out all transcripts for exonic variants (default: first transcript only)
            --sortout			output is sorted by Chr and Start (default: same order as query)
            --nastring <string>		string to display when a score is not available (default: null)
            --csvout			generate comma-delimited CSV file (default: tab-delimited txt file)
            

 Function: automatically run a pipeline on a list of variants and summarize 
 their functional effects in a comma-delimited file, to be opened by Excel for 
 manual filtering
 
 Example: #recessive disease
          table_annovar.pl infile humandb/ -protocol gene,phastConsElements44way,genomicSuperDups,esp6500si_all,1000g2012apr_all,snp135,avsift,ljb_all -operation g,r,r,f,f,f,f,f -nastring NA
          table_annovar.pl infile humandb/ -buildver hg19 -protocol gene,phastConsElements44waygenomicSuperDups,esp6500si_all,1000g2012apr_all,snp137,avsift,ljb_all -operation g,r,r,f,f,f,f,f
                  
 Version: $LastChangedDate: 2013-02-08 11:10:50 -0800 (Fri, 08 Feb 2013) $

=head1 OPTIONS

=over 8

=item B<--help>

print a brief usage message and detailed explanation of options.

=item B<--man>

print the complete manual of the program.

=item B<--verbose>

use verbose output.

=item B<--outfile>

the prefix of output file names

=item B<--buildver>

specify the genome build version

=item B<--remove>

remove all temporary files. By default, all temporary files will be kept for 
user inspection, but this will easily clutter the directory.

=item B<--genetype>

specify the gene definition, such as refgene (default), ucsc known gene, ensembl 
gene and gencode gene.

=item B<--maf_threshold>

specify the MAF threshold for allele frequency databases. This argument works 
for 1000 Genomes Project, ESP database and CG (complete genomics) database.

=item B<--checkfile>

the program will check if all required database files exist before execution of annotation

=item B<--genericdbfile>

specify the genericdb file used in -dbtype generic

=item B<--ljb_sift_threshold>

specify the LJB_SIFT threshold for filter operation (default: 0.95)

=item B<--ljb_pp2_threshold>

specify the LJB_PP2 threshold for filter operation (default: 0.85)

=back

=head1 DESCRIPTION

ANNOVAR is a software tool that can be used to functionally annotate a list of 
genetic variants, possibly generated from next-generation sequencing 
experiments. For example, given a whole-genome resequencing data set for a human 
with specific diseases, typically around 3 million SNPs and around half million 
insertions/deletions will be identified. Given this massive amounts of data (and 
candidate disease- causing variants), it is necessary to have a fast algorithm 
that scans the data and identify a prioritized subset of variants that are most 
likely functional for follow-up Sanger sequencing studies and functional assays.

by default, for hg18, the arguments are

variants_reduction.pl x1.avinput humandb -protocol nonsyn_splicing,1000g2010jul_ceu,1000g2010jul_jptchb,1000g2010jul_yri,snp132,esp5400_ea,esp5400_aa,recessive -operation g,f,f,f,f,f,f,m

for hg19, the arguments are

variants_reduction.pl x1.avinput humandb -protocol nonsyn_splicing,1000g2012feb_all,snp135,esp5400_ea,esp5400_aa,recessive -operation g,f,f,f,m


ANNOVAR is freely available to the community for non-commercial use. For 
questions or comments, please contact kai@openbioinformatics.org.


=cut